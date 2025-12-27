"""
Scrapling-based scraper with adaptive element tracking.

Provides:
- Faster parsing than BeautifulSoup (774x in benchmarks)
- Adaptive selectors that survive site changes
- StealthyFetcher for anti-bot bypass
- Integration with mubeng proxy rotation
- Auto-encoding detection (windows-1251, UTF-8, etc.)

Usage:
    class ImotBgScraper(ScraplingMixin, BaseSiteScraper):
        ...
"""

import hashlib
import json
import re
from pathlib import Path
from typing import List, Optional, Tuple, Union

import chardet
import httpx
from loguru import logger
from scrapling import Adaptor
from scrapling.fetchers import Fetcher, StealthyFetcher

from config.settings import MUBENG_PROXY, PROXY_TIMEOUT_MS, PROXY_TIMEOUT_SECONDS

# Storage for adaptive selectors
SELECTOR_STORAGE = Path(__file__).parent.parent / "data" / "scrapling_selectors"
SELECTOR_STORAGE.mkdir(parents=True, exist_ok=True)

# Mubeng CA certificate for HTTPS MITM proxy
# -----------------------------------------
# Mubeng intercepts HTTPS traffic to rotate through upstream proxies.
# This requires Firefox/Camoufox to trust mubeng's CA certificate.
# Without this, you'll get SEC_ERROR_UNKNOWN_ISSUER errors.
#
# The certificate is extracted by setup.sh from mubeng's /cert endpoint.
# See: docs/architecture/SSL_PROXY_SETUP.md for full documentation.
#
# Note: Target websites never see this certificate - they receive normal
# HTTPS requests. This cert is only for the local browser-to-mubeng connection.
MUBENG_CA_CERT = Path(__file__).parent.parent / "data" / "certs" / "mubeng-ca.pem"

# Common encodings for Bulgarian/Cyrillic sites
CYRILLIC_ENCODINGS = ["windows-1251", "utf-8", "iso-8859-5", "koi8-r"]


def detect_encoding(content: bytes, headers: dict = None) -> str:
    """
    Detect encoding from content and headers.

    Priority:
    1. HTTP Content-Type header
    2. HTML meta charset tag
    3. chardet auto-detection
    4. Default to utf-8

    Args:
        content: Raw bytes from response
        headers: HTTP response headers

    Returns:
        Detected encoding string
    """
    # 1. Check HTTP headers
    if headers:
        content_type = headers.get("content-type", "")
        charset_match = re.search(r"charset=([^\s;]+)", content_type, re.IGNORECASE)
        if charset_match:
            encoding = charset_match.group(1).strip('"\'')
            logger.debug(f"Encoding from header: {encoding}")
            return encoding

    # 2. Check HTML meta tag (look in first 1024 bytes)
    head_content = content[:1024].decode("ascii", errors="ignore")

    # <meta charset="...">
    meta_match = re.search(r'<meta[^>]+charset=["\']?([^"\'\s>]+)', head_content, re.IGNORECASE)
    if meta_match:
        encoding = meta_match.group(1)
        logger.debug(f"Encoding from meta charset: {encoding}")
        return encoding

    # <meta http-equiv="Content-Type" content="...; charset=...">
    http_equiv_match = re.search(
        r'<meta[^>]+content=["\'][^"\']*charset=([^"\'\s;]+)',
        head_content,
        re.IGNORECASE
    )
    if http_equiv_match:
        encoding = http_equiv_match.group(1)
        logger.debug(f"Encoding from meta http-equiv: {encoding}")
        return encoding

    # 3. Auto-detect with chardet
    detected = chardet.detect(content[:10000])  # Sample first 10KB
    if detected and detected.get("encoding"):
        confidence = detected.get("confidence", 0)
        encoding = detected["encoding"]
        logger.debug(f"Encoding from chardet: {encoding} (confidence: {confidence:.0%})")
        if confidence > 0.7:
            return encoding

    # 4. Default
    logger.debug("Encoding defaulting to utf-8")
    return "utf-8"


