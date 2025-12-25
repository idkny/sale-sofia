---
id: scraping_landscape_2025
type: research
subject: autobiz
description: "Latest scraping developments, anti-bot systems, and bypass techniques (2025)"
created_at: 2025-12-07
updated_at: 2025-12-07
tags: [scraping, anti-bot, stealth, cloudflare, research]
---

# Web Scraping Landscape 2025

> Research task A.0: Stay current with anti-detection techniques, new libraries, and detection methods.

---

## Executive Summary

**Key Changes in 2025:**
1. **puppeteer-extra-stealth deprecated** (Feb 2025) - no longer maintained
2. **FlareSolverr deprecated** - can't bypass modern Cloudflare
3. **Cloudflare AI Labyrinth** - new AI honeypot traps scrapers
4. **TLS fingerprinting** - now primary detection method
5. **Residential proxy detection** - new APIs can detect residential proxies
6. **Patchright & Camoufox** - currently the most effective open-source tools

**Our Stack Status:**
| Tool | Status | Notes |
|------|--------|-------|
| Camoufox | ✅ Excellent | Best Firefox option, actively maintained |
| Patchright | ✅ Excellent | Best Chromium option, v1.57.0 |
| Nodriver | ✅ Good | 25% success rate baseline |
| Scrapling | ✅ Good | Fast, adaptive, but limited Cloudflare bypass |
| Playwright Stealth | ⚠️ Outdated | Based on deprecated puppeteer-stealth |

---

## 1. Anti-Bot Detection Systems (2025)

### 1.1 Cloudflare Changes

#### New: AI Labyrinth
Cloudflare's most significant 2025 addition. Instead of blocking bots, it traps them.

**How it works:**
1. Adds invisible honeypot links to pages
2. Bots that follow links enter AI-generated maze
3. Content looks real but is useless
4. Going 4+ links deep = definite bot fingerprint
5. Available to all plans (including Free)

**Impact on us:** Must avoid following all links blindly. Check for `nofollow` tags and suspicious link patterns.

