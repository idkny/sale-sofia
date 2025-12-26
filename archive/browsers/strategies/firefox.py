import logging
from typing import Tuple

from camoufox.async_api import AsyncCamoufox
from playwright.async_api import Browser, BrowserContext

from ..utils import xvfb_manager
from .base import BaseBrowserStrategy

logger = logging.getLogger(__name__)


class FirefoxStrategy(BaseBrowserStrategy):
    """Strategy for launching a headless Firefox browser with Camoufox."""

    def __init__(self, proxy: dict | None = None, profile_name: str | None = None):
        # SECURITY: Reject if no proxy - prevents real IP exposure
        if proxy is None:
            raise ValueError("FirefoxStrategy requires a proxy to prevent real IP exposure")
        self.proxy = proxy
        self.profile_name = profile_name  # Note: profile_name is not directly used by AsyncCamoufox
        self.browser: Browser | None = None
        self.camoufox_instance = None

    async def launch(self, **kwargs) -> Tuple[Browser, BrowserContext]:
        """Launches a headless Firefox browser using the AsyncCamoufox context manager."""
        logger.info("Launching headless Firefox with Camoufox profile")
        try:
            self.camoufox_instance = AsyncCamoufox(
                proxy=self.proxy,
                headless=True,
                **kwargs,
            )
            self.browser = await self.camoufox_instance.__aenter__()
            # The context is typically the browser object itself in this setup,
            # or we create a new one if needed.
            context = self.browser.contexts[0] if self.browser.contexts else await self.browser.new_context()
            return self.browser, context
        except Exception as e:
            logger.error(f"Failed to launch headless Firefox with Camoufox: {e}")
            if self.camoufox_instance:
                await self.camoufox_instance.__aexit__(None, None, None)
            raise

    async def close(self) -> None:
        """Closes the browser and the Camoufox instance."""
        if self.camoufox_instance:
            await self.camoufox_instance.__aexit__(None, None, None)
            logger.info("Closed Firefox browser.")


class FirefoxGuiStrategy(FirefoxStrategy):
    """Strategy for launching a GUI Firefox browser with Camoufox."""

    async def launch(self, **kwargs) -> Tuple[Browser, BrowserContext]:
        """Launches a GUI Firefox browser with a Camoufox profile."""
        logger.info("Launching GUI Firefox with Camoufox profile")
        try:
            # xvfb_manager is still useful here for GUI in headless environments
            with xvfb_manager():
                self.camoufox_instance = AsyncCamoufox(
                    proxy=self.proxy,
                    headless=False,
                    **kwargs,
                )
                self.browser = await self.camoufox_instance.__aenter__()
                context = self.browser.contexts[0] if self.browser.contexts else await self.browser.new_context()
                return self.browser, context
        except Exception as e:
            logger.error(f"Failed to launch GUI Firefox with Camoufox: {e}")
            if self.camoufox_instance:
                await self.camoufox_instance.__aexit__(None, None, None)
            raise
