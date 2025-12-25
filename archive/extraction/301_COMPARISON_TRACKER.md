---
id: 20251202_comparison_tracker
type: tracker
subject: extraction
description: "Phase 1.1 COMPLETE - Pattern comparison across 9 repositories"
created_at: 2025-12-01
updated_at: 2025-12-02
tags: [comparison, tracker, extraction, repositories, phase1.1-complete]
---

# Repository Comparison Tracker

**Phase 1.1 Status**: COMPLETE (Session 9)
**Total**: 9/9 repos | 65 files | 18 subjects

---

## Quick Reference - Best Sources Per Module

| AutoBiz Module | Primary Source | Secondary | Key Patterns |
|----------------|----------------|-----------|--------------|
| **Data Layer** | Competitor-Intel, Auto-Biz | Market_AI | Content hash, UPSERT, keyword workflow |
| **Scraper** | Competitor-Intel | Auto-Biz | RateLimiter, anti-bot, page history |
| **Browser** | Auto-Biz | Scraper | Strategy pattern, Camoufox, profiles |
| **Proxies** | Competitor-Intel | - | Scoring, auto-prune, PacketStream |
| **URL Classifier** | Bg-Estate, Auto-Biz | - | Rule+ML hybrid, status workflow |
| **AI/LLM** | Ollama-Rag, MarketIntel | Bg-Estate | Hybrid RAG, JSON mode, model factory |
| **Workflow** | Market_AI | Auto-Biz | LangGraph, Celery, argparse CLI |
| **NLP** | Competitor-Intel | - | KeyBERT, YAKE, RAKE, Gensim |

---

## Repositories Analyzed

| # | Repository | Status | Date | Type | Files Extracted |
|---|------------|--------|------|------|-----------------|
| 1 | `idkny/MarketIntel` | DONE | 2025-12-01 | Production Code | 5 |
| 2 | `idkny/SerpApi` | DONE | 2025-12-01 | Planning/Spec | 6 |
| 3 | `idkny/Ollama-Rag` | DONE | 2025-12-01 | Production Code | 6 |
| 4 | `idkny/Scraper` | DONE | 2025-12-01 | Production Code | 5 |
| 5 | `idkny/Auto-Biz` | DONE | 2025-12-01 | Production Code | 8 |
| 6 | `idkny/Market_AI` | DONE | 2025-12-01 | Production Code | 7 |
| 7 | `idkny/Competitor-Intel` | DONE | 2025-12-01 | Production Code | 9 |
| 8 | `idkny/SEO` | DONE | 2025-12-01 | Production Code | 4 |
| 9 | `idkny/Bg-Estate` | **DONE** | 2025-12-01 | Production Code | **1** |

---

## Subject Comparison Matrix

### DATABASE / SCHEMAS

| Pattern | MarketIntel | SerpApi | Ollama-Rag | Scraper | Auto-Biz | Best Version |
|---------|-------------|---------|------------|---------|----------|--------------|
| Tables count | 5 | 10 (spec) | 4 (inferred) | 1 (listings) | 7 (inferred) | **Auto-Biz** (most complete) |
| Query executor | `_execute_query()` | `_execute_query()` | None | Basic insert | get_db_connection() | MarketIntel |
| Get or insert | Yes | Yes (spec) | No | No | **Yes** | MarketIntel/Auto-Biz |
| Cache table | Yes | No | No | No | No | MarketIntel |
| Session linking | Yes | Yes (spec) | No | No | No | MarketIntel |
| Keyword workflow | Partial | Full | No | No | **Yes (status)** | **Auto-Biz** |
| UPSERT pattern | No | No | No | No | **Yes (ON CONFLICT)** | **Auto-Biz** |
| History tracking | No | No | No | No | **Yes** | **Auto-Biz** |
| Classification | No | No | No | No | **Yes (multi-status)** | **Auto-Biz** |
| row_factory | Yes | N/A | Yes | No | **Yes** | Same |
| Junction tables | Yes | Yes | Yes (topics) | No | Yes | Same pattern |

### API CLIENT

