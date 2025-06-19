# core/rag_pipeline.py
from __future__ import annotations          # opcional, ajuda com type-hints cíclicos

# ───────────── Imports do próprio core (agora relativos) ─────────────
from . import setup_langsmith               # configura LangSmith
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
    PINECONE_API_KEY,      # ← novo
    ANTHROPIC_API_KEY      # ← novo
)
from .setup_langsmith import tracing_enabled

# ───────────── Imports externos ─────────────
from typing import List, Dict, Any
import streamlit as st
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
    
@traceable(name="📄 Load Documents (Docling)")
@log_time
def load_documents_with_docling(
    file_path: str,
    export_type: ExportType = ExportType.DOC_CHUNKS
) -> List[LCDocument]:
    """
    1° - O DoclingLoader lê o PDF, extrai o texto estruturado em “chunks”
         e retorna uma lista de Documentos.
    """
    loader = DoclingLoader(file_path=file_path, export_type=export_type)
    return loader.load()

@traceable(name="🧊 Create/Load Vectorstore (Pinecone)")
@log_time
def create_or_load_vectorstore(
    file_path: str,
    documents: List[LCDocument],
    embeddings: HuggingFaceEmbeddings
):# -> FAISS:
    """
    Substitui o FAISS por Pinecone.

    3° - Cria ou carrega um índice FAISS:
         - Gera um hash a partir do nome do arquivo para nomear a pasta de índice.
         - Se já existir, carrega; caso contrário, cria e salva o novo índice.
    """
    try:
        # Inicializa cliente Pinecone
        pc = Pinecone(api_key=PINECONE_API_KEY)

        index_name = PINECONE_INDEX_NAME

        # Confere se o index existe
        if index_name not in pc.list_indexes().names():
            st.error(f"Index '{index_name}' não existe no Pinecone.")
            return None

        for doc in documents:
            doc.metadata = sanitize_metadata(doc.metadata)

        # Cria vectorstore com LangChain + Pinecone
        vectorstore = PineconeLang.from_documents(
            documents=documents,
            embedding=embeddings,
            index_name=index_name,
            namespace="default",
            batch_size=PINECONE_BATCH_SIZE  # ou outro valor ideal baseado na RAM . Se estiver passando documentos muito grandes ou muitos documentos, vale usar batch_size
        )

        return vectorstore

    except Exception as e:
        st.error(f"Erro ao conectar ao Pinecone: {e}")
        return None


def create_rag_chain(vectorstore: VectorStore) -> Any:
    """
    4° - Cria o retriever com MMR e configura o LLM ANTHROPIC + Claude,
         monta a cadeia de documentos e retrieval e retorna um wrapper.
    """
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 20, "fetch_k": 100, "lambda_mult": 0.8},
    )

    llm = ChatAnthropic(
        temperature=0.1,
        model_name=LLM_MODEL_NAME,
        api_key=ANTHROPIC_API_KEY,
        max_tokens=1000,  # Resposta gerada
    )
    
    # Prompt padrão com contexto e instruções
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
        """
        Wrapper que:
        a) Estima tokens e alerta se próximo do limite
        b) Invoca o chain original
        c) Exibe metadados e trechos do contexto recuperado
        d) Formata a resposta final
        """
        def __init__(self, chain):
            self._chain = chain

        if tracing_enabled:

            @traceable(name="LegalMentor-RAG")
            def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                approx = count_tokens(
                    template.format(
                        context="",
                        input=inputs.get("input", "")
                    ),
                    model_name=EMBEDDING_MODEL_NAME
                )

                st.info(f"📏 Prompt estimado em ~{approx} tokens (limite configurado: {TOKEN_LIMIT}).")

                if approx > TOKEN_LIMIT:
                    st.warning("Atenção: o prompt está acima do limite seguro e pode causar erro.")

                output = self._chain.invoke(inputs)

                if "answer" in output:
                    output["answer"] = format_response(output["answer"])

                return output
        else:
            def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                approx = count_tokens(
                    template.format(
                        context="",
                        input=inputs.get("input", "")
                    ),
                    model_name=EMBEDDING_MODEL_NAME
                )

                st.info(f"📏 Prompt estimado em ~{approx} tokens (limite configurado: {TOKEN_LIMIT}).")

                if approx > TOKEN_LIMIT:
                    st.warning("Atenção: o prompt está acima do limite seguro e pode causar erro.")

                output = self._chain.invoke(inputs)

                if "answer" in output:
                    output["answer"] = format_response(output["answer"])

                return output

        __call__ = invoke  # permite usar o wrapper como função


    return RagChainWrapper(retrieval_chain)

@traceable(name="🧩 Pipeline: Processar Documento", metadata={"modelo": EMBEDDING_MODEL_NAME})
@log_time
def process_document(file_path: str = None) -> Any:
    """
    6° - Pipeline completo:
         1) Carrega e prefixa documentos
         2) (Opcional) Chunk splitting
         3) Cria/recupera vectorstore Pinecone
         4) Constrói e retorna a cadeia RAG personalizada
    """
    # 1) Load & prefix
    if file_path:
        docs = load_documents_with_docling(file_path)
        if not docs or not isinstance(docs, list) or all(not doc.page_content.strip() for doc in docs):
            st.warning("📄 O Docling não encontrou texto acessível no PDF. Usando OCR avançado com LayoutLM como fallback.")
            docs = layout_ocr_from_pdf(file_path)

        st.info(f"📚 Documento carregado com {len(docs)} chunks estruturados.")

        docs = prefix_documents_for_e5(docs)
        # ⚠️ Ajustar chunks que ultrapassam o limite de tokens
        docs = adjust_chunks_to_token_limit(docs, EMBEDDING_TOKEN_LIMIT)
        st.info(f"🔍 Após ajuste de tokens, total de chunks: {len(docs)}")
    else:
        docs = []


    # 2) (opcional) split: use este passo somente se
    #    – você estiver carregando o documento como um único bloco de texto (por ex. via PdfPlumber / PyPDF2),
    #    – ou se quiser forçar chunks de tamanho fixo diferentes dos produzidos pelo Docling;
    #    Caso contrário, o DoclingLoader com export_type=DOC_CHUNKS já retorna trechos bem estruturados
    #    (títulos, parágrafos, tabelas) e não vale a pena requebrá-los com RecursiveCharacterTextSplitter.
    #
    # Para ativar, basta descomentar a linha abaixo:
    # docs = split_text_into_chunks(docs)

    # 3) embeddings e vectorstore
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    vs = create_or_load_vectorstore(file_path or "default", docs, embeddings)

    # 4) Cria e retorna o wrapper da chain
    return create_rag_chain(vs)
