from bs4 import BeautifulSoup


class HtmlContentExtractor:
    def extract(self, html: str) -> tuple[str | None, str]:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg", "nav", "footer", "header"]):
            tag.decompose()
        title = soup.title.string.strip() if soup.title and soup.title.string else None
        candidates = soup.select("article, main, section, p")
        text = "\n".join(node.get_text(" ", strip=True) for node in candidates)
        if len(text) < 200:
            text = soup.get_text("\n", strip=True)
        return title, "\n".join(line for line in text.splitlines() if line.strip())