| Pattern | MarketIntel | SerpApi | Ollama-Rag | Scraper | Best Version |
|---------|-------------|---------|------------|---------|--------------|
| Endpoints covered | ~5 | 12+ (spec) | 1 (Ollama health) | DDG only | SerpApi (more complete) |
| HTTP retry | Exp backoff + jitter | None (spec) | None | **Async decorator** | **MERGE** |
| Response cache | SQLite + TTL | None (spec) | None | None | MarketIntel |
| In-flight dedup | Yes | No | No | No | MarketIntel |
| Cache key gen | SHA256 | No | No | No | MarketIntel |
| Engine registry | No | Yes (spec) | No | No | SerpApi |
| Async support | No | No | No | **Yes (retry_async)** | **Scraper** |
| Health checks | No | No | Yes (Ollama) | **Yes (proxy judges)** | Both |
| DuckDuckGo | No | No | No | **Yes** | **Scraper** |

### DATA EXTRACTORS

| Pattern | MarketIntel | SerpApi | Ollama-Rag | Scraper | Best Version |
|---------|-------------|---------|------------|---------|--------------|
| Response parsing | Yes | Comprehensive (spec) | No | Basic (item standardize) | SerpApi (more types) |
| Text cleaning | Basic | `_clean_text()` | No | No | Same |
| URL cleaning | No | No | Yes (GitHub) | Yes (safety) | Both |
| Pydantic models | No | No | No | No | Need to add |
| Error handling | Basic | Basic | Comprehensive | **Async retry** | **Scraper** |

### AI / LLM

| Pattern | MarketIntel | SerpApi | Ollama-Rag | Scraper | Best Version |
|---------|-------------|---------|------------|---------|--------------|
| Ollama client | OllamaClient (raw) | Placeholder (spec) | ChatOllama (LangChain) | ChatOllama (util copy) | MarketIntel (JSON mode) |
| LangChain | No | No | Yes (summarize, cluster) | Yes (copied from Ollama-Rag) | **Ollama-Rag** |
| RAG | No | No | Yes (hybrid BM25+Vector) | Yes (LlamaIndex copy) | **Ollama-Rag** |
| Embeddings | No | No | HuggingFace BGE | HuggingFace BGE (copy) | **Ollama-Rag** |
| JSON mode | Yes | Mentioned | No | No | MarketIntel |
| AI classification | Confidence-based | Placeholder | No | No | MarketIntel |
| Summarization | No | No | Yes (LangChain chain) | Yes (copied) | **Ollama-Rag** |
| Document clustering | No | No | Yes (KMeans) | Yes (copied) | **Ollama-Rag** |

### CONFIG

| Pattern | MarketIntel | SerpApi | Ollama-Rag | Scraper | Best Version |
|---------|-------------|---------|------------|---------|--------------|
| Pydantic Settings | Yes | No (os.getenv) | No (YAML only) | No (dict) | MarketIntel |
| YAML config | Yes | No | Yes | **JSON+YAML** | Scraper (flexible) |
| .env secrets | Yes | Yes | No | Yes (dotenv) | MarketIntel |
| Engine registry | No | Yes (spec) | No | No | SerpApi |
| Status enums | No | Yes (spec) | No | No | SerpApi |
| .gitignore | Good | Comprehensive | Basic | Good | SerpApi |
| Type validation | Yes (Pydantic) | No | No | No | MarketIntel |
| Device auto-detect | No | No | Yes (CUDA/CPU) | Yes (copied) | **Ollama-Rag** |
| **Path management** | Basic | Basic | Basic | **Centralized (paths.py)** | **Scraper** |
| **Site config schema** | No | No | No | **Yes (JSON selectors)** | **Scraper** |

### WORKFLOW / PIPELINE

