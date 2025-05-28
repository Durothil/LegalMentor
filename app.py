from pathlib import Path
import streamlit as st

from rag_pipeline import process_document

# Configurações de pasta
DATA_FOLDER = Path("data")
DOCUMENTS_FOLDER = DATA_FOLDER / "documentos"
INDEXES_FOLDER = DATA_FOLDER / "indexes"

# Garante que as pastas existem
DOCUMENTS_FOLDER.mkdir(parents=True, exist_ok=True)
INDEXES_FOLDER.mkdir(parents=True, exist_ok=True)

# Configuração da página
st.set_page_config(page_title="RAG Jurídico", layout="wide")
st.title("📚 RAG Jurídico")
st.subheader("Análise Inteligente de Documentos Jurídicos")

# Inicializa session_state
if "rag_chain" not in st.session_state:
    st.session_state.rag_chain = None

if "document_path" not in st.session_state:
    st.session_state.document_path = None

if "history" not in st.session_state:
    st.session_state.history = []  # Lista de dicts {"question": ..., "answer": ...}

# Upload de documento
uploaded_file = st.file_uploader("📎 Envie um PDF jurídico", type=["pdf"])
if uploaded_file:
    try:
        # Salva o arquivo
        file_path = DOCUMENTS_FOLDER / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"✅ Documento '{uploaded_file.name}' salvo em `{file_path}`")
        st.session_state.document_path = file_path
    except Exception as e:
        st.error(f"❌ Falha ao salvar o documento: {e}")

# Se quiser iniciar direto com os dados já indexados no Pinecone
st.markdown("### Ou use os documentos existentes no Pinecone")
if st.button("📦 Iniciar com documentos existentes"):
    try:
        with st.spinner("Conectando com os documentos existentes no Pinecone..."):
            chain = process_document(None)  # passamos None para não carregar novos arquivos
        if chain is None:
            st.error("❌ Não foi possível criar a pipeline RAG.")
        else:
            st.success("✅ RAG iniciado com documentos do Pinecone!")
            st.session_state.rag_chain = chain
            st.session_state.history.clear()
    except Exception as e:
        st.error(f"❌ Erro ao iniciar com documentos do Pinecone: {e}")

# Upload e processamento de novo documento
st.markdown("### Ou envie um novo documento PDF para análise")
if st.session_state.document_path:
    if st.button("🔍 Processar documento"):
        try:
            with st.spinner("Processando documento, aguarde... ⏳"):
                chain = process_document(str(st.session_state.document_path))
            if chain is None:
                st.error("❌ Não foi possível criar a pipeline RAG.")
            else:
                st.success("✅ Documento processado com sucesso!")
                st.session_state.rag_chain = chain
                st.session_state.history.clear()
        except Exception as e:
            st.error(f"❌ Erro ao processar documento: {e}")


st.divider()

# Interface de consulta
st.subheader("🤖 Faça uma pergunta sobre o documento")

if st.session_state.rag_chain:
    pergunta = st.text_input("Digite sua pergunta aqui", key="input")
    if pergunta:
        try:
            with st.spinner("Consultando o documento... 🤖"):
                resultado = st.session_state.rag_chain.invoke({"input": pergunta})
            resposta = resultado.get("answer", "❌ Sem resposta.")
            # Armazena no histórico
            st.session_state.history.append({"question": pergunta, "answer": resposta})
            # Exibe
            st.markdown(f"**Você:** {pergunta}")
            st.markdown(f"**IA:** {resposta}")
        except Exception as e:
            st.error(f"❌ Erro na consulta: {e}")
else:
    st.info("📎 Primeiro carregue e processe um documento para perguntar.")

# Mostrar histórico
if st.session_state.history:
    st.divider()
    st.subheader("🕘 Histórico de Perguntas e Respostas")
    for i, turno in enumerate(st.session_state.history, 1):
        st.markdown(f"**{i}. Você:** {turno['question']}")
        st.markdown(f"**{i}. IA:** {turno['answer']}")
