from hashlib import sha256

from app.retrieval.documents import DocumentChunk, RetrievedDocument


class TextChunker:
    def __init__(self, chunk_size: int = 900, overlap: int = 120) -> None:
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, document: RetrievedDocument) -> list[DocumentChunk]:
        text = " ".join(document.content.split())
        if not text:
            return []
        chunks: list[DocumentChunk] = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end]
            chunk_id = sha256(f"{document.url}:{start}:{chunk_text}".encode()).hexdigest()
            chunks.append(
                DocumentChunk(
                    id=chunk_id,
                    text=chunk_text,
                    metadata={
                        "url": document.url,
                        "title": document.title or "",
                        "start": start,
                        "score": document.score,
                    },
                )
            )
            if end == len(text):
                break
            start = max(0, end - self.overlap)
        return chunks