| Pattern | MarketIntel | SerpApi | Ollama-Rag | Scraper | Best Version |
|---------|-------------|---------|------------|---------|--------------|
| Orchestration | Yes | Comprehensive (spec) | RAG pipeline | **Strategy fallback** | SerpApi (batch) |
| Nested loops | loc*kw*engine | loc*kw*engine | Single query | **strategy loop** | Same pattern |
| Error resilience | Continue on error | Continue on error | Try/catch | **Cooldown manager** | **Scraper** |
| Discovery pipeline | Yes | Multi-source (spec) | No | No | SerpApi |
| CLI review | No | Yes (spec) | Yes (REPL) | **Yes (argparse)** | SerpApi |
| Entry point CLI | No | Yes (spec) | Yes (simple) | **Yes (multi-module)** | Scraper |
| Async | No | No | No | **Yes** | **Scraper** |
| Self-healing | No | No | Yes (auto-restart) | No | **Ollama-Rag** |
| Benchmarking | No | No | Yes (keyword-based) | No | **Ollama-Rag** |
| **Strategy pattern** | No | No | No | **Yes** | **Scraper** |
| **Per-strategy cooldown** | No | No | No | **Yes** | **Scraper** |

### AUTOMATION / SERVER MANAGEMENT

| Pattern | MarketIntel | SerpApi | Ollama-Rag | Scraper | Best Version |
|---------|-------------|---------|------------|---------|--------------|
| Health checks | No | No | Yes (Ollama) | **Yes (proxy judges)** | Both |
| Auto-restart | No | No | Yes | No | **Ollama-Rag** |
| Port binding check | No | No | Yes | No | **Ollama-Rag** |
| GPU cleanup | No | No | Yes | Yes (copied) | **Ollama-Rag** |
| Dynamic batching | No | No | Yes (memory-aware) | Yes (copied) | **Ollama-Rag** |
| Signal handlers | No | No | Yes (SIGTERM) | No | **Ollama-Rag** |

### SCRAPER / BROWSER (NEW - Scraper Only)

| Pattern | MarketIntel | SerpApi | Ollama-Rag | Scraper | Best Version |
|---------|-------------|---------|------------|---------|--------------|
| Playwright | No | No | No | **Yes** | **Scraper** |
| Camoufox (Firefox) | No | No | No | **Yes** | **Scraper** |
| Fingerprint Chromium | No | No | No | **Yes** | **Scraper** |
| StealthyFetcher | No | No | No | **Yes** | **Scraper** |
| Fingerprint debug | No | No | No | **Yes (WebGL, UA)** | **Scraper** |
| Mode selection | No | No | No | **Yes (http/stealth/browser)** | **Scraper** |
| Anti-detection flags | No | No | No | **Yes** | **Scraper** |
| Custom browser binaries | No | No | No | **Yes** | **Scraper** |
| WebsiteManager | No | No | No | **Yes** | **Scraper** |
| Site config (selectors) | No | No | No | **Yes** | **Scraper** |
| Dynamic module loading | No | No | No | **Yes (importlib)** | **Scraper** |

### PROXIES (NEW - Scraper Only)

| Pattern | MarketIntel | SerpApi | Ollama-Rag | Scraper | Best Version |
|---------|-------------|---------|------------|---------|--------------|
| Proxy validation | No | No | No | **Yes (pycurl)** | **Scraper** |
| Multi-protocol | No | No | No | **Yes (http/https/socks4/socks5)** | **Scraper** |
| Anonymity detection | No | No | No | **Yes (Transparent/Anonymous/Elite)** | **Scraper** |
| Country lookup | No | No | No | **Yes (ip2c.org)** | **Scraper** |
| Free proxy pool | No | No | No | **Yes (ProxyService)** | **Scraper** |
| Paid proxy (PacketStream) | No | No | No | **Yes (PaidProxyService)** | **Scraper** |
| Auto-replenishment | No | No | No | **Yes (threshold trigger)** | **Scraper** |
| Rust scraper binary | No | No | No | **Yes (subprocess)** | **Scraper** |
| Proxy orchestrator | No | No | No | **Yes (strategy rotation)** | **Scraper** |
| JSON persistence | No | No | No | **Yes (valid_proxies.txt)** | **Scraper** |

### ERROR HANDLING (NEW)

| Pattern | MarketIntel | SerpApi | Ollama-Rag | Scraper | Best Version |
|---------|-------------|---------|------------|---------|--------------|
| Retry decorator | Sync with params | Basic | None | **Async with backoff** | **MERGE** |
| Exponential backoff | Yes | No | No | **Yes** | Both |
| Jitter | Yes | No | No | **Yes** | Both |
| Max delay cap | Yes | No | No | **Yes** | Both |
| Cooldown manager | No | No | No | **Yes (per-strategy)** | **Scraper** |
| URL safety check | No | No | No | **Yes (Google+VirusTotal)** | **Scraper** |
| Suspicious TLD check | No | No | No | **Yes (heuristic)** | **Scraper** |

