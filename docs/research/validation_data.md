# DATA Module Validation Report

**Date**: 2025-12-28
**Scope**: Pre-Celery integration validation
**Verdict**: Partially ready - fix critical issues before 10+ workers

---

## Executive Summary

Core mechanisms (WAL mode, retry logic, parameterized queries) are correctly implemented. However, critical issues exist that will cause failures under 10+ concurrent workers.

---

## Correctly Implemented

| Component | Status | Notes |
|-----------|--------|-------|
| WAL mode | CORRECT | `PRAGMA journal_mode = WAL` enables concurrent reads |
| Busy timeout | CORRECT | 30s wait before error |
| Retry decorator | CORRECT | Exponential backoff + jitter |
| Parameterized queries | CORRECT | No SQL injection risk |
| Field allowlist | CORRECT | `update_listing_evaluation()` validates field names |
| Upsert pattern | CORRECT | `ON CONFLICT(url) DO UPDATE` |
| Foreign keys | CORRECT | `PRAGMA foreign_keys = ON` |

---

## Broken or Will Fail Under Load

| Issue | Severity | Evidence |
|-------|----------|----------|
| Startup race condition | CRITICAL | Lines 1316-1320: 10 workers run `init_db()` simultaneously |
| add_viewing() not atomic | HIGH | Lines 557, 568: two separate commits |
| Read functions unprotected | HIGH | All `get_*` functions lack `@retry_on_busy()` |
| 3 retries insufficient | MEDIUM | `SQLITE_BUSY_RETRIES = 3` not enough for 10+ workers |

---

## Critical Fixes Required

1. **Move init to startup script** (not module import)
2. **Add @retry_on_busy() to read functions** (especially `get_listing_by_url`)
3. **Increase SQLITE_BUSY_RETRIES to 5**
4. **Make add_viewing() atomic** (single commit)

---

## Database Throughput Reality

- SQLite WAL: **only ONE writer at a time**
- 10 workers saving simultaneously: writes queue up, 0.5-2s clear time
- Under continuous load: queue never clears, timeouts cascade

**Bottom line**: Fix critical issues before deploying with 10+ Celery workers.
