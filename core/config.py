# core/config.py
from pathlib import Path
import os

# ───────────── Carrega .env se existir ─────────────
try:
    from dotenv import load_dotenv
    load_dotenv()  # carrega variáveis da raiz
except ImportError:
    pass  # python-dotenv não instalado → ignora

# ───────────── Tenta ler st.secrets (para Streamlit) ─────────────
try:
    import streamlit as st
    try:
        _st_secrets = dict(st.secrets)       # falha se não houver arquivo
    except FileNotFoundError:
        _st_secrets = {}
except ImportError:
    _st_secrets = {}

def _get_secret(name: str, default: str | None = None):
    """env var → st.secrets → default"""
    return os.getenv(name) or _st_secrets.get(name, default)

# ───── Segredos expostos ao restante do código ─────
PINECONE_API_KEY  = _get_secret("PINECONE_API_KEY")
ANTHROPIC_API_KEY = _get_secret("ANTHROPIC_API_KEY")

# ========== EMBEDDINGS ==========
EMBEDDING_MODEL_NAME  = "intfloat/multilingual-e5-large"
EMBEDDING_TOKEN_LIMIT = 512

# ========== LLM ==========
LLM_MODEL_NAME = "claude-sonnet-4-20250514"
TOKEN_LIMIT    = 7000

# ========== PINECONE ==========
PINECONE_INDEX_NAME = "legalmentor"
PINECONE_BATCH_SIZE = 64

# ========== DIRETÓRIOS ==========
DATA_FOLDER      = Path("data")
DOCUMENTS_FOLDER = DATA_FOLDER / "documentos"
INDEX_FOLDER     = DATA_FOLDER / "indexes"
