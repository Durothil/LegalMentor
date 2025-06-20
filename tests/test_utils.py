import os
import sys
import types
# Stub streamlit before importing core.utils to prevent Deprecation errors
sys.modules['streamlit'] = types.SimpleNamespace(secrets={})

import types
import shutil
import pytest
import tempfile
types
from pathlib import Path

import core.utils as utils
from types import SimpleNamespace

# Fixture to patch AutoTokenizer
class DummyTokenizer:
    def __init__(self): pass
    def encode(self, text, truncation=False):
        # Return list of single-character tokens
        return list(text)
    def decode(self, tokens, skip_special_tokens=True):
        return ''.join(tokens)

@pytest.fixture(autouse=True)
def patch_tokenizer(monkeypatch):
    dummy = DummyTokenizer()
    # Patch AutoTokenizer.from_pretrained
    monkeypatch.setattr(utils, 'AutoTokenizer', types.SimpleNamespace(from_pretrained=lambda model_name: dummy))
    yield

# Tests for sanitize_metadata
def test_sanitize_metadata_various_types():
    meta = {
        's': 'string',
        'i': 10,
        'f': 3.14,
        'b': True,
        'lst': ['a', 'b'],
        'other': {'x':1}
    }
    cleaned = utils.sanitize_metadata(meta)
    assert cleaned['s'] == 'string'
    assert cleaned['i'] == 10
    assert cleaned['f'] == 3.14
    assert cleaned['b'] is True
    assert cleaned['lst'] == ['a', 'b']
    assert isinstance(cleaned['other'], str)

# Tests for split_text_by_token_limit
def test_split_text_by_token_limit_simple():
    text = 'abcdef'
    parts = utils.split_text_by_token_limit(text, max_tokens=2)
    assert parts == ['ab', 'cd', 'ef']

# Tests for adjust_chunks_to_token_limit
@pytest.mark.parametrize('chunks,limit,expected', [
    ([SimpleNamespace(page_content='abcd', metadata={})], 2, ['ab','cd']),
    ([SimpleNamespace(page_content='', metadata={'m':1})], 10, [''])
])
def test_adjust_chunks_to_token_limit(monkeypatch, chunks, limit, expected):
    # Stub split_text_by_token_limit
    monkeypatch.setattr(utils, 'split_text_by_token_limit', lambda text, max_tokens: expected)
    docs = [SimpleNamespace(page_content='unused', metadata={'m':1})]
    adjusted = utils.adjust_chunks_to_token_limit(docs, limit)
    assert [d.page_content for d in adjusted] == expected
    assert all(d.metadata == {'m':1} for d in adjusted)

# Tests for prefix_documents_for_e5
def test_prefix_documents_for_e5():
    docs = [SimpleNamespace(page_content='text', metadata={})]
    out = utils.prefix_documents_for_e5(docs)
    assert out[0].page_content.startswith('passage: text')

# Tests for hash_filename
def test_hash_filename_ext_and_repeatability():
    name1 = utils.hash_filename('file.txt')
    name2 = utils.hash_filename('file.txt')
    assert name1 == name2
    assert name1.endswith('.txt')
    assert len(name1) > len('.txt')

# Tests for log_time decorator
def test_log_time_decorator(capsys):
    @utils.log_time
    def dummy(x):
        return x * 2
    result = dummy(3)
    captured = capsys.readouterr()
    assert 'dummy levou' in captured.out
    assert result == 6

# Tests for extract_metadata
def test_extract_metadata_with_source_and_default():
    doc = SimpleNamespace(metadata={'source':'ABC'})
    assert utils.extract_metadata(doc) == '[Origem: ABC]'
    doc2 = SimpleNamespace(metadata={})
    assert 'Desconhecida' in utils.extract_metadata(doc2)

# Tests for ensure_directory
def test_ensure_directory(tmp_path):
    d = tmp_path / 'subdir'
    utils.ensure_directory(str(d))
    assert d.exists() and d.is_dir()

# Tests for format_response
def test_format_response_cleanup():
    text = '\n ** Hello **\r\nWorld\n\n'
    out = utils.format_response(text)
    assert 'Hello' in out
    assert 'World' in out
    assert '\r' not in out
    assert '**' not in out
