from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.retrieval.documents import RetrievedDocument
from app.retrieval.extractor import HtmlContentExtractor


class BrowserNavigationError(RuntimeError):
    pass


class PlaywrightBrowser:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.extractor = HtmlContentExtractor()

    @asynccontextmanager
    async def _browser(self):
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise BrowserNavigationError("Playwright is not installed") from exc

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                yield browser
            finally:
                await browser.close()

    async def fetch(self, url: str) -> RetrievedDocument:
        async with self._browser() as browser:
            page = await browser.new_page()
            page.set_default_timeout(self.settings.browser_timeout_ms)
            response = await page.goto(url, wait_until="domcontentloaded")
            if response is None or response.status >= 400:
                status = response.status if response else "no response"
                raise BrowserNavigationError(f"Failed to load {url}: {status}")
            html = await page.content()
            title, content = self.extractor.extract(html)
            return RetrievedDocument(url=url, title=title, content=content, score=0.0)

