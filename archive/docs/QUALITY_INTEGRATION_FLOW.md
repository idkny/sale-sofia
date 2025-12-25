# Quality Checker Integration - Pipeline Flow

## Complete Pipeline Visualization

```
┌─────────────────────────────────────────────────────────────────────┐
│  scrape_new_proxies_task()                                          │
│  - Uses proxy-scraper-checker binary                                │
│  - Outputs: proxies_pretty.json (raw scraped proxies)              │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  check_scraped_proxies_task()                                       │
│  - Dispatcher: splits proxies into chunks of 100                    │
│  - Spawns parallel check_proxy_chunk_task() workers                 │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
         ┌─────────────────┴─────────────────┐
         │   Parallel Worker Tasks (1 per chunk of 100)
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  check_proxy_chunk_task(chunk) - Worker                             │
│                                                                      │
│  STAGE 1: LIVENESS CHECK                                            │
│  ├─ State: CHECKING                                                 │
│  ├─ Uses: mubeng binary                                             │
│  ├─ Timeout: 120 seconds                                            │
│  └─ Result: live_proxies_in_chunk[]                                 │
│                                                                      │
│  STAGE 2: ANONYMITY CHECK                                           │
│  ├─ State: ANONYMITY                                                │
│  ├─ Uses: enrich_proxy_with_anonymity()                             │
│  ├─ Tests: ipinfo.io to detect IP leakage                           │
│  ├─ Timeout: 10 seconds per proxy                                   │
│  ├─ Progress: Updates every 10 proxies                              │
│  └─ Result: Proxies enriched with anonymity level                   │
│      - Transparent (shows your real IP)                             │
│      - Anonymous (hides IP, shows proxy usage)                      │
│      - Elite (fully anonymous)                                      │
│                                                                      │
│  STAGE 3: QUALITY CHECK ← NEW!                                      │
│  ├─ State: QUALITY                                                  │
│  ├─ Filter: Only non-transparent proxies                            │
│  ├─ Uses: enrich_proxy_with_quality()                               │
│  ├─ Tests:                                                          │
│  │   ├─ Google search (detects captchas)                            │
│  │   └─ imot.bg homepage (validates target site)                    │
│  ├─ Timeout: 15 seconds per proxy                                   │
│  ├─ Progress: Updates every 5 proxies                               │
│  └─ Result: Proxies enriched with:                                  │
│      - google_passed: bool                                          │
│      - target_passed: bool                                          │
│      - quality_checked_at: timestamp                                │
│                                                                      │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
         ┌─────────────────┴─────────────────┐
         │   Collect results from all workers
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  process_check_results_task(results)                                │
│                                                                      │
│  1. Combine all chunks                                              │
│  2. Filter out Transparent proxies                                  │
│  3. Log quality statistics ← NEW!                                   │
│     - Total quality-checked                                         │
│     - Passed both checks (Google + target)                          │
│     - Passed Google only                                            │
│     - Passed target only                                            │
│  4. Sort by speed (timeout)                                         │
│  5. Save to:                                                        │
│     - proxies/live_proxies.json (with quality fields)               │
│     - proxies/live_proxies.txt                                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Transformation Example

### Input (scraped proxy)
```json
{
  "host": "185.10.68.95",
  "port": 3128,
  "protocol": "http"
}
```

### After Liveness Check
```json
{
  "host": "185.10.68.95",
  "port": 3128,
  "protocol": "http",
  "timeout": 1.234
}
```

### After Anonymity Check
```json
{
  "host": "185.10.68.95",
  "port": 3128,
  "protocol": "http",
  "timeout": 1.234,
  "anonymity": "Elite",
  "anonymity_checked_at": 1703123456.789
}
```

### After Quality Check (NEW!)
```json
{
  "host": "185.10.68.95",
  "port": 3128,
  "protocol": "http",
  "timeout": 1.234,
  "anonymity": "Elite",
  "anonymity_checked_at": 1703123456.789,
  "google_passed": true,
  "target_passed": true,
  "quality_checked_at": 1703123457.890
}
```

## Progress State Metadata

### CHECKING State
```json
{
  "stage": "liveness",
  "total": 100,
  "checked": 0,
  "live": 0
}
```

### ANONYMITY State
```json
{
  "stage": "anonymity",
  "total": 100,
  "live": 45,
  "checked": 30
}
```

### QUALITY State (NEW!)
```json
{
  "stage": "quality",
  "total": 100,
  "live": 45,
  "quality_candidates": 40,
  "checked": 20
}
```

## Filtering Strategy

### In Pipeline (Automatic)
- Transparent proxies are filtered OUT (they expose your real IP)
- Quality-failed proxies are kept IN (user can filter later)

### Post-Pipeline (Manual)
Users can filter based on quality fields:

```python
# Only proxies that work with Google
google_ok = [p for p in proxies if p.get("google_passed")]

# Only proxies that work with imot.bg
imot_ok = [p for p in proxies if p.get("target_passed")]

# Only proxies that work with both
premium = [p for p in proxies
           if p.get("google_passed") and p.get("target_passed")]

# Elite + working with target site
elite_working = [p for p in proxies
                 if p.get("anonymity") == "Elite"
                 and p.get("target_passed")]
```

## Performance Characteristics

### Per 100 proxies (1 chunk):
- Liveness check: ~120 seconds (parallel via mubeng)
- Anonymity check: ~10-30 proxies survive → 100-300 seconds
- Quality check: ~5-20 non-transparent proxies → 75-300 seconds
- **Total: ~5-10 minutes per chunk**

### For 1000 proxies:
- 10 chunks running in parallel
- **Total: ~5-10 minutes** (parallel execution)

### Optimization:
- Quality checks only run on non-transparent proxies (saves ~50% time)
- Progress updates reduce overhead (every 5 instead of every 1)
- Uses httpx for async-capable HTTP client
