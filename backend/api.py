# backend/api.py
import sys, pathlib, uuid, shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
# Permite importar módulos que já estão na raiz
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from rag_pipeline import process_document            # usa seu código existente

app = FastAPI(title="LegalMentor API")
app.state.chains = {}                                # memória simples
UPLOAD_DIR = pathlib.Path("uploaded_docs")
UPLOAD_DIR.mkdir(exist_ok=True)

class QueryIn(BaseModel):
    doc_id: str
    pergunta: str

@app.post("/rag/init")
def init_with_existing():
    """
    Cria uma cadeia RAG apenas carregando o índice Pinecone já existente.
    Armazena com doc_id = 'default'.
    """
    chain = process_document(None)          # None → só carregar índice
    if chain is None:
        raise HTTPException(500, "Falha ao carregar índice Pinecone.")
    app.state.chains["default"] = chain
    return {"doc_id": "default"}

@app.post("/rag/upload")
def upload_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Apenas PDF é aceito.")
    doc_path = UPLOAD_DIR / f"{uuid.uuid4()}.pdf"
    shutil.copyfileobj(file.file, doc_path.open("wb"))

    chain = process_document(str(doc_path))     
    app.state.chains[str(doc_path)] = chain
    return {"doc_id": str(doc_path)}

@app.post("/rag/query")
def query(data: QueryIn):
    chain = app.state.chains.get(data.doc_id)
    if not chain:
        raise HTTPException(404, "Documento não encontrado")
    resposta = chain.invoke({"input": data.pergunta})
    return resposta