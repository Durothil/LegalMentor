from pathlib import Path

# Nome do modelo de embeddings
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-large"

# Nome do modelo de LLM (Claude)
LLM_MODEL_NAME = "claude-sonnet-4-20250514"

# Limite de tokens seguros no prompt
TOKEN_LIMIT = 7000

# Diretórios padrão de dados
DATA_FOLDER = Path("data")
DOCUMENTS_FOLDER = DATA_FOLDER / "documentos"
INDEX_FOLDER = DATA_FOLDER / "indexes"

PINECONE_INDEX_NAME = "legalmentor"