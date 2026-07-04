import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Optional
from schemas import (
    UploadResponse,
    GrammarCheckRequest,
    GrammarError,
    NoteCreateRequest,
    NoteResponse,
    NoteListItem,
    DeleteResponse
)
from utils import strip_markdown
from grammar_service import get_grammar_tool
from services import NoteService


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("notes-api")

app = FastAPI(
    title="API de Notas Markdown",
    description="API para gerenciamento, validação e verificação gramatical de notas em Markdown.",
    version="1.0.0"
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erro não tratado detectado no endpoint {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocorreu uma falha interna no processamento desta requisição."}
    )


# --- Endpoints ---

@app.get("/health", tags=["Sistema"])
def health_check():
    return {
        "status": "ok",
        "message": "API de notas Markdown funcionando!"
    }

@app.post("/notes/upload", response_model=UploadResponse, tags=["Notas"])
async def upload_note(file: UploadFile = File(...)):
    content = await file.read()
    return NoteService.save_uploaded_file(file, content)

@app.post("/notes/check-grammar", response_model=List[GrammarError], tags=["Análise"])
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

@app.post("/notes", response_model=NoteResponse, tags=["Notas"])
async def create_note(payload: NoteCreateRequest):
    return NoteService.create_note(
        title=payload.title,
        content=payload.content,
        tags=payload.tags or []
    )

@app.get("/notes", response_model=List[NoteListItem], tags=["Notas"])
def list_notes(
    sort_by: str = Query("date", description="Ordenar por: 'date' ou 'title'"),
    order: str = Query("desc", description="Ordem: 'asc' ou 'desc'"),
    q: Optional[str] = Query(None, description="Filtro opcional de busca por texto no título, tags ou conteúdo")
):
    if sort_by not in ["date", "title"]:
        raise HTTPException(status_code=400, detail="O parâmetro 'sort_by' deve ser 'date' ou 'title'.")
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="O parâmetro 'order' deve ser 'asc' ou 'desc'.")
        
    return NoteService.list_notes(sort_by=sort_by, order=order, q=q)

@app.get("/notes/{filename}/html", response_class=HTMLResponse, tags=["Visualização"])
def get_note_html(filename: str):
    return NoteService.render_note_to_html(filename)

@app.delete("/notes/{filename}", response_model=DeleteResponse, tags=["Notas"])
def delete_note_by_filename(filename: str):
    return NoteService.delete_note(filename)