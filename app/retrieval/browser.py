from __future__ import annotations

import ipaddress
import logging
import socket
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from app.core.config import get_settings
from app.retrieval.documents import RetrievedDocument
from app.retrieval.extractor import HtmlContentExtractor

logger = logging.getLogger(__name__)


class BrowserNavigationError(RuntimeError):
    pass


class PlaywrightBrowser:
    BLOCKED_HOSTS = {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
        "metadata.google.internal",
        "169.254.169.254",
    }

    MAX_HTML_SIZE = 5 * 1024 * 1024

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
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-extensions",
                ],
            )

            try:
                yield browser
            finally:
                await browser.close()

    async def fetch(self, url: str) -> RetrievedDocument:
        self._validate_url(url)

        async with self._browser() as browser:
            context = await browser.new_context(
                java_script_enabled=True,
                ignore_https_errors=False,
            )

            try:
                page = await context.new_page()

                page.set_default_timeout(self.settings.browser_timeout_ms)

                response = await page.goto(
                    url,
                    wait_until="domcontentloaded",
                )

                if response is None:
                    raise BrowserNavigationError(f"No response received while loading '{url}'")

                final_url = page.url

                self._validate_url(final_url)

                if response.status >= 400:
                    raise BrowserNavigationError(f"Failed to load '{final_url}' with status code {response.status}")

                html = await page.content()

                if len(html.encode("utf-8")) > self.MAX_HTML_SIZE:
                    raise BrowserNavigationError(
                        f"Page content exceeds maximum allowed size ({self.MAX_HTML_SIZE} bytes)"
                    )

                title, content = self.extractor.extract(html)

                return RetrievedDocument(
                    url=final_url,
                    title=title,
                    content=content,
                    score=0.0,
                    metadata={
                        "http_status": response.status,
                    },
                )

            except BrowserNavigationError:
                raise

            except Exception as exc:
                logger.exception(
                    "Browser navigation failed",
                    extra={"url": url},
                )
                raise BrowserNavigationError(f"Failed to navigate to '{url}'") from exc

            finally:
                await context.close()

    def _validate_url(self, url: str) -> None:
        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            raise BrowserNavigationError(f"Unsupported URL scheme '{parsed.scheme}'")

        if not parsed.hostname:
            raise BrowserNavigationError("URL does not contain a valid hostname")

        host = parsed.hostname.lower()

        if host in self.BLOCKED_HOSTS:
            raise BrowserNavigationError(f"Blocked host '{host}'")

        self._validate_host_resolution(host)

    def _validate_host_resolution(self, host: str) -> None:
        try:
            addresses = socket.getaddrinfo(
                host,
                None,
                proto=socket.IPPROTO_TCP,
            )
        except socket.gaierror as exc:
            raise BrowserNavigationError(f"Unable to resolve host '{host}'") from exc

        for entry in addresses:
            ip = entry[4][0]

            try:
                ip_obj = ipaddress.ip_address(ip)
            except ValueError:
                continue

            if (
                ip_obj.is_private
                or ip_obj.is_loopback
                or ip_obj.is_link_local
                or ip_obj.is_reserved
                or ip_obj.is_multicast
            ):
                raise BrowserNavigationError(f"Blocked private or reserved address '{ip}'")
