# core/rag_pipeline.py
from __future__ import annotations

# ─────────────────── Imports internos ───────────────────
from .layout_ocr import layout_ocr_from_pdf
from .utils import (
    sanitize_metadata,
    log_time,
    prefix_documents_for_e5,
    count_tokens,
    format_response,
    adjust_chunks_to_token_limit,
)
from .config import (
    EMBEDDING_MODEL_NAME,
    LLM_MODEL_NAME,
    TOKEN_LIMIT,
    PINECONE_INDEX_NAME,
    EMBEDDING_TOKEN_LIMIT,
    PINECONE_BATCH_SIZE,
    PINECONE_API_KEY,
    USE_LANGGRAPH,
    USE_RERANKING,
    ANTHROPIC_API_KEY,
)
from .setup_langsmith import tracing_enabled

# ────────── Streamlit opcional (dummy se não instalado) ──────────
try:
    import streamlit as st
except ImportError:                         # backend não tem Streamlit
    class _Dummy:
        def __getattr__(self, _):           # qualquer atributo é no-op
            return lambda *a, **kw: None
    st = _Dummy()

# ───────────── Imports externos ─────────────
import logging
from typing import List, Dict, Any
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.vectorstores import VectorStore
from langchain_community.vectorstores import Pinecone as PineconeLang
from pinecone import Pinecone
from langchain_core.documents import Document as LCDocument
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_docling import DoclingLoader
from langchain_docling.loader import ExportType
from langsmith import traceable
from .graph_wrapper import GraphChainWrapper


logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════
@traceable(name="📄 Load Documents (Docling)")
@log_time
def load_documents_with_docling(
    file_path: str,
    export_type: ExportType = ExportType.DOC_CHUNKS
) -> List[LCDocument]:
    loader = DoclingLoader(file_path=file_path, export_type=export_type)
    return loader.load()

# ════════════════════════════════════════════════════════════════
@traceable(name="🧊 Create/Load Vectorstore (Pinecone)")
@log_time
def create_or_load_vectorstore(
    file_path: str,
    documents: List[LCDocument],
    embeddings: HuggingFaceEmbeddings
) -> VectorStore | None:
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index_name = PINECONE_INDEX_NAME

        if index_name not in pc.list_indexes().names():
            logger.error("Index '%s' não existe no Pinecone.", index_name)
            return None

        for doc in documents:
            doc.metadata = sanitize_metadata(doc.metadata)

        return PineconeLang.from_documents(
            documents=documents,
            embedding=embeddings,
            index_name=index_name,
            namespace="default",
            batch_size=PINECONE_BATCH_SIZE,
        )

    except Exception as exc:  # noqa: BLE001
        logger.exception("Erro ao conectar ao Pinecone: %s", exc)
        return None

# ════════════════════════════════════════════════════════════════
def create_rag_chain(vectorstore: VectorStore):
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 20, "fetch_k": 100, "lambda_mult": 0.8},
    )

    llm = ChatAnthropic(
        temperature=0.1,
        model_name=LLM_MODEL_NAME,
        api_key=ANTHROPIC_API_KEY,
        max_tokens=1000,
    )

    template = """
Você é um assistente jurídico especializado. Analise cuidadosamente o seguinte contexto extraído de documentos jurídicos e responda de forma objetiva, sem adicionar informações externas.

Se não souber a resposta, diga "Não encontrei informações suficientes no documento."

<context>
{context}
</context>

Pergunta: {input}

Resposta:
"""
    prompt = ChatPromptTemplate.from_template(template)
    document_chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    class RagChainWrapper:
        def __init__(self, chain):  # noqa: D401
            self._chain = chain

        # ────── Método único (traceable se LangSmith ativo) ──────
        if tracing_enabled:
            @traceable(name="LegalMentor-RAG")
            def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:  # noqa: D401
                return _invoke_core(self._chain, inputs, template)
        else:
            def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                return _invoke_core(self._chain, inputs, template)

        __call__ = invoke

    base_chain = RagChainWrapper(retrieval_chain)
    setattr(base_chain, "retriever", retriever)
    return GraphChainWrapper(
        base_chain,
        use_langgraph=USE_LANGGRAPH,
        use_rerank=USE_RERANKING
    )

# ----------------------------------------------------------------
def _invoke_core(chain, inputs, template):
    approx = count_tokens(
        template.format(context="", input=inputs.get("input", "")),
        model_name=EMBEDDING_MODEL_NAME,
    )
    logger.info("Prompt ~%d tokens (limite %d).", approx, TOKEN_LIMIT)

    output = chain.invoke(inputs)
    if "answer" in output:
        output["answer"] = format_response(output["answer"])
    return output

# ════════════════════════════════════════════════════════════════
@traceable(name="🧩 Pipeline: Processar Documento", metadata={"modelo": EMBEDDING_MODEL_NAME})
@log_time
def process_document(file_path: str | None = None):
    # 1. Carrega & prefixa
    if file_path:
        docs = load_documents_with_docling(file_path)
        if not docs or all(not d.page_content.strip() for d in docs):
            logger.warning("Docling não encontrou texto; usando OCR fallback.")
            docs = layout_ocr_from_pdf(file_path)

        logger.info("📚 Documento carregado com %d chunks.", len(docs))
        docs = prefix_documents_for_e5(docs)
        docs = adjust_chunks_to_token_limit(docs, EMBEDDING_TOKEN_LIMIT)
        logger.info("🔍 Após ajuste: %d chunks.", len(docs))
    else:
        docs = []

    # 2. Embeddings + vectorstore
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    vs = create_or_load_vectorstore(file_path or "default", docs, embeddings)
    if vs is None:
        raise RuntimeError("Vectorstore não pôde ser criado/carregado.")

    # 3. Cadeia RAG
    return create_rag_chain(vs)
