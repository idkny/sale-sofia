# Quality Checker - Usage Guide

## Quick Start

### Run the complete pipeline with quality checks
```bash
python main.py proxy scrape-and-check
```

This will:
1. Scrape new proxies
2. Check liveness (mubeng)
3. Check anonymity (ipinfo.io)
4. Check quality (Google + imot.bg) ← NEW!
5. Save results to `proxies/live_proxies.json`

## Monitoring Progress

The Celery worker logs show detailed progress:

```
[INFO] Chunk liveness check: 45/100 proxies alive
[INFO] Checking anonymity for 45 live proxies...
[INFO] Anonymity check complete: {'Elite': 20, 'Anonymous': 15, 'Transparent': 10}
[INFO] Checking quality for 35 non-transparent proxies...
[INFO] Quality check complete: 28/35 passed both checks (Google: 30, Target: 32)
```

## Understanding the Output

### Output File: `proxies/live_proxies.json`

```json
[
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
]
```

### Field Meanings

| Field | Type | Description |
|-------|------|-------------|
| `host` | string | Proxy IP address |
| `port` | int | Proxy port number |
| `protocol` | string | http or https |
| `timeout` | float | Response time in seconds (speed metric) |
| `anonymity` | string | Transparent / Anonymous / Elite |
| `anonymity_checked_at` | float | Unix timestamp of anonymity check |
| `google_passed` | bool | True if Google search works (no captcha) |
| `target_passed` | bool | True if imot.bg loads correctly |
| `quality_checked_at` | float | Unix timestamp of quality check |

## Filtering Proxies

### Python Script

```python
import json

# Load all proxies
with open("proxies/live_proxies.json") as f:
    all_proxies = json.load(f)

# Strategy 1: Premium proxies (both checks passed)
premium = [
    p for p in all_proxies
    if p.get("google_passed") and p.get("target_passed")
]
print(f"Premium proxies: {len(premium)}")

# Strategy 2: Target-focused (imot.bg works, don't care about Google)
imot_ready = [
    p for p in all_proxies
    if p.get("target_passed")
]
print(f"Imot.bg ready: {len(imot_ready)}")

# Strategy 3: Elite + target site working
elite_imot = [
    p for p in all_proxies
    if p.get("anonymity") == "Elite" and p.get("target_passed")
]
print(f"Elite + imot.bg: {len(elite_imot)}")

# Strategy 4: Fast + working (timeout < 2s, target works)
fast_working = [
    p for p in all_proxies
    if p.get("timeout", 999) < 2.0 and p.get("target_passed")
]
print(f"Fast + working: {len(fast_working)}")

# Save filtered list
with open("proxies/premium_proxies.json", "w") as f:
    json.dump(premium, f, indent=2)
```

### Command Line (jq)

```bash
# Count premium proxies
jq '[.[] | select(.google_passed == true and .target_passed == true)] | length' \
  proxies/live_proxies.json

# Extract only proxies that work with imot.bg
jq '[.[] | select(.target_passed == true)]' \
  proxies/live_proxies.json > proxies/imot_ready.json

# Get elite proxies that work with target site
jq '[.[] | select(.anonymity == "Elite" and .target_passed == true)]' \
  proxies/live_proxies.json > proxies/elite_working.json

# Sort by speed and filter working
jq '[.[] | select(.target_passed == true)] | sort_by(.timeout)' \
  proxies/live_proxies.json > proxies/fast_working.json
```

## Quality Check Statistics

After each run, check the logs for statistics:

```
[INFO] Quality statistics: 350 proxies checked.
       Passed both checks: 280,
       Google only: 310,
       Target only: 295
```

This tells you:
- 350 proxies were quality-checked (non-transparent)
- 280 work with both Google and imot.bg
- 310 work with Google (may have issues with imot.bg)
- 295 work with imot.bg (may trigger Google captchas)

## Recommended Workflows

### Workflow 1: Maximize Quality
```bash
# Run full check
python main.py proxy scrape-and-check

# Filter to premium only
jq '[.[] | select(.google_passed == true and .target_passed == true)]' \
  proxies/live_proxies.json > proxies/premium.json

# Use premium.json for scraping
```

### Workflow 2: Target-Site Focused
```bash
# Run full check
python main.py proxy scrape-and-check

# Filter to imot.bg working proxies
jq '[.[] | select(.target_passed == true)]' \
  proxies/live_proxies.json > proxies/imot_ready.json

# Use imot_ready.json for scraping
```

### Workflow 3: Speed Prioritized
```bash
# Run full check
python main.py proxy scrape-and-check

# Get fast proxies that work with target
jq '[.[] | select(.target_passed == true and .timeout < 2)] | sort_by(.timeout)' \
  proxies/live_proxies.json > proxies/fast.json

# Use fast.json for scraping
```

## Troubleshooting

### Too Many Proxies Fail Quality Checks

If most proxies fail `google_passed` or `target_passed`:

1. **Check if sites are actually up:**
   ```bash
   curl -I https://www.google.com
   curl -I https://www.imot.bg
   ```

2. **Try a known-good proxy manually:**
   ```bash
   curl -x http://185.10.68.95:3128 https://www.google.com
   curl -x http://185.10.68.95:3128 https://www.imot.bg
   ```

3. **Review quality_checker.py timeout:**
   - Default: 15 seconds
   - May need to increase for slow proxies
   - Edit line 188 in `proxies/tasks.py`: `enrich_proxy_with_quality(proxy, timeout=30)`

### Quality Checks Are Slow

To speed up:

1. **Reduce quality check timeout:**
   - Edit line 188: `enrich_proxy_with_quality(proxy, timeout=10)`

2. **Skip quality checks entirely** (temporary):
   - Comment out lines 168-212 in `proxies/tasks.py`
   - Re-run check

3. **Increase progress update frequency:**
   - Change line 190: `if (i + 1) % 10 == 0:` (update every 10 instead of 5)

## Advanced: Custom Quality Checks

To add your own target site:

```python
# Edit proxies/quality_checker.py

# Add new indicators for your site
MY_SITE_INDICATORS = [
    "expected text",
    "another indicator",
]

# Modify check_target_site() to support your site
if "mysite.com" in target_url.lower():
    response_text_lower = response.text.lower()
    for indicator in MY_SITE_INDICATORS:
        if indicator.lower() in response_text_lower:
            return True
    return False
```

Then in tasks.py, call with custom URL:
```python
# This requires modifying the enrich_proxy_with_quality function
# to accept a custom target_url parameter
```

## Next Steps

1. Run the integrated pipeline: `python main.py proxy scrape-and-check`
2. Review the logs for quality statistics
3. Filter the output JSON based on your needs
4. Use the filtered proxies in your scrapers
5. Monitor which proxies get blocked over time
6. Re-run quality checks periodically to refresh the list
