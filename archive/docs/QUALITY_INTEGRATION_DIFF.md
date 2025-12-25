# Quality Checker Integration - Code Changes

## File Modified: `/home/wow/Projects/sale-sofia/proxies/tasks.py`

### Change 1: Import Statement (Line 14)

```diff
  from celery_app import celery_app
  from paths import MUBENG_EXECUTABLE_PATH, PROXIES_DIR, PROXY_CHECKER_DIR, PSC_EXECUTABLE_PATH
  from proxies.anonymity_checker import enrich_proxy_with_anonymity, get_real_ip
+ from proxies.quality_checker import enrich_proxy_with_quality
```

### Change 2: Updated Docstring for `check_proxy_chunk_task()` (Lines 94-102)

```diff
  @celery_app.task(bind=True, max_retries=2)
  def check_proxy_chunk_task(self, proxy_chunk: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
      """
      Worker task that checks a small chunk of proxies for liveness and returns the live ones.
      Uses mubeng binary with 120 second timeout.

      Progress states reported via self.update_state():
      - CHECKING: Running mubeng liveness check
      - ANONYMITY: Checking anonymity levels for live proxies
+     - QUALITY: Checking quality (Google captcha, target site) for non-transparent proxies
      """
```

### Change 3: Quality Check Stage Added (Lines 168-212)

```diff
              # Count anonymity levels
              anon_counts = {}
              for p in live_proxies_in_chunk:
                  level = p.get("anonymity", "Unknown")
                  anon_counts[level] = anon_counts.get(level, 0) + 1
              logger.info(f"Anonymity check complete: {anon_counts}")

+         # Quality check stage: Only check non-transparent proxies
+         quality_candidates = [
+             p for p in live_proxies_in_chunk
+             if p.get("anonymity") not in ("Transparent", "1")
+         ]
+
+         if quality_candidates:
+             logger.info(f"Checking quality for {len(quality_candidates)} non-transparent proxies...")
+             self.update_state(
+                 state="QUALITY",
+                 meta={
+                     "stage": "quality",
+                     "total": chunk_size,
+                     "live": len(live_proxies_in_chunk),
+                     "quality_candidates": len(quality_candidates),
+                     "checked": 0
+                 }
+             )
+
+             for i, proxy in enumerate(quality_candidates):
+                 enrich_proxy_with_quality(proxy, timeout=15)
+                 # Update progress every 5 proxies
+                 if (i + 1) % 5 == 0:
+                     self.update_state(
+                         state="QUALITY",
+                         meta={
+                             "stage": "quality",
+                             "total": chunk_size,
+                             "live": len(live_proxies_in_chunk),
+                             "quality_candidates": len(quality_candidates),
+                             "checked": i + 1
+                         }
+                     )
+
+             # Count quality results
+             google_passed = sum(1 for p in quality_candidates if p.get("google_passed"))
+             target_passed = sum(1 for p in quality_candidates if p.get("target_passed"))
+             both_passed = sum(
+                 1 for p in quality_candidates
+                 if p.get("google_passed") and p.get("target_passed")
+             )
+             logger.info(
+                 f"Quality check complete: {both_passed}/{len(quality_candidates)} passed both checks "
+                 f"(Google: {google_passed}, Target: {target_passed})"
+             )
+
      except subprocess.TimeoutExpired:
```

### Change 4: Updated Docstring for `process_check_results_task()` (Lines 227-233)

```diff
  @celery_app.task
  def process_check_results_task(results: List[List[Dict[str, Any]]]):
      """
      Callback task that collects results from all chunk tasks,
      combines them, and saves the final master list.
+
+     Logs quality check statistics but does not filter by quality.
+     Users can filter the live_proxies.json file based on google_passed/target_passed fields.
      """
```

### Change 5: Quality Statistics Logging Added (Lines 251-267)

```diff
      if not all_live_proxies:
          logger.warning("No live proxies were found across all chunks.")
          return "Completed: No live proxies found."

+     # Log quality check statistics (if quality checks were performed)
+     quality_checked = [p for p in all_live_proxies if "quality_checked_at" in p]
+     if quality_checked:
+         google_passed = sum(1 for p in quality_checked if p.get("google_passed"))
+         target_passed = sum(1 for p in quality_checked if p.get("target_passed"))
+         both_passed = sum(
+             1 for p in quality_checked
+             if p.get("google_passed") and p.get("target_passed")
+         )
+         logger.info(
+             f"Quality statistics: {len(quality_checked)} proxies checked. "
+             f"Passed both checks: {both_passed}, "
+             f"Google only: {google_passed}, "
+             f"Target only: {target_passed}"
+         )
+     else:
+         logger.info("No quality checks were performed on proxies.")
+
      # Sort by timeout (speed)
      all_live_proxies.sort(key=lambda p: p.get("timeout", 999))
```

## Summary of Changes

| Change | Lines | Type | Description |
|--------|-------|------|-------------|
| Import | 14 | Addition | Import `enrich_proxy_with_quality` function |
| Docstring | 101 | Update | Document new QUALITY progress state |
| Quality Stage | 168-212 | Addition | Add quality check loop after anonymity |
| Docstring | 231-232 | Addition | Document quality stats logging behavior |
| Statistics | 251-267 | Addition | Log aggregate quality check results |

## Total Lines Changed
- **Lines added:** ~60
- **Lines modified:** 2 (docstrings)
- **Lines removed:** 0

## No Breaking Changes
- All existing functionality preserved
- Quality checks are additive, not replacing anything
- Output files retain same structure with new optional fields
- Can be disabled by commenting out lines 168-212

## Verification Commands

```bash
# Check syntax
python3 -m py_compile /home/wow/Projects/sale-sofia/proxies/tasks.py

# Run test
python /home/wow/Projects/sale-sofia/test_syntax.py

# Test full pipeline
python main.py proxy scrape-and-check
```

## Rollback Procedure

If needed, revert changes:

```python
# Comment out the import
# from proxies.quality_checker import enrich_proxy_with_quality

# Comment out lines 168-212 (quality check stage)
# Comment out lines 251-267 (quality statistics)

# Or restore from git:
git checkout proxies/tasks.py
```
