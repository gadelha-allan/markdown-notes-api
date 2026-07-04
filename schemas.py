from pydantic import BaseModel
from typing import List, Optional

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

class NoteListItem(BaseModel):
    filename: str
    title: str
    created_at: str
    size: int


class DeleteResponse(BaseModel):
    message: str