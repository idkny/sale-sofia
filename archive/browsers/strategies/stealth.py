import logging
from typing import Tuple

from playwright.async_api import Browser, BrowserContext
from playwright_stealth import Stealth

from .chromium import ChromiumGuiStrategy, ChromiumStrategy

logger = logging.getLogger(__name__)


class StealthStrategy(ChromiumStrategy):
    """A strategy that launches a headless Chromium browser with stealth evasions."""

    async def launch(self, **kwargs) -> Tuple[Browser, BrowserContext]:
        """Launches a headless browser and applies stealth settings to new pages."""
        browser, context = await super().launch(**kwargs)

        async def apply_stealth_on_page(page):
            stealth = Stealth(page)
            await stealth.apply_stealth()
            logger.debug("Applied stealth evasions to new page.")

        context.on("page", apply_stealth_on_page)
        logger.info("Stealth mode enabled. Evasions will be applied to all new pages.")
        return browser, context


class StealthGuiStrategy(ChromiumGuiStrategy):
    """A strategy that launches a GUI Chromium browser with stealth evasions."""

    async def launch(self, **kwargs) -> Tuple[Browser, BrowserContext]:
        """Launches a GUI browser and applies stealth settings to new pages."""
        browser, context = await super().launch(**kwargs)

        async def apply_stealth_on_page(page):
            stealth = Stealth(page)
            await stealth.apply_stealth()
            logger.debug("Applied stealth evasions to new page.")

        context.on("page", apply_stealth_on_page)
        logger.info("Stealth GUI mode enabled. Evasions will be applied to all new pages.")
        return browser, context
