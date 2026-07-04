import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="API de Notas Markdown",
    description="API para gerenciamento, validação e renderização de notas em Markdown.",
    version="0.2.0"
)

class UploadResponse(BaseModel):
    filename: str
    path: str
    size: int

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "API de notas Markdown funcionando!"
    }

@app.post("/notes/upload", response_model=UploadResponse)
async def upload_note(file: UploadFile = File(...)):
    filename = file.filename
    
    
    if not (filename.endswith(".md") or filename.endswith(".markdown")):
        raise HTTPException(
            status_code=400,
            detail="Extensão de arquivo inválida. Apenas arquivos .md ou .markdown são aceitos."
        )
    
    content = await file.read()
    size = len(content)
    
    
    file_path = filename
    
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao salvar o arquivo: {str(e)}"
        )
        
    return UploadResponse(
        filename=filename,
        path=os.path.abspath(file_path),
        size=size
    )