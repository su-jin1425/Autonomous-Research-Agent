from app.retrieval.chunking import TextChunker
from app.retrieval.documents import RetrievedDocument


def test_chunker_creates_stable_metadata() -> None:
    document = RetrievedDocument(
        url="https://example.com/research",
        title="Example Research",
        content=" ".join(["evidence"] * 300),
        score=0.8,
    )

    chunks = TextChunker(chunk_size=120, overlap=20).chunk(document)

    assert len(chunks) > 1
    assert chunks[0].metadata["url"] == document.url
    assert chunks[0].metadata["title"] == document.title
    assert chunks[0].id != chunks[1].id

