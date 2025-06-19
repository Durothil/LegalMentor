# core/setup_langsmith.py
import os

# ───────────── Carregar .env (para backend) ─────────────
# Se você já chama load_dotenv() no backend/api.py, pode pular esta parte.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv não está instalado → ignore, pois vars podem vir do ambiente
    pass

# ───────────── Tentar importar streamlit ─────────────
try:
    import streamlit as st
    try:
        _st_secrets = dict(st.secrets)     # força parse; ignora se arquivo faltar
    except FileNotFoundError:
        _st_secrets = {}
except ImportError:
    _st_secrets = {}

def _get_secret(name: str, default: str | None = None):
    """env var → st.secrets → default"""
    return os.getenv(name) or _st_secrets.get(name, default)

# ───────────── Ativar tracing se flag == "true" ─────────────
tracing_enabled = _get_secret("LANGSMITH_TRACING", "false").lower() == "true"

if tracing_enabled:
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = _get_secret("LANGSMITH_API_KEY", "")
    os.environ["LANGSMITH_ENDPOINT"] = _get_secret("LANGSMITH_ENDPOINT", "")
    os.environ["LANGCHAIN_PROJECT"] = _get_secret("LANGSMITH_PROJECT", "LegalMentor")

    from langsmith import Client
    client = Client(
        api_key=_get_secret("LANGSMITH_API_KEY", ""),
        api_url=_get_secret("LANGSMITH_ENDPOINT", ""),
    )
else:
    client = None