**Source:** [Cloudflare Blog - AI Labyrinth](https://blog.cloudflare.com/ai-labyrinth/)

#### Cloudflare v3 Challenges
- Challenges now run in JavaScript Virtual Machine (sandboxed)
- Per-customer ML models that learn traffic patterns
- Residential proxy detection improved
- Session consistency checks

#### Bot Scores
- Each request gets a score (lower = more suspicious)
- Detection IDs flag unusual headers, missing metadata, abnormal frequencies

### 1.2 Akamai Updates (2025)

- 21.5% market share (up from 21.4%)
- AI-powered detection learning behavioral patterns over time
- Trust scores based on HTTP characteristics + historical data
- Directory of known bots for real-time categorization

### 1.3 DataDome Updates (2025)

**Q3 2025:**
- AI traffic control improvements
- GraphQL-level signals (v1.4.0) - detects actions within GraphQL requests
- AI-powered email scoring

**Q2 2025:**
- Akamai Edge Worker integration with auto client-side script injection
- New PoP in Mexico City (34 total)
- 9.4% market share (up from 6.5%)

**Source:** [DataDome Q3 2025 Updates](https://datadome.co/changelog/ai-adaptability-ease-q3-product-updates-2025/)

### 1.4 Kasada

- No CAPTCHAs - suspects ALL requests
- Server + client side challenges
- Response headers: `x-kpsdk-ct`, `x-kpsdk-r`, `x-kpsdk-c`
- JavaScript fingerprinting of browser environment
- Execution timing analysis (too fast/slow = suspicious)

### 1.5 PerimeterX (HUMAN)

- TLS fingerprinting
- IP fingerprinting
- JavaScript client fingerprinting
- Common on e-commerce, ticketing, login forms

---

## 2. Detection Techniques

### 2.1 TLS Fingerprinting (PRIMARY in 2025)

**Why it matters:** Happens BEFORE HTTP headers/cookies - can't evade with header manipulation.

**What's analyzed:**
- Cipher suites
- TLS extensions
- Protocol versions
- Creates unique signature per client

**Bypass tools:**
| Tool | Language | Notes |
|------|----------|-------|
| curl-impersonate | C | Mimics Chrome/Firefox TLS exactly |
| tls-client | Go | Mimics JA3 fingerprints |
| TLS Requests | Python | Browser-like TLS behavior |
| Cloak | PHP | Low-level TLS control |
| burp-awesome-tls | Java | Burp Suite extension |

**Key insight:** Mimicking old browser versions (Chrome 95) is MORE suspicious in 2025. Always use current versions.

**Source:** [ZenRows - TLS Fingerprint](https://www.zenrows.com/blog/what-is-tls-fingerprint)

### 2.2 HTTP/2 Fingerprinting

- New detection vector in 2025
- Analyzes HTTP/2 settings, priorities, window sizes
- BrowserLeaks has experimental HTTP/2 test

### 2.3 IP Reputation

**Datacenter IPs:**
- 90% effectiveness drop since 2020
- 20-40% success rate on protected sites
- ASN/subnet analysis flags them instantly

**Residential Proxies:**
- 85-95% success rate
- But NEW detection in 2025:
  - IPinfo Residential Proxy Detection API
  - Ja4T fingerprints detect residential proxy traffic
  - Packet length analysis (1456 packet, 1388 TCP)
  - 60% true positive rate on residential detection

**Recommendation:** Residential still best, but rotate frequently and use quality providers.

**Source:** [IPinfo Residential Proxy Detection](https://www.helpnetsecurity.com/2025/07/09/ipinfo-residential-proxy-detection-api/)

### 2.4 Behavioral Analysis

- Mouse movement patterns
- Scroll behavior
- Click patterns
- Time between actions
- Typing rhythm

---

## 3. Stealth Libraries (2025 Status)

### 3.1 RECOMMENDED: Camoufox

**Status:** ✅ EXCELLENT - Our primary choice

**Key features:**
- C++ level fingerprint modification (not JS injection - undetectable)
- Canvas fingerprint spoofing (closed source patch)
- WebRTC IP spoofing at protocol level
- Font metric randomization (0-0.1px shifts)
- Auto geo-sync from proxy IP (timezone, locale, WebRTC)
- Natural mouse movement algorithm
- 200MB memory usage (lighter than Firefox)
- Playwright API compatible

**2025 Note:** Original maintainer @daijro hospitalized March 2025. Fork by @coryking maintains Firefox 142.0.1.

**Source:** [Camoufox GitHub](https://github.com/daijro/camoufox), [Camoufox Docs](https://camoufox.com/)

### 3.2 RECOMMENDED: Patchright

**Status:** ✅ EXCELLENT - Best Chromium option

**Version:** 1.57.0 (Dec 2025)

**Key patches:**
- Fixes Runtime.enable CDP leak (main detection vector)
- Uses isolated ExecutionContexts for JS
- Disables Console API (trade-off for stealth)
- Closed Shadow Root interaction
- XPath in Closed Shadow Roots

**Required config for undetection:**
```python
await browser.launch_persistent_context(
    channel="chrome",        # Use Chrome, not Chromium
    headless=False,          # Required
    no_viewport=True         # Required
)
# Do NOT set custom headers or user_agent
```

**Limitation:** Chromium only. No Firefox/Webkit.

**Source:** [Patchright GitHub](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright)

### 3.3 GOOD: Nodriver / Zendriver

**Status:** ✅ Good - CDP-minimal approach

**Nodriver:**
- Successor to undetected-chromedriver
- Custom DevTools protocol implementation
- Async-first framework
- 25% baseline success rate vs major anti-bots
- Passes CDP detection tests

**Zendriver:**
- Fork with more active development
- Docker support
- Same core principles

**Source:** [Nodriver GitHub](https://github.com/ultrafunkamsterdam/nodriver)

### 3.4 GOOD: Botright

**Status:** ✅ Good - Playwright-based

**Version:** 0.5.1

**Key features:**
- Uses real local Chromium browser
- Self-scraped Chrome fingerprints
- Free CAPTCHA solving (CV/AI)
- Removes `navigator.webdriver`

**Best with:** Ungoogled Chromium + residential proxies

**Source:** [Botright GitHub](https://github.com/Vinyzu/Botright/)

### 3.5 GOOD: SeleniumBase UC Mode

**Status:** ✅ Good for small scale

**Features:**
- Auto user-agent rotation
- Built-in Cloudflare/CAPTCHA handling
- `uc_gui_click_captcha()` for Linux servers

**Limitations:**
- Detected in headless mode
- Memory-intensive for CAPTCHA solving
- Not suitable for large-scale scraping

**Source:** [SeleniumBase UC Mode Docs](https://seleniumbase.io/help_docs/uc_mode/)

### 3.6 USEFUL: Scrapling

**Status:** ✅ Good for basic scraping

**Version:** 0.3

**Features:**
- Adaptive element tracking (survives website changes)
- StealthyFetcher with Cloudflare Turnstile solving
- 20-30% faster in v0.3
- Built-in MCP server for AI integration
- 1775x faster than BeautifulSoup

**Limitations:**
- Limited against advanced Cloudflare
- Not for scale on protected sites

**Source:** [Scrapling GitHub](https://github.com/D4Vinci/Scrapling)

### 3.7 NEW: humanization-playwright

**Status:** 🆕 New - Human simulation

**Version:** 0.1.2

**Features:**
- Cubic Bezier curves for mouse movement
- Jitter and pauses
- Variable typing speeds
- Hesitations after spaces
- Mouse overshoot corrections
- Built on Patchright

**Source:** [PyPI](https://pypi.org/project/humanization-playwright/)

### 3.8 DEPRECATED

| Tool | Status | Recommendation |
|------|--------|----------------|
| puppeteer-extra-stealth | ❌ Deprecated Feb 2025 | Use Patchright |
| FlareSolverr | ❌ Deprecated | Use Camoufox/Patchright |
| selenium-stealth | ⚠️ Stale | Use SeleniumBase UC |
| cloudscraper | ⚠️ Hit or miss | Use browser automation |

---

## 4. Bypass Techniques (2025)

### 4.1 Proxy Strategy

**Hierarchy (best to worst):**
1. **Mobile proxies** - Highest trust
2. **Residential proxies** - 85-95% success
3. **ISP proxies** - Datacenter IPs with residential ASN
4. **Datacenter proxies** - 20-40% success

**2025 insight:** IPv6 addresses sometimes bypass Cloudflare better (less reputation tracking).

### 4.2 Browser Selection

| Scenario | Tool |
|----------|------|
| Cloudflare sites | Camoufox (geoip=True) |
| Heavy protection (Akamai/DataDome) | Patchright (headless=False) |
| JavaScript challenges | Nodriver/Zendriver |
| Basic scraping | Scrapling StealthyFetcher |
| CAPTCHAs needed | Botright (free AI solving) |

### 4.3 Behavioral Simulation

**Must-haves in 2025:**
- Random delays between actions
- Bezier curve mouse movements
- Variable scroll heights
- Random element clicks
- Typing with hesitations

**Tools:**
- humanization-playwright
- Camoufox natural mouse
- Botright human simulation

### 4.4 Origin Server Bypass

- Find origin IP behind CDN
- Send requests directly
- Bypasses Cloudflare completely
- **Does NOT work** for DataDome/PerimeterX (inline)

### 4.5 CAPTCHA Solving

**Cloudflare Turnstile modes:**
1. Non-interactive (invisible)
2. Invisible (brief verification)
3. Interactive (user action)

**Solutions:**
- Botright (free, AI-based)
- 2Captcha / CapSolver (paid services)
- SeleniumBase `uc_gui_click_captcha()`

---

## 5. Fingerprint Testing Sites

| Site | Best For | URL |
|------|----------|-----|
| **BrowserLeaks** | Deep technical debugging | https://browserleaks.com/ |
| **Pixelscan** | Quick validation | https://pixelscan.net/ |
| **CreepJS** | Behavioral fingerprinting | https://creepjs.vercel.app/ |
| **F.vision** | DataDome testing | - |
| **Whoer.net** | Casual checks | https://whoer.net/ |

**New BrowserLeaks tests:**
- QUIC/HTTP/3 fingerprinting
- TCP/IP fingerprinting
- HTTP/2 fingerprinting
- Chrome extension detection

---

## 6. Recommendations for AutoBiz

### 6.1 Immediate Actions

1. **Keep Camoufox as primary** - Already integrated, best Firefox option
2. **Keep Patchright as secondary** - Already integrated, best for heavy protection
3. **Update user agents** - We have `is_ua_outdated()`, ensure it's running
4. **Consider humanization-playwright** - For sites needing behavioral simulation

### 6.2 New Integrations to Consider

| Tool | Priority | Reason |
|------|----------|--------|
| Zendriver | P2 | More active than Nodriver |
| TLS fingerprint library | P2 | For request-based scraping |
| humanization-playwright | P2 | Better behavioral simulation |

### 6.3 Architecture Considerations

1. **AI Labyrinth avoidance:**
   - Don't follow all links
   - Check `rel="nofollow"` before following
   - Set max crawl depth
   - Validate content relevance before storing

2. **TLS fingerprinting:**
   - Browser automation preferred over requests
   - If using requests, add tls-client or curl-impersonate

3. **Proxy strategy:**
   - Residential for protected sites
   - Implement IPv6 support
   - Add proxy rotation per-request, not per-session

4. **Fingerprint validation:**
   - Run Pixelscan checks periodically
   - Log BrowserLeaks results for debugging
   - Track detection rates per strategy

---

## 7. Sources

### Anti-Bot Systems
- [ZenRows - Bypass Bot Detection 2025](https://www.zenrows.com/blog/bypass-bot-detection)
- [ScrapeOps - How to Bypass Anti-Bots](https://scrapeops.io/web-scraping-playbook/how-to-bypass-antibots/)
- [Cloudflare AI Labyrinth](https://blog.cloudflare.com/ai-labyrinth/)
- [DataDome Q3 2025 Updates](https://datadome.co/changelog/ai-adaptability-ease-q3-product-updates-2025/)

### Cloudflare Bypass
- [ZenRows - Bypass Cloudflare 2025](https://www.zenrows.com/blog/bypass-cloudflare)
- [Scrapfly - Cloudflare Bypass](https://scrapfly.io/blog/posts/how-to-bypass-cloudflare-anti-scraping)
- [ScrapingBee - Cloudflare at Scale](https://www.scrapingbee.com/blog/how-to-bypass-cloudflare-antibot-protection-at-scale/)

### TLS Fingerprinting
- [ZenRows - TLS Fingerprint](https://www.zenrows.com/blog/what-is-tls-fingerprint)
- [Scrapfly - TLS Blocking](https://scrapfly.io/blog/posts/how-to-avoid-web-scraping-blocking-tls)
- [GitHub - TLS Requests](https://github.com/thewebscraping/tls-requests)

### Stealth Libraries
- [Camoufox Docs](https://camoufox.com/)
- [Patchright GitHub](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright)
- [Nodriver GitHub](https://github.com/ultrafunkamsterdam/nodriver)
- [Botright GitHub](https://github.com/Vinyzu/Botright/)
- [Scrapling GitHub](https://github.com/D4Vinci/Scrapling)
- [SeleniumBase UC Mode](https://seleniumbase.io/help_docs/uc_mode/)

### Proxy Detection
- [IPinfo Residential Proxy Detection](https://www.helpnetsecurity.com/2025/07/09/ipinfo-residential-proxy-detection-api/)
- [Datacenter vs Residential Proxies](https://sslinsights.com/datacenter-proxy-vs-residential-proxy/)

### Anti-Bot Evolution
- [Castle.io - Anti-Detect Framework Evolution](https://blog.castle.io/from-puppeteer-stealth-to-nodriver-how-anti-detect-frameworks-evolved-to-evade-bot-detection/)
- [The Web Scraping Club - Browser Automation 2025](https://substack.thewebscraping.club/p/browser-automation-landscape-2025)

---

**Last Updated:** 2025-12-07
**Task:** A.0 Research: Latest Scraping Developments
**Instance:** 1
