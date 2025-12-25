# Data Flow

> How data moves through the system. Read when debugging data issues or understanding the pipeline.

---

## 1. Scraping Pipeline

```
┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│ start_urls   │ ──→ │ Orchestrator │ ──→ │    Redis     │
│   (YAML)     │     │             │     │   Started    │
└──────────────┘     └─────────────┘     └──────────────┘
                            │
                            ↓
                     ┌─────────────┐     ┌──────────────┐
                     │   Celery    │ ←── │ Proxy Tasks  │
                     │   Worker    │     │  (scrape,    │
                     └─────────────┘     │   check)     │
                            │            └──────────────┘
                            ↓
                     ┌─────────────┐
                     │   Mubeng    │ (proxy rotator on :8089)
                     │   Rotator   │
                     └─────────────┘
                            │
                            ↓
┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  Playwright  │ ←── │  Browser    │ ←── │  Strategy    │
│   Browser    │     │   Handle    │     │  (stealth)   │
└──────────────┘     └─────────────┘     └──────────────┘
        │
        ↓
┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│    HTML      │ ──→ │  Scraper    │ ──→ │ ListingData  │
│   Content    │     │ (imot.bg)   │     │  (dataclass) │
└──────────────┘     └─────────────┘     └──────────────┘
                            │
                            ↓
                     ┌─────────────┐
                     │   SQLite    │ (data/bg-estate.db)
                     │  Database   │
                     └─────────────┘
                            │
                            ↓
                     ┌─────────────┐
                     │  Streamlit  │ (app/)
                     │  Dashboard  │
                     └─────────────┘
```

**Key Files**:
- `config/start_urls.yaml` - Starting URLs per site
- `orchestrator.py` - Service lifecycle
- `browsers/browsers_main.py` - Browser factory
- `websites/*/` - Site-specific scrapers
- `data/data_store_main.py` - SQLite operations

---

## 2. Proxy Management Pipeline

```
┌──────────────────────────────────────────────────────────┐
│                    CELERY TASK CHAIN                      │
└──────────────────────────────────────────────────────────┘
        │
        ↓
┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│    PSC       │ ──→ │   Mubeng    │ ──→ │  Anonymity   │
│  (scrape)    │     │  (liveness) │     │   Checker    │
│ ~5000 raw    │     │  ~500 live  │     │ Elite/Anon   │
└──────────────┘     └─────────────┘     └──────────────┘
                            │
                            ↓
                     ┌─────────────┐     ┌──────────────┐
                     │   Quality   │ ──→ │  Filter &    │
                     │   Checker   │     │    Save      │
                     │  (IP check) │     │  .json/.txt  │
                     └─────────────┘     └──────────────┘
                            │
                            ↓
                     ┌─────────────┐
                     │   Mubeng    │ (rotator mode)
                     │   Server    │ → http://localhost:8089
                     └─────────────┘
```

**Key Files**:
- `proxies/tasks.py` - Celery task definitions
- `proxies/mubeng_manager.py` - Mubeng binary wrapper
- `proxies/anonymity_checker.py` - Elite/Anonymous detection
- `proxies/quality_checker.py` - IP verification
- `proxies/live_proxies.json` - Output file

---

## 3. Quality Checker Deep Dive

The quality checker tests proxies **beyond basic liveness** to verify they actually work and hide your IP.

### Purpose

After mubeng confirms a proxy is "alive", quality checker answers:
1. Does the proxy actually hide my IP? (IP check)
2. Can it reach target sites without getting blocked? (Target check - currently disabled)

### Two Checks

| Check | What It Does | Status |
|-------|--------------|--------|
| **IP Check** | Requests IP services (ipify, icanhazip) and verifies exit IP differs from real IP | Active |
| **Target Check** | Loads imot.bg and looks for expected content ("имоти") | Disabled* |

*Target check disabled because free proxies are too slow/unreliable for the 60s timeout.

### IP Check Flow

```
Proxy → IP Check Service (ipify.org)
         ↓
       Response: "1.2.3.4"
         ↓
       Compare to your real IP's /24 subnet
         ↓
       Same subnet → REJECT (proxy not actually proxying)
       Different   → PASS
```

### Security Feature

**Location**: `proxies/quality_checker.py:143-155`

```python
# CRITICAL: Reject if exit_ip matches our real IP
if exit_ip.startswith(real_ip_prefix + "."):
    logger.warning(f"Proxy returned our real IP - rejecting")
    return False, None
```

This catches "fake" proxies that appear alive but route traffic directly (exposing your IP).

### Output Fields Added to Proxy

```python
{
    "ip_check_passed": True,       # Did IP check pass?
    "ip_check_exit_ip": "1.2.3.4", # What IP did we exit from?
    "target_passed": None,          # Currently disabled
    "quality_checked_at": 1703...   # Unix timestamp
}
```

---

## 4. Entry Point Flow

**Location**: `main.py`

```python
def main():
    load_dotenv()
    setup_logging(LOGS_DIR)
    run_auto_mode()

def run_auto_mode():
    with Orchestrator() as orch:
        orch.start_redis()
        orch.start_celery()
        orch.wait_for_proxies()

        proxy_url, process, temp_file = setup_mubeng_rotator(port=8089)

        for site, urls in get_start_urls().items():
            scraper = get_scraper(site)
            for url in urls:
                asyncio.run(scrape_from_start_url(scraper, url, proxy=proxy_url))
```

---

## Quick Debugging Guide

| Symptom | Check |
|---------|-------|
| No proxies available | `proxies/live_proxies.json` exists and has entries |
| Proxy not hiding IP | Quality checker logs, `/24 subnet` matching |
| Scraping fails | Browser logs, proxy connectivity |
| Data not in DB | `data/bg-estate.db`, scraper extraction logs |
| Dashboard empty | SQLite query, Streamlit connection |