### SEARCH ENGINE

| Pattern | MarketIntel | SerpApi | Ollama-Rag | Scraper | Best Version |
|---------|-------------|---------|------------|---------|--------------|
| SerpAPI client | Yes | Yes (spec) | No | No (placeholder) | MarketIntel |
| DuckDuckGo | No | No | No | **Yes (complete)** | **Scraper** |
| Multi-keyword | Yes | Yes (spec) | No | **Yes** | Same |
| Multi-region | No | No | No | **Yes** | **Scraper** |
| Multi-type (text/news/etc) | No | No | No | **Yes** | **Scraper** |
| Export formats | No | No | No | **Yes (JSONL/CSV/TXT/MD)** | **Scraper** |
| Free alternative | No | No | No | **Yes** | **Scraper** |

---

## Files by Subject

### database/
- `database_MarketIntel.md` - Schema + CRUD patterns (implemented)
- `database_MarketIntel_schema.sql` - Raw SQL (5 tables)
- `database_SerpApi_schemas.md` - Schema spec (10 tables)
- `database_SerpApi_crud.md` - CRUD patterns (spec)
- `database_OllamaRag_schemas.md` - Inferred schema (4 tables)

### api_client/
- `api_client_MarketIntel.md` - Cache, retry, dedup (implemented)
- `api_client_SerpApi.md` - 12+ endpoints (spec)

### data_extractors/
- `data_extractors_SerpApi.md` - JSON parsing patterns (spec)

### ai_llm/
- `ai_llm_MarketIntel.md` - Ollama client, classification (implemented)
- `ai_llm_OllamaRag.md` - RAG, embeddings, LangChain (implemented)

### config/
- `config_MarketIntel.md` - Pydantic + YAML (implemented)
- `config_SerpApi.md` - Env vars + .gitignore (spec)
- `config_OllamaRag.md` - Pure YAML (implemented)

### workflow/
- `workflow_MarketIntel.md` - Registry, pipelines (implemented)
- `workflow_SerpApi.md` - Orchestration + discovery (spec)
- `workflow_OllamaRag.md` - RAG pipeline + benchmark (implemented)

### automation/
- `automation_OllamaRag.md` - Server management, health checks

### utils/
- `utils_OllamaRag.md` - URL handling, file operations

### proxies/ (NEW)
- **`proxies_Scraper.md`** - ProxyChecker, ProxyService, PaidProxyService, ProxyOrchestrator

### browser/ (NEW)
- **`browser_Scraper.md`** - Playwright, Camoufox, StealthyFetcher, fingerprint debug

### scraper/ (NEW)
- **`scraper_Scraper.md`** - WebsiteManager, site configs, strategy pattern

### error_handling/ (NEW)
- **`error_handling_Scraper.md`** - retry_async, CooldownManager, URL safety

### search_engine/ (NEW)
- **`search_engine_Scraper.md`** - DuckDuckGoMultiSearch

---

## Cross-Repo Insights

### Overlapping Patterns (Same concept, different implementations)

| Pattern | Repos | Notes |
|---------|-------|-------|
| `_execute_query()` | MarketIntel, SerpApi | Same pattern, MarketIntel has caching |
| Get-or-insert | MarketIntel, SerpApi | Identical pattern |
| Continue-on-error | MarketIntel, SerpApi, Ollama-Rag, Scraper | Same approach |
| Session linking | MarketIntel, SerpApi | Same concept, different table names |
| YAML config | MarketIntel, Ollama-Rag, Scraper | MarketIntel adds Pydantic |
| Junction tables | All three | Same many-to-many pattern |
| **Retry with backoff** | MarketIntel, Scraper | MarketIntel sync, **Scraper async** |
| **Health checks** | Ollama-Rag, Scraper | Different targets (Ollama vs proxy judges) |

### Unique Patterns (Only in one repo)

