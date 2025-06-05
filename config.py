from pathlib import Path

# ========== EMBEDDINGS ==========
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-large"
EMBEDDING_TOKEN_LIMIT = 512  # Limite máximo aceito por chunk para embeddings

# ========== LLM ==========
LLM_MODEL_NAME = "claude-sonnet-4-20250514"
TOKEN_LIMIT = 7000  # Limite de tokens no prompt para não ultrapassar o máximo da LLM

# ========== VECTORSTORE / PINECONE ==========
PINECONE_INDEX_NAME = "legalmentor"
PINECONE_BATCH_SIZE = 64  # Envio em lotes para o Pinecone (ajustável conforme RAM)

# ========== DIRETÓRIOS ==========
DATA_FOLDER = Path("data")
DOCUMENTS_FOLDER = DATA_FOLDER / "documentos"
INDEX_FOLDER = DATA_FOLDER / "indexes"
