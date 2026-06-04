from urllib.parse import urlparse

from app.retrieval.documents import RetrievedDocument


class SourceValidator:
    TRUSTED_TLDS = {".edu", ".gov", ".org"}

    def score(self, document: RetrievedDocument) -> float:
        score = 0.25
        parsed = urlparse(document.url)
        host = parsed.netloc.lower()
        if parsed.scheme == "https":
            score += 0.2
        if any(host.endswith(tld) for tld in self.TRUSTED_TLDS):
            score += 0.2
        if document.title:
            score += 0.1
        content_length = len(document.content)
        if content_length > 1000:
            score += 0.15
        elif content_length > 300:
            score += 0.1
        if document.score:
            score += min(document.score, 1.0) * 0.1
        return round(min(score, 1.0), 4)