| Pattern | Repo | Value |
|---------|------|-------|
| SQLite response cache | MarketIntel | HIGH - reuse |
| SHA256 cache keys | MarketIntel | HIGH - reuse |
| Exp backoff + jitter | MarketIntel | HIGH - reuse |
| In-flight deduplication | MarketIntel | HIGH - reuse |
| JSON mode Ollama | MarketIntel | HIGH - reuse |
| 12+ SerpAPI endpoints | SerpApi | HIGH - reference |
| Keyword status workflow | SerpApi | MEDIUM - consider |
| CLI review workflow | SerpApi | MEDIUM - consider |
| **Hybrid RAG (BM25+Vector)** | Ollama-Rag | **HIGH - DIRECT PORT** |
| **HuggingFace BGE embeddings** | Ollama-Rag | **HIGH - DIRECT PORT** |
| **LangChain summarization** | Ollama-Rag | **HIGH - DIRECT PORT** |
| **Document clustering** | Ollama-Rag | **MEDIUM - consider** |
| **Ollama auto-restart** | Ollama-Rag | **HIGH - DIRECT PORT** |
| **GPU memory cleanup** | Ollama-Rag | **HIGH - DIRECT PORT** |
| **Dynamic batch sizing** | Ollama-Rag | **HIGH - DIRECT PORT** |
| **Port binding check** | Ollama-Rag | **HIGH - DIRECT PORT** |
| Polymorphic FK (Entities) | SerpApi | LOW - complex |
| **ProxyChecker (pycurl)** | Scraper | **HIGH - DIRECT PORT** |
| **ProxyService (free)** | Scraper | **HIGH - DIRECT PORT** |
| **PaidProxyService (PacketStream)** | Scraper | **HIGH - DIRECT PORT** |
| **ProxyOrchestrator** | Scraper | **HIGH - DIRECT PORT** |
| **Playwright + Camoufox** | Scraper | **HIGH - DIRECT PORT** |
| **StealthyFetcher** | Scraper | **HIGH - DIRECT PORT** |
| **Fingerprint debug (WebGL)** | Scraper | **MEDIUM - consider** |
| **WebsiteManager** | Scraper | **HIGH - DIRECT PORT** |
| **Site config schema** | Scraper | **HIGH - DIRECT PORT** |
| **CooldownManager** | Scraper | **HIGH - DIRECT PORT** |
| **retry_async decorator** | Scraper | **HIGH - DIRECT PORT** |
| **URL safety (Google+VT)** | Scraper | **MEDIUM - consider** |
| **DuckDuckGoMultiSearch** | Scraper | **HIGH - DIRECT PORT** |

### Best-of-Breed Recommendations (UPDATED)

| Subject | Take From | Reason |
|---------|-----------|--------|
| Database schema | MarketIntel | Simpler, production-tested |
| Database CRUD | Both | Merge get-or-insert + keyword workflow |
| API client infra | MarketIntel | Cache, retry, dedup are essential |
| API endpoints | SerpApi | More comprehensive mapping |
| Data extractors | SerpApi | More response types covered |
| Ollama client | **MERGE** | MarketIntel (JSON mode) + Ollama-Rag (health/restart) |
| RAG pipeline | **Ollama-Rag** | Only repo with RAG implementation |
| Embeddings | **Ollama-Rag** | HuggingFace BGE, local, no API |
| Summarization | **Ollama-Rag** | LangChain chain + clustering |
| Config | MarketIntel | Pydantic is better than raw YAML |
| Orchestration | SerpApi | More complete with discovery |
| CLI tools | SerpApi + **Scraper** | Entry points + argparse patterns |
| Server automation | **Ollama-Rag** | Only repo with health/restart patterns |
| GPU management | **Ollama-Rag** | Only repo with GPU patterns |
| **Proxy management** | **Scraper** | **ONLY repo with proxies** |
| **Browser automation** | **Scraper** | **ONLY repo with Playwright/Camoufox** |
| **Scraper framework** | **Scraper** | **ONLY repo with site scraping** |
| **Retry (async)** | **Scraper** | Better for scraping workloads |
| **Cooldown/rate limit** | **Scraper** | **ONLY repo with per-strategy cooldown** |
| **Free search** | **Scraper** | DuckDuckGo for testing/low-budget |
| **URL safety** | **Scraper** | **ONLY repo with malware checks** |

