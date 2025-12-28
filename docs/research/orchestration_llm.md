# Orchestration Research: LLM Module

## Executive Summary

The LLM module provides **per-listing extraction using Ollama** to fill gaps in CSS-based scraping. It's optional, per-scraper configurable. **Key gap**: No rate limiting. For parallel scraping, consider async LLM enrichment as a separate phase.

---

## 1. Module Purpose

### What It Does
Extracts structured data from free-text descriptions using local Ollama:
- Room/bedroom/bathroom counts
- Furnishing state, condition
- Boolean features (elevator, parking, balcony)
- Enums (orientation, heating_type, view_type)

### Design: Dictionary-First, LLM-Fallback
1. Pre-scan with Bulgarian keywords (100% reliable)
2. Extract numbers via regex (100% reliable)
3. Extract booleans/enums via keywords
4. Use LLM only for fields dictionary missed

### Two Main Functions
| Function | Input | Output | Status |
|----------|-------|--------|--------|
| `extract_description(text)` | Description | ExtractedDescription (17+ fields) | Active |
| `map_fields(content)` | Page content | MappedFields (10 fields) | Legacy, unused |

---

## 2. How LLM Extraction Is Triggered

### Per-Listing, Optional, Gap-Filling
```python
# In scraper's extract_listing()
if self.use_llm and LLM_AVAILABLE and description:
    try:
        llm_result = llm_extract(description)
        if llm_result.confidence >= 0.7:
            # Only fill None fields
            if rooms_count is None and llm_result.rooms:
                rooms_count = llm_result.rooms
    except Exception as e:
        logger.warning(...)  # Continue with partial data
```

### Triggering Conditions
| Condition | Check |
|-----------|-------|
| Feature enabled | `self.use_llm` flag |
| Module available | `LLM_AVAILABLE` import check |
| Description exists | `description is not None` |
| Confidence passes | `result.confidence >= 0.7` |

### Current Integration
- imot_scraper.py - Uses LLM
- bazar_scraper.py - No LLM calls

---

## 3. API & Models Used

### Ollama Local Server
| Setting | Value |
|---------|-------|
| Host | localhost:11434 |
| API | POST /api/generate |
| Protocol | Local HTTP only |

### Models
| Model | VRAM | Purpose |
|-------|------|---------|
| qwen2.5:1.5b | 1.2GB | Primary (better quality) |
| qwen2.5:0.5b | 500MB | Fallback (faster) |

### Configuration
```yaml
# config/ollama.yaml
ollama:
  host: localhost
  port: 11434
  keep_alive: 1h
  tasks:
    description_extraction:
      primary_model: qwen2.5:1.5b
      fallback_model: qwen2.5:0.5b
      temperature: 0.0
      max_tokens: 500
      timeout: 30
  cache:
    enabled: true
    ttl_days: 7
```

---

## 4. Rate Limiting & Concurrency

### No Explicit Rate Limits
| Aspect | Current | Issue |
|--------|---------|-------|
| Per-instance limit | None | Ollama can be flooded |
| Global concurrency | None | Multiple scrapers clash |
| Request queuing | None | Blocking during scrape |
| Backoff/retry | Basic try/except | No exponential backoff |

### Ollama Server Management
- Self-healing: auto-restart if health check fails
- Health check: HTTP GET to localhost:11434
- Startup: 10+ seconds if restart needed

### Caching
- Redis-based, optional
- Key: MD5 hash of description
- TTL: 7 days
- Hit rate: 5-30% (most listings unique)

---

## 5. Integration with Scraping Flow

### Sequential, In-Process
```
extract_listing(html, url)
├─ CSS extraction
├─ Extract description text
└─ [IF use_llm enabled]
   └─ llm_extract(description)  ← BLOCKING
      ├─ Dictionary scan
      ├─ Ollama API call (if needed)
      ├─ Confidence check
      └─ Gap-fill results
└─ Merge into ListingData
```

### Gap-Filling Strategy
Never overrides CSS extraction - only fills `None` fields.

### Error Handling
Simple exception catch, no retry:
```python
try:
    llm_result = llm_extract(description)
except Exception:
    pass  # Continue with partial data
```

---

## 6. What Orchestrator Needs to Know

