import asyncio
import os

import pytest

from browsers.browsers_main import BrowserHandle, create_instance


@pytest.mark.asyncio
async def test_create_and_use_browser():
    """
    Tests the creation of a browser instance, navigating to a page,
    and taking a screenshot.
    """
    browser_handle = None
    try:
        # 1. Create a chromium browser instance
        browser_handle = await create_instance("chromium")
        assert browser_handle is not None
        assert isinstance(browser_handle, BrowserHandle)

        # 2. Navigate to a test page
        await browser_handle.new_tab("https://www.google.com")

        # 3. Take a screenshot
        screenshot_path = "/tmp/test_screenshot.png"
        await browser_handle.screenshot(path=screenshot_path)
        assert os.path.exists(screenshot_path)
        os.remove(screenshot_path)

    finally:
        # 4. Close the browser
        if browser_handle:
            await browser_handle.close()
