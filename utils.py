import os
from typing import List
import time
import hashlib
from langsmith import traceable
from langchain_core.documents import Document as LCDocument
from transformers import AutoTokenizer
from typing import Union
from pathlib import Path
from config import EMBEDDING_TOKEN_LIMIT

@traceable(name="🧼 Sanitizar Metadados")
def sanitize_metadata(metadata: dict) -> dict:
    """Garante que os metadados estejam no formato aceito pelo Pinecone."""
    cleaned = {}
    for k, v in metadata.items():
        if isinstance(v, (str, int, float, bool)):
            cleaned[k] = v
        elif isinstance(v, list) and all(isinstance(i, str) for i in v):
            cleaned[k] = v
        else:
            cleaned[k] = str(v)
    return cleaned

@traceable(name="✂️ Ajustar Chunks por Token", metadata={"limite_tokens": EMBEDDING_TOKEN_LIMIT})
def adjust_chunks_to_token_limit(docs: List[LCDocument], max_tokens: int) -> List[LCDocument]:
    adjusted = []
    for doc in docs:
        sub_chunks = split_text_by_token_limit(doc.page_content, max_tokens=max_tokens)
        for chunk in sub_chunks:
            adjusted.append(LCDocument(page_content=chunk, metadata=doc.metadata))
    return adjusted

@traceable(name="🧮 Contar Tokens")
def count_tokens(text: str, model_name: str = "intfloat/multilingual-e5-large") -> int:
    """Conta quantos tokens o texto possui com base no modelo informado."""
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return len(tokenizer.encode(text))

@traceable(name="✂️ Quebrar Texto por Limite de Tokens")
def split_text_by_token_limit(text: str, max_tokens: int = 512, model_name: str = "intfloat/multilingual-e5-large") -> List[str]:
    """Divide o texto em partes menores respeitando o limite de tokens do modelo."""
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokens = tokenizer.encode(text, truncation=False)
    
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i + max_tokens]
        chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
        chunks.append(chunk_text.strip())
    
    return chunks

@traceable(name="🔤 Prefixar para E5")
def prefix_documents_for_e5(documents: List[LCDocument]) -> List[LCDocument]:
    """Adiciona prefixo 'passage:' no conteúdo dos documentos (necessário para E5 embeddings)."""
    for doc in documents:
        doc.page_content = f"passage: {doc.page_content.strip()}"
    return documents

def hash_filename(filename: str) -> str:
    """Gera um nome de arquivo hash único baseado no nome original."""
    base, ext = os.path.splitext(filename)
    hashed = hashlib.md5(base.encode()).hexdigest()
    return f"{hashed}{ext}"


def log_time(func):
    """Decorator para medir o tempo de execução de uma função."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        print(f"⏱️ {func.__name__} levou {duration:.2f}s para executar.")
        return result
    return wrapper


def extract_metadata(document: LCDocument) -> str:
    """
    Retorna uma string curta contendo a origem do documento,
    útil para exibição como fonte em respostas da IA.
    """
    meta = document.metadata or {}
    return f"[Origem: {meta.get('source', 'Desconhecida')}]"


def ensure_directory(path: Union[str, Path]) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)

@traceable(name="🧹 Formatador de Resposta")
def format_response(text: str) -> str:
    """Formata a resposta da IA com legibilidade aprimorada."""
    cleaned = text.strip().replace("\r", "").replace("**", "")
    return "\n".join([linha.strip() for linha in cleaned.split("\n") if linha.strip()])

# def format_response(text: str) -> str:
#     """Formata a resposta da IA removendo espaços extras e limpando markdown."""
#     return text.strip().replace("\n\n", "\n")
