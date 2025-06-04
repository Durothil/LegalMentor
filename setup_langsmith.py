# langsmith_setup.py
import os
import streamlit as st
from langsmith import Client

# Define se o tracing está ativado
tracing_enabled = st.secrets.get("LANGSMITH_TRACING", "false").lower() == "true"

# Define as variáveis de ambiente esperadas pelo LangSmith
if tracing_enabled:
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = st.secrets["LANGSMITH_API_KEY"]
    os.environ["LANGSMITH_ENDPOINT"] = st.secrets["LANGSMITH_ENDPOINT"]
    os.environ["LANGCHAIN_PROJECT"] = st.secrets.get("LANGSMITH_PROJECT", "LegalMentor")

    client = Client(
        api_key=st.secrets["LANGSMITH_API_KEY"],
        api_url=st.secrets["LANGSMITH_ENDPOINT"],
    )
else:
    client = None
