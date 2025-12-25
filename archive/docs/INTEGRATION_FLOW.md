# ScoredProxyPool Integration Flow

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         main.py                                  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ run_auto_mode()                                            │ │
│  │                                                            │ │
│  │  1. Start Redis & Celery                                  │ │
│  │  2. Wait for proxies (min 5)                              │ │
│  │  3. Initialize ScoredProxyPool  ← NEW                     │ │
│  │  4. Start mubeng rotator (localhost:8089)                 │ │
│  │  5. Pre-flight check with recovery                        │ │
│  │  6. Scrape all start URLs                                 │ │
│  │     - Pass proxy_pool to scraper                          │ │
│  │     - Collect stats from each run                         │ │
│  │  7. Save final scores           ← NEW                     │ │
│  │  8. Print summary statistics    ← NEW                     │ │
│  │  9. Stop mubeng & cleanup                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ scrape_from_start_url()                                    │ │
│  │                                                            │ │
│  │  Phase 1: Collect listing URLs (with pagination)          │ │
│  │    - Load search pages                                    │ │
│  │    - Extract listing URLs                                 │ │
│  │    - Record failures if page load fails  ← NEW            │ │
│  │                                                            │ │
│  │  Phase 2: Scrape each listing                             │ │
│  │    for each listing:                                      │ │
│  │      - Load page                                          │ │
│  │      - Extract data                                       │ │
│  │      - Save to database                                   │ │
│  │      - Record success/failure       ← NEW                 │ │
│  │                                                            │ │
│  │  Return: {scraped, failed, total_attempts}  ← NEW         │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

                              │
                              ▼

┌─────────────────────────────────────────────────────────────────┐
│                   ScoredProxyPool                                │
│                 (proxies/proxy_scorer.py)                        │
│                                                                   │
│  - Loads proxies from live_proxies.json                         │
│  - Loads/saves scores from/to proxy_scores.json                 │
│  - Thread-safe scoring with locks                               │
│  - Auto-save on each update                                     │
│                                                                   │
│  Methods used:                                                   │
│    __init__(proxies_file)     - Initialize pool                 │
│    record_result(proxy, bool) - Track success/failure           │
│    reload_proxies()           - Reload after refresh            │
│    save_scores()              - Persist to disk                 │
│    get_stats()                - Get pool statistics             │
└─────────────────────────────────────────────────────────────────┘

                              │
                              ▼

┌─────────────────────────────────────────────────────────────────┐
│                     Data Flow                                    │
│                                                                   │
│  live_proxies.json  ──→  ScoredProxyPool  ──→  proxy_scores.json│
│  (from Celery tasks)     (in-memory)          (persisted)        │
│                                                                   │
│  Structure:                  Tracks:              Structure:     │
│  [                          - Score              {               │
│    {                        - Failures             "host:port": {│
│      "host": "1.2.3.4",     - Last used             "score": 1.0│
│      "port": 8080,                                  "failures": 0│
│      "protocol": "http",                            "last_used": │
│      "timeout": 2.5                                   timestamp  │
│    },                                              }             │
│    ...                                           }               │
│  ]                                                                │
└─────────────────────────────────────────────────────────────────┘
```

## Detailed Scraping Flow

```
START SCRAPING
    │
    ├─ Initialize proxy_pool
    │   └─ Load live_proxies.json
    │   └─ Load proxy_scores.json (if exists)
    │   └─ Print initial stats
    │
    ├─ Start mubeng rotator
    │   └─ Serves at http://localhost:8089
    │   └─ Rotates among all proxies from live_proxies.json
    │
    ├─ For each start URL:
    │   │
    │   ├─ Phase 1: Collect listing URLs
    │   │   │
    │   │   ├─ Load search page
    │   │   │   ├─ SUCCESS → Extract URLs
    │   │   │   │   └─ (no recording)
    │   │   │   │
    │   │   │   └─ FAILURE → Break pagination
    │   │   │       └─ record_result(proxy, success=False)  ← NEW
    │   │   │
    │   │   └─ Repeat for next page...
    │   │
    │   └─ Phase 2: Scrape each listing
    │       │
    │       ├─ Load listing page
    │       │
    │       ├─ Extract listing data
    │       │   ├─ SUCCESS → Save to DB
    │       │   │   ├─ stats["scraped"] += 1
    │       │   │   └─ record_result(proxy, success=True)  ← NEW
    │       │   │
    │       │   └─ FAILURE → Log warning
    │       │       ├─ stats["failed"] += 1
    │       │       └─ record_result(proxy, success=False)  ← NEW
    │       │
    │       └─ Sleep 6 seconds (rate limit)
    │
    ├─ Print per-URL stats
    │   └─ [STATS] Scraped: X, Failed: Y  ← NEW
    │
    ├─ Aggregate all stats
    │
    ├─ Save final scores
    │   └─ proxy_pool.save_scores()  ← NEW
    │
    ├─ Print summary
    │   ├─ [SUMMARY] Total scraped: X, Failed: Y, Success rate: Z%  ← NEW
    │   └─ [SUCCESS] Final proxy stats: N proxies, avg score: S  ← NEW
    │
    └─ Stop mubeng & cleanup

