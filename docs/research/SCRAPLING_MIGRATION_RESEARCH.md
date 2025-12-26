# Scrapling Migration Research

**Created:** 2025-12-25
**Purpose:** Analyze how Scrapling can replace our custom browser module
**Status:** Research Complete - Ready for Implementation Planning

---

## Research Question

Can Scrapling's built-in fetchers fully replace our custom `browsers/` module, and what are the implications for project architecture?

---

## Scrapling Fetcher Analysis

Scrapling provides three fetcher classes that cover all browser automation needs.

### Fetcher (Fast HTTP)

The `Fetcher` class provides fast HTTP requests with TLS fingerprint impersonation. It does not execute JavaScript but is extremely fast and stealthy for simple pages.

Key capabilities include TLS fingerprint spoofing for Chrome, Firefox, and Safari browsers, automatic header management, HTTP/3 support, and proxy integration. This is ideal for search result pages that don't require JavaScript rendering.

### StealthyFetcher (Anti-Bot Bypass)

The `StealthyFetcher` class uses Camoufox, a modified version of Firefox, internally. This provides the highest level of anti-detection capability.

Features include Cloudflare Turnstile and Interstitial bypass, WebRTC leak protection via `block_webrtc=True`, human-like behavior simulation via `humanize=True`, GeoIP-based fingerprinting, and full JavaScript execution. This is ideal for protected listing pages that may have anti-bot measures.

### DynamicFetcher (Playwright Chromium)

The `DynamicFetcher` class provides full browser automation via Playwright's Chromium. It offers a stealth mode option but is slower than StealthyFetcher. This serves as a fallback option if StealthyFetcher encounters issues with specific sites.

---

## Overlap with Current Browser Module

Our current `browsers/` module contains 12 files implementing various browser strategies. Analysis shows complete overlap with Scrapling's capabilities.

The `FirefoxStrategy` using Camoufox is directly replaced by `StealthyFetcher`, which bundles Camoufox internally. The `ChromiumStealthStrategy` using Playwright with playwright-stealth is replaced by `DynamicFetcher` with stealth mode. The `ChromiumStrategy` using fingerprint-chromium is replaced by `DynamicFetcher`, though StealthyFetcher is actually more stealthy. The `StealthStrategy` is also replaced by `DynamicFetcher`. The `emunium_wrapper.py` providing human-like interactions is replaced by the `humanize=True` parameter in StealthyFetcher. Finally, `profile_manager.py` and session handling are replaced by Scrapling's session classes.

---

## Dependency Analysis

Current browser-related dependencies in requirements.txt:

The `camoufox[geoip]` package is used by FirefoxStrategy but Scrapling's StealthyFetcher bundles Camoufox internally, making this redundant. The `emunium` package provides human-like mouse movements but StealthyFetcher's `humanize=True` provides equivalent functionality. The `playwright` package is used by chromium strategies and Scrapling uses it internally for DynamicFetcher. The `playwright-stealth` package adds stealth to Playwright but Scrapling handles this internally. The `pyvirtualdisplay` package provides Xvfb for headless GUI but Scrapling manages headless/GUI mode internally.

The conclusion is that `scrapling[fetchers]` includes all necessary browser dependencies. Only `playwright` should remain as an explicit dependency for version control purposes.

---

## Architectural Decisions

### Synchronous Execution from Single Location

The current codebase uses synchronous Playwright calls managed from main.py. Scrapling supports both synchronous and asynchronous fetchers.

For consistency with the existing architecture and to maintain a single location for process management, synchronous fetcher methods should be used. All parallel processing should remain centralized in main.py rather than distributed across modules.

This means using `StealthyFetcher.fetch()` rather than `StealthyFetcher.async_fetch()`, matching the current Playwright usage pattern. This also leaves room for future browser/tool additions without architectural changes.

### Fetcher Selection Strategy

Based on the decision to optimize for speed where possible:

Search pages should use the fast `Fetcher` class since these pages typically don't have heavy anti-bot protection. Listing pages should use `StealthyFetcher` since individual property pages may have more protection and contain the critical data we need.

This hybrid approach balances speed and stealth effectively.

### Git Strategy for Browser Module

The browser module should be preserved in git history for potential future reference. Files should be completely removed from the local project to avoid dead code. The current state should be committed, then files removed with a descriptive commit message.

---

## Impact Assessment

### Files to Remove from Local Project

The entire `browsers/` directory can be removed:

- `browsers/strategies/base.py` - Abstract base class
- `browsers/strategies/firefox.py` - Camoufox wrapper, replaced by StealthyFetcher
- `browsers/strategies/chromium.py` - fingerprint-chromium, replaced by DynamicFetcher
- `browsers/strategies/chromium_stealth.py` - Playwright+stealth, replaced by DynamicFetcher
- `browsers/strategies/stealth.py` - Stealth wrapper, replaced by DynamicFetcher
- `browsers/strategies/__init__.py` - Package init
- `browsers/browsers_main.py` - Factory pattern, replaced by Scrapling
- `browsers/emunium_wrapper.py` - Human-like behavior, replaced by humanize=True
- `browsers/profile_manager.py` - Not actively used
- `browsers/validator.py` - Debug tool
- `browsers/utils.py` - xvfb_manager, not needed
- `browsers/__init__.py` - Package init

Total: 12 files, approximately 500+ lines of code.

### Dependencies to Remove

- `camoufox[geoip]` - bundled in scrapling
- `emunium` - replaced by humanize=True
- `playwright-stealth` - handled internally by Scrapling
- `pyvirtualdisplay` - handled internally by Scrapling

### Files Unchanged

The `orchestrator.py` file has no browser usage and remains unchanged. The `proxies/` module handles proxy validation/rotation independently. The scraper files already use ScraplingMixin for parsing. Celery tasks have no direct browser usage. The dashboard app has no browser usage.

---

## ScraplingMixin Current State

The existing `ScraplingMixin` in `websites/scrapling_base.py` already has `fetch_stealth()` and `fetch_fast()` methods defined. These methods are sufficient for the migration.

The main change needed is in main.py where browser creation currently happens. This code needs to be replaced with calls to the scraper's fetch methods, keeping all processing centralized in main.py.

---

## Risk Factors

### Performance Difference

StealthyFetcher may be slower than our current chromiumstealth strategy due to additional anti-detection measures. This is acceptable given the improved stealth capabilities. Using fast Fetcher for search pages mitigates overall performance impact.

### Cloudflare Handling

Scrapling claims to bypass "all types of Cloudflare's Turnstile and Interstitial." This needs verification with imot.bg and bazar.bg during testing phase.

### Session State

For multi-page scraping, if sites track session state across pages, StealthySession may be needed. This should be evaluated during implementation if issues arise.

---

## Conclusions

Scrapling fully replaces our custom browser module with equivalent or better capabilities. The StealthyFetcher using Camoufox internally provides the same anti-detection as our FirefoxStrategy. The migration eliminates significant code complexity while maintaining all required functionality.

The hybrid approach of using Fetcher for search pages and StealthyFetcher for listings optimizes the speed/stealth tradeoff appropriately.

Synchronous execution should be maintained with all processing centralized in main.py, allowing for future flexibility in browser/tool selection.

---

## Next Steps

This research is complete. The implementation phase should create a task list in `docs/tasks/` with specific steps for:

1. Updating requirements.txt
2. Modifying main.py to use Scrapling fetchers (sync, centralized)
3. Removing browser module files from local project
4. Committing removal to git with descriptive message
5. Testing the changes
6. Updating documentation

---

*Research completed: 2025-12-25*
