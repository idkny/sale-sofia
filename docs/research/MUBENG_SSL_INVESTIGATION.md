# Mubeng & SSL Certificate Investigation

> **Purpose**: Deep investigation into whether mubeng and its SSL certificate are necessary for the project
> **Created**: 2025-12-30 (Session 58)
> **Status**: Complete - Recommendation provided

---

## Table of Contents

1. [Investigation Summary](#investigation-summary)
2. [What is Mubeng](#what-is-mubeng)
3. [Git History Analysis](#git-history-analysis)
4. [Proxy Architecture Evolution](#proxy-architecture-evolution)
5. [SSL Certificate Deep Dive](#ssl-certificate-deep-dive)
6. [Current Usage Analysis](#current-usage-analysis)
7. [Online Research Findings](#online-research-findings)
8. [Recommendation](#recommendation)

---

## Investigation Summary

**Question**: Is mubeng necessary? Can we remove it and simplify the project?

**Answer**:
- **Mubeng binary**: Can be removed (only used for `--check` mode in Celery)
- **SSL certificate infrastructure**: Should be KEPT (dormant but valuable for future)
- **Current scraping**: Works WITHOUT mubeng or certificate (uses direct proxy tunnels)

---

## What is Mubeng

**Source**: [GitHub - mubeng/mubeng](https://github.com/mubeng/mubeng)

Mubeng is a Go-based proxy checker and IP rotator with two modes:

### Mode 1: Proxy Checker (`--check`)
```bash
mubeng --check -f proxies.txt -o live_proxies.txt -t 45s
```
- Tests proxy liveness in bulk
- Currently used in `proxies/tasks.py` for Celery proxy validation
- **Can be replaced with ~25 lines of Python async httpx**

### Mode 2: Proxy Server (MITM)
```bash
mubeng -a localhost:8089 -f proxies.txt -r 1
```
- Runs as local proxy server
- Rotates through upstream proxies
- **Does MITM interception for HTTPS** - this is why SSL certificate was needed
- **NOT used in current architecture** (removed in Session 50)

---

## Git History Analysis

### Key Commits

| Commit | Date | Change |
|--------|------|--------|
| `159b7e8` | 2025-12-26 | **Added SSL certificate support** - "Fixes SEC_ERROR_UNKNOWN_ISSUER" |
| `3a11b91` | 2025-12-29 | **Session 50: Removed mubeng from scraping** - "Remove mubeng server from scraping flow" |
| `936a6c5` | 2025-12-30 | Session 53: Simplified proxy scoring |
| Sessions 54-57 | 2025-12-30 | Proxy cleanup (~465 lines removed) |

### Commit 159b7e8 Analysis (SSL Certificate Addition)

**Commit message**:
> "Add SSL certificate support for mubeng HTTPS proxy"
> "Fixes SEC_ERROR_UNKNOWN_ISSUER when scraping HTTPS sites through mubeng proxy with Camoufox/Firefox"

**Files changed**:
- `setup.sh` - Added certificate extraction (~44 lines)
- `websites/scrapling_base.py` - Added `certificatePaths` to Camoufox config
- `docs/architecture/SSL_PROXY_SETUP.md` - Full documentation (378 lines)

**Why it was needed**:
When using mubeng server mode, traffic flows:
```
Browser → mubeng:8089 (MITM) → upstream proxy → target website
```
Mubeng intercepts HTTPS, presents its own certificate. Firefox needs to trust it.

### Commit 3a11b91 Analysis (Architecture Change)

**Commit message**:
> "Session 50: Fix proxy system - remove mubeng/preflight blocking"
> "Remove mubeng server from scraping flow (keep for Celery tasks)"
> "Pass live proxy to Fetcher/StealthyFetcher"

**New flow**:
```
Browser → direct proxy:port → target website
```
No mubeng MITM = no certificate needed for this flow.

---

## Proxy Architecture Evolution

### Before Session 50 (OLD)

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser (Camoufox/Firefox)                                     │
│    ↓                                                            │
│  MUBENG SERVER (localhost:8089) ← MITM PROXY                   │
│    │  - Intercepts HTTPS                                        │
│    │  - Presents mubeng certificate to browser                  │
│    │  - Browser needs certificatePaths config                   │
│    ↓                                                            │
│  Upstream Proxy Pool (rotating)                                 │
│    ↓                                                            │
│  Target Website (imot.bg, bazar.bg)                            │
└─────────────────────────────────────────────────────────────────┘

SSL Certificate: REQUIRED (SEC_ERROR_UNKNOWN_ISSUER without it)
```

### After Session 50 (CURRENT)

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser (Camoufox via StealthyFetcher)                        │
│    ↓                                                            │
│  Direct Proxy (http://proxyhost:port) ← HTTP CONNECT TUNNEL    │
│    │  - Creates encrypted tunnel                                │
│    │  - Does NOT intercept HTTPS content                        │
│    │  - Browser sees target's real certificate                  │
│    ↓                                                            │
│  Target Website (imot.bg, bazar.bg)                            │
└─────────────────────────────────────────────────────────────────┘

SSL Certificate: NOT REQUIRED (tunnel mode, no MITM)
```

---

## SSL Certificate Deep Dive

### Two Types of Proxy Connections

| Type | How HTTPS Works | Certificate Needed? |
|------|-----------------|---------------------|
| **HTTP CONNECT Tunnel** | Proxy creates TCP pipe, traffic encrypted end-to-end | NO |
| **MITM Proxy** | Proxy terminates SSL, decrypts, re-encrypts | YES |

### When SEC_ERROR_UNKNOWN_ISSUER Occurs

From [Mozilla Support](https://support.mozilla.org/en-US/kb/error-codes-secure-websites):
> "If you encounter this problem on a multitude of unrelated HTTPS sites, this indicates that something on your system or network intercepts your connection and injects certificates in a way that Firefox does not trust."

This happens when:
1. Corporate firewalls doing SSL inspection
2. MITM proxies (like mubeng server mode)
3. Some "free" proxies that intercept traffic

### Why Current Architecture Works Without Certificate

1. `main.py` uses `StealthyFetcher.fetch(proxy="http://host:port")`
2. Scrapling passes proxy to Camoufox
3. Camoufox/Firefox uses HTTP CONNECT method for HTTPS
4. Proxy creates tunnel, doesn't inspect content
5. Browser sees target website's real certificate
6. No MITM = no certificate needed

### Why Some Proxies Might Still Fail

Not all "free" proxies are tunnel proxies. Some do MITM to:
- Insert ads
- Track users
- Modify content

These proxies fail with SSL errors and get removed from our pool during liveness checking. This is actually fine - we just discard them as "dead" proxies.

---

## Current Usage Analysis

### What Uses Mubeng

| Component | Mubeng Usage | Status |
|-----------|--------------|--------|
| `proxies/tasks.py` | `mubeng --check` for bulk liveness | **ACTIVE** |
| `main.py` | None | N/A |
| `scrapling_base.py` | References `MUBENG_PROXY`, `MUBENG_CA_CERT` | **DEAD CODE** |

### What Uses SSL Certificate

| Component | Certificate Usage | Status |
|-----------|-------------------|--------|
| `scrapling_base.py:fetch_stealth()` | `certificatePaths` config | **DEAD CODE** (method not called) |
| `main.py` | None | N/A |

### Code Path Analysis

**main.py scraping flow**:
```python
# Line 395 - uses StealthyFetcher directly, NOT fetch_stealth()
response = StealthyFetcher.fetch(
    url=url,
    proxy=effective_proxy,  # Direct proxy like "http://host:port"
    ...
)
```

**scrapling_base.py fetch_stealth()** (UNUSED):
```python
# This method uses mubeng + certificate but is NEVER called from main.py
if MUBENG_CA_CERT.exists():
    config["certificatePaths"] = [str(MUBENG_CA_CERT)]
proxy_config = {"server": MUBENG_PROXY}  # localhost:8089
```

---

## Online Research Findings

### Camoufox GitHub Issues

**Issue #293**: [Proxy error of SEC_ERROR_UNKNOWN_ISSUER](https://github.com/daijro/camoufox/issues/293)

Key finding:
> "Setting a MITM proxy returns SEC_ERROR_UNKNOWN_ISSUER. Works in standard Playwright but not in Camoufox."

Solution mentioned:
```python
context = await browser.new_context(ignore_https_errors=True)
```

**Issue #362**: [How to disable SSL verification?](https://github.com/daijro/camoufox/issues/362)
- Users requesting ability to disable SSL verification for certain proxy types
- Issue remains open

### Scrapling Documentation

**Source**: [Scrapling StealthyFetcher](https://scrapling.readthedocs.io/en/latest/fetching/stealthy/)

- StealthyFetcher uses Camoufox internally
- Proxy parameter: string or dict with server/username/password
- **No exposed `certificatePaths` or `ignore_https_errors` parameter**
- Certificate handling must be done if using Camoufox directly

### mitmproxy Documentation

**Source**: [How mitmproxy works](https://docs.mitmproxy.org/stable/concepts/how-mitmproxy-works/)

> "The MITM in its name stands for Man-In-The-Middle... The basic idea is to pretend to be the server to the client, and pretend to be the client to the server."

Confirms: MITM proxies require client to trust proxy's CA certificate.

---

## Recommendation

### What to Remove

| Component | Action | Reason |
|-----------|--------|--------|
| Mubeng binary | **REMOVE** | Only used for `--check`, replaceable with Python |
| `_run_mubeng_liveness_check()` | **REPLACE** | Use async httpx batch checking |
| Certificate extraction in `setup.sh` | **KEEP** | Low cost, useful if needed |
| `MUBENG_CA_CERT` in scrapling_base.py | **KEEP** | Dormant, zero runtime cost |
| `fetch_stealth()` method | **KEEP** | Might be useful for direct Camoufox usage |

### Why Keep Certificate Infrastructure

1. **Zero runtime cost** - Code only runs if certificate exists
2. **Future browser support** - If we add direct Camoufox (not via Scrapling)
3. **Commercial MITM proxies** - Some paid proxy services use MITM
4. **Debugging** - Useful for traffic inspection with mitmproxy
5. **Only ~30 lines of dormant code** - Not worth removing

### Implementation Plan

**Phase 1: Remove mubeng binary dependency**
- Replace `_run_mubeng_liveness_check()` with async httpx (~25 lines)
- Remove mubeng download from `setup.sh`
- Keep SSL certificate extraction (optional, for future use)

**Phase 2: Optional cleanup**
- Mark `fetch_stealth()` as deprecated with docstring
- Update `MUBENG_PROXY` comment to indicate it's for future use
- Update `SSL_PROXY_SETUP.md` to note current architecture doesn't need it

### Effort Estimate

- Phase 1: ~2 hours (write httpx checker, update tasks.py, test)
- Phase 2: ~30 minutes (documentation updates)

---

## Files Referenced

| File | Purpose |
|------|---------|
| `proxies/tasks.py` | Contains `_run_mubeng_liveness_check()` |
| `websites/scrapling_base.py` | Contains unused `fetch_stealth()` with certificate |
| `main.py` | Current scraping flow (no mubeng) |
| `setup.sh` | Mubeng installation + certificate extraction |
| `docs/architecture/SSL_PROXY_SETUP.md` | SSL certificate documentation |
| `config/settings.py` | `MUBENG_PROXY` setting |

---

## Related Documents

- [PROXY_SYSTEM_REVIEW.md](../../archive/research/PROXY_SYSTEM_REVIEW.md) - Proxy architecture review (archived)
- [SSL_PROXY_SETUP.md](../architecture/SSL_PROXY_SETUP.md) - SSL certificate setup guide
- [116_GENERIC_SCRAPER_TEMPLATE.md](../specs/116_GENERIC_SCRAPER_TEMPLATE.md) - Generic scraper spec

---

*Investigation completed: 2025-12-30*