---

## Decision Log

Record decisions about which patterns to use:

| Date | Subject | Decision | Rationale |
|------|---------|----------|-----------|
| 2025-12-01 | SerpApi type | Planning doc | No actual code, but valuable specs |
| 2025-12-01 | Ollama-Rag type | Production code | Working RAG implementation |
| 2025-12-01 | RAG source | Ollama-Rag | Only repo with RAG, hybrid retrieval is best practice |
| 2025-12-01 | Embeddings | Ollama-Rag | Local HuggingFace, no API dependency |
| 2025-12-01 | Server management | Ollama-Rag | Only repo with health checks, auto-restart |
| 2025-12-01 | New subject: automation | Created | Server management patterns from Ollama-Rag |
| 2025-12-01 | New subject: utils | Created | File/URL handling utilities |
| **2025-12-01** | **Scraper type** | **Production code** | **Working scraper framework, some stubs** |
| **2025-12-01** | **Proxy source** | **Scraper** | **ONLY repo with proxy management** |
| **2025-12-01** | **Browser source** | **Scraper** | **ONLY repo with fingerprinting** |
| **2025-12-01** | **New subject: proxies** | **Created** | **Proxy validation, rotation, orchestration** |
| **2025-12-01** | **New subject: browser** | **Created** | **Playwright, Camoufox, stealth mode** |
| **2025-12-01** | **New subject: scraper** | **Created** | **WebsiteManager, site configs** |
| **2025-12-01** | **New subject: error_handling** | **Created** | **Retry, cooldown, URL safety** |
| **2025-12-01** | **New subject: search_engine** | **Created** | **DuckDuckGo client** |
| **2025-12-01** | **Retry decorator** | **MERGE** | **MarketIntel sync + Scraper async** |
| **2025-12-01** | **Auto-Biz type** | **Production code** | **Most comprehensive - CLI, Celery, browser, proxies** |
| **2025-12-01** | **CLI source** | **Auto-Biz** | **ONLY repo with full argparse CLI** |
| **2025-12-01** | **Celery source** | **Auto-Biz** | **ONLY repo with Celery task queue** |
| **2025-12-01** | **Browser strategy** | **Auto-Biz** | **Better than Scraper - dynamic discovery + profiles** |
| **2025-12-01** | **Loguru** | **Auto-Biz** | **ONLY repo with production logging setup** |
| **2025-12-01** | **Setup script** | **Auto-Biz** | **ONLY repo with complete setup automation** |
| **2025-12-01** | **ALL HIGH PRIORITY DONE** | **Phase 1.1 COMPLETE** | **Ready for Phase 1.2 or MEDIUM repos** |

---

## Repo Quality Summary

| Repo | Type | Code Quality | Completeness | Unique Value |
|------|------|--------------|--------------|--------------|
| MarketIntel | Production | 7/10 | HIGH | Caching, retry, OllamaClient |
| SerpApi | Spec/Planning | N/A | LOW (no code) | Endpoint specs, orchestration design |
| Ollama-Rag | Production | 6/10 | MEDIUM | RAG, embeddings, server management |
| Scraper | Production | 7/10 | MEDIUM | Proxies, browser, scraper framework, DDG |
| **Auto-Biz** | **Production** | **8/10** | **HIGH** | **CLI, Celery, browser profiles, Loguru, setup** |

### Scraper Issues Found
- Missing `http_fetcher.py` (imported but not present)
- Missing `Scraper/methods/*` files
- `serpapi.py` and `search-engine.py` are empty placeholders
- Database handler is basic (no get_or_insert)
- Some RAG code duplicated from Ollama-Rag

### Auto-Biz Issues Found
- FormatClassifier is placeholder (HuggingFace model not loaded)
- Code duplication between browsers/utils.py and utils/utils.py
- EmuniumWrapper is placeholder
- No explicit SQL schema (must be inferred from code)

---

## Final Integration Plan

