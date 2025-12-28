# Pre-Production Audit - Final Action Item

**Date**: 2025-12-28
**Status**: 1 action item remaining

---

## Summary

6 AI agents audited the codebase. 4 potential issues were identified and analyzed for impact.

**Result**: 3 of 4 were cancelled after deep analysis. 1 safe change to implement.

| Original Issue | After Impact Analysis | Verdict |
|----------------|----------------------|---------|
| DB error handling | "Fail fast" is CORRECT | Cancelled |
| PROXY_WAIT_TIMEOUT | Parameter is dead code | Cancelled |
| SQL field allowlist | Low risk, defensive | **Proceed** |
| Port validation | Already type-safe | Deferred |

---

## Action Item: Add Field Allowlist to `update_listing_evaluation()`

### Location
`data/data_store_main.py` - function `update_listing_evaluation()` around line 454

### Problem
The function builds SQL dynamically from kwargs field names without validation:
```python
for field, value in field_map.items():
    updates.append(f"{field} = ?")  # field name not validated
```

### Risk Level: LOW
- All current callers pass hardcoded field names
- No user input or LLM-generated field names
- This is pure defense-in-depth

### Implementation

Add this allowlist before the loop (around line 460):

```python
ALLOWED_UPDATE_FIELDS = {
    # Explicit function parameters
    "status", "decision", "decision_reason", "follow_up_actions",
    "estimated_renovation_eur", "user_notes",
    # User evaluation
    "date_found", "has_legal_issues", "floor_plan_url", "building_condition_notes",
    # Feature flags from original schema
    "has_elevator", "has_balcony", "has_garden", "has_parking", "has_storage", "condition",
    # Extended features
    "has_security_entrance", "has_ac_preinstalled", "has_central_heating",
    "has_gas_heating", "has_double_glazing", "has_security_door",
    "has_video_intercom", "has_separate_kitchen",
    # Furnishing
    "is_furnished", "has_builtin_wardrobes", "has_appliances", "is_recently_renovated",
    # Outdoor
    "has_terrace", "has_multiple_balconies", "has_laundry_space", "has_garage",
    # Location amenities
    "near_park", "near_schools", "near_supermarket", "near_restaurants", "is_quiet_street",
}

# Validate field names before building SQL
for field in field_map.keys():
    if field not in ALLOWED_UPDATE_FIELDS:
        raise ValueError(f"Invalid field name for update: {field}")
```

### Current Callers (all safe)

| File | Fields Passed |
|------|---------------|
| `app/pages/2_Listings.py:258` | status, decision, decision_reason, estimated_renovation_eur, user_notes |
| `tests/test_db_concurrency.py:148` | user_notes, estimated_renovation_eur |
| `tests/test_db_concurrency.py:191` | status, decision |

All callers use hardcoded fields that are in the allowlist. No breakage expected.

---

## Testing

### Before Change - Verified 2025-12-28
```bash
PYTHONPATH=/home/wow/Projects/sale-sofia pytest tests/test_db_concurrency.py -v
```

**Result: 17 passed in 4.14s**

```
tests/test_db_concurrency.py::TestParallelWrites::test_10_parallel_save_listing PASSED
tests/test_db_concurrency.py::TestParallelWrites::test_50_parallel_save_listing_stress PASSED
tests/test_db_concurrency.py::TestParallelWrites::test_parallel_updates PASSED
tests/test_db_concurrency.py::TestParallelWrites::test_parallel_insert_and_update PASSED
tests/test_db_concurrency.py::TestMixedReadsWrites::test_reads_during_writes PASSED
tests/test_db_concurrency.py::TestMixedReadsWrites::test_concurrent_count_queries PASSED
tests/test_db_concurrency.py::TestRetryDecorator::test_retries_on_database_locked PASSED
tests/test_db_concurrency.py::TestRetryDecorator::test_no_retry_on_other_errors PASSED
tests/test_db_concurrency.py::TestRetryDecorator::test_exhausts_retries_and_raises PASSED
tests/test_db_concurrency.py::TestRetryDecorator::test_succeeds_on_first_try PASSED
tests/test_db_concurrency.py::TestRetryDecorator::test_retry_logging PASSED
tests/test_db_concurrency.py::TestRetryDecorator::test_retry_with_different_max_attempts PASSED
tests/test_db_concurrency.py::TestWALMode::test_wal_mode_enabled PASSED
tests/test_db_concurrency.py::TestWALMode::test_busy_timeout_set PASSED
tests/test_db_concurrency.py::TestConflictHandling::test_duplicate_url_updates_existing PASSED
tests/test_db_concurrency.py::TestConflictHandling::test_parallel_duplicate_url_inserts PASSED
tests/test_db_concurrency.py::TestConcurrencyIntegration::test_realistic_scraping_scenario PASSED
```

### After Change - Run Same Command
```bash
PYTHONPATH=/home/wow/Projects/sale-sofia pytest tests/test_db_concurrency.py -v
```

Expected: 17 passed (no regression)

### Full Suite Verification
```bash
PYTHONPATH=/home/wow/Projects/sale-sofia pytest tests/ -v --tb=short
```

Expected: 563+ tests passing

---

## Post-Production Cleanup (Not Blocking)

These can be done after production launch:

1. **Consolidate duplicates**: `_calculate_delay()`, `detect_encoding()`, `_extract_domain()`
2. **Add missing tests**: property_fingerprinter, property_merger, mubeng_manager
3. **Remove dead code**: `archive/browsers/`, `update_listing_features()`, timeout parameter in `wait_for_proxies()`
4. **Centralize config**: DEFAULT_HEADERS, Redis config

---

## Cancelled Changes (Why)

### DB Error Handling - CANCELLED
Adding try/except to `get_db_connection()` would be WORSE:
- If it returns None, 40+ callers crash with `AttributeError: 'NoneType' has no attribute 'execute'`
- Silent failure in init_db() means tables don't exist → "no such table" errors later
- Current "fail fast at import" is the CORRECT design for production

### PROXY_WAIT_TIMEOUT - CANCELLED
The timeout parameter is dead code:
```python
def wait_for_proxies(..., timeout: int = 2400):
    return self.wait_for_refresh_completion(...)  # timeout NOT passed!
```
- main.py already passes 600s explicitly
- Changing default has zero effect

### Port Validation - DEFERRED
All port sources are already typed integers:
- YAML parses numeric as int
- os.getenv() uses explicit int() cast
- Hard-coded literals are obviously integers
- No user input paths to port values
