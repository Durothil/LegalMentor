# frontend/app.py  –  Streamlit → FastAPI
import sys
import requests
import streamlit as st

# ───────────────── Config API ─────────────────
API_URL = "http://localhost:8000"           # ajuste se o backend estiver noutro host/porta

# ─────────── Verificação de versão Python ────
if sys.version_info < (3, 12):
    raise RuntimeError("❌ Este projeto requer Python ≥ 3.12")

# ───────────── Configuração de página ────────
st.set_page_config(page_title="RAG Jurídico", layout="wide")
st.title("📚 RAG Jurídico")
st.subheader("Análise Inteligente de Documentos Jurídicos")

# ───────────── State inicial ─────────────────
if "doc_id"   not in st.session_state: st.session_state.doc_id   = None
if "history"  not in st.session_state: st.session_state.history  = []
if "use_mcp"  not in st.session_state: st.session_state.use_mcp  = False

# ───────────── Sidebar (MCP switch) ──────────
with st.sidebar:
    st.header("⚙️ Configurações")

    st.session_state.use_mcp = st.checkbox(
        "🧠 Usar MCP", value=st.session_state.use_mcp,
        help="Ativa memória + planner (MCP)"
    )

    if st.session_state.use_mcp:
        if st.button("👁️ Ver memória MCP"):
            try:
                mem = requests.get(f"{API_URL}/mcp/memory?last_n=10").json()
                st.write(f"Interações armazenadas: **{mem['memory_size']}**")
                st.json(mem["recent_interactions"])
            except Exception as e:
                st.error(f"Falha ao consultar memória: {e}")

# ───────────── Upload de PDF ─────────────────
uploaded_file = st.file_uploader("📎 Envie um PDF jurídico", type=["pdf"])
if uploaded_file:
    try:
        with st.spinner("Enviando e processando no back-end…"):
            resp = requests.post(
                f"{API_URL}/rag/upload",
                files={"file": (uploaded_file.name, uploaded_file, "application/pdf")}
            )
        resp.raise_for_status()
        st.session_state.doc_id = resp.json()["doc_id"]
        st.success("✅ Documento processado! Agora faça perguntas.")
    except Exception as e:
        st.error(f"❌ Falha no upload/processamento: {e}")

# ────────── Botão para índice existente ──────
st.markdown("### Já tenho documentos indexados")
if st.button("📦 Conectar ao índice existente"):
    try:
        with st.spinner("Conectando…"):
            resp = requests.post(f"{API_URL}/rag/init")
            resp.raise_for_status()
            st.session_state.doc_id = resp.json()["doc_id"]    # sempre 'default'
            st.success("✅ Conectado! Agora faça perguntas.")
    except Exception as e:
        st.error(f"❌ Erro: {e}")

st.divider()

# ───────────── Caixa de pergunta ─────────────
st.subheader("🤖 Faça uma pergunta sobre o documento")

if st.session_state.doc_id:
    # Indicador visual do modo
    modo = "🧠 MCP" if st.session_state.use_mcp else "⚡ RAG"
    st.caption(f"Modo atual: **{modo}**")

    pergunta = st.text_input("Digite sua pergunta aqui")
    if pergunta:
        try:
            with st.spinner("Consultando o back-end…"):
                resp = requests.post(
                    f"{API_URL}/rag/query",
                    json={
                        "doc_id":   st.session_state.doc_id,
                        "pergunta": pergunta,
                        "use_mcp":  st.session_state.use_mcp
                    }
                )
            resp.raise_for_status()
            data      = resp.json()
            resposta  = data.get("answer", "❌ Sem resposta.")
            mcp_on    = data.get("mcp_used", False)

            # Histórico local
            st.session_state.history.append(
                {"question": pergunta, "answer": resposta, "mcp": mcp_on}
            )

            # Exibe resposta
            st.markdown(f"**Você:** {pergunta}")
            st.markdown(f"**IA:** {resposta}")

            # Exibe plano MCP (se houver)
            if mcp_on and data.get("plan"):
                with st.expander("📋 Estratégia MCP"):
                    st.json(data["plan"])

        except Exception as e:
            st.error(f"❌ Erro na consulta: {e}")

else:
    st.info("📎 Faça upload de um PDF ou conecte ao índice existente.")

# ─────────────── Histórico de chat ───────────
if st.session_state.history:
    st.divider()
    st.subheader("🕘 Histórico de Perguntas e Respostas")
    for i, turno in enumerate(st.session_state.history, 1):
        icon = "🧠" if turno.get("mcp") else "⚡"
        st.markdown(f"**{i}. {icon} Você:** {turno['question']}")
        st.markdown(f"**{i}. IA:** {turno['answer']}")
