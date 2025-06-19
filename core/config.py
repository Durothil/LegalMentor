# core/config.py
from pathlib import Path
import os

# ───────────── Carrega .env se existir ─────────────
try:
    from dotenv import load_dotenv
    load_dotenv()  # carrega variáveis da raiz
except ImportError:
    pass  # python-dotenv não instalado → ignora

# ───────────── Tenta ler st.secrets (APENAS se Streamlit estiver disponível) ─────────────
try:
    import streamlit as st
    HAS_STREAMLIT = True
    try:
        _st_secrets = dict(st.secrets)
    except (FileNotFoundError, RuntimeError):
        _st_secrets = {}
except ImportError:
    HAS_STREAMLIT = False
    _st_secrets = {}

def _get_secret(name: str, default: str | None = None):
    """Ordem: env var → st.secrets → default"""
    # Primeiro tenta variável de ambiente
    value = os.getenv(name)
    if value:
        return value
    
    # Se tem Streamlit E está rodando no frontend, tenta secrets
    if HAS_STREAMLIT and _st_secrets:
        return _st_secrets.get(name, default)
    
    # Senão, retorna default
    return default

# ───── Segredos expostos ao restante do código ─────
PINECONE_API_KEY  = _get_secret("PINECONE_API_KEY")
ANTHROPIC_API_KEY = _get_secret("ANTHROPIC_API_KEY")

# Validação importante para o backend
if not PINECONE_API_KEY:
    print("⚠️ PINECONE_API_KEY não encontrada. Configure no .env ou variáveis de ambiente.")
if not ANTHROPIC_API_KEY:
    print("⚠️ ANTHROPIC_API_KEY não encontrada. Configure no .env ou variáveis de ambiente.")

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