def fetch_with_encoding(
    url: str,
    proxy: Optional[str] = None,
    timeout: int = PROXY_TIMEOUT_SECONDS,
    headers: dict = None,
) -> Tuple[str, str]:
    """
    Fetch URL with automatic encoding detection.

    Args:
        url: Target URL
        proxy: Optional proxy URL
        timeout: Request timeout in seconds
        headers: Optional custom headers

    Returns:
        Tuple of (decoded_html, detected_encoding)
    """
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "bg-BG,bg;q=0.9,en;q=0.8",
    }
    if headers:
        default_headers.update(headers)

    with httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        proxy=proxy,
    ) as client:
        response = client.get(url, headers=default_headers)
        response.raise_for_status()

        # Get raw bytes
        content = response.content

        # Detect encoding
        encoding = detect_encoding(content, dict(response.headers))

        # Decode
        try:
            html = content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            # Fallback: try common Cyrillic encodings
            for enc in CYRILLIC_ENCODINGS:
                try:
                    html = content.decode(enc)
                    encoding = enc
                    logger.warning(f"Fallback encoding used: {enc}")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                # Last resort: decode with errors ignored
                html = content.decode("utf-8", errors="replace")
                encoding = "utf-8 (with replacements)"

        return html, encoding


class ScraplingMixin:
    """
    Mixin class to add Scrapling capabilities to scrapers.

    Benefits over BeautifulSoup:
    - 774x faster parsing performance
    - Auto-encoding detection (windows-1251, UTF-8 for Bulgarian sites)
    - Adaptive selectors that survive site HTML changes

    Core Methods:
    - parse(): Parse HTML with Scrapling Adaptor
    - css()/css_first(): Select elements with adaptive matching
    - get_text()/get_attr(): Safe element data extraction
    - fetch_stealth(): Fetch with anti-bot bypass
    - fetch_fast(): Fast HTTP fetch without JS

    Adaptive Mode (selector resilience):
    - First run: auto_save=True saves element signatures to data/scrapling_selectors/
    - Subsequent runs: auto_match=True finds elements even if CSS selectors break
    - Toggle via: scraper.adaptive_mode = True/False

    Usage:
        class MyScraper(ScraplingMixin, BaseSiteScraper):
            def __init__(self):
                super().__init__()
                self.adaptive_mode = True

            def extract(self, html):
                page = self.parse(html)
                title = self.css_first(page, "h1", identifier="my_title",
                                       auto_save=True, auto_match=self.adaptive_mode)
                return self.get_text(title)

    See also:
    - websites/SCRAPER_GUIDE.md - Full usage documentation
    - docs/architecture/DESIGN_PATTERNS.md - Mixin pattern explanation
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selector_storage_path = SELECTOR_STORAGE / f"{self.site_name}_selectors.json"
        self._adaptive_enabled = True
        self.use_llm = False  # Enable LLM-powered extraction (set True in scraper)

    def parse(self, html: str, url: str = "") -> Adaptor:
        """
        Parse HTML with Scrapling.

        Args:
            html: Raw HTML content
            url: Page URL (used for relative link resolution)

        Returns:
            Adaptor object for element selection
        """
        return Adaptor(html, url=url, auto_save=self._adaptive_enabled)

    def css(
        self,
        page: Adaptor,
        selector: str,
        auto_match: bool = False,
        auto_save: bool = False,
        identifier: str = "",
    ) -> List:
        """
        Select elements using CSS selector.

        Args:
            page: Scrapling Adaptor object
            selector: CSS selector string
            auto_match: If True, use fuzzy matching to find elements
                       even if the selector changed (requires prior auto_save)
            auto_save: If True, save element signature for future auto_match
            identifier: Unique ID for this selector (for auto_match/auto_save)

        Returns:
            List of matching elements
        """
        try:
            return page.css(
                selector,
                identifier=identifier,
                auto_match=auto_match,
                auto_save=auto_save,
            )
        except Exception as e:
            logger.warning(f"CSS selector failed: {selector} - {e}")
            return []

    def css_first(
        self,
        page: Adaptor,
        selector: str,
        auto_match: bool = False,
        auto_save: bool = False,
        identifier: str = "",
        default=None,
    ):
        """
        Select first matching element.

        Args:
            page: Scrapling Adaptor object
            selector: CSS selector string
            auto_match: If True, use fuzzy matching (requires prior auto_save)
            auto_save: If True, save element signature for future auto_match
            identifier: Unique ID for this selector
            default: Value to return if no match found

        Returns:
            First matching element or default
        """
        try:
            result = page.css_first(
                selector,
                identifier=identifier,
                auto_match=auto_match,
                auto_save=auto_save,
            )
            return result if result else default
        except Exception as e:
            logger.warning(f"CSS first selector failed: {selector} - {e}")
            return default

    def xpath(self, page: Adaptor, query: str) -> List:
        """
        Select elements using XPath.

        Args:
            page: Scrapling Adaptor object
            query: XPath query string

        Returns:
            List of matching elements
        """
        try:
            return page.xpath(query)
        except Exception as e:
            logger.warning(f"XPath query failed: {query} - {e}")
            return []

    def get_text(self, element, default: str = "") -> str:
        """
        Safely extract text from element.

        Args:
            element: Scrapling element
            default: Value if element is None or has no text

        Returns:
            Element text or default
        """
        if element is None:
            return default
        try:
            # Try .text first
            text = element.text
            if text and text.strip():
                return text.strip()

            # Fallback: extract from html_content
            if hasattr(element, 'html_content'):
                html = element.html_content
                # Strip HTML tags
                clean = re.sub(r'<[^>]+>', ' ', html)
                clean = re.sub(r'\s+', ' ', clean).strip()
                return clean if clean else default

            return default
        except Exception:
            return default

    def get_page_text(self, page: Adaptor) -> str:
        """
        Extract all visible text from page.

        Strips HTML tags and normalizes whitespace.

        Args:
            page: Scrapling Adaptor object

        Returns:
            Clean text content
        """
        try:
            html = page.html_content

            # Remove script and style content
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', html)

            # Decode HTML entities
            import html as html_lib
            text = html_lib.unescape(text)

            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text).strip()

            return text
        except Exception as e:
            logger.warning(f"get_page_text failed: {e}")
            return ""

    def get_attr(self, element, attr: str, default: str = "") -> str:
        """
        Safely get attribute from element.

        Args:
            element: Scrapling element
            attr: Attribute name
            default: Value if not found

        Returns:
            Attribute value or default
        """
        if element is None:
            return default
        try:
            return element.attrib.get(attr, default)
        except Exception:
            return default

    # --- Fetcher Methods ---

    def fetch(
        self,
        url: str,
        proxy: Optional[str] = None,
        timeout: int = PROXY_TIMEOUT_SECONDS,
    ) -> Adaptor:
        """
        Fetch page with automatic encoding detection.

        Recommended for Bulgarian sites (handles windows-1251, UTF-8, etc.)

        Args:
            url: Target URL
            proxy: Optional proxy URL (defaults to mubeng if available)
            timeout: Request timeout in seconds

        Returns:
            Scrapling Adaptor with properly decoded content
        """
        try:
            html, encoding = fetch_with_encoding(url, proxy=proxy, timeout=timeout)
            logger.debug(f"Fetched {url} with encoding: {encoding}")
            return Adaptor(html, url=url, auto_save=self._adaptive_enabled)
        except Exception as e:
            logger.error(f"Fetch failed: {url} - {e}")
            raise

    def fetch_stealth(
        self,
        url: str,
        humanize: bool = True,
        timeout: int = PROXY_TIMEOUT_MS,
        skip_proxy: bool = False,
    ) -> Adaptor:
        """
        Fetch page with Camoufox (anti-bot bypass).

        Uses modified Firefox (Camoufox) with:
        - Fingerprint spoofing
        - WebRTC leak protection
        - Human-like behavior simulation
        - Mubeng proxy rotation with SSL certificate (default)

        Args:
            url: Target URL
            humanize: Simulate human mouse movement
            timeout: Request timeout in ms
            skip_proxy: Set True to skip mubeng proxy

        Returns:
            Scrapling Adaptor with page content
        """
        from camoufox.sync_api import Camoufox

        try:
            # Build Camoufox config with SSL certificate
            # The certificatePaths option tells Camoufox to trust mubeng's CA,
            # allowing HTTPS traffic to flow through the MITM proxy without
            # SEC_ERROR_UNKNOWN_ISSUER errors. See: docs/architecture/SSL_PROXY_SETUP.md
            config = {}
            if MUBENG_CA_CERT.exists():
                config["certificatePaths"] = [str(MUBENG_CA_CERT)]

            # Build proxy config
            proxy_config = None
            if not skip_proxy:
                proxy_config = {"server": MUBENG_PROXY}

            with Camoufox(
                headless=True,
                humanize=humanize,
                geoip=True,
                block_webrtc=True,
                proxy=proxy_config,
                config=config,
            ) as browser:
                page = browser.new_page()
                page.goto(url, timeout=timeout, wait_until="networkidle")
                html = page.content()

            logger.debug(f"Camoufox fetch: {url} - success")
            return Adaptor(html, url=url, auto_save=self._adaptive_enabled)
        except Exception as e:
            logger.error(f"Camoufox fetch failed: {url} - {e}")
            raise

    def fetch_fast(
        self,
        url: str,
        timeout: int = PROXY_TIMEOUT_MS // 3,
        skip_proxy: bool = False,
    ) -> Adaptor:
        """
        Fast HTTP fetch without browser (no JS execution).

        Use for:
        - Simple pages without JS protection
        - API endpoints
        - Pages that don't need full rendering

        Args:
            url: Target URL
            timeout: Request timeout in ms
            skip_proxy: Set True to skip mubeng proxy

        Returns:
            Scrapling Adaptor with page content
        """
        try:
            fetch_kwargs = {
                "url": url,
                "timeout": timeout,
            }
            if not skip_proxy:
                fetch_kwargs["proxy"] = MUBENG_PROXY

            page = Fetcher.fetch(**fetch_kwargs)
            logger.debug(f"Fetcher: {url} - success")
            return page
        except Exception as e:
            logger.error(f"Fetcher failed: {url} - {e}")
            raise

    # --- Adaptive Selector Management ---

    def save_selectors(self, selectors: dict):
        """
        Save selector patterns for future adaptive matching.

        Args:
            selectors: Dict of {name: selector} mappings
        """
        try:
            existing = self._load_selectors()
            existing.update(selectors)
            with open(self._selector_storage_path, "w") as f:
                json.dump(existing, f, indent=2)
            logger.info(f"Saved {len(selectors)} selectors for {self.site_name}")
        except Exception as e:
            logger.warning(f"Failed to save selectors: {e}")

    def _load_selectors(self) -> dict:
        """Load saved selector patterns."""
        if self._selector_storage_path.exists():
            try:
                with open(self._selector_storage_path) as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    # --- Utility Methods ---

    def extract_all_links(self, page: Adaptor, pattern: str = None) -> List[str]:
        """
        Extract all links from page, optionally filtered by pattern.

        Args:
            page: Scrapling Adaptor object
            pattern: Regex pattern to filter URLs

        Returns:
            List of URLs
        """
        links = []
        for a in page.css("a[href]"):
            href = self.get_attr(a, "href")
            if href and not href.startswith(("#", "javascript:")):
                if pattern is None or re.search(pattern, href):
                    links.append(href)
        return list(set(links))  # Deduplicate

    def extract_images(self, page: Adaptor, pattern: str = None) -> List[str]:
        """
        Extract all image URLs from page.

        Args:
            page: Scrapling Adaptor object
            pattern: Regex pattern to filter image URLs

        Returns:
            List of image URLs
        """
        images = []
        for img in page.css("img[src], img[data-src]"):
            src = self.get_attr(img, "src") or self.get_attr(img, "data-src")
            if src and not src.startswith("data:"):
                if pattern is None or re.search(pattern, src):
                    images.append(src)
        return list(set(images))

    def generate_content_hash(self, page: Adaptor, selector: str = None) -> str:
        """
        Generate hash of page content for change detection.

        Args:
            page: Scrapling Adaptor object
            selector: Optional CSS selector to hash only specific content

        Returns:
            MD5 hash of content
        """
        if selector:
            element = self.css_first(page, selector)
            content = self.get_text(element) if element else ""
        else:
            content = page.text if hasattr(page, 'text') else str(page)

        return hashlib.md5(content.encode()).hexdigest()
