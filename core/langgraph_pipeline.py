from typing import Dict, Any, List
from langchain.schema import Document as LCDocument
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from typing_extensions import TypedDict
import logging
import time

logger = logging.getLogger(__name__)

class RAGState(TypedDict):
    """Estado compartilhado entre os nós do grafo"""
    query: str
    documents: List[LCDocument]
    answer: str
    metadata: Dict[str, Any]
    step_count: int

class LangGraphRAGPipeline:
    """Pipeline RAG usando LangGraph - Wrapper do pipeline existente"""
    def __init__(self, existing_chain, use_rerank: bool = True):
        self.existing_chain = existing_chain
        self.use_rerank = use_rerank
        # Captura o retriever na inicialização
        if hasattr(existing_chain, 'retriever'):
            self.retriever = existing_chain.retriever
        else:
            raise RuntimeError(
                "Chain existente não expõe 'retriever'. "
                "Defina ou injete o atributo antes de usar LangGraph."
            )
        self.graph = self._build_graph()
    
    def _build_graph(self) -> CompiledStateGraph:
        """Constrói e compila o grafo de nós"""
        workflow = StateGraph(RAGState)
        # 1) Recuperação de documentos
        workflow.add_node("retrieve", self._retrieve_node)
        # 2) Re-ranking opcional (stub)
        if self.use_rerank:
            workflow.add_node("rerank", self._rerank_node)
        # 3) Geração de resposta
        workflow.add_node("generate", self._generate_node)
        # Define fluxo de execução
        workflow.set_entry_point("retrieve")
        if self.use_rerank:
            workflow.add_edge("retrieve", "rerank")
            workflow.add_edge("rerank", "generate")
        else:
            workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)
        return workflow.compile()
    
    def _retrieve_node(self, state: RAGState) -> RAGState:
        """Nó de recuperação de documentos"""
        logger.info(f"🔍 Retrieving documents for query: {state['query']}")
        # invoke retriever usando o novo método para evitar warning de depreciação
        docs = self.retriever.invoke(state['query'], {})
        state['documents'] = docs
        state['step_count'] += 1
        state['metadata']['retrieve_count'] = len(docs)
        logger.info(f"📥 Retrieved {len(docs)} documents")
        return state
    
    def _rerank_node(self, state: RAGState) -> RAGState:
        """Nó de re-ranking (opcional stub)"""
        logger.info("🔄 Reranking documents")
        state['metadata']['rerank_applied'] = True
        state['step_count'] += 1
        logger.info(f"✅ Reranked {len(state['documents'])} documents")
        return state

    def _generate_node(self, state: RAGState) -> RAGState:
        """Nó de geração via LLM sem re-recuperar documentos"""
        logger.info("🤖 Generating response from retrieved documents")
        # Executa apenas a parte de combinação e geração
        # Use o retriever_chain (combine_docs_chain) com as chaves esperadas
        # 'input' para pergunta e 'context' para documentos
        chain = self.existing_chain._chain
        response = chain.invoke({
            "input": state['query'],
            "context": state['documents']
        })
        answer = response.get('answer') or response.get('output') or ''
        state['answer'] = answer
        state['step_count'] += 1
        state['metadata']['generation_complete'] = True
        logger.info("✅ Response generated")
        return state
    
    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Executa o grafo e retorna o resultado no formato compatível"""
        initial_state: RAGState = {
            'query': inputs.get('input') or inputs.get('question', ''),
            'documents': [],
            'answer': '',
            'metadata': {
                'langgraph_used': True,
                'start_time': time.time()
            },
            'step_count': 0
        }
        final_state = self.graph.invoke(initial_state)
        end_time = time.time()
        final_state['metadata']['total_time'] = end_time - final_state['metadata']['start_time']
        final_state['metadata']['total_steps'] = final_state['step_count']
        return {
            'answer': final_state['answer'],
            'source_documents': final_state['documents'],
            'metadata': final_state['metadata']
        }
    
    # Permite chamar diretamente como chain
    __call__ = invoke
