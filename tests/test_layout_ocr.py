import sys
import types
import pytest

# Helper to create dummy modules
def stub_module(name, attrs=None):
    m = types.ModuleType(name)
    attrs = attrs or {}
    for k, v in attrs.items():
        setattr(m, k, v)
    return m

# Stub heavy external dependencies
sys.modules['streamlit'] = stub_module('streamlit', {'info': lambda msg: None})
sys.modules['langsmith'] = stub_module('langsmith', {'traceable': lambda name=None, **kw: (lambda f: f)})
sys.modules['transformers'] = stub_module('transformers', {
    'LayoutLMv2Processor': types.SimpleNamespace(
        from_pretrained=lambda x: types.SimpleNamespace(
            __call__=lambda *args, **kwargs: {'input_ids': [], 'attention_mask': []}
        )
    )
})
# Stub PIL.Image for type annotations
sys.modules['PIL'] = stub_module('PIL')
image_mod = stub_module('PIL.Image', {'Image': type('ImageClass', (), {})})
sys.modules['PIL.Image'] = image_mod
# Ensure from PIL import Image returns our stub
setattr(sys.modules['PIL'], 'Image', image_mod)

sys.modules['pytesseract'] = stub_module('pytesseract', {
    'image_to_data': lambda img, output_type, lang: {
        'text': [], 'left': [], 'top': [], 'width': [], 'height': [], 'line_num': []
    },
    'Output': types.SimpleNamespace(DICT=None)
})
sys.modules['pdf2image'] = stub_module('pdf2image', {'convert_from_path': lambda fp, dpi: []})
sys.modules['sentence_transformers'] = stub_module('sentence_transformers', {
    'SentenceTransformer': type('SentenceTransformer', (), {
        '__init__': lambda self, model: None,
        'encode': lambda self, text, convert_to_tensor: text
    })
})
sys.modules['sentence_transformers.util'] = stub_module('sentence_transformers.util', {
    'cos_sim': lambda e1, e2: types.SimpleNamespace(item=lambda: 1.0)
})
sys.modules['langchain_core.documents'] = stub_module('langchain_core.documents', {
    'Document': lambda page_content, metadata: types.SimpleNamespace(
        page_content=page_content,
        metadata=metadata
    )
})
# Utils stubs
sys.modules['core.utils'] = stub_module('core.utils', {
    'split_text_by_token_limit': lambda s, limit: [s],
    'adjust_chunks_to_token_limit': lambda docs, limit: docs
})
sys.modules['core.config'] = stub_module('core.config', {'EMBEDDING_TOKEN_LIMIT': 1000})
sys.modules['core.utils'] = stub_module('core.utils', {
    'split_text_by_token_limit': lambda s, limit: [s],
    'adjust_chunks_to_token_limit': lambda docs, limit: docs
})
sys.modules['core.config'] = stub_module('core.config', {'EMBEDDING_TOKEN_LIMIT': 1000})

# Now import functions under test
from core.layout_ocr import (
    split_legal_chunks_regex,
    adaptive_similarity_threshold,
    group_similar_chunks,
    layout_ocr_from_pdf,
    image_to_layout_chunks
)
from langchain_core.documents import Document as LCDocument

# Tests for split_legal_chunks_regex
... # previous tests ...

# Tests for adaptive_similarity_threshold
def test_adaptive_similarity_threshold():
    assert adaptive_similarity_threshold("short") == 0.80
    long_text = "x" * 300
    assert adaptive_similarity_threshold(long_text) == 0.70

# Tests for group_similar_chunks
def test_group_similar_chunks():
    chunks = [LCDocument(page_content="a", metadata={}), LCDocument(page_content="b", metadata={})]
    result = group_similar_chunks(chunks)
    # Since similarity is stubbed to 1.0, chunks should merge into one
    assert len(result) == 1
    assert "a" in result[0].page_content and "b" in result[0].page_content

# Tests for layout_ocr_from_pdf pipeline
def test_layout_ocr_from_pdf(monkeypatch):
    import core.layout_ocr as lo
    # Stub convert_from_path imported in module to return one fake image
    fake_image = types.SimpleNamespace(size=(100, 100))
    monkeypatch.setattr(lo, 'convert_from_path', lambda fp, dpi: [fake_image])
    # Stub image_to_layout_chunks and grouping on the module
    monkeypatch.setattr(lo, 'image_to_layout_chunks', lambda img, page_number: [LCDocument(page_content="x", metadata={})])
    monkeypatch.setattr(lo, 'group_similar_chunks', lambda docs: docs)
    monkeypatch.setattr(lo, 'adjust_chunks_to_token_limit', lambda docs, limit: docs)

    result = lo.layout_ocr_from_pdf("dummy.pdf")
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].page_content == "x"
