"""
Browser-based page fetcher for JavaScript-rendered content.

Uses Playwright to fetch pages with a real browser, executing JavaScript
and waiting for dynamic content to load.
"""

import asyncio
import os
import logging
import concurrent.futures
from typing import Optional, Tuple
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


class BrowserFetcher:
    """Fetch pages using a headless browser for JavaScript-rendered content."""

    async def fetch_with_browser(
        self,
        url: str,
        wait_for_selector: Optional[str] = None,
        timeout: int = 15000
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Fetch a URL using a headless browser.

        Args:
            url: The URL to fetch
            wait_for_selector: Optional CSS selector to wait for before capturing content
            timeout: Maximum time to wait in milliseconds (default: 15000)

        Returns:
            (html, text) tuple
        """
        debug_mode = os.getenv("DEBUG_SCRAPING", "").lower() == "true"

        async with async_playwright() as p:
            try:
                # Launch headless browser
                browser = await p.chromium.launch(headless=True)

                # Create context with cookies if available
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )

                # Add LinkedIn cookie if available
                linkedin_cookie = os.getenv("LINKEDIN_LI_AT")
                if linkedin_cookie:
                    await context.add_cookies([{
                        "name": "li_at",
                        "value": linkedin_cookie,
                        "domain": ".linkedin.com",
                        "path": "/"
                    }])
                    if debug_mode:
                        logger.info("Added li_at cookie to browser context")

                page = await context.new_page()

                if debug_mode:
                    logger.info(f"Browser: Navigating to {url}")

                # Navigate and wait for network to be idle
                await page.goto(url, wait_until="networkidle", timeout=timeout)

                # Wait for specific selector if provided
                if wait_for_selector:
                    if debug_mode:
                        logger.info(f"Browser: Waiting for selector '{wait_for_selector}'")
                    await page.wait_for_selector(wait_for_selector, timeout=timeout)
                elif "linkedin.com/jobs" in url:
                    # LinkedIn-specific: wait for job title to appear
                    try:
                        await page.wait_for_selector(
                            ".job-details-jobs-unified-top-card__job-title",
                            timeout=timeout
                        )
                        if debug_mode:
                            logger.info("Browser: LinkedIn job title loaded")
                    except PlaywrightTimeoutError:
                        logger.warning("Timeout waiting for LinkedIn job title selector")

                # Get content
                html = await page.content()
                text = await page.inner_text("body")

                if debug_mode:
                    logger.info(f"Browser: Captured {len(html)} chars of HTML")

                return html, text

            except PlaywrightTimeoutError as e:
                logger.error(f"Browser timeout fetching {url}: {e}")
                return None, None
            except Exception as e:
                logger.error(f"Browser error fetching {url}: {e}")
                return None, None
            finally:
                await browser.close()

    def fetch(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Synchronous wrapper for fetch_with_browser.
        Works in both sync and async contexts (e.g., FastAPI endpoints).

        Args:
            url: The URL to fetch

        Returns:
            (html, text) tuple
        """
        try:
            # Check if we're already in an async event loop (e.g., FastAPI)
            loop = asyncio.get_running_loop()

            # We're in an async context - run in a new thread to avoid conflict
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._run_in_new_loop, url)
                return future.result()
        except RuntimeError:
            # No running loop - safe to use asyncio.run()
            return asyncio.run(self.fetch_with_browser(url))

    def _run_in_new_loop(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Helper to run async code in a new event loop (for thread pool)."""
        return asyncio.run(self.fetch_with_browser(url))
