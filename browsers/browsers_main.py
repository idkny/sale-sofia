import asyncio
import logging
import pkgutil
import time
from typing import Dict, Type

from playwright.async_api import Page

from . import strategies
from .strategies.base import BaseBrowserStrategy
from .utils import validate_proxy

logger = logging.getLogger(__name__)

_strategy_registry: Dict[str, Type[BaseBrowserStrategy]] = {}


def _discover_strategies():
    """Dynamically discovers and registers browser strategies."""
    logger.info("Discovering browser strategies...")
    for _, name, _ in pkgutil.iter_modules(strategies.__path__):
        logger.info(f"Found strategy module: {name}")
        try:
            module = __import__(f"{strategies.__name__}.{name}", fromlist=["*"])
            for item_name in dir(module):
                item = getattr(module, item_name)
                if isinstance(item, type) and issubclass(item, BaseBrowserStrategy) and item is not BaseBrowserStrategy:
                    strategy_name = item.__name__.replace("Strategy", "").lower()
                    logger.info(f"Found strategy class: {item.__name__}, registering as '{strategy_name}'")
                    register_strategy(strategy_name, item)
        except Exception as e:
            logger.error(f"Failed to import or register strategy from {name}: {e}")


def register_strategy(name: str, strategy_class: Type[BaseBrowserStrategy]):
    """Registers a new browser strategy."""
    if name in _strategy_registry:
        logger.warning(f"Strategy '{name}' is already registered. Overwriting.")
    _strategy_registry[name] = strategy_class
    logger.info(f"Registered browser strategy: '{name}'")


class BrowserHandle:
    """A handle to a managed browser instance, providing a clean public API."""

    def __init__(self, strategy: BaseBrowserStrategy):
        self._strategy = strategy
        self._browser = None
        self._context = None
        self._start_time = time.monotonic()

    async def _initialize(self):
        self._browser, self._context = await self._strategy.launch()

    async def new_tab(self, url: str | None = None) -> Page:
        """Opens a new tab/page in the browser context."""
        page = await self._context.new_page()
        if url:
            await page.goto(url)
        return page

    async def goto(self, url: str, **kwargs):
        """Navigates the main page to a URL."""
        await self.page.goto(url, **kwargs)

    async def evaluate(self, expression: str, **kwargs):
        """Evaluates a JavaScript expression in the page context."""
        return await self.page.evaluate(expression, **kwargs)

    async def screenshot(self, path: str, **kwargs):
        """Takes a screenshot of the current page."""
        await self.page.screenshot(path=path, **kwargs)

    async def start_har(self, path: str, **kwargs):
        """Starts HAR (HTTP Archive) tracing."""
        await self._context.tracing.start(screenshots=True, snapshots=True, sources=True)

    async def stop_har(self, path: str):
        """Stops HAR tracing and saves the file."""
        await self._context.tracing.stop(path=path)

    @property
    def page(self) -> Page:
        """Returns the primary page, creating one if necessary."""
        if not self._context.pages:
            # This should ideally not happen if a tab is created.
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.new_tab())
        return self._context.pages[0]

    async def close(self):
        """Closes the browser and cleans up all resources."""
        if self._context:
            await self._context.close()
        if self._strategy:
            await self._strategy.close()
        elapsed_s = time.monotonic() - self._start_time
        logger.info(f"Browser session closed. Duration: {elapsed_s:.2f}s")

    async def __aenter__(self):
        await self._initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


async def create_instance(
    browser_type: str,
    proxy: str | dict | None = None,
    profile_name: str | None = None,
    *,
    headless: bool | None = None,  # Note: headless is handled by strategy choice
) -> BrowserHandle:
    """Creates and returns a browser instance based on the specified type.

    Args:
        browser_type: The type of browser to create (e.g., 'firefox', 'stealth').
        proxy: The proxy server to use (URL string or dict).
        profile_name: The name of the browser profile to use.
        headless: This is now controlled by the strategy (e.g., 'chromium' vs 'chromium_gui').

    Returns:
        An initialized BrowserHandle.

    """
    if not _strategy_registry:
        _discover_strategies()

    # Ensure chromium is extracted if a chromium-based browser is requested
    if "chromium" in browser_type:
        from .utils import extract_chromium

        extract_chromium()

    browser_type = browser_type.lower()
    if browser_type not in _strategy_registry:
        raise ValueError(
            f"Unsupported browser type: '{browser_type}'. Available types: {list(_strategy_registry.keys())}"
        )

    strategy_class = _strategy_registry[browser_type]

    # Prepare strategy-specific arguments
    validated_proxy = validate_proxy(proxy)

    # SECURITY: Reject if no proxy - prevents real IP exposure
    if validated_proxy is None:
        raise ValueError(
            "Proxy is required but none provided. "
            "Refusing to create browser without proxy to prevent real IP exposure."
        )

    strategy_args = {"proxy": validated_proxy, "profile_name": profile_name}

    strategy = strategy_class(**strategy_args)
    handle = BrowserHandle(strategy)
    await handle._initialize()  # Initialize the handle to get browser and context

    logger.info(
        "Browser instance created successfully",
        extra={
            "browser_type": browser_type,
            "proxy_id": str(proxy)[:30] if proxy else None,
        },
    )
    return handle


async def run_fingerprint_validation(
    browser_type: str,
    profile_name: str | None = None,
    proxy: str | dict | None = None,
):
    """Runs the full fingerprint validation suite for a given configuration."""
    from .validator import validate_fingerprint_async  # Local import

    logger.info(f"Starting fingerprint validation for browser '{browser_type}' with profile '{profile_name}'")
    results = await validate_fingerprint_async(
        browser_type=browser_type,
        profile_name=profile_name,
        proxy=proxy,
    )
    # Here you can add logic to log, save, or assert the results
    logger.info(f"Validation finished. Results: {results}")
    return results


if __name__ == "__main__":
    # This allows running the validation script directly
    # Example: python -m browsers.browsers_main
    async def main():
        # Test Firefox with uk_desktop_mac profile
        await run_fingerprint_validation(browser_type="firefox", profile_name="uk_desktop_mac")

        # Test Chromium Stealth (no specific profile needed for this one)
        await run_fingerprint_validation(browser_type="chromiumstealth")

        # Test Chromium Stealth (no specific profile needed for this one)
        await run_fingerprint_validation(browser_type="chromiumstealth")

    asyncio.run(main())
