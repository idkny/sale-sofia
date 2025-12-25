---
id: 20251201_browser_scraper
type: extraction
subject: browser
source_repo: Scraper
description: "Browser fingerprinting, stealth mode, Playwright automation"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [extraction, browser, fingerprinting, playwright, camoufox, stealth]
---

# SUBJECT: browser/

**Source**: `idkny/Scraper`
**Files Extracted**: 4 files
**Quality**: HIGH VALUE - UNIQUE (no other repo has browser fingerprinting)

---

## 1. Fingerprint Agent Factory (fingerprints.py)

Main entry point for fingerprinted agents with mode selection.

```python
# Scraper/Fingerprint/fingerprint.py
from Fingerprint.browsers import launch_camoufox_browser, launch_fingerprint_chromium
from Fingerprint.stealth import get_stealth_fetcher
from Fingerprint.http_fetcher import get_http_fetcher
from Fingerprint.Proxy_Service.free_proxies import ProxyService
from Fingerprint.Proxy_Service.paid_proxies import PaidProxyService


def get_proxy(protocols=None, anonymity=None, country=None, paid=False, as_dict=False):
    """Get proxy from free or paid service."""
    if paid:
        return PaidProxyService().get_proxy(
            protocol=protocols[0] if protocols else "http",
            country=country[0] if country else None,
            as_dict=as_dict
        )
    else:
        return ProxyService().get_proxy(
            protocol=protocols,
            anonymity=anonymity,
            country=country,
            require_geolocation=False,
            require_anonymous=False
        )


def get_fingerprint_agent(
    mode: str = "http",
    browser: str = None,
    proxy: str = None,
    headless: bool = True,
    stealth: bool = True
):
    """
    Returns a fingerprinted agent based on mode:
    - "http": basic HTTP fetcher with spoofed headers
    - "stealth": Scrapling StealthyFetcher
    - "browser": Playwright browser (firefox/chromium)
    """
    if mode == "http":
        return get_http_fetcher(proxy)

    elif mode == "stealth":
        return get_stealth_fetcher(proxy)

    elif mode == "browser":
        if browser == "firefox":
            return launch_camoufox_browser(proxy=proxy, headless=headless)
        elif browser == "chromium":
            return launch_fingerprint_chromium(proxy=proxy, headless=headless)
        else:
            raise ValueError("Invalid browser type. Choose 'firefox' or 'chromium'.")

    else:
        raise ValueError("Invalid mode. Choose from 'http', 'stealth', or 'browser'.")
```

---

## 2. Browser Launchers (browsers.py)

Playwright-based browser automation with fingerprint-resistant builds.

```python
# Scraper/Fingerprint/browsers.py

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from Fingerprint.utils.fingerprint_utils import get_fingerprint_debug_info

# Define paths to fingerprinted browser builds using pathlib
CAMOUFOX_PATH = Path("/usr/bin/firefox-camoufox")  # Update to actual path
FINGERPRINT_CHROMIUM_PATH = Path("/usr/bin/fingerprint-chromium")  # Update to actual path


async def _launch_browser(browser_type, executable_path, headless, args, debug=False):
    """Internal browser launcher with Playwright."""
    async with async_playwright() as p:
        browser = await getattr(p, browser_type).launch(
            executable_path=str(executable_path),
            headless=headless,
            args=args
        )
        context = await browser.new_context()
        page = await context.new_page()

        if debug:
            await page.goto("https://fingerprintjs.com/demo")
            await get_fingerprint_debug_info(page)
            await page.wait_for_timeout(5000)

        return page


def launch_camoufox_browser(proxy=None, headless=True, debug=False):
    """
    Launch fingerprint-resistant Firefox (Camoufox).
    Camoufox is a hardened Firefox fork designed to evade fingerprinting.
    """
    args = []
    if proxy:
        args.append(f"--proxy-server={proxy}")
    return asyncio.run(_launch_browser(
        browser_type="firefox",
        executable_path=CAMOUFOX_PATH,
        headless=headless,
        args=args,
        debug=debug
    ))


def launch_fingerprint_chromium(proxy=None, headless=True, debug=False):
    """
    Launch Chromium with anti-detection flags.
    Disables automation detection features.
    """
    args = [
        "--disable-blink-features=AutomationControlled",
        "--start-maximized",
    ]
    if proxy:
        args.append(f"--proxy-server={proxy}")
    return asyncio.run(_launch_browser(
        browser_type="chromium",
        executable_path=FINGERPRINT_CHROMIUM_PATH,
        headless=headless,
        args=args,
        debug=debug
    ))
```

---

## 3. Stealth Fetcher (stealth.py)

Scrapling-based stealth HTTP fetcher for anti-bot bypass.

