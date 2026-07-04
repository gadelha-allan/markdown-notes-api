import re
import os
import unicodedata

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
    
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)

def extract_title_from_filename(filename: str) -> str:
    base, _ = os.path.splitext(filename)
    base = re.sub(r'-\d{14}$', '', base)
    clean = base.replace('-', ' ').replace('_', ' ')
    return clean.strip().title()