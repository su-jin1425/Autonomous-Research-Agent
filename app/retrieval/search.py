from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from urllib.parse import urlencode

import httpx

from app.retrieval.documents import RetrievedDocument
from app.retrieval.extractor import HtmlContentExtractor


logger = logging.getLogger(__name__)


class SearchProviderError(RuntimeError):
    pass


class SearchProvider(ABC):
    provider_name: str

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[RetrievedDocument]:
        raise NotImplementedError


class DuckDuckGoProvider(SearchProvider):
    provider_name = "duckduckgo"

    def __init__(
        self,
        timeout_seconds: float = 12.0,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.extractor = HtmlContentExtractor()

    async def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[RetrievedDocument]:
        params = urlencode(
            {
                "q": query,
            }
        )

        url = f"https://duckduckgo.com/html/?{params}"

        headers = {
            "User-Agent": (
                "AutonomousResearchAgent/1.0 "
                "(Research Retrieval Engine)"
            )
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                follow_redirects=True,
            ) as client:
                response = await client.get(
                    url,
                    headers=headers,
                )

                response.raise_for_status()

        except Exception as exc:
            raise SearchProviderError(
                f"DuckDuckGo search failed: {exc}"
            ) from exc

        links = self._extract_result_links(
            response.text,
        )

        results: list[RetrievedDocument] = []

        for index, link in enumerate(
            links[:limit],
            start=1,
        ):
            results.append(
                RetrievedDocument(
                    url=link["url"],
                    title=link["title"],
                    content=link["snippet"],
                    score=1.0 / index,
                    metadata={
                        "provider": self.provider_name,
                        "rank": index,
                        "search_query": query,
                    },
                )
            )

        if results:
            return results

        title, content = self.extractor.extract(
            response.text,
        )

        return [
            RetrievedDocument(
                url=url,
                title=title,
                content=content[:2000],
                score=0.1,
                metadata={
                    "provider": self.provider_name,
                    "search_query": query,
                    "fallback": 1,
                },
            )
        ]

    def _extract_result_links(
        self,
        html: str,
    ) -> list[dict[str, str]]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        results: list[dict[str, str]] = []

        for result in soup.select(".result"):
            anchor = result.select_one(
                ".result__a"
            )

            if (
                not anchor
                or not anchor.get("href")
            ):
                continue

            snippet_node = result.select_one(
                ".result__snippet"
            )

            results.append(
                {
                    "url": str(anchor["href"]),
                    "title": anchor.get_text(
                        " ",
                        strip=True,
                    ),
                    "snippet": (
                        snippet_node.get_text(
                            " ",
                            strip=True,
                        )
                        if snippet_node
                        else ""
                    ),
                }
            )

        return results


class WebSearchClient:
    def __init__(
        self,
        provider: SearchProvider | None = None,
        timeout_seconds: float = 12.0,
        max_retries: int = 2,
    ) -> None:
        self.provider = (
            provider
            or DuckDuckGoProvider(
                timeout_seconds=timeout_seconds
            )
        )

        self.max_retries = max_retries

    async def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[RetrievedDocument]:
        last_error: Exception | None = None

        for attempt in range(
            self.max_retries + 1
        ):
            try:
                return await self.provider.search(
                    query=query,
                    limit=limit,
                )

            except Exception as exc:
                last_error = exc

                logger.warning(
                    "Search provider failed",
                    extra={
                        "provider": getattr(
                            self.provider,
                            "provider_name",
                            "unknown",
                        ),
                        "attempt": attempt + 1,
                        "query": query,
                    },
                )

        raise SearchProviderError(
            f"Search failed after {self.max_retries + 1} attempts"
        ) from last_error