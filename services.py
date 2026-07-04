import os
import json
from datetime import datetime
from fastapi import HTTPException, UploadFile
from typing import List, Optional
from utils import slugify, extract_title_from_filename
from schemas import NoteListItem, NoteResponse, UploadResponse, DeleteResponse

import markdown
from pygments.formatters import HtmlFormatter

MAX_FILE_SIZE = 5 * 1024 * 1024
DATA_DIR = "data"


os.makedirs(DATA_DIR, exist_ok=True)

class NoteService:
    @staticmethod
    def save_uploaded_file(file: UploadFile, content: bytes) -> UploadResponse:
        
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail="O arquivo excede o tamanho máximo permitido de 5MB."
            )
            
        filename = file.filename
        if not (filename.endswith(".md") or filename.endswith(".markdown")):
            raise HTTPException(
                status_code=400,
                detail="Extensão de arquivo inválida. Apenas arquivos .md ou .markdown são aceitos."
            )
        
        
        secure_filename = os.path.basename(filename)
        file_path = os.path.join(DATA_DIR, secure_filename)
        
        try:
            with open(file_path, "wb") as f:
                f.write(content)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro interno ao salvar o arquivo: {str(e)}"
            )
        return UploadResponse(
            filename=secure_filename,
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
        
        md_filepath = os.path.join(DATA_DIR, md_filename)
        json_filepath = os.path.join(DATA_DIR, json_filename)
        
        created_at_str = datetime.now().isoformat()
        
        metadata = {
            "title": title,
            "tags": tags,
            "created_at": created_at_str,
            "md_file": md_filename
        }
        
        try:
            with open(md_filepath, "w", encoding="utf-8") as md_file:
                md_file.write(content)
                
            with open(json_filepath, "w", encoding="utf-8") as json_file:
                json.dump(metadata, json_file, ensure_ascii=False, indent=4)
        except Exception as e:
            for path in [md_filepath, json_filepath]:
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
            for item in os.listdir(DATA_DIR):
                filepath = os.path.join(DATA_DIR, item)
                
                if os.path.isfile(filepath) and (item.endswith(".md") or item.endswith(".markdown")):
                    base_name, _ = os.path.splitext(item)
                    json_filepath = os.path.join(DATA_DIR, f"{base_name}.json")
                    
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

    @staticmethod
    def render_note_to_html(filename: str) -> str:
        if os.path.basename(filename) != filename:
            raise HTTPException(
                status_code=400,
                detail="Nome de arquivo inválido para operações de leitura."
            )
            
        if not (filename.endswith(".md") or filename.endswith(".markdown")):
            raise HTTPException(
                status_code=400,
                detail="Apenas arquivos .md ou .markdown podem ser renderizados."
            )
        
        filepath = os.path.join(DATA_DIR, filename)    
        
        if not os.path.isfile(filepath):
            raise HTTPException(
                status_code=404,
                detail="Arquivo de nota não localizado."
            )
            
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Não foi possível ler o arquivo solicitado: {str(e)}"
            )

        html_body = markdown.markdown(
            content,
            extensions=[
                "markdown.extensions.extra",
                "markdown.extensions.codehilite"
            ],
            extension_configs={
                "markdown.extensions.codehilite": {
                    "css_class": "codehilite",
                    "use_pygments": True
                }
            }
        )

        pygments_css = HtmlFormatter(style="github").get_style_defs(".codehilite")

        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{extract_title_from_filename(filename)}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            word-wrap: break-word;
            max-width: 850px;
            margin: 0 auto;
            padding: 40px 20px;
            background-color: #ffffff;
            color: #24292e;
        }}
        h1, h2, h3, h4, h5, h6 {{ margin-top: 24px; margin-bottom: 16px; font-weight: 600; line-height: 1.25; padding-bottom: 0.3em; border-bottom: 1px solid #eaecef; }}
        a {{ color: #0366d6; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        p, blockquote, ul, ol, dl, table, pre {{ margin-top: 0; margin-bottom: 16px; }}
        code {{ padding: 0.2em 0.4em; margin: 0; font-size: 85%; background-color: rgba(27,31,35,0.05); border-radius: 3px; font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; }}
        pre {{ padding: 16px; overflow: auto; font-size: 85%; line-height: 1.45; background-color: #f6f8fa; border-radius: 3px; }}
        pre code {{ background-color: transparent; padding: 0; font-size: 100%; }}
        blockquote {{ padding: 0 1em; color: #6a737d; border-left: 0.25em solid #dfe2e5; }}
        table {{ border-spacing: 0; border-collapse: collapse; width: 100%; margin-top: 0; margin-bottom: 16px; }}
        table th, table td {{ padding: 6px 13px; border: 1px solid #dfe2e5; }}
        table tr {{ background-color: #fff; border-top: 1px solid #c6cbd1; }}
        table tr:nth-child(even) {{ background-color: #f6f8fa; }}
        {pygments_css}
    </style>
</head>
<body>
    {html_body}
</body>
</html>
"""
        return full_html

    @staticmethod
    def delete_note(filename: str) -> DeleteResponse:
        if os.path.basename(filename) != filename:
            raise HTTPException(
                status_code=400,
                detail="Nome de arquivo inválido para operações de remoção."
            )
            
        if not (filename.endswith(".md") or filename.endswith(".markdown")):
            raise HTTPException(
                status_code=400,
                detail="Apenas arquivos .md ou .markdown podem ser removidos."
            )
            
        filepath = os.path.join(DATA_DIR, filename)
            
        if not os.path.isfile(filepath):
            raise HTTPException(
                status_code=404,
                detail="Arquivo de nota não localizado para exclusão."
            )
            
        try:
            
            os.remove(filepath)
            

            base_name, _ = os.path.splitext(filename)
            json_filepath = os.path.join(DATA_DIR, f"{base_name}.json")
            if os.path.exists(json_filepath):
                os.remove(json_filepath)
                
            return DeleteResponse(message="Nota removida com sucesso.")
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Não foi possível remover o arquivo: {str(e)}"
            )