END SCRAPING
```

## Scoring Logic

```
record_result(proxy_url, success=True/False)
    │
    ├─ Extract host:port from URL
    │   └─ "http://localhost:8089" → "localhost:8089"
    │
    ├─ Find in scores dict
    │   ├─ Found:
    │   │   ├─ If success=True:
    │   │   │   ├─ score *= 1.1 (+10% reward)
    │   │   │   └─ failures = 0 (reset counter)
    │   │   │
    │   │   └─ If success=False:
    │   │       ├─ score *= 0.5 (-50% penalty)
    │   │       ├─ failures += 1
    │   │       │
    │   │       └─ Check auto-prune conditions:
    │   │           ├─ failures >= 3? → Remove proxy
    │   │           └─ score < 0.01? → Remove proxy
    │   │
    │   └─ Not found:
    │       └─ Log warning (happens with mubeng URL)
    │
    └─ Save scores to disk (async I/O)
```

## Recovery Flow with Proxy Refresh

```
Pre-flight Check Fails
    │
    ├─ Level 1: Mubeng Auto-Rotation (6 attempts)
    │   └─ Mubeng rotates internally on each failure
    │
    ├─ Level 2: Soft Restart (3 attempts)
    │   ├─ Stop mubeng
    │   ├─ Restart mubeng (same proxy list)
    │   └─ Try pre-flight again
    │
    └─ Level 3: Full Refresh (final attempt)
        ├─ Stop mubeng
        ├─ Trigger Celery proxy refresh (5-10 min)
        ├─ Wait for completion
        │
        ├─ Reload proxy pool  ← NEW
        │   └─ proxy_pool.reload_proxies()
        │   └─ Re-initialize scores for new proxies
        │
        ├─ Restart mubeng with fresh proxies
        └─ Try pre-flight again
```

## Data Persistence

```
Session Start:
    ├─ Load live_proxies.json
    │   └─ List of available proxies
    │
    └─ Load proxy_scores.json (if exists)
        └─ Historical scores from previous sessions

During Session:
    ├─ Each record_result() call:
    │   ├─ Update in-memory scores
    │   └─ Save to proxy_scores.json

Session End:
    └─ Final save_scores() call
        └─ Ensure all scores persisted

Next Session Start:
    └─ Scores are loaded and used
        └─ Historical performance influences initial state
```

## Mubeng Integration Note

```
┌──────────────────────────────────────────────────────────────┐
│  IMPORTANT: Scoring tracks mubeng endpoint, not individual  │
│  proxies, because mubeng hides which proxy was actually     │
│  used for each request.                                      │
│                                                              │
│  Scraper → http://localhost:8089 → Mubeng → Random Proxy    │
│            └─ This is what gets scored                       │
│                                                              │
│  This provides:                                              │
│  ✓ Overall proxy pool health monitoring                     │
│  ✓ Historical performance tracking                          │
│  ✓ Foundation for future direct proxy selection             │
│                                                              │
│  This does NOT provide:                                      │
│  ✗ Individual proxy performance scores (mubeng hides this)  │
│  ✗ Weighted proxy selection (mubeng uses random)            │
│  ✗ Adaptive proxy ranking (mubeng rotation is fixed)        │
└──────────────────────────────────────────────────────────────┘
```

## Example Session Output

```bash
$ python main.py

============================================================
SOFIA REAL ESTATE SCRAPER - AUTO MODE
============================================================

[INFO] Found 5 start URLs across 3 sites

[INFO] Checking proxy availability...
[INFO] Initializing proxy scoring system...
[SUCCESS] Proxy pool initialized: 47 proxies, avg score: 1.15

[INFO] Starting proxy rotator...
[SUCCESS] Proxy rotator running at http://localhost:8089

[INFO] Running pre-flight proxy check...
[SUCCESS] Pre-flight check passed (attempt 1)

============================================================
STARTING CRAWL
============================================================

[SITE] imoti.net (2 start URLs)

[1/2] https://www.imoti.net/pcgi/...
[INFO] Starting crawl from: https://www.imoti.net/pcgi/...
[INFO] Target: 100 listings
[Page 1] Loading: ...
  Found 25 new listings (total: 25)
[1/25] https://www.imoti.net/bg/...
  -> Saved: 155000 EUR, 85 sqm
[2/25] https://www.imoti.net/bg/...
  -> Saved: 175000 EUR, 95 sqm
...
[STATS] Scraped: 95, Failed: 5

[2/2] https://www.imoti.net/pcgi/...
[STATS] Scraped: 98, Failed: 2

============================================================
CRAWL COMPLETE
============================================================

[SUMMARY] Total scraped: 450, Failed: 15, Success rate: 96.8%

[INFO] Saving final proxy scores...
[SUCCESS] Final proxy stats: 47 proxies, avg score: 1.08

[INFO] Stopping proxy rotator...
[INFO] All processes stopped. Goodbye!
```

## File Structure After Integration

```
/home/wow/Projects/sale-sofia/
├── main.py                           (modified - integration code)
├── proxies/
│   ├── proxy_scorer.py              (existing - scoring logic)
│   ├── live_proxies.json            (existing - available proxies)
│   └── proxy_scores.json            (created - persisted scores)
├── test_integration.py              (new - test suite)
├── check_syntax.py                  (new - syntax checker)
├── PROXY_SCORER_INTEGRATION.md      (new - detailed docs)
├── INTEGRATION_SUMMARY.md           (new - quick reference)
└── INTEGRATION_FLOW.md              (new - this file)
```

## Summary

The integration adds **monitoring and tracking** capabilities to the scraping pipeline:

- ✓ Tracks success/failure of every listing scrape
- ✓ Records search page load failures
- ✓ Persists scores across sessions
- ✓ Provides statistics and summaries
- ✓ Gracefully degrades if initialization fails
- ✓ Reloads pool after proxy refresh
- ✓ Thread-safe and production-ready

Future enhancements can build on this foundation to add **actionable optimizations** like weighted proxy selection or intelligent filtering.
