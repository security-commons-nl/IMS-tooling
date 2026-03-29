"""Document parsing — extract text from PDF, DOCX, Markdown."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def parse_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    from docx import Document

    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def parse_markdown(file_path: str) -> str:
    """Read a Markdown file as plain text."""
    return Path(file_path).read_text(encoding="utf-8")


def parse_document(file_path: str, source_type: str) -> str:
    """Parse a document based on its type."""
    parsers = {
        "pdf": parse_pdf,
        "docx": parse_docx,
        "markdown": parse_markdown,
    }
    parser = parsers.get(source_type)
    if not parser:
        raise ValueError(f"Unsupported source type: {source_type}")
    return parser(file_path)
