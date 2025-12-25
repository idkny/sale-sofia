import logging

from emunium import EmuniumPlaywright
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class EmuniumWrapper:
    """Wraps a Playwright Page object with Emunium for human-like interactions."""

    def __init__(self, page: Page):
        if not page:
            raise ValueError("A valid Playwright Page object must be provided.")
        self._page = page
        self._emunium = EmuniumPlaywright(self._page)
        logger.debug("Emunium wrapper initialized for page.")

    @property
    def emunium(self) -> EmuniumPlaywright:
        """Returns the EmuniumPlaywright instance."""
        return self._emunium

    # You can expose other Emunium methods here if needed, for example:
    async def type_at(self, selector: str, text: str, **kwargs):
        """A convenient shortcut to Emunium's type_at method."""
        logger.info(f'Emunium typing at "{selector}"')
        await self._emunium.type_at(selector, text, **kwargs)

    async def click_at(self, selector: str, **kwargs):
        """A convenient shortcut to Emunium's click_at method."""
        logger.info(f'Emunium clicking at "{selector}"')
        await self._emunium.click_at(selector, **kwargs)