| Subject | Source Repo | Files to Port | Target Location |
|---------|-------------|---------------|-----------------|
| Database schema | MarketIntel | `database_MarketIntel_schema.sql` | `autobiz/tools/data/` |
| Database CRUD | Both | Merge patterns | `autobiz/tools/data/` |
| API client | MarketIntel + SerpApi | Infra + endpoints | `autobiz/tools/api/` |
| Data extractors | SerpApi | Port with Pydantic | `autobiz/tools/api/` |
| AI/LLM | MarketIntel + Ollama-Rag | OllamaClient + RAG | `autobiz/tools/llm/` |
| RAG pipeline | **Ollama-Rag** | Hybrid retrieval | `autobiz/tools/rag/` |
| Embeddings | **Ollama-Rag** | HuggingFace BGE | `autobiz/tools/rag/` |
| Summarization | **Ollama-Rag** | LangChain chain | `autobiz/tools/llm/` |
| Config | MarketIntel | Pydantic Settings | `autobiz/core/` |
| Workflow | SerpApi | Orchestration pattern | `autobiz/pipelines/` |
| Server automation | **Ollama-Rag** | Health, restart, GPU | `autobiz/core/` |
| **Proxy management** | **Scraper** | **ProxyChecker, ProxyService, Orchestrator** | **`autobiz/tools/proxies/`** |
| **Browser automation** | **Scraper** | **Playwright, Camoufox, StealthyFetcher** | **`autobiz/tools/browser/`** |
| **Scraper framework** | **Scraper** | **WebsiteManager, site configs** | **`autobiz/tools/scraper/`** |
| **Error handling** | **MarketIntel + Scraper** | **Retry (sync+async), cooldown** | **`autobiz/core/`** |
| **Search** | **MarketIntel + Scraper** | **SerpAPI + DuckDuckGo** | **`autobiz/tools/search/`** |
| **URL safety** | **Scraper** | **Google Safe Browsing + VirusTotal** | **`autobiz/tools/security/`** |

---

## Total Extraction Progress

| Metric | Count |
|--------|-------|
| Repos analyzed | **9/9** (ALL COMPLETE) |
| Repos excluded | **6** (AutoBiz-skeleton, bbot, Call-Center, OBS, aroma-web, Air_Central) |
| Extraction files | **63** |
| Subjects covered | **18** (database, api_client, data_extractors, ai_llm, config, workflow, automation, utils, proxies, browser, scraper, error_handling, search_engine, testing, nlp, analysis, discovery, parser, cli, apps) |
| HIGH priority repos done | **4/4** (MarketIntel, Ollama-Rag, Scraper, Auto-Biz) |
| MEDIUM repos analyzed | **5/5** (Market_AI, Competitor-Intel, SEO, Bg-Estate, SerpApi) |
| Remaining repos | **0** |
| Next step | **Phase 1.1 COMPLETE - Ready for Phase 1.2 (Design Data Layer)** |

---

## Auto-Biz Unique Patterns

| Pattern | Description | Value |
|---------|-------------|-------|
| **CLI argparse** | Full subparsers with command handlers | **HIGH - DIRECT PORT** |
| **Celery integration** | chord/group/chain for parallel processing | **HIGH - DIRECT PORT** |
| **Multi-stage proxy validation** | mubeng -> ipify -> Google | **HIGH - DIRECT PORT** |
| **Browser strategy pattern** | Dynamic discovery + registry | **HIGH - DIRECT PORT** |
| **Profile manager** | TTL cache, auto-generation | **HIGH - DIRECT PORT** |
| **Fingerprint validation** | SannySoft, CreepJS, Pixelscan tests | **HIGH - DIRECT PORT** |
| **Loguru setup** | Rotation, retention, stdlib redirect | **HIGH - DIRECT PORT** |
| **Setup automation** | Complete setup.sh with binary downloads | **HIGH - DIRECT PORT** |
| **UPSERT pattern** | ON CONFLICT DO UPDATE | **HIGH - DIRECT PORT** |
| **Classification history** | Full audit trail | **HIGH - DIRECT PORT** |
| **paths.py** | Centralized path management | **HIGH - DIRECT PORT** |
| **Model factory** | Task-based LLM provider switching | **MEDIUM - consider** |
| **Xvfb manager** | Virtual display context manager | **HIGH - DIRECT PORT** |
| **TokenUsageTracker** | LLM callback for token accounting | **MEDIUM - consider** |

