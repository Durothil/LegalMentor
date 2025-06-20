import os
import sys
import importlib
import types
import pytest

CONFIG_MODULE = 'core.config'

# Utility to reload config with controlled environment and streamlit
def reload_config(monkeypatch, env_vars=None, st_secrets=None, has_streamlit=True):
    # Prevent real dotenv loading
    monkeypatch.setitem(sys.modules, 'dotenv', types.SimpleNamespace(load_dotenv=lambda: None))
    # Remove cached config module
    if CONFIG_MODULE in sys.modules:
        del sys.modules[CONFIG_MODULE]

    # Setup environment variables
    env_vars = env_vars or {}
    monkeypatch.delenv('PINECONE_API_KEY', raising=False)
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    for k, v in env_vars.items():
        monkeypatch.setenv(k, v)

    # Stub or remove streamlit
    if has_streamlit:
        stub_st = types.SimpleNamespace(secrets=st_secrets or {})
        monkeypatch.setitem(sys.modules, 'streamlit', stub_st)
    else:
        if 'streamlit' in sys.modules:
            del sys.modules['streamlit']
        monkeypatch.setitem(sys.modules, 'streamlit', None)

    # Import and reload config module
    importlib.invalidate_caches()
    config = importlib.import_module(CONFIG_MODULE)
    return importlib.reload(config)

def test_get_secret_prefers_env(monkeypatch):
    cfg = reload_config(monkeypatch, env_vars={'PINECONE_API_KEY': 'env_key', 'ANTHROPIC_API_KEY': 'env_anth'})
    assert cfg._get_secret('PINECONE_API_KEY', default='def') == 'env_key'
    assert cfg._get_secret('ANTHROPIC_API_KEY', default='def') == 'env_anth'

def test_get_secret_uses_st_secrets(monkeypatch):
    cfg = reload_config(monkeypatch,
                        env_vars={},
                        st_secrets={'PINECONE_API_KEY': 'st_key', 'ANTHROPIC_API_KEY': 'st_anth'},
                        has_streamlit=True)
    assert cfg._get_secret('PINECONE_API_KEY', default='def') == 'st_key'
    assert cfg._get_secret('ANTHROPIC_API_KEY', default='def') == 'st_anth'

def test_get_secret_default_when_missing(monkeypatch):
    cfg = reload_config(monkeypatch, env_vars={}, st_secrets={}, has_streamlit=False)
    assert cfg._get_secret('PINECONE_API_KEY', default='def') == 'def'
    assert cfg._get_secret('UNKNOWN', default=None) is None

def test_constants_from_config(monkeypatch):
    # Provide env for keys, no st
    cfg = reload_config(monkeypatch, env_vars={'PINECONE_API_KEY': 'x', 'ANTHROPIC_API_KEY': 'y'}, has_streamlit=False)
    assert cfg.PINECONE_API_KEY == 'x'
    assert cfg.ANTHROPIC_API_KEY == 'y'
    # Check other constants
    assert isinstance(cfg.EMBEDDING_MODEL_NAME, str)
    assert isinstance(cfg.LLM_MODEL_NAME, str)
    assert cfg.EMBEDDING_TOKEN_LIMIT > 0
    assert cfg.PINECONE_BATCH_SIZE > 0
    assert isinstance(cfg.DATA_FOLDER, cfg.Path)

def test_warning_printed_when_keys_missing(monkeypatch, capsys):
    # No env, no st
    cfg = reload_config(monkeypatch, env_vars={}, st_secrets={}, has_streamlit=False)
    # Reload prints warnings on import
    # Capture printed output
    captured = capsys.readouterr()
    assert '⚠️ PINECONE_API_KEY não encontrada' in captured.out
    assert '⚠️ ANTHROPIC_API_KEY não encontrada' in captured.out
