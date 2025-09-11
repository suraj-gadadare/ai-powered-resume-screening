from typing import Union
from io import BytesIO
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document

def _safe_read_txt(uploaded_file) -> str:
    data = uploaded_file.read()
    if isinstance(data, bytes):
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data.decode("latin-1", errors="ignore")
    return str(data)

def _extract_pdf(uploaded_file) -> str:
    # pdfminer can read file-like objects
    uploaded_file.seek(0)
    return pdf_extract_text(uploaded_file)

def _extract_docx(uploaded_file) -> str:
    uploaded_file.seek(0)
    doc = Document(uploaded_file)
    return "\n".join([p.text for p in doc.paragraphs])

def extract_text_from_file(uploaded_file: Union[BytesIO, object]) -> str:
    """Extract raw text from TXT, PDF, or DOCX uploaded files."""
    name = getattr(uploaded_file, "name", "").lower()
    if name.endswith(".txt"):
        uploaded_file.seek(0)
        return _safe_read_txt(uploaded_file)
    if name.endswith(".pdf"):
        return _extract_pdf(uploaded_file)
    if name.endswith(".docx"):
        return _extract_docx(uploaded_file)
    # Fallback: try reading as text
    uploaded_file.seek(0)
    return _safe_read_txt(uploaded_file)