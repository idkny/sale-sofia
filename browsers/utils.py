import asyncio
import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

import tldextract
import yaml
from loguru import logger
from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from pydantic import BaseModel
from pyvirtualdisplay import Display

from paths import CHROMIUM_DIR


def validate_proxy(proxy: str | dict | None) -> dict | None:
    """Validates and formats the proxy input."""
    if isinstance(proxy, str) and proxy:
        # Assuming the string is a URL like 'http://user:pass@host:port'
        # Playwright expects a dict with 'server' and optionally 'username', 'password'
        parsed = urlparse(proxy)
        if not parsed.hostname:
            return None
        proxy_dict = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
        if parsed.username:
            proxy_dict["username"] = parsed.username
        if parsed.password:
            proxy_dict["password"] = parsed.password
        return proxy_dict
    elif isinstance(proxy, dict):
        # Assume it's already in the correct dict format for Playwright
        return proxy
    return None


@contextmanager
def xvfb_manager(width=1920, height=1080):
    """A context manager to run code within a virtual X display."""
    display = None
    try:
        display = Display(visible=0, size=(width, height))
        display.start()
        logger.info(f"Started virtual display: {display.display}")
        yield
    except Exception as e:
        logger.error(f"Failed to start virtual display: {e}")
        # If display fails to start, still yield to not break the calling code
        yield
    finally:
        if display and display.is_alive():
            display.stop()
            logger.info("Stopped virtual display.")


def extract_chromium():
    """Checks for the ungoogled-chromium browser directory and provides instructions if it's missing."""
    if not CHROMIUM_DIR.is_dir():
        error_msg = (
            f"Chromium directory not found at '{CHROMIUM_DIR}'. "
            "Please run the setup script to download and extract it: ./setup.sh"
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)


class CamoufoxProfile(BaseModel):
    """Pydantic model for Camoufox fingerprint profiles."""

    os: str
    screen: dict[str, Any]
    webgl: dict[str, Any]
    fonts: list[str]
    geolocation: Optional[dict[str, Any]] = None
    locale: Optional[dict[str, Any]] = None
    timezone: Optional[str] = None
    navigator: dict[str, Any]


def load_camoufox_profile(profile_name: str) -> CamoufoxProfile:
    """Loads a Camoufox profile from the browsers/profile/camoufox directory."""
    profile_path = Path(f"/home/wow/Projects/Bg-Estate/browsers/profile/camoufox/{profile_name}.yaml")
    with open(profile_path, "r") as f:
        profile_data = yaml.safe_load(f)
    return CamoufoxProfile(**profile_data)


async def fetch_html(page: Page, url: str, timeout_seconds: int = 15) -> tuple[str, str | None]:
    """Fetch the HTML content of a URL using a provided Playwright Page object.

    Args:
        page (Page): An active Playwright Page to use for navigation.
        url (str): The URL to fetch.
        timeout_seconds (int): The timeout for the page navigation.

    Returns:
        A tuple containing:
        - The HTML content as a string (or an empty string on failure).
        - An error message string if an error occurred, otherwise None.

    """
    try:
        logger.info(f"Fetching URL: {url}")
        await page.goto(url, timeout=timeout_seconds * 1000, wait_until="domcontentloaded")
        await asyncio.sleep(10)  # Added delay for observation
        html_content = await page.content()
        logger.success(f"Successfully fetched HTML for: {url}")
        return html_content, None
    except PlaywrightTimeoutError:
        error_msg = f"Timeout error ({timeout_seconds}s) while fetching: {url}"
        logger.warning(error_msg)
        return "", error_msg
    except Exception as e:
        error_msg = f"An unexpected error occurred while fetching {url}: {e}"
        logger.error(error_msg)
        return "", error_msg


class AnalyzePageParams(BaseModel):
    """Parameters for analyzing a web page."""

    url: str


async def _extract_element_details(page: Page, selector_query: str, element_type_label: str) -> list[dict[str, Any]]:
    elements_found = []
    try:
        element_handles = await page.query_selector_all(selector_query)
        for el_handle in element_handles:
            tag_name = await el_handle.evaluate("element => element.tagName.toLowerCase()")
            text_content = await el_handle.text_content()
            attrs = await el_handle.evaluate(
                """element => Array.from(element.attributes).reduce("""
                """(obj, attr) => { obj[attr.name] = attr.value; return obj; }, {})"""
            )

            robust_selector = selector_query

            elements_found.append(
                {
                    "selector_used": selector_query,
                    "identified_selector": robust_selector,
                    "tag_name": tag_name,
                    "text_content": text_content.strip() if text_content else None,
                    "attributes": attrs,
                    "element_type": element_type_label,
                }
            )
    except Exception as e:
        logger.error(f"Error extracting {element_type_label} with selector '{selector_query}': {e}")
    return elements_found


async def _extract_and_deduplicate_elements(
    page: Page, queries: list[str], element_type_label: str
) -> list[dict[str, Any]]:
    all_elements = []
    for query in queries:
        all_elements.extend(await _extract_element_details(page, query, element_type_label))
    if all_elements:
        return [json.loads(s) for s in {json.dumps(d, sort_keys=True) for d in all_elements}]
    return []


def _get_link_category(href: str, page_current_url: str, page_domain_info: Any) -> str:
    """Determines if a link is internal, external, or invalid."""
    if not href:
        return "invalid"
    href = href.strip()

    if href.startswith(("mailto:", "tel:", "javascript:", "#")):
        return "invalid"

    if not href.startswith(("http://", "https://")):
        href = urljoin(page_current_url, href)

    try:
        parsed_link = urlparse(href)
        if parsed_link.scheme not in ["http", "https"]:
            return "invalid"
        link_domain_info = tldextract.extract(href)
        if not link_domain_info.registered_domain:
            return "invalid"
        if link_domain_info.registered_domain == page_domain_info.registered_domain:
            return "internal"
        else:
            return "external"
    except ValueError:
        logger.warning(f"Could not parse href: '{href}' on page {page_current_url}")
        return "invalid"


async def _analyze_links(page: Page, page_current_url: str) -> tuple[float, float]:
    internal_links_count, external_links_count = 0, 0
    if not page_current_url:
        logger.warning("Could not determine page.url for link analysis.")
        return 0.0, 0.0

    try:
        page_domain_info = tldextract.extract(page_current_url)
        link_locators = page.locator("a[href]")
        num_links = await link_locators.count()
        if num_links > 0:
            for i in range(num_links):
                href = await link_locators.nth(i).get_attribute("href")
                link_category = _get_link_category(href, page_current_url, page_domain_info)

                if link_category == "internal":
                    internal_links_count += 1
                elif link_category == "external":
                    external_links_count += 1

            total_valid_links = internal_links_count + external_links_count
            if total_valid_links > 0:
                return (
                    round(internal_links_count / total_valid_links, 3),
                    round(external_links_count / total_valid_links, 3),
                )
    except Exception as e:
        logger.error(f"Error during link analysis for {page_current_url}: {e}")
    return 0.0, 0.0


async def _determine_site_type(url: str, page: Page, property_card_elements: list[dict[str, Any]]) -> str:
    site_type = "unknown"
    if (
        any(keyword in url for keyword in ["realestate", "property", "listing", "imot"])
        or len(property_card_elements) > 0
    ):
        site_type = "listing"
    elif "blog" in url or await page.query_selector("article.post, section.blog-post, div.article-content"):
        site_type = "content/blog"
    return site_type
