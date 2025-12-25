import logging
from abc import ABC, abstractmethod
from typing import Tuple

from playwright.async_api import Browser, BrowserContext

logger = logging.getLogger(__name__)


class BaseBrowserStrategy(ABC):
    """Abstract base class for all browser launching strategies."""

    @abstractmethod
    async def launch(self, **kwargs) -> Tuple[Browser, BrowserContext]:
        """Launches a browser and returns the browser and context handles."""
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """Closes the browser and cleans up resources."""
        raise NotImplementedError
