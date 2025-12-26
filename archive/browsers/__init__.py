"""Browser automation and fingerprinting module for the scraper.

This module provides a unified interface (`create_instance`) to launch various
secure and fingerprinted browser types, including:

- `chromium` / `chromium_gui`: Launches a fingerprinted version of Chromium.
- `firefox` / `firefox_gui`: Launches Firefox with the Camoufox privacy patch.
- `stealth` / `stealth_gui`: A Chromium-based browser with additional stealth evasions.

The module is designed with a modular strategy pattern, allowing for easy
extension with new browser engines.
"""

import logging

from .browsers_main import (
    BrowserHandle,
    create_instance,
    register_strategy,
)

# Configure a null handler for the library to avoid "No handler found" warnings
# if the main application doesn't configure logging.
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    "BrowserHandle",
    "create_instance",
    "register_strategy",
]
