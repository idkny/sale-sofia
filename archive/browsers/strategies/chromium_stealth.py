import logging
from typing import Tuple

from playwright.async_api import Browser, BrowserContext, async_playwright
from playwright_stealth import Stealth

from ..utils import xvfb_manager
from .base import BaseBrowserStrategy

logger = logging.getLogger(__name__)


class ChromiumStealthStrategy(BaseBrowserStrategy):
    """Strategy for launching a headless Chromium browser with playwright-stealth."""

    def __init__(self, proxy: dict | None = None, profile_name: str | None = None):
        self.proxy = proxy
        # profile_name is not used in this strategy, but is kept for consistency
        self.profile_name = profile_name
        self.playwright = None
        self.browser: Browser | None = None

    async def launch(self, **kwargs) -> Tuple[Browser, BrowserContext]:
        """Launches a headless Chromium browser with stealth settings."""
        logger.info("Launching headless Chromium with playwright-stealth")

        self.playwright = await async_playwright().start()
        try:
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                proxy=self.proxy,
                **kwargs,
            )
            context = await self.browser.new_context()
            stealth = Stealth()
            await stealth.apply_stealth_async(context)
            return self.browser, context
        except Exception as e:
            logger.error(f"Failed to launch headless Chromium with stealth: {e}")
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            raise

    async def close(self) -> None:
        """Closes the browser and the Playwright instance."""
        if self.browser:
            await self.browser.close()
            logger.info("Closed Chromium browser.")
        if self.playwright:
            await self.playwright.stop()


class ChromiumStealthGuiStrategy(ChromiumStealthStrategy):
    """Strategy for launching a GUI Chromium browser with playwright-stealth."""

    async def launch(self, **kwargs) -> Tuple[Browser, BrowserContext]:
        """Launches a GUI Chromium browser with stealth settings."""
        logger.info("Launching GUI Chromium with playwright-stealth")

        self.playwright = await async_playwright().start()
        try:
            with xvfb_manager():
                self.browser = await self.playwright.chromium.launch(
                    headless=False,
                    proxy=self.proxy,
                    **kwargs,
                )
            context = await self.browser.new_context()
            stealth = Stealth()
            await stealth.apply_stealth_async(context)
            return self.browser, context
        except Exception as e:
            logger.error(f"Failed to launch GUI Chromium with stealth: {e}")
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            raise
