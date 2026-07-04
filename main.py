import os
import re
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(
    title="API de Notas Markdown",
    description="API para gerenciamento, validação e verificação gramatical de notas em Markdown.",
    version="0.3.0"
)


tool = None

def get_grammar_tool():
    global tool
    if tool is None:
        try:
            import language_tool_python
            tool = language_tool_python.LanguageTool('pt-BR')
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao inicializar o serviço de gramática (certifique-se de ter o Java instalado): {str(e)}"
            )
    return tool


# --- Modelos Pydantic ---

class UploadResponse(BaseModel):
    filename: str
    path: str
    size: int

class GrammarCheckRequest(BaseModel):
    content: str

class GrammarError(BaseModel):
    message: str
    suggestions: List[str]
    offset: int
    context: str


# --- Funções Auxiliares ---

def strip_markdown(text: str) -> str:
    """
    Remove elementos básicos de formatação Markdown para deixar o texto limpo,
    reduzindo ruídos e falsos positivos para a análise gramatical.
    """
    
    text = re.sub(r'```[\s\S]*?```', '', text)
    
    text = re.sub(r'`[^`]+`', '', text)
    
    text = re.sub(r'#+\s*(.*)', r'\1', text)
    
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text)
    
    text = re.sub(r'\*\*([^*]+)\*\*|__([^_]+)__', r'\1\2', text)
    text = re.sub(r'\*([^*]+)\*|_([^_]+)_', r'\1\2', text)
    
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    return text


# --- Endpoints ---

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

@app.post("/notes/check-grammar", response_model=List[GrammarError])
async def check_grammar(payload: GrammarCheckRequest):
    
    clean_text = strip_markdown(payload.content)
    
    if not clean_text.strip():
        return []
    
    
    checker = get_grammar_tool()
    
    try:
        matches = checker.check(clean_text)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar a verificação de gramática: {str(e)}"
        )
    
    errors = []
    for match in matches:
        errors.append(GrammarError(
            message=match.message,
            suggestions=match.replacements[:5],  # Limita a 5 sugestões para manter conciso
            offset=match.offset,
            context=match.context
        ))
        
    return errors