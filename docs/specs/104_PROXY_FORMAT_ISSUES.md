# Proxy Format Issues - AutoBiz vs Current

**Issue**: Different tools need proxies in different formats. Are we converting correctly?

---

## Format Requirements by Tool

| Tool | Expected Format | Example |
|------|-----------------|---------|
| **Mubeng** (checker/server) | String: `protocol://host:port` | `http://1.2.3.4:8080` |
| **Playwright** | Dict: `{"server": "host:port"}` | `{"server": "localhost:8089"}` |
| **Camoufox** | Dict with specific structure | Needs conversion function |

---

## AutoBiz Implementation

### Mubeng Format (correct)
```python
# proxies_AutoBiz.md line 384
temp_input_file.write(f"{protocol}://{proxy['host']}:{proxy['port']}\n")
```

### Playwright Format
```python
# browser_AutoBiz.md line 72-76
proxy_dict = {
    "server": f"{host}:{port}",  # NO PROTOCOL
    "username": "user",
    "password": "pass"
}
```

### Camoufox Conversion Function
```python
# browser_AutoBiz.md line 271-283
def _format_proxy_for_camoufox(proxy_dict: dict) -> dict:
    """Convert Playwright proxy dict to Camoufox format."""
    server = proxy_dict.get("server", "")
    # Parse and validate URL
    # Return properly formatted dict for Camoufox
    return formatted_proxy
```

---

## Current Implementation

### Mubeng Format (correct ✅)
```python
# proxies/tasks.py line 108
temp_input_file.write(f"{protocol}://{proxy['host']}:{proxy['port']}\n")
```

### Playwright Format (⚠️ BUG?)
```python
# proxies/proxies_main.py line 193-202
def validate_proxy(proxy: str | dict | None) -> dict | None:
    if isinstance(proxy, str):
        return {"server": proxy}  # Keeps full URL WITH protocol!
    # ...
```

When `proxy = "http://localhost:8089"`:
- Returns: `{"server": "http://localhost:8089"}` ← **INCLUDES PROTOCOL**
- Expected: `{"server": "localhost:8089"}` ← **NO PROTOCOL**

### Camoufox Conversion (⚠️ MISSING)
```python
# browsers/strategies/firefox.py line 29-30
self.camoufox_instance = AsyncCamoufox(
    proxy=self.proxy,  # Passed raw, NO CONVERSION
    headless=True,
)
```

AutoBiz has `_format_proxy_for_camoufox()`, current has nothing.

---

## Potential Bugs

### Bug 1: Protocol in Server Field
**Location**: `proxies/proxies_main.py:193-202`
**Problem**: `validate_proxy()` includes protocol in server field
**Risk**: Playwright may not handle `http://` prefix correctly
**Fix**: Strip protocol from server field

### Bug 2: Missing Camoufox Conversion
**Location**: `browsers/strategies/firefox.py:29-30`
**Problem**: No conversion function like AutoBiz's `_format_proxy_for_camoufox()`
**Risk**: Camoufox may reject or ignore proxy silently
**Fix**: Add format conversion function

### Bug 3: Inconsistent Format Handling
**Problem**: Mubeng uses string, browsers use dict, no clear transformation layer
**Risk**: Format errors may fail silently
**Fix**: Create explicit format converter functions

---

## Verification Needed

Before fixing, verify:
1. Does Playwright actually fail with protocol in server field?
2. Does Camoufox actually need special formatting?
3. Are current scrapes working despite these issues?

**Test**: Run a scrape with logging to see actual proxy format at each stage.

---

## Proposed Fix

Add to `proxies/proxies_main.py`:

```python
def format_proxy_for_mubeng(proxy: dict) -> str:
    """Format proxy dict for mubeng CLI."""
    return f"{proxy.get('protocol', 'http')}://{proxy['host']}:{proxy['port']}"

def format_proxy_for_playwright(proxy_url: str) -> dict:
    """Format proxy URL for Playwright. Strips protocol."""
    from urllib.parse import urlparse
    parsed = urlparse(proxy_url)
    return {"server": f"{parsed.hostname}:{parsed.port}"}

def format_proxy_for_camoufox(proxy: dict) -> dict:
    """Format proxy for Camoufox."""
    # Camoufox-specific formatting
    return {
        "server": f"{proxy.get('host')}:{proxy.get('port')}",
        "bypass": ["localhost", "127.0.0.1"]
    }
```