### Startup Requirements
1. **Ollama must be running**
   - Call `ensure_ollama_ready()` before scraping
   - Blocks 10+ seconds if restart needed

2. **Redis optional but recommended**
   - Caching disabled if unavailable

3. **Model pre-warming** (not yet done)
   - First call incurs 2-3 second overhead
   - `keep_alive: 1h` prevents unload

### Metrics Available
```python
from llm import get_metrics
{
    "extractions_total": count,
    "extractions_success": count,
    "extractions_failed": count,
    "cache_hits": count,
    "avg_time_ms": float,
    "avg_confidence": float,
    "cache_hit_rate": percentage
}
```

### Alert Conditions
- `avg_time_ms > 500` - Ollama under load
- `cache_hit_rate < 20%` - consider description dedup
- `extractions_failed / total > 0.1` - health issue

---

## 7. Concurrency Considerations for Parallel Scraping

### Issue 1: Sequential Extraction Blocks Scraping
If 10 scrapers run parallel with `use_llm=True`:
- Each blocks on LLM calls to same Ollama instance
- Effective rate: 2-5 per second (model speed limit)
- Risk: Timeouts, cascading failures

### Issue 2: Single Ollama Instance
If Ollama crashes:
- All scraping blocks
- Auto-restart waits 10+ seconds
- Multiple scrapers hitting `ensure_ready()` = race condition

### Issue 3: Memory Contention
| Scenario | RAM | Risk |
|----------|-----|------|
| Ollama + 1 scraper | 1.5GB | OK |
| Ollama + 4 browser scrapers | 1.5GB + 2GB | Tight |
| Ollama + 10 scrapers | 1.5GB + 5GB+ | OOM |

### Issue 4: Low Cache Hit Rate
- MD5 of description = cache hit only on exact match
- Most listings unique → 5-30% hit rate
- Solution: Deduplicate descriptions before LLM

---

## 8. Recommended Pattern for Phase 4.3

### Async LLM Enrichment
```python
if mode == "PARALLEL_WITH_LLM":
    # Phase 1: Fast scraping (no LLM)
    listings = scrape_all_sites(use_llm=False)  # Parallel

    # Phase 2: Find unique descriptions
    unique_descriptions = deduplicate([l.description for l in listings])

    # Phase 3: Async LLM enrichment via Celery
    enrichments = chord([
        extract_llm_task.s(desc) for desc in unique_descriptions
    ])(aggregate_enrichments.s())

    # Phase 4: Apply results to listings
    for listing in listings:
        if listing.description in enrichments:
            listing.merge_enrichment(enrichments[listing.description])

    # Phase 5: Store
    store_all(listings)
```

### Benefits
- Parallel scraping unblocked
- Batched, deduplicated LLM calls
- Cache-friendly (10 unique → 10 calls vs 1000)
- Tolerates Ollama downtime

---

## 9. Dependency Map

```
Orchestrator
├─ Redis (optional, for caching)
├─ Ollama (critical)
│  ├─ Health: GET http://localhost:11434/
│  ├─ Start: subprocess.Popen(["ollama", "serve"])
│  └─ Models: auto-downloaded on first use
└─ Scraper config
   └─ use_llm flag (per-scraper)
```

### Startup Sequence
1. Start/check Redis (optional)
2. Start/check Ollama
3. Pre-warm model (optional, 2-3s one-time)
4. Enable scrapers with `use_llm` settings

---

## 10. Gaps for Phase 4.3

| Gap | Impact | Solution |
|-----|--------|----------|
| No LLM rate limiting | Timeout risks | Central rate limiter |
| Sequential extraction | Blocks parallel | Async extraction phase |
| Single Ollama instance | Single point of failure | Health monitoring + fallback |
| Memory contention | OOM on small machines | Resource limits |
| Low cache hit rate | Wasted calls | Pre-dedup descriptions |
| No warmup | First call slow | Pre-warm on startup |

---

## Performance Targets

| Metric | Observed | Target |
|--------|----------|--------|
| Extraction time | 100-300ms | <500ms |
| Success rate | ~95% | >90% |
| Avg confidence | 0.82 | >0.7 |
| Cache hit rate | 5-30% | >50% (with dedup) |
