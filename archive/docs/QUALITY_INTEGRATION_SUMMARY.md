# Quality Checker Integration - Summary

## Overview
Integrated `quality_checker.py` into the `proxies/tasks.py` pipeline to add Google captcha detection and target site validation checks.

## Changes Made

### File: `/home/wow/Projects/sale-sofia/proxies/tasks.py`

#### 1. Import Addition (Line 14)
```python
from proxies.quality_checker import enrich_proxy_with_quality
```

#### 2. Updated `check_proxy_chunk_task()` Function

**Added to docstring:**
- New progress state: `QUALITY` - Checking quality (Google captcha, target site) for non-transparent proxies

**New quality check stage (Lines 168-212):**
After the anonymity check completes, the function now:

1. Filters to only non-transparent proxies (Anonymous and Elite)
2. Reports QUALITY progress state via `self.update_state()`
3. Calls `enrich_proxy_with_quality(proxy, timeout=15)` for each candidate
4. Updates progress every 5 proxies
5. Logs statistics:
   - How many passed both checks (Google + target site)
   - How many passed Google only
   - How many passed target site only

**Quality check is skipped for:**
- Transparent proxies (don't hide your IP, already filtered in next stage)
- Proxies that failed liveness check
- Proxies that failed anonymity check

#### 3. Updated `process_check_results_task()` Function

**Added to docstring:**
- Notes that quality stats are logged but no filtering is applied
- Users can manually filter `live_proxies.json` based on `google_passed`/`target_passed` fields

**New quality statistics logging (Lines 251-267):**
After combining all chunk results, the function now:

1. Counts how many proxies have quality check data
2. Logs aggregate statistics:
   - Total proxies that were quality-checked
   - How many passed both checks
   - How many passed Google only
   - How many passed target site only

**Design decision:**
- Quality checks do NOT filter out proxies
- All non-transparent live proxies are saved to `live_proxies.json`
- Quality fields (`google_passed`, `target_passed`, `quality_checked_at`) are included in the JSON
- Users can filter manually or programmatically based on their needs

## Pipeline Flow

```
Scraped Proxies
    ↓
[CHECKING] Liveness check (mubeng)
    ↓
[ANONYMITY] Anonymity check (ipinfo.io)
    ↓
Filter out Transparent proxies
    ↓
[QUALITY] Quality check (Google + imot.bg) ← NEW STAGE
    ↓
Save to live_proxies.json with quality fields
```

## Output Data Structure

Each proxy in `live_proxies.json` now includes:

```json
{
  "host": "1.2.3.4",
  "port": 8080,
  "protocol": "http",
  "timeout": 1.234,
  "anonymity": "Elite",
  "anonymity_checked_at": 1703123456.789,
  "google_passed": true,         // NEW: Google captcha check result
  "target_passed": true,          // NEW: imot.bg site check result
  "quality_checked_at": 1703123457.890  // NEW: Quality check timestamp
}
```

## Progress States

The Celery task now reports 3 states:

1. **CHECKING** - Running mubeng liveness check
   - Meta: `{stage, total, checked, live}`

2. **ANONYMITY** - Checking anonymity levels
   - Meta: `{stage, total, live, checked}`

3. **QUALITY** - Checking Google captcha + target site ← NEW
   - Meta: `{stage, total, live, quality_candidates, checked}`

## Usage

### Run the integrated pipeline:
```bash
# Scrape and check (includes quality checks)
python main.py proxy scrape-and-check

# Or use separate commands
python main.py proxy scrape
python main.py proxy check
```

### Filter quality proxies manually:
```python
import json

# Load proxies
with open("proxies/live_proxies.json") as f:
    proxies = json.load(f)

# Filter to only proxies that passed both quality checks
high_quality = [
    p for p in proxies
    if p.get("google_passed") and p.get("target_passed")
]

print(f"Found {len(high_quality)} high-quality proxies")
```

## Testing

To verify syntax:
```bash
python3 test_syntax.py
```

## Notes

- Quality checks use 15 second timeout per proxy
- Progress updates every 5 proxies during quality stage
- Quality checks are only run on non-transparent proxies (saves time)
- All quality check data is preserved in the output JSON for later filtering
- The quality checker validates against:
  - Google search (detects captchas)
  - imot.bg homepage (validates target site access)
