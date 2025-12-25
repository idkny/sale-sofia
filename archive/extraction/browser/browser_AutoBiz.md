---
id: 20251201_browser_autobiz
type: extraction
subject: browser
source_repo: Auto-Biz
description: "Browser automation, strategy pattern, fingerprinting, profile management from Auto-Biz"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [browser, playwright, camoufox, fingerprinting, strategy-pattern, auto-biz]
---

# SUBJECT: browser/

**Source Repository**: Auto-Biz (https://github.com/idkny/Auto-Biz)
**Extracted From**: `browsers/browsers_main.py`, `browsers/strategies/*.py`, `browsers/profile_manager.py`, `browsers/validator.py`, `browsers/utils.py`

---

## 1. EXTRACTED CODE

### 1.1 Strategy Pattern with Dynamic Discovery

```python
"""Browser automation and management."""

import importlib
import logging
import pkgutil
import time
from typing import Any

from playwright.sync_api import Page

from . import strategies
from .strategies.base import BaseBrowserStrategy

logger = logging.getLogger(__name__)

_strategy_registry: dict[str, type[BaseBrowserStrategy]] = {}


def _discover_strategies():
    """Dynamically discovers and registers browser strategies."""
    logger.info("Discovering browser strategies...")
    for _, name, _ in pkgutil.iter_modules(strategies.__path__):
        logger.info(f"Found strategy module: {name}")

        try:
            module = importlib.import_module(f".{name}", package=strategies.__name__)
            for item_name in dir(module):
                item = getattr(module, item_name)
                if isinstance(item, type) and issubclass(item, BaseBrowserStrategy) and item is not BaseBrowserStrategy:
                    strategy_name = item.__name__.replace("Strategy", "").lower()
                    logger.info(f"Registering strategy: '{strategy_name}'")
                    register_strategy(strategy_name, item)
        except ImportError as e:
            logger.exception(f"Failed to import strategy module {name}: {e}")


def register_strategy(name: str, strategy_class: type[BaseBrowserStrategy]) -> None:
    """Registers a new browser strategy."""
    if name in _strategy_registry:
        logger.warning(f"Strategy '{name}' is already registered. Overwriting.")
    _strategy_registry[name] = strategy_class


def create_instance(
    browser_type: str,
    proxy: str | dict | None = None,
    profile_name: str | None = None,
    *,
    as_emunium: bool = False,
    headless: bool | None = None,
    max_tabs: int = 10,
    cdp_url: str | None = None,
    ignore_https_errors: bool = False,
    run_on_main_display: bool = False,
) -> "BrowserHandle":
    """Creates and returns a browser instance based on the specified type."""
    if not _strategy_registry:
        _discover_strategies()

    if "chromium" in browser_type:
        from .utils import extract_chromium
        extract_chromium()

    browser_type = browser_type.lower()
    if browser_type not in _strategy_registry:
        raise ValueError(
            f"Unsupported browser type: '{browser_type}'. "
            f"Available: {list(_strategy_registry.keys())}"
        )

    strategy_class = _strategy_registry[browser_type]

    from .utils import validate_proxy
    validated_proxy = validate_proxy(proxy)

    strategy_args = {
        "proxy": validated_proxy,
        "profile_name": profile_name,
        "ignore_https_errors": ignore_https_errors,
    }
    if "gui" in browser_type:
        if cdp_url:
            strategy_args["cdp_url"] = cdp_url
        strategy_args["run_on_main_display"] = run_on_main_display

    strategy = strategy_class(**strategy_args)
    handle = BrowserHandle(strategy, as_emunium=as_emunium)
    return handle
```

### 1.2 BrowserHandle Context Manager

```python
import threading

class BrowserHandle:
    """A handle to a managed browser instance, providing a clean public API."""

    def __init__(self, strategy: BaseBrowserStrategy, as_emunium: bool = False) -> None:
        self._strategy = strategy
        self._as_emunium = as_emunium
        self._browser = None
        self._context = None
        self._start_time = time.monotonic()
        self.emunium: EmuniumWrapper | None = None

    def _initialize(self) -> None:
        print(f"[BrowserHandle._initialize] Thread ID: {threading.get_ident()}")
        self._browser, self._context = self._strategy.launch()
        if self._as_emunium:
            self.emunium = EmuniumWrapper(self.page)

    def new_tab(self, url: str | None = None) -> Page:
        """Opens a new tab/page in the browser context."""
        page = self._context.new_page()
        if url:
            page.goto(url)
        return page

    def goto(self, url: str, **kwargs: Any) -> None:
        """Navigates the main page to a URL."""
        self.page.goto(url, **kwargs)

    def evaluate(self, expression: str, **kwargs: Any) -> Any:
        """Evaluates a JavaScript expression in the page context."""
        return self.page.evaluate(expression, **kwargs)

    def screenshot(self, path: str, **kwargs: Any) -> None:
        """Takes a screenshot of the current page."""
        self.page.screenshot(path=path, **kwargs)

    def start_har(self, path: str, **kwargs: Any) -> None:
        """Starts HAR (HTTP Archive) tracing."""
        self._context.tracing.start(screenshots=True, snapshots=True, sources=True)

    def stop_har(self, path: str) -> None:
        """Stops HAR tracing and saves the file."""
        self._context.tracing.stop(path=path)

    @property
    def page(self) -> Page:
        """Returns the primary page, creating one if necessary."""
        if not self._context.pages:
            return self.new_tab()
        return self._context.pages[0]

    def close(self) -> None:
        """Closes the browser and cleans up all resources."""
        if self._context:
            self._context.close()
        if self._strategy:
            self._strategy.close()
        elapsed_s = time.monotonic() - self._start_time
        logger.info(f"Browser session closed. Duration: {elapsed_s:.2f}s")

    def __enter__(self) -> "BrowserHandle":
        self._initialize()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
```

### 1.3 Base Strategy Classes

```python
"""Base classes for browser strategies."""

from abc import ABC, abstractmethod
from typing import Any, Tuple

from playwright.sync_api import Browser, BrowserContext


class BaseBrowserStrategy(ABC):
    """Abstract base class for all browser launching strategies."""

    def __init__(
        self,
        proxy: dict | None = None,
        profile_name: str | None = None,
        ignore_https_errors: bool = False
    ) -> None:
        self.proxy = proxy
        self.profile_name = profile_name
        self.ignore_https_errors = ignore_https_errors
        self.browser: Browser | None = None

    @abstractmethod
    def launch(self, **kwargs: Any) -> Tuple[Browser, BrowserContext]:
        """Launches a browser and returns the browser and context handles."""
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Closes the browser and cleans up resources."""
        raise NotImplementedError


class GuiBrowserStrategy(BaseBrowserStrategy):
    """Strategy for launching a browser with GUI."""

    def __init__(
        self,
        proxy: dict | None = None,
        profile_name: str | None = None,
        ignore_https_errors: bool = False,
        cdp_url: str | None = None,
        run_on_main_display: bool = False,
    ) -> None:
        super().__init__(proxy, profile_name, ignore_https_errors)
        self.cdp_url = cdp_url
        self.run_on_main_display = run_on_main_display
```

### 1.4 Camoufox Stealth Strategy

```python
"""Stealth browser strategies."""

from playwright.sync_api import Browser, BrowserContext, Page
try:
    from playwright_stealth import stealth_sync
except ImportError:
    stealth_sync = None

from .base import BaseBrowserStrategy
from browsers.utils import xvfb_manager
from camoufox.sync_api import Camoufox
from urllib.parse import urlparse


class StealthFirefoxGUIStrategy(BaseBrowserStrategy):
    """A strategy that launches a GUI Firefox browser with Camoufox."""

    def __init__(
        self,
        proxy: dict | None = None,
        profile_name: str | None = None,
        ignore_https_errors: bool = False,
        run_on_main_display: bool = False,
    ) -> None:
        super().__init__(proxy, profile_name, ignore_https_errors)
        self.run_on_main_display = run_on_main_display
        self.xvfb_context = None
        self.camoufox_instance = None

    def _format_proxy_for_camoufox(self) -> dict | None:
        """Converts Playwright-style proxy dict to Camoufox-style."""
        if not self.proxy or "server" not in self.proxy:
            return None

        proxy_url = f"http://{self.proxy['server']}"
        parsed_url = urlparse(proxy_url)

        return {
            "server": f"{parsed_url.scheme}://{parsed_url.hostname}:{parsed_url.port}",
            "username": self.proxy.get("username"),
            "password": self.proxy.get("password"),
        }

    def launch(self, **kwargs: Any) -> tuple[Browser, BrowserContext]:
        """Launches a GUI Firefox browser with a Camoufox profile."""
        logger.info("Launching GUI Firefox with Camoufox profile")

        camoufox_proxy = self._format_proxy_for_camoufox()

        try:
            if not self.run_on_main_display:
                self.xvfb_context = xvfb_manager()
                self.xvfb_context.__enter__()

            camoufox_profile_data = {}
            if self.profile_name:
                from browsers.utils import load_camoufox_profile, flatten_camoufox_profile
                camoufox_profile = load_camoufox_profile(self.profile_name)
                camoufox_profile_data = camoufox_profile.model_dump()
                camoufox_profile_data = flatten_camoufox_profile(camoufox_profile_data)

            self.camoufox_instance = Camoufox(
                proxy=camoufox_proxy,
                headless=False,
                geoip=True if camoufox_proxy else False,
                i_know_what_im_doing=True,
                config=camoufox_profile_data,
                **kwargs,
            )
            self.browser = self.camoufox_instance.__enter__()
            context = (
                self.browser.contexts[0]
                if self.browser.contexts
                else self.browser.new_context(ignore_https_errors=self.ignore_https_errors)
            )

            if stealth_sync:
                def apply_stealth_on_page(page: Page) -> None:
                    stealth_sync(page)

                context.on("page", apply_stealth_on_page)
                for page in context.pages:
                    apply_stealth_on_page(page)

            return self.browser, context
        except Exception as e:
            logger.error(f"Failed to launch GUI Firefox with Camoufox: {e}")
            if self.camoufox_instance:
                self.camoufox_instance.__exit__(None, None, None)
            if self.xvfb_context:
                self.xvfb_context.__exit__(None, None, None)
            raise
```

### 1.5 Profile Manager with TTL Cache

```python
"""Manages browser profiles and fingerprints."""

import random
import time
from pathlib import Path
from typing import Any

import yaml
from cachetools import TTLCache

from paths import CAMOUFOX_PROFILE_DIR

DEFAULT_PROFILE_POOL_SIZE = 5


class ProfileManager:
    """Manages the selection and generation of browser profiles."""

    def __init__(self, profile_dir: Path = CAMOUFOX_PROFILE_DIR) -> None:
        self.profile_dir = profile_dir
        self.profile_cache = TTLCache(maxsize=1024, ttl=24 * 60 * 60)  # 24-hour non-reuse
        self._ensure_profile_pool()

    def _ensure_profile_pool(self) -> None:
        """Ensures a minimum number of profiles are available."""
        profiles = list(self.profile_dir.glob("*.yaml"))
        if len(profiles) < DEFAULT_PROFILE_POOL_SIZE:
            for _ in range(DEFAULT_PROFILE_POOL_SIZE - len(profiles)):
                self.generate_and_save_profile()

    def select_profile(self, browser_family: str, profile_name: str | None = None) -> dict[str, Any]:
        """Selects a random, unused profile."""
        if profile_name:
            profile_path = self.profile_dir / f"{profile_name}.yaml"
            if not profile_path.exists():
                raise FileNotFoundError(f"Profile '{profile_name}' not found")
            return self._load_profile(profile_path)

        available_profiles = list(self.profile_dir.glob("*.yaml"))
        if not available_profiles:
            raise RuntimeError("No browser profiles available")

        selected_profile_path = random.choice(available_profiles)
        return self._load_profile(selected_profile_path)

    def _load_profile(self, profile_path: Path) -> dict[str, Any]:
        with open(profile_path, "r") as f:
            return yaml.safe_load(f)

    def generate_and_save_profile(self) -> dict[str, Any]:
        """Generates a new profile and saves it as YAML."""
        profile = self._generate_plausible_profile()
        timestamp = int(time.time() * 1000)
        file_name = f"profile_{timestamp}.yaml"
        profile_path = self.profile_dir / file_name
        with open(profile_path, "w") as f:
            yaml.safe_dump(profile, f)
        return profile

    def _generate_plausible_profile(self) -> dict[str, Any]:
        """Generates a randomized browser profile."""
        screen_resolutions = ["1920x1080", "1366x768", "1440x900"]
        timezones = ["Europe/London", "America/New_York", "Asia/Tokyo"]
        languages = ["en-US", "en-GB", "fr-FR", "de-DE"]
        gpu_vendors = ["Google Inc.", "NVIDIA Corporation", "Intel Inc."]

        return {
            "userAgent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/{random.randint(100, 120)}.0.0.0",
            "screen": {
                "width": int(random.choice(screen_resolutions).split("x")[0]),
                "height": int(random.choice(screen_resolutions).split("x")[1]),
            },
            "timezone": {"id": random.choice(timezones)},
            "locale": random.choice(languages),
            "webgl": {
                "renderer": f"ANGLE (Unknown, {random.choice(gpu_vendors)}, ...)",
                "vendor": random.choice(gpu_vendors),
            },
            "deviceMemory": random.choice([2, 4, 8]),
            "hardwareConcurrency": random.choice([4, 8, 16]),
            "platform": "Win32",
        }
```

### 1.6 Fingerprint Validation Suite

```python
"""Fingerprint validation tests."""

def run_programmatic_checks(page: Page) -> dict[str, Any]:
    """Runs comprehensive programmatic fingerprint checks."""
    fingerprint = {}

    # Navigator properties
    navigator_props = ["userAgent", "platform", "webdriver", "languages", "vendor"]
    for prop in navigator_props:
        fingerprint[prop] = page.evaluate(f"navigator.{prop}")

    # Screen properties
    screen_props = ["width", "height", "colorDepth", "pixelDepth"]
    for prop in screen_props:
        fingerprint[f"screen_{prop}"] = page.evaluate(f"screen.{prop}")

    # Timezone
    fingerprint["timezone"] = page.evaluate("Intl.DateTimeFormat().resolvedOptions().timeZone")

    # WebGL
    fingerprint["webgl_vendor"] = page.evaluate("""
        () => {
            try {
                const canvas = document.createElement('canvas');
                const gl = canvas.getContext('webgl');
                const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                return gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
            } catch (e) { return 'N/A'; }
        }
    """)

    # Canvas Fingerprint
    fingerprint["canvas_fingerprint"] = page.evaluate("""
        () => {
            try {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                ctx.textBaseline = 'top';
                ctx.font = "14px 'Arial'";
                ctx.fillStyle = '#f60';
                ctx.fillRect(125, 1, 62, 20);
                ctx.fillStyle = '#069';
                ctx.fillText('Hello, world!', 2, 15);
                return canvas.toDataURL();
            } catch (e) { return 'N/A'; }
        }
    """)

    return fingerprint


def test_sannysoft(browser: BrowserHandle) -> dict[str, Any]:
    """Navigates to SannySoft's test page."""
    browser.goto("https://bot.sannysoft.com/", wait_until="networkidle", timeout=60000)
    browser.page.wait_for_selector("table", timeout=60000)
    return browser.evaluate("""() => {
        const data = {};
        document.querySelectorAll('table tr').forEach(row => {
            const cols = row.querySelectorAll('td');
            if (cols.length === 2) {
                data[cols[0].textContent.trim()] = cols[1].textContent.trim();
            }
        });
        return data;
    }""")


def validate_fingerprint(
    browser_type: str,
    profile_name: str | None = None,
    proxy: dict | None = None,
    run_on_main_display: bool = False,
) -> dict[str, Any]:
    """Launches browser and runs fingerprint validation tests."""
    validation_results = {"browser_type": browser_type, "tests": {}}

    browser_handle = None
    try:
        browser_handle = create_instance(
            browser_type=browser_type,
            profile_name=profile_name,
            proxy=proxy,
            as_emunium=True,
            ignore_https_errors=True if proxy else False,
            run_on_main_display=run_on_main_display,
        )
        page = browser_handle.new_tab()

        validation_results["tests"]["programmatic_checks"] = run_programmatic_checks(page)
        validation_results["tests"]["sannysoft"] = test_sannysoft(browser_handle)

    except Exception as e:
        validation_results["error"] = str(e)
    finally:
        if browser_handle:
            browser_handle.close()

    return validation_results
```

---

## 2. CONCLUSIONS

### What is Good / Usable

1. **Strategy Pattern**: Clean dynamic discovery and registration
2. **BrowserHandle**: Context manager with session timing
3. **Camoufox Integration**: Full fingerprinting with profile support
4. **Profile Manager**: TTL cache, auto-generation, YAML storage
5. **Xvfb Manager**: Virtual display context manager
6. **Validation Suite**: Multiple test sites (SannySoft, CreepJS, Pixelscan)
7. **HAR Tracing**: Built-in support for network capture

### What is Outdated

1. **EmuniumWrapper**: Placeholder, needs implementation

### What Must Be Rewritten

1. **Async/sync mixing**: Some strategies mix sync/async Playwright APIs

### How it Fits into AutoBiz

- **DIRECT PORT**: Strategy pattern, BrowserHandle, ProfileManager
- **MERGE with Scraper**: StealthyFetcher patterns
- **KEEP**: Validation suite for testing

### Conflicts or Duplicates with Previous Repos

| Pattern | Auto-Biz | Scraper | Best |
|---------|----------|---------|------|
| Strategy pattern | Yes (full) | Yes (partial) | **Auto-Biz** |
| Camoufox | Yes | Yes | **Auto-Biz** (profiles) |
| Profile mgmt | Yes (TTL cache) | No | **Auto-Biz** |
| Fingerprint debug | Yes (console) | Yes (file save) | **MERGE** |
| Validation tests | Full suite | None | **Auto-Biz** |
| StealthyFetcher | No | Yes | **Scraper** |

### Best Version Recommendation

**Auto-Biz is BEST for browser automation**:
- Most complete strategy pattern with dynamic discovery
- Profile management with TTL cache
- Full validation test suite
- Merge StealthyFetcher from Scraper for Scrapling support
