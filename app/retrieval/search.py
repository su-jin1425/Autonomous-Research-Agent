from urllib.parse import urlencode

import httpx

from app.retrieval.documents import RetrievedDocument
from app.retrieval.extractor import HtmlContentExtractor


class WebSearchClient:
    def __init__(self, timeout_seconds: float = 12.0) -> None:
        self.timeout_seconds = timeout_seconds
        self.extractor = HtmlContentExtractor()

    async def search(self, query: str, limit: int = 5) -> list[RetrievedDocument]:
        params = urlencode({"q": query})
        url = f"https://duckduckgo.com/html/?{params}"
        async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "research-agent-v2/0.1"})
            response.raise_for_status()
        title, content = self.extractor.extract(response.text)
        links = self._extract_result_links(response.text)
        results = [
            RetrievedDocument(
                url=link["url"],
                title=link["title"],
                content=link["snippet"],
                score=1.0 / (index + 1),
                metadata={"rank": index + 1, "search_query": query},
            )
            for index, link in enumerate(links[:limit])
        ]
        if results:
            return results
        return [RetrievedDocument(url=url, title=title, content=content[:2000], score=0.1)]

    def _extract_result_links(self, html: str) -> list[dict[str, str]]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        results: list[dict[str, str]] = []
        for result in soup.select(".result"):
            anchor = result.select_one(".result__a")
            if not anchor or not anchor.get("href"):
                continue
            snippet_node = result.select_one(".result__snippet")
            results.append(
                {
                    "url": str(anchor["href"]),
                    "title": anchor.get_text(" ", strip=True),
                    "snippet": snippet_node.get_text(" ", strip=True) if snippet_node else "",
                }
            )
        return results

