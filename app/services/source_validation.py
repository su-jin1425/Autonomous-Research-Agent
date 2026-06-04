from __future__ import annotations

import re
from urllib.parse import urlparse

from app.retrieval.documents import RetrievedDocument


class SourceValidator:
    TRUSTED_DOMAINS = {
        "reuters.com",
        "apnews.com",
        "nature.com",
        "science.org",
        "arxiv.org",
        "nih.gov",
        "nasa.gov",
        "who.int",
        "oecd.org",
        "worldbank.org",
        "imf.org",
        "europa.eu",
    }

    TRUSTED_TLDS = {
        ".gov",
        ".edu",
    }

    LOW_TRUST_INDICATORS = {
        "click here",
        "buy now",
        "sponsored",
        "advertisement",
        "casino",
        "betting",
        "crypto giveaway",
    }

    def score(self, document: RetrievedDocument) -> float:
        parsed = urlparse(document.url)

        host = parsed.hostname.lower() if parsed.hostname else ""

        score = 0.0

        score += self._scheme_score(parsed.scheme)
        score += self._domain_score(host)
        score += self._title_score(document)
        score += self._content_score(document)
        score += self._search_score(document)
        score += self._citation_score(document)

        return round(min(max(score, 0.0), 1.0), 4)

    def _scheme_score(self, scheme: str) -> float:
        if scheme == "https":
            return 0.15
        return 0.0

    def _domain_score(self, host: str) -> float:
        score = 0.0

        if host in self.TRUSTED_DOMAINS:
            score += 0.35

        elif any(host.endswith(tld) for tld in self.TRUSTED_TLDS):
            score += 0.25

        return score

    def _title_score(self, document: RetrievedDocument) -> float:
        if not document.title:
            return 0.0

        title = document.title.strip()

        if len(title) < 5:
            return 0.0

        return 0.10

    def _content_score(self, document: RetrievedDocument) -> float:
        content = document.content.strip()

        if not content:
            return 0.0

        content_length = len(content)

        score = 0.0

        if content_length >= 3000:
            score += 0.20
        elif content_length >= 1500:
            score += 0.15
        elif content_length >= 500:
            score += 0.10

        lowered = content.lower()

        penalty_count = sum(
            1
            for indicator in self.LOW_TRUST_INDICATORS
            if indicator in lowered
        )

        score -= min(penalty_count * 0.05, 0.15)

        return score

    def _search_score(self, document: RetrievedDocument) -> float:
        if document.score <= 0:
            return 0.0

        return min(document.score, 1.0) * 0.10

    def _citation_score(self, document: RetrievedDocument) -> float:
        content = document.content

        url_count = len(
            re.findall(
                r"https?://[^\s]+",
                content,
                flags=re.IGNORECASE,
            )
        )

        if url_count >= 5:
            return 0.10

        if url_count >= 2:
            return 0.05

        return 0.0