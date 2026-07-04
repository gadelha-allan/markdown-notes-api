import os
import re
import json
import unicodedata
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(
    title="API de Notas Markdown",
    description="API para gerenciamento, validação e verificação gramatical de notas em Markdown.",
    version="0.4.0"
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


class NoteCreateRequest(BaseModel):
    title: str
    content: str
    tags: Optional[List[str]] = []


class NoteResponse(BaseModel):
    title: str
    content: str
    tags: List[str]
    filename: str
    metadata_filename: str
    created_at: str
    size: int


# --- Funções Auxiliares ---

def strip_markdown(text: str) -> str:
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

def slugify(text: str) -> str:
    """
    Gera um slug simplificado a partir de uma string (remove acentos,
    caracteres especiais e converte espaços em hifens).
    """
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)


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
            suggestions=match.replacements[:5],
            offset=match.offset,
            context=match.context
        ))
    return errors

@app.post("/notes", response_model=NoteResponse)
async def create_note(payload: NoteCreateRequest):
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    base_slug = slugify(payload.title) or "nota-sem-titulo"
    base_name = f"{base_slug}-{timestamp}"
    
    md_filename = f"{base_name}.md"
    json_filename = f"{base_name}.json"
    
    created_at_str = datetime.now().isoformat()
    
    
    metadata = {
        "title": payload.title,
        "tags": payload.tags,
        "created_at": created_at_str,
        "md_file": md_filename
    }
    
    try:
        
        with open(md_filename, "w", encoding="utf-8") as md_file:
            md_file.write(payload.content)
            
       
        with open(json_filename, "w", encoding="utf-8") as json_file:
            json.dump(metadata, json_file, ensure_ascii=False, indent=4)
            
    except Exception as e:
        
        for path in [md_filename, json_filename]:
            if os.path.exists(path):
                os.remove(path)
        raise HTTPException(
            status_code=500,
            detail=f"Não foi possível salvar os arquivos da nota: {str(e)}"
        )
        
    return NoteResponse(
        title=payload.title,
        content=payload.content,
        tags=payload.tags or [],
        filename=md_filename,
        metadata_filename=json_filename,
        created_at=created_at_str,
        size=len(payload.content.encode("utf-8"))
    )