import asyncio
import logging
from typing import Any, Dict

from playwright.async_api import Page

from .browsers_main import create_instance

logger = logging.getLogger(__name__)


async def run_programmatic_checks_async(page: Page) -> Dict[str, Any]:
    """Runs a series of programmatic checks to validate the browser's fingerprint."""
    logger.info("Running programmatic fingerprint checks...")
    try:
        # Check 1: Navigator properties
        navigator_props = await page.evaluate(
            """
            () => ({
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                webdriver: navigator.webdriver,
                plugins: Array.from(navigator.plugins).map(p => p.name),
                languages: navigator.languages,
            })
        """
        )

        # Check 2: Screen properties
        screen_props = await page.evaluate(
            """
            () => ({
                width: screen.width,
                height: screen.height,
                availWidth: screen.availWidth,
                availHeight: screen.availHeight,
                colorDepth: screen.colorDepth,
                pixelDepth: screen.pixelDepth,
            })
        """
        )

        # Check 3: WebGL Fingerprint
        webgl_props = await page.evaluate(
            """
            () => {
                try {
                    const canvas = document.createElement('canvas');
                    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    if (!gl) return { error: 'WebGL not supported' };
                    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                    return {
                        vendor: gl.getParameter(gl.VENDOR),
                        renderer: gl.getParameter(gl.RENDERER),
                        unmasked_vendor: debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : 'N/A',
                        unmasked_renderer: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'N/A',
                    };
                } catch (e) {
                    return { error: e.message };
                }
            }
        """
        )

        # Check 4: Timezone
        timezone = await page.evaluate("() => Intl.DateTimeFormat().resolvedOptions().timeZone")

        result = {
            "programmatic_status": "success",
            "details": {
                "navigator": navigator_props,
                "screen": screen_props,
                "webgl": webgl_props,
                "timezone": timezone,
            },
        }
        logger.info("Programmatic checks completed successfully.")
        return result
    except Exception as e:
        logger.error(f"Error during programmatic checks: {e}")
        return {"programmatic_status": "failure", "error": str(e)}


async def test_sannysoft_async(page: Page) -> Dict[str, Any]:
    """Navigates to SannySoft's test page and extracts key results."""
    url = "https://bot.sannysoft.com/"
    logger.info(f"Navigating to {url} for fingerprint validation...")
    try:
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(5)  # Allow some time for all scripts to run

        # Extract results from the table
        results_table = await page.evaluate(
            """
            () => {
                const results = {};
                const rows = document.querySelectorAll('.table-striped tbody tr');
                rows.forEach(row => {
                    const testName = row.querySelector('td:nth-child(1)').innerText.trim();
                    const result = row.querySelector('td:nth-child(3)').innerText.trim();
                    results[testName] = result;
                });
                return results;
            }
        """
        )

        logger.info("Sannysoft results extracted successfully.")
        return {"sannysoft_status": "success", "details": results_table}
    except Exception as e:
        logger.error(f"Error testing sannysoft.com: {e}")
        return {"sannysoft_status": "failure", "error": str(e)}


async def test_amiunique_async(page: Page) -> Dict[str, Any]:
    """Navigates to amiunique.org and extracts fingerprinting results."""
    url = "https://amiunique.org/fp"
    logger.info(f"Navigating to {url} for fingerprint validation...")
    try:
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(5)
        # This site is complex to scrape, so we'll just confirm it loads
        # and maybe grab the main fingerprint ID if possible.
        fingerprint_id = await page.evaluate("() => document.querySelector('.fingerprint-header h2')?.innerText")
        return {
            "amiunique_status": "success",
            "details": {"fingerprint_id": fingerprint_id or "Not found"},
        }
    except Exception as e:
        logger.error(f"Error testing amiunique.org: {e}")
        return {"amiunique_status": "failure", "error": str(e)}


async def test_pixelscan_async(page: Page) -> Dict[str, Any]:
    """Navigates to pixelscan.net and extracts the bot score."""
    url = "https://pixelscan.net/"
    logger.info(f"Navigating to {url} for fingerprint validation...")
    try:
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(10)  # This site can be slow to load results
        score = await page.evaluate("() => document.querySelector('.score-container .score')?.innerText")
        return {"pixelscan_status": "success", "details": {"score": score or "Not found"}}
    except Exception as e:
        logger.error(f"Error testing pixelscan.net: {e}")
        return {"pixelscan_status": "failure", "error": str(e)}


async def test_creepjs_async(page: Page) -> Dict[str, Any]:
    """Navigates to creepjs and extracts the fingerprint report."""
    url = "https://abrahamjuliot.github.io/creepjs/"
    logger.info(f"Navigating to {url} for fingerprint validation...")
    try:
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(10)  # Wait for all the checks to run
        fingerprint = await page.evaluate("() => window.fingerprint")
        return {"creepjs_status": "success", "details": fingerprint}
    except Exception as e:
        logger.error(f"Error testing creepjs: {e}")
        return {"creepjs_status": "failure", "error": str(e)}


async def validate_fingerprint_async(
    browser_type: str, profile_name: str | None = None, proxy: dict | None = None
) -> Dict[str, Any]:
    """
    Launches a browser with the specified strategy and profile, then runs fingerprint validation tests.
    """
    logger.info(f"Starting fingerprint validation for browser type: {browser_type}, profile: {profile_name}")
    validation_results = {"browser_type": browser_type, "profile_name": profile_name, "tests": {}}

    browser_handle = None
    try:
        browser_handle = await create_instance(browser_type=browser_type, proxy=proxy, profile_name=profile_name)
        page = await browser_handle.new_tab()

        validation_results["tests"]["programmatic"] = await run_programmatic_checks_async(page)

        # Run external checks
        validation_results["tests"]["sannysoft"] = await test_sannysoft_async(page)
        validation_results["tests"]["amiunique"] = await test_amiunique_async(page)
        validation_results["tests"]["pixelscan"] = await test_pixelscan_async(page)
        validation_results["tests"]["creepjs"] = await test_creepjs_async(page)

    except Exception as e:
        logger.error(f"Overall error during fingerprint validation: {e}", exc_info=True)
        validation_results["overall_status"] = "failure"
        validation_results["error"] = str(e)
    finally:
        if browser_handle:
            await browser_handle.close()
            logger.info("Browser closed after validation.")

    if "overall_status" not in validation_results:
        validation_results["overall_status"] = "success"  # Assume success if no errors caught

    logger.info(f"Fingerprint validation complete for {browser_type}. Results: {validation_results}")
    return validation_results


if __name__ == "__main__":
    # Example usage for testing
    async def main():
        # Test Firefox with uk_desktop_mac profile
        firefox_results = await validate_fingerprint_async(browser_type="firefox", profile_name="uk_desktop_mac")
        print("\n--- Firefox (uk_desktop_mac) Results ---")
        print(firefox_results)

        # Test Chromium Stealth
        chromium_stealth_results = await validate_fingerprint_async(browser_type="chromiumstealth")
        print("\n--- Chromium Stealth Results ---")
        print(chromium_stealth_results)

    asyncio.run(main())
