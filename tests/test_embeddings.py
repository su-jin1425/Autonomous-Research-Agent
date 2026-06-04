from app.vectorstore.embeddings import EmbeddingProvider


def test_embedding_provider_is_deterministic() -> None:
    provider = EmbeddingProvider()

    first = provider.embed(["fastapi redis research"])[0]
    second = provider.embed(["fastapi redis research"])[0]
    third = provider.embed(["gardening soil compost"])[0]

    assert first == second
    assert first != third
    assert len(first) == 128


def test_hash_embedding_is_normalized() -> None:
    provider = EmbeddingProvider()

    vector = provider._hash_embedding("autonomous research agent")

    norm = sum(value * value for value in vector) ** 0.5

    assert len(vector) == 128
    assert abs(norm - 1.0) < 1e-6
