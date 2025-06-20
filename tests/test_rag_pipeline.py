import sys, types
import pytest

# Helper to create dummy modules
def stub_module(name, attrs=None):
    m = types.ModuleType(name)
    attrs = attrs or {}
    for k, v in attrs.items():
        setattr(m, k, v)
    return m

# Stub heavy external modules before importing rag_pipeline
sys.modules['streamlit'] = stub_module('streamlit')
sys.modules['streamlit.delta_generator'] = stub_module('streamlit.delta_generator')
sys.modules['streamlit.cursor'] = stub_module('streamlit.cursor')
sys.modules['streamlit.runtime'] = stub_module('streamlit.runtime')
sys.modules['streamlit.runtime.runtime'] = stub_module('streamlit.runtime.runtime')
sys.modules['streamlit.proto'] = stub_module('streamlit.proto')
sys.modules['streamlit.proto.BackMsg_pb2'] = stub_module('streamlit.proto.BackMsg_pb2')

sys.modules['langchain_huggingface'] = stub_module('langchain_huggingface', {'HuggingFaceEmbeddings': type('HuggingFaceEmbeddings', (), {'__init__': lambda self, model_name: None})})
sys.modules['langchain_core.vectorstores'] = stub_module('langchain_core.vectorstores', {'VectorStore': type('VectorStore', (), {})})
sys.modules['langchain_community.vectorstores'] = stub_module('langchain_community.vectorstores', {'Pinecone': type('PineconeLang', (), {'from_documents': staticmethod(lambda *args, **kwargs: None)})})
sys.modules['pinecone'] = stub_module('pinecone', {'Pinecone': type('Pinecone', (), {'__init__': lambda self, api_key: None, 'list_indexes': lambda self: types.SimpleNamespace(names=[])})})
sys.modules['langchain_core.documents'] = stub_module('langchain_core.documents', {'Document': type('LCDocument', (), {})})
sys.modules['langchain_anthropic'] = stub_module('langchain_anthropic', {'ChatAnthropic': type('ChatAnthropic', (), {'__init__': lambda self, *args, **kwargs: None})})
sys.modules['langchain_core.prompts'] = stub_module('langchain_core.prompts', {'ChatPromptTemplate': type('ChatPromptTemplate', (), {'from_template': staticmethod(lambda t: None)})})

# Chain modules
tmp = stub_module('langchain.chains.combine_documents.stuff', {'create_stuff_documents_chain': lambda *args, **kwargs: None})
sys.modules['langchain.chains.combine_documents.stuff'] = tmp
sys.modules['langchain.chains.retrieval'] = stub_module('langchain.chains.retrieval', {'create_retrieval_chain': lambda *args, **kwargs: None})

# Docling stubs
sys.modules['langchain_docling'] = stub_module('langchain_docling', {'DoclingLoader': type('DoclingLoader', (), {'__init__': lambda self, file_path, export_type: None, 'load': lambda self: []})})
sys.modules['langchain_docling.loader'] = stub_module('langchain_docling.loader', {'ExportType': type('ExportType', (), {'DOC_CHUNKS': None})})

# LangSmith stub
def _noop(f): return f
sys.modules['langsmith'] = stub_module('langsmith', {'traceable': lambda name=None, **kwargs: _noop})

# Stub core submodules
def dummy_layout(file_path): return []
sys.modules['core.layout_ocr'] = stub_module('core.layout_ocr', {'layout_ocr_from_pdf': dummy_layout})
sys.modules['core.utils'] = stub_module('core.utils', {
    'sanitize_metadata': lambda md: md,
    'log_time': lambda f: f,
    'prefix_documents_for_e5': lambda docs: docs,
    'count_tokens': lambda text, model_name: 0,
    'format_response': lambda ans: ans,
    'adjust_chunks_to_token_limit': lambda docs, limit: docs,
})
sys.modules['core.config'] = stub_module('core.config', {
    'EMBEDDING_MODEL_NAME': 'embed_model',
    'LLM_MODEL_NAME': 'llm_model',
    'TOKEN_LIMIT': 100,
    'PINECONE_INDEX_NAME': 'idx',
    'EMBEDDING_TOKEN_LIMIT': 1000,
    'PINECONE_BATCH_SIZE': 10,
    'PINECONE_API_KEY': 'key',
    'ANTHROPIC_API_KEY': 'anthro_key'
})
sys.modules['core.setup_langsmith'] = stub_module('core.setup_langsmith', {'tracing_enabled': False})

