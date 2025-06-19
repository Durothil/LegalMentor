# frontend/app.py  –  Streamlit chamando a API FastAPI
import sys
import requests
import streamlit as st

# ─────────────────── Config API ───────────────────
API_URL = "http://localhost:8000"     # ajuste se o backend estiver em outro host

# ───────────────── Verificação de versão ──────────
if sys.version_info < (3, 12):
    raise RuntimeError("❌ Este projeto requer Python >= 3.12")

# ───────────────── Config. de página ──────────────
st.set_page_config(page_title="RAG Jurídico", layout="wide")
st.title("📚 RAG Jurídico")
st.subheader("Análise Inteligente de Documentos Jurídicos")

# ────────────── Inicialização de estado ───────────
if "doc_id" not in st.session_state:
    st.session_state.doc_id = None
if "history" not in st.session_state:
    st.session_state.history = []

# ───────────────── Upload de PDF ──────────────────
uploaded_file = st.file_uploader("📎 Envie um PDF jurídico", type=["pdf"])

if uploaded_file:
    try:
        with st.spinner("Enviando e processando no back-end..."):
            resp = requests.post(
                f"{API_URL}/rag/upload",
                files={"file": (uploaded_file.name, uploaded_file, "application/pdf")}
            )
        resp.raise_for_status()
        st.session_state.doc_id = resp.json()["doc_id"]
        st.success("✅ Documento processado! Agora faça perguntas.")
    except Exception as e:
        st.error(f"❌ Falha no upload/processamento: {e}")

# ───────────── Botão para índice já existente ────────────
st.markdown("### Já tenho documentos indexados")
if st.button("📦 Iniciar com documentos existentes"):
    with st.spinner("Conectando ao índice existente..."):
        try:
            resp = requests.post(f"{API_URL}/rag/init")
            resp.raise_for_status()
            st.session_state.doc_id = resp.json()["doc_id"]   # 'default'
            st.success("✅ Conectado! Agora faça perguntas.")
        except Exception as e:
            st.error(f"❌ Erro: {e}")

st.divider()

# ───────────────── Caixa de Pergunta ──────────────
st.subheader("🤖 Faça uma pergunta sobre o documento")

if st.session_state.doc_id:
    pergunta = st.text_input("Digite sua pergunta aqui")
    if pergunta:
        try:
            with st.spinner("Consultando o back-end... 🤖"):
                resp = requests.post(
                    f"{API_URL}/rag/query",
                    json={
                        "doc_id": st.session_state.doc_id,
                        "pergunta": pergunta
                    }
                )
            resp.raise_for_status()
            resposta = resp.json().get("answer", "❌ Sem resposta.")
            # histórico
            st.session_state.history.append(
                {"question": pergunta, "answer": resposta}
            )
            # exibe
            st.markdown(f"**Você:** {pergunta}")
            st.markdown(f"**IA:** {resposta}")
        except Exception as e:
            st.error(f"❌ Erro na consulta: {e}")
else:
    st.info("📎 Faça upload de um PDF ou conecte ao índice existente.")

# ──────────────── Histórico de Chat ───────────────
if st.session_state.history:
    st.divider()
    st.subheader("🕘 Histórico de Perguntas e Respostas")
    for i, turno in enumerate(st.session_state.history, 1):
        st.markdown(f"**{i}. Você:** {turno['question']}")
        st.markdown(f"**{i}. IA:** {turno['answer']}")
