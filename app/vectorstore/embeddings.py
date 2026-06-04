from hashlib import blake2b
from math import sqrt

from app.core.config import get_settings


class EmbeddingProvider:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._model = None

    def embed(self, texts: list[str]) -> list[list[float]]:
        model = self._load_model()
        if model is not None:
            vectors = model.encode(texts, normalize_embeddings=True)
            return [list(map(float, vector)) for vector in vectors]
        return [self._hash_embedding(text) for text in texts]

    def _load_model(self):
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            return None
        self._model = SentenceTransformer(self.settings.embedding_model)
        return self._model

    def _hash_embedding(self, text: str, dimensions: int = 128) -> list[float]:
        vector = [0.0] * dimensions
        for token in text.lower().split():
            digest = blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign
        norm = sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

