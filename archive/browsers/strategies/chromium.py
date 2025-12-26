import logging
import os
from typing import Tuple

from playwright.async_api import Browser, BrowserContext, async_playwright

from ..utils import xvfb_manager
from .base import BaseBrowserStrategy

logger = logging.getLogger(__name__)

FPC_BIN_PATH = os.environ.get("FPC_BIN", "/home/wow/Projects/Bg-Estate/browsers/chromium/chrome")


class ChromiumStrategy(BaseBrowserStrategy):
    """Strategy for launching a headless Chromium browser with fingerprinting."""

    def __init__(self, proxy: dict | None = None, profile_name: str | None = None):
        # SECURITY: Reject if no proxy - prevents real IP exposure
        if proxy is None:
            raise ValueError("ChromiumStrategy requires a proxy to prevent real IP exposure")
        self.proxy = proxy
        self.playwright = None
        self.browser: Browser | None = None

    async def launch(self, **kwargs) -> Tuple[Browser, BrowserContext]:
        """Launches a headless, fingerprinted Chromium browser."""
        if not os.path.exists(FPC_BIN_PATH):
            logger.error(f"fingerprint-chromium binary not found at {FPC_BIN_PATH}")
            raise FileNotFoundError(f"FPC_BIN not found: {FPC_BIN_PATH}")

        logger.info(
            "Launching headless fingerprinted Chromium",
        )

        self.playwright = await async_playwright().start()
        try:
            with xvfb_manager():
                self.browser = await self.playwright.chromium.launch(
                    executable_path=FPC_BIN_PATH,
                    headless=True,
                    proxy=self.proxy,
                    args=self._create_chromium_args(**kwargs),
                    **kwargs,
                )
            context = await self.browser.new_context()
            return self.browser, context
        except Exception as e:
            logger.error(f"Failed to launch headless Chromium: {e}")
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            raise

    def _create_chromium_args(self, **kwargs) -> list[str]:
        """Creates the command-line arguments for fingerprint-chromium."""
        args = [
            f"--fingerprint-seed={kwargs.get('seed', 'default')}",
            f"--timezone-id={kwargs.get('timezone', 'UTC')}",
            # Add other fingerprinting arguments as needed
        ]
        return args

    async def close(self) -> None:
        """Closes the browser and the Playwright instance."""
        if self.browser:
            await self.browser.close()
            logger.info("Closed Chromium browser.")
        if self.playwright:
            await self.playwright.stop()


class ChromiumGuiStrategy(ChromiumStrategy):
    """Strategy for launching a GUI, fingerprinted Chromium browser."""

    async def launch(self, **kwargs) -> Tuple[Browser, BrowserContext]:
        """Launches a GUI, fingerprinted Chromium within an Xvfb frame if needed."""
        if not os.path.exists(FPC_BIN_PATH):
            logger.error(f"fingerprint-chromium binary not found at {FPC_BIN_PATH}")
            raise FileNotFoundError(f"FPC_BIN not found: {FPC_BIN_PATH}")

        logger.info(
            "Launching GUI fingerprinted Chromium",
        )

        self.playwright = await async_playwright().start()
        try:
            with xvfb_manager():
                self.browser = await self.playwright.chromium.launch(
                    executable_path=FPC_BIN_PATH,
                    headless=False,
                    proxy=self.proxy,
                    args=self._create_chromium_args(**kwargs),
                    **kwargs,
                )
            context = await self.browser.new_context()
            return self.browser, context
        except Exception as e:
            logger.error(f"Failed to launch GUI Chromium: {e}")
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            raise
