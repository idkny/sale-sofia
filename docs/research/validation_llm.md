# LLM Module Validation Report

**Date**: 2025-12-28
**Scope**: Pre-Celery integration validation
**Verdict**: Correctly designed for single-threaded, needs modifications for parallel

---

## Executive Summary

The LLM module is **correctly decoupled** from scraping (optional, gap-fill only, graceful fallback). Error handling won't crash workers. However, **rate limiting is missing** and singleton patterns have race conditions for multi-threaded Celery.

---

## Correctly Implemented

| Component | Status | Notes |
|-----------|--------|-------|
| Optional by flag | CORRECT | `use_llm` flag in ScraplingMixin |
| Gap-fill only | CORRECT | Never overrides CSS-extracted values |
| Graceful fallback | CORRECT | Exception caught, continues with partial data |
| Redis caching | CORRECT | TTL-controlled, graceful degradation |
| Dictionary-first | CORRECT | Reduces LLM calls with keyword extraction |
| Pydantic schemas | CORRECT | Type-safe extraction results |

---

## Broken or Will Fail

| Issue | Severity | Impact |
|-------|----------|--------|
| Config file loading | HIGH | Worker crashes if `ollama.yaml` missing |
| No rate limiting | HIGH | 10 workers flood Ollama (handles 2-5 req/s) |
| Non-atomic metrics | MEDIUM | `_metrics["total"] += 1` race condition |
| Singleton race conditions | MEDIUM | Multiple instances on first access |
| ensure_ready() stampede | MEDIUM | 10 workers block 10+ seconds if Ollama down |

---

## Recommended Approach for Phase 4.3

### Option A: In-Process LLM (Quick Fix)

1. Add semaphore rate limiter to `_call_ollama()` (2-3 req/s max)
2. Use `threading.Lock` for singleton initialization
3. Pre-warm Ollama in Celery `worker_init` signal

### Option B: Async LLM Task (Better Architecture)

```python
# Separate scraping from LLM enrichment
@celery.task
def scrape_listing(url):
    return scraper.extract(html, use_llm=False)  # Fast

@celery.task
def enrich_with_llm(listing_id, description):
    result = llm_extract(description)  # Separate queue
    store_enrichment(listing_id, result)
```

Benefits:
- Scraping not blocked by LLM
- LLM queue can have single worker (natural rate limit)
- Easier to debug and monitor separately
