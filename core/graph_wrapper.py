from .langgraph_pipeline import LangGraphRAGPipeline
from .config import USE_LANGGRAPH
import logging

logger = logging.getLogger(__name__)

def wrap_with_langgraph(existing_chain, use_rerank: bool = True):
    """Factory function to wrap an existing chain with LangGraph if enabled."""
    if not USE_LANGGRAPH:
        logger.info("LangGraph disabled, using original chain")
        return existing_chain
    logger.info("🔗 Wrapping chain with LangGraph")
    return LangGraphRAGPipeline(existing_chain, use_rerank=use_rerank)

class GraphChainWrapper:
    """Wrapper that chooses between the original chain or LangGraph pipeline."""
    def __init__(self, original_chain, use_langgraph: bool = True, use_rerank: bool = True):
        self.original_chain = original_chain
        self.using_langgraph = use_langgraph
        if use_langgraph:
            logger.info("⚙️ Initializing LangGraphRAGPipeline")
            self.active_chain = LangGraphRAGPipeline(original_chain, use_rerank=use_rerank)
        else:
            self.active_chain = original_chain

    def invoke(self, inputs):
        """Executes the chosen chain and annotates metadata."""
        result = self.active_chain.invoke(inputs)
        # Ensure metadata exists
        if 'metadata' not in result:
            result['metadata'] = {}
        result['metadata']['using_langgraph'] = self.using_langgraph
        return result

    __call__ = invoke

    def __getattr__(self, name):
        return getattr(self.active_chain, name)
