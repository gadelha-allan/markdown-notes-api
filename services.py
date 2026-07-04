import os
import json
from datetime import datetime
from fastapi import HTTPException, UploadFile
from typing import List, Optional
from utils import slugify, extract_title_from_filename
from schemas import NoteListItem, NoteResponse, UploadResponse

class NoteService:
    @staticmethod
    def save_uploaded_file(file: UploadFile, content: bytes) -> UploadResponse:
        filename = file.filename
        if not (filename.endswith(".md") or filename.endswith(".markdown")):
            raise HTTPException(
                status_code=400,
                detail="Extensão de arquivo inválida. Apenas arquivos .md ou .markdown são aceitos."
            )
        
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
            size=len(content)
        )

    @staticmethod
    def create_note(title: str, content: str, tags: List[str]) -> NoteResponse:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        base_slug = slugify(title) or "nota-sem-titulo"
        base_name = f"{base_slug}-{timestamp}"
        
        md_filename = f"{base_name}.md"
        json_filename = f"{base_name}.json"
        created_at_str = datetime.now().isoformat()
        
        metadata = {
            "title": title,
            "tags": tags,
            "created_at": created_at_str,
            "md_file": md_filename
        }
        
        try:
            with open(md_filename, "w", encoding="utf-8") as md_file:
                md_file.write(content)
                
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
            title=title,
            content=content,
            tags=tags,
            filename=md_filename,
            metadata_filename=json_filename,
            created_at=created_at_str,
            size=len(content.encode("utf-8"))
        )

    @staticmethod
    def list_notes(
        sort_by: str = "date",
        order: str = "desc",
        q: Optional[str] = None
    ) -> List[NoteListItem]:
        notes_list = []
        
        try:
            for item in os.listdir("."):
                if os.path.isfile(item) and (item.endswith(".md") or item.endswith(".markdown")):
                    filepath = os.path.join(".", item)
                    
                    
                    base_name, _ = os.path.splitext(item)
                    json_filepath = f"{base_name}.json"
                    
                    title = extract_title_from_filename(item)
                    tags = []
                    created_at_str = None
                    
                    if os.path.exists(json_filepath):
                        try:
                            with open(json_filepath, "r", encoding="utf-8") as jf:
                                meta = json.load(jf)
                                title = meta.get("title", title)
                                tags = meta.get("tags", [])
                                created_at_str = meta.get("created_at")
                        except Exception:
                            pass
                    
                    
                    if not created_at_str:
                        created_at_epoch = os.path.getctime(filepath)
                        created_at_str = datetime.fromtimestamp(created_at_epoch).isoformat()
                    
                    if q:
                        q_lower = q.lower()
                        content = ""
                        try:
                            with open(filepath, "r", encoding="utf-8") as f:
                                content = f.read().lower()
                        except Exception:
                            pass
                        
                        match_title = q_lower in title.lower()
                        match_content = q_lower in content
                        match_tags = any(q_lower in tag.lower() for tag in tags)
                        
                        if not (match_title or match_content or match_tags):
                            continue
                            
                    size = os.path.getsize(filepath)
                    
                    notes_list.append(NoteListItem(
                        filename=item,
                        title=title,
                        created_at=created_at_str,
                        size=size
                    ))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao listar os arquivos: {str(e)}")

    
        reverse_order = (order == "desc")
        if sort_by == "title":
            notes_list.sort(key=lambda x: x.title.lower(), reverse=reverse_order)
        else:
            notes_list.sort(key=lambda x: x.created_at, reverse=reverse_order)

        return notes_list