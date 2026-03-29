"""Embedding generation and text chunking for RAG."""

from app.services import llm_client


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks by word count."""
    words = text.split()
    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap
    return chunks


async def generate_embedding(text: str) -> list[float]:
    """Generate an embedding vector for the given text."""
    return await llm_client.create_embedding(text)
