# backend/api.py
import sys, pathlib, uuid, shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from core.rag_pipeline import process_document
from core.mcp import mcp_instance  # Importa MCP

app = FastAPI(title="LegalMentor API")
app.state.chains = {}
UPLOAD_DIR = pathlib.Path("uploaded_docs")
UPLOAD_DIR.mkdir(exist_ok=True)

class QueryIn(BaseModel):
    doc_id: str
    pergunta: str
    use_mcp: Optional[bool] = False  # Flag opcional

@app.post("/rag/init")
def init_with_existing():
    chain = process_document(None)
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
    
    # Se usar MCP
    if data.use_mcp:
        # 1. Planejar
        plan = mcp_instance.plan(data.pergunta)
        
        # 2. Enriquecer pergunta com contexto
        enriched_question = mcp_instance.enrich_question(data.pergunta)
        
        # 3. Executar
        resposta = chain.invoke({"input": enriched_question})
        
        # 4. Memorizar
        mcp_instance.remember(
            data.pergunta, 
            resposta.get("answer", ""),
            {"plan": plan}
        )
        
        # 5. Adicionar metadados MCP na resposta
        resposta["mcp_used"] = True
        resposta["plan"] = plan
    else:
        # RAG direto (comportamento original)
        resposta = chain.invoke({"input": data.pergunta})
        resposta["mcp_used"] = False
    
    return resposta

# Endpoint opcional para ver memória (REMOVER EM PRODUÇÃO ou adicionar auth)
@app.get("/mcp/memory")
def get_memory(last_n: int = 5):
    """
    Visualiza memória MCP
    ⚠️ ATENÇÃO: Este endpoint está público! 
    Em produção, adicione autenticação ou remova.
    """
    return {
        "memory_size": len(mcp_instance.memory),
        "recent_interactions": mcp_instance.get_serializable_memory(last_n),
        "warning": "Este endpoint deve ser protegido em produção"
    }