```python
# Scraper/Fingerprint/stealth.py

from scrapling.fetchers import StealthyFetcher


def get_stealth_fetcher(proxy=None):
    """
    Initializes a StealthyFetcher with optional proxy support.
    This fetcher is optimized to bypass anti-bot protections with minimal overhead.
    """
    options = {}

    if proxy:
        options["proxy"] = proxy

    # Add realistic headers (Scrapling may already do this internally)
    options["headers"] = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "DNT": "1",
        "Connection": "keep-alive",
        # Add more realistic headers here if needed
    }

    return StealthyFetcher(options=options)
```

---

## 4. Fingerprint Debug Info (fingerprint_manager.py)

Browser fingerprint extraction for debugging and verification.

```python
from pathlib import Path  # for future use if you later save data

def get_fingerprint(strategy: str, config: dict) -> dict:
    """Placeholder fingerprint manager: could expand to load real profiles."""
    return {
        "strategy": strategy,
        "user_agent": "Mozilla/5.0",
        "viewport": {"width": 1920, "height": 1080},
        "timezone": "Europe/Sofia"
    }


async def get_fingerprint_debug_info(page):
    """
    Extract browser fingerprint for debugging.
    Tests: User-Agent, platform, hardware, screen, WebGL.
    """
    data = await page.evaluate("""
        () => {
            return {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                hardwareConcurrency: navigator.hardwareConcurrency,
                deviceMemory: navigator.deviceMemory,
                screen: {
                    width: screen.width,
                    height: screen.height
                },
                webglVendor: (() => {
                    try {
                        let canvas = document.createElement('canvas');
                        let gl = canvas.getContext('webgl');
                        let debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                        return {
                            vendor: gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL),
                            renderer: gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
                        };
                    } catch (e) {
                        return null;
                    }
                })()
            };
        }
    """)
    print(data)
```

---

## CONCLUSIONS

### What is GOOD / Usable (Direct Port)

1. **Agent Factory Pattern** (`get_fingerprint_agent`)
   - Clean mode selection (http, stealth, browser)
   - Proxy integration built-in
   - Headless control

2. **Playwright Integration**
   - Async browser automation
   - Custom browser binary support
   - Anti-detection flags for Chromium

3. **Stealth Fetcher**
   - Scrapling integration for anti-bot bypass
   - Realistic headers

4. **Fingerprint Debug**
   - WebGL extraction
   - Hardware info
   - Screen/viewport

### What is OUTDATED

- Hardcoded browser paths (`/usr/bin/firefox-camoufox`) - need config
- Missing `http_fetcher.py` file (imported but not present)
- Basic User-Agent strings (need rotation)

### What Must Be REWRITTEN

1. **Browser paths** - Move to config, support multiple platforms
2. **Add http_fetcher.py** - Missing implementation
3. **Fingerprint profiles** - Load from JSON/YAML instead of hardcoded
4. **User-Agent rotation** - Add pool of real UAs
5. **Add async context manager** - Better resource cleanup

### How It Fits Into AutoBiz

**Location**: `autobiz/tools/browser/`
- `browser_factory.py` - Agent factory (get_fingerprint_agent)
- `browsers.py` - Playwright launchers
- `stealth.py` - StealthyFetcher wrapper
- `fingerprints.py` - Fingerprint profiles and debug

**Integration Points**:
- Scraper uses browser agents for JS-heavy sites
- Anti-bot bypass for protected APIs
- Fingerprint verification for QA

### Conflicts/Duplicates

- **No conflicts** - This is the ONLY repo with browser fingerprinting
- MarketIntel has no browser automation
- SerpApi specification has no browser support
- Ollama-Rag has no browser support

### Best Version

**SCRAPER is the ONLY version** - Direct port recommended

---

## Dependencies

```txt
# requirements.txt additions
playwright>=1.40.0
scrapling>=0.2.0
camoufox>=0.4.11
```

**Browser Installation**:
```bash
# Install Playwright browsers
playwright install chromium firefox

# For Camoufox (fingerprint-resistant Firefox)
# See: https://github.com/AresS31/camoufox
```

---

## Usage Example

```python
# HTTP mode (fastest, basic)
agent = get_fingerprint_agent(mode="http", proxy="http://proxy:8080")

# Stealth mode (anti-bot bypass)
agent = get_fingerprint_agent(mode="stealth", proxy="http://proxy:8080")

# Browser mode - Firefox (best fingerprint resistance)
page = get_fingerprint_agent(
    mode="browser",
    browser="firefox",
    proxy="http://proxy:8080",
    headless=True
)

# Browser mode - Chromium (faster, less stealth)
page = get_fingerprint_agent(
    mode="browser",
    browser="chromium",
    headless=False  # Visible for debugging
)

# Debug fingerprint
await get_fingerprint_debug_info(page)
```