---

## Market_AI Unique Patterns

| Pattern | Description | Value |
|---------|-------------|-------|
| **LangGraph StateGraph** | Full workflow graph with 8 agents | **HIGH - DIRECT PORT** |
| **Pydantic state schema** | MarketingGraphState with sub-schemas | **HIGH - DIRECT PORT** |
| **Conditional edges** | should_continue router for approval/rejection | **HIGH - DIRECT PORT** |
| **SqliteSaver checkpointing** | State persistence across interruptions | **HIGH - DIRECT PORT** |
| **Agent I/O models** | RouterInV1, QAReportV1, ApprovalDecisionV1 | **HIGH - DIRECT PORT** |
| **HITL gate** | Human-in-the-loop approval node | **HIGH - DIRECT PORT** |
| **System preamble** | Guardrails/compliance injection pattern | **MEDIUM - consider** |
| **Tool contract** | {ok, data, cost, latency_ms, trace_id, retries} | **HIGH - DIRECT PORT** |
| **Model slots** | Task-specific model configuration | **HIGH - DIRECT PORT** |
| **mask_pii** | PII redaction for emails/phones | **HIGH - DIRECT PORT** |
| **pytest patterns** | Unit + integration tests with mocker | **HIGH - DIRECT PORT** |
| **Targeting config** | Cities + keywords structured data | **MEDIUM - consider** |
| **10-table schema** | Complete market research database | **HIGH - DIRECT PORT** |
| **7 data extractors** | SerpAPI response parsers | **HIGH - DIRECT PORT** |
| **12+ API endpoints** | Comprehensive SerpAPI coverage | **HIGH - DIRECT PORT** |

---

## Competitor-Intel Unique Patterns

| Pattern | Description | Value |
|---------|-------------|-------|
| **NLP suite (4 methods)** | KeyBERT, YAKE, RAKE, Gensim for keyword extraction | **HIGH - UNIQUE** |
| **9-table SEO schema** | pages, links, media, structured, texts, phrases, phrase_usage, page_history, domain_metadata | **HIGH - DIRECT PORT** |
| **Content change detection** | SHA256 hash comparison with version archiving | **HIGH - DIRECT PORT** |
| **Anti-bot detection** | domain_metadata with delay adaptation | **HIGH - DIRECT PORT** |
| **RobustProxyTransport** | Scored proxy pool with auto-pruning | **HIGH - DIRECT PORT** |
| **ProxyValidator (async)** | Parallel validation with response time ranking | **HIGH - DIRECT PORT** |
| **PaidProxyService** | PacketStream.io integration with country targeting | **HIGH - DIRECT PORT** |
| **Mubeng integration** | Production proxy rotation | **HIGH - DIRECT PORT** |
| **RateLimiter** | Domain-aware with anti-bot adaptation | **HIGH - DIRECT PORT** |
| **Trafilatura extraction** | Boilerplate removal for body text | **HIGH - UNIQUE** |
| **extruct (5 formats)** | JSON-LD, microdata, RDFa, OpenGraph, microformat | **HIGH - UNIQUE** |
| **Keyword usage mapping** | in_title, in_h1, in_h2, in_anchor, in_alt, in_body | **HIGH - DIRECT PORT** |
| **SEO strength formula** | Weighted scoring (title*1.0, h1*0.9, body*0.5, anchor*0.4, alt*0.2) | **HIGH - DIRECT PORT** |
| **7-step pipeline** | enumerate→fetch→extract-text→extract-structured→phrase-mine→usage-map→export | **HIGH - DIRECT PORT** |
| **Sitemap discovery** | advertools with homepage fallback | **HIGH - DIRECT PORT** |
| **Streamlit dashboard** | Full competitor comparison UI | **MEDIUM - consider** |
| **Log parsing (regex)** | Status codes, URLs, errors from logs | **MEDIUM - consider** |
| **lxml parser** | Case-insensitive XPath for SEO elements | **HIGH - DIRECT PORT** |