# Now import the module under test
from core import rag_pipeline
from core.rag_pipeline import (
    _invoke_core,
    load_documents_with_docling,
    create_or_load_vectorstore,
    create_rag_chain
)

# Dummy classes for testing
class DummyChain:
    def __init__(self): self.invoked_with = None
    def invoke(self, inputs): self.invoked_with = inputs; return {"answer": "raw output", "foo": "bar"}

class DummyVectorStore:
    def __init__(self): self.retriever = "dummy_retriever"
    def as_retriever(self, search_type, search_kwargs):
        assert search_type == "mmr"
        assert isinstance(search_kwargs, dict) and "k" in search_kwargs
        return self.retriever

# Disable LangSmith tracing fixture
@pytest.fixture(autouse=True)
def disable_tracing(monkeypatch):
    monkeypatch.setattr(rag_pipeline, "tracing_enabled", False)

# Tests
def test_invoke_core_formats_answer(monkeypatch):
    monkeypatch.setattr(rag_pipeline, "count_tokens", lambda text, model_name: 10)
    monkeypatch.setattr(rag_pipeline, "format_response", lambda ans: ans.strip().upper())
    dummy_chain = DummyChain()
    output = _invoke_core(dummy_chain, {"input": "abc"}, "template {context}{input}")
    assert output["answer"] == "RAW OUTPUT"
    assert dummy_chain.invoked_with == {"input": "abc"}


def test_create_rag_chain(monkeypatch):
    called = {}
    class FakeChatAnthropic:
        def __init__(self, temperature, model_name, api_key, max_tokens):
            called.update({"model_name": model_name})
    monkeypatch.setattr(rag_pipeline, "ChatAnthropic", FakeChatAnthropic)
    monkeypatch.setattr(rag_pipeline, "_invoke_core", lambda chain, inputs, template: {"ok": True})
    vs = DummyVectorStore()
    wrapper = create_rag_chain(vs)
    assert wrapper.invoke({}) == {"ok": True}
    assert called.get("model_name") == rag_pipeline.LLM_MODEL_NAME


def test_load_documents_with_docling(monkeypatch):
    class FakeLoader:
        def __init__(self, file_path, export_type):
            assert file_path == "file.pdf" and export_type == rag_pipeline.ExportType.DOC_CHUNKS
        def load(self): return ["doc1"]
    monkeypatch.setattr(rag_pipeline, "DoclingLoader", FakeLoader)
    docs = load_documents_with_docling("file.pdf", export_type=rag_pipeline.ExportType.DOC_CHUNKS)
    assert docs == ["doc1"]


def test_create_or_load_vectorstore_success(monkeypatch):
    class FakePC:
        def __init__(self, api_key): assert api_key == "key"
        def list_indexes(self):
            class X:
                def names(self):
                    return ["idx"]
            return X()
    monkeypatch.setattr(rag_pipeline, "PineconeLang", type("L", (), {"from_documents": staticmethod(lambda *args, **kwargs: "vs")}))
    # Ensure Pinecone client stub is used for success scenario
    monkeypatch.setattr(rag_pipeline, "Pinecone", FakePC)
    vs = create_or_load_vectorstore("file", documents=[type("D", (), {"metadata": {}})()], embeddings=None)
    assert vs == "vs"


def test_create_or_load_vectorstore_failure(monkeypatch):
    class FakePC2:
        def __init__(self, api_key): pass
        def list_indexes(self): return types.SimpleNamespace(names=[])
    monkeypatch.setattr(rag_pipeline, "Pinecone", FakePC2)
    vs = create_or_load_vectorstore("f", documents=[], embeddings=None)
    assert vs is None
