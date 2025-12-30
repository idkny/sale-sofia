# Sofia Apartment Search - Architecture

> **Core architecture overview.** Start here, then navigate to relevant docs based on your task.

---

## Task-Based Navigation

**Read this file first**, then ONLY the docs relevant to your task:

| Your Task | Read These | Skip These |
|-----------|------------|------------|
| **Adding a scraper** | ADDING_COMPONENTS.md, CONVENTIONS.md | DATA_FLOW.md, SSL_PROXY_SETUP.md |
| **Adding proxy source** | ADDING_COMPONENTS.md (proxy section) | CONVENTIONS.md, DESIGN_PATTERNS.md |
| **Debugging data flow** | DATA_FLOW.md | ADDING_COMPONENTS.md, SSL_PROXY_SETUP.md |
| **Writing new Python code** | CONVENTIONS.md | DATA_FLOW.md |
| **Understanding patterns** | DESIGN_PATTERNS.md | FILE_STRUCTURE.md, SSL_PROXY_SETUP.md |
| **Creating new files** | FILE_STRUCTURE.md | DATA_FLOW.md, DESIGN_PATTERNS.md |
| **Working with proxies/SSL** | SSL_PROXY_SETUP.md, DATA_FLOW.md (proxy section) | ADDING_COMPONENTS.md |
| **Error handling/resilience** | DESIGN_PATTERNS.md (patterns 10-16) | ADDING_COMPONENTS.md, SSL_PROXY_SETUP.md |
| **Celery/async tasks** | DATA_FLOW.md, check `scraping/tasks.py` | ADDING_COMPONENTS.md |
| **LLM integration** | Check `llm/` module directly | Most architecture docs |
| **Generic scraper (YAML)** | ADDING_COMPONENTS.md (Option 1) | SSL_PROXY_SETUP.md |
| **Starting a new phase** | TASK_PHASE_WORKFLOW.md | Most other docs |
| **General exploration** | All | None |

**Rule**: ARCHITECTURE.md → Find task above → Read only those files → Check `config/settings.py`

---

## Quick Links

| Topic | Document |
|-------|----------|
| **Task phase workflow** | [TASK_PHASE_WORKFLOW.md](TASK_PHASE_WORKFLOW.md) |
| Design patterns used | [DESIGN_PATTERNS.md](DESIGN_PATTERNS.md) |
| Data flow diagrams | [DATA_FLOW.md](DATA_FLOW.md) |
| Adding new components | [ADDING_COMPONENTS.md](ADDING_COMPONENTS.md) |
| Coding conventions | [CONVENTIONS.md](CONVENTIONS.md) |
| File placement rules | [FILE_STRUCTURE.md](FILE_STRUCTURE.md) |
| SSL/Proxy setup | [SSL_PROXY_SETUP.md](SSL_PROXY_SETUP.md) |

---

## Overview

**Purpose**: Automated apartment scraper for Bulgarian real estate sites, with scoring and dashboard.

**Goals**:
- Scrape listings from multiple Bulgarian real estate sites
- Use proxy rotation for anonymity
- Score listings against personal criteria
- Track evaluation via Streamlit dashboard

---

## Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python 3.12+ |
| HTML Parsing | Scrapling (774x faster than BeautifulSoup) |
| HTTP/Browser | Scrapling Fetchers (Fetcher, StealthyFetcher) |
| Task Queue | Celery + Redis |
| Database | SQLite |
| Dashboard | Streamlit |
| Proxy Rotation | Mubeng (Go) |
| Proxy Scraping | proxy-scraper-checker (Rust) |

### Scrapling (HTML Parser + Fetching)

We use [Scrapling](https://github.com/D4Vinci/Scrapling) for both parsing and fetching:
- **774x faster** parsing performance
- **Auto-encoding** detection (windows-1251, UTF-8 for Bulgarian sites)
- **Adaptive selectors** that survive site HTML changes
- **Two fetchers**: `Fetcher` (fast HTTP), `StealthyFetcher` (anti-bot bypass)

**Key files:**
- `websites/scrapling_base.py` - ScraplingMixin class
- `websites/SCRAPER_GUIDE.md` - Usage documentation
- `data/scrapling_selectors/` - Saved element signatures for adaptive matching

---

## Architecture Style

**Layered Architecture with Pipeline Processing**

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  app/ - Streamlit dashboard, scoring                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
│  main.py, orchestrator.py, celery_app.py, scraping/         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER                            │
│  websites/ - scrapers    proxies/ - proxy management        │
│  resilience/ - error handling, retry logic                  │
│  llm/ - LLM extraction                                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                       │
│  data/, config/, Redis, Celery                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Layers Summary

| Layer | Location | Purpose |
|-------|----------|---------|
| Presentation | `app/` | Streamlit dashboard, scoring |
| Application | `main.py`, `orchestrator.py`, `scraping/` | Workflows, service lifecycle, Celery tasks |
| Domain | `websites/`, `proxies/`, `resilience/`, `llm/` | Business logic, scraping, error handling |
| Infrastructure | `data/`, `config/`, `utils/` | External services, persistence, utilities |

---

## Project Structure

```
sale-sofia/
├── main.py              # Entry point (scraping workflow)
├── orchestrator.py      # Service lifecycle (Redis, Celery, Mubeng)
├── celery_app.py        # Celery configuration
├── paths.py             # Path constants
├── conftest.py          # Pytest configuration
│
├── app/                 # Dashboard (Streamlit)
│   └── pages/           # Streamlit pages
│
├── scraping/            # Celery scraping tasks & metrics
│   ├── tasks.py         # Celery task definitions
│   ├── async_fetcher.py # Async HTTP fetching
│   ├── metrics.py       # Scraping metrics
│   └── session_report.py# Session reporting
│
├── websites/            # Scrapers
│   ├── base_scraper.py  # Base class (ListingData)
│   ├── scrapling_base.py# ScraplingMixin
│   ├── generic/         # Generic YAML-driven scraper (experimental)
│   ├── imot_bg/         # imot.bg scraper
│   └── bazar_bg/        # bazar.bg scraper
│
├── resilience/          # Error handling, retry logic
│   ├── exceptions.py    # Exception hierarchy
│   ├── error_classifier.py
│   ├── retry.py         # Retry decorators
│   ├── circuit_breaker.py
│   ├── rate_limiter.py
│   ├── checkpoint.py    # Session recovery
│   └── response_validator.py
│
├── proxies/             # Proxy management
│   ├── tasks.py         # Celery proxy tasks
│   ├── mubeng_manager.py
│   ├── proxy_validator.py
│   ├── proxy_scorer.py
│   └── live_proxies.json
│
├── llm/                 # LLM integration (Ollama)
│   ├── llm_main.py      # OllamaClient facade
│   ├── prompts.py       # Prompt templates
│   ├── dictionary.py    # Bulgarian dictionary
│   └── schemas.py       # Pydantic models
│
├── config/              # Configuration
│   ├── settings.py      # Centralized settings (SINGLE SOURCE)
│   ├── start_urls.yaml  # Starting URLs per site
│   ├── sites/           # Per-site YAML configs (generic scraper)
│   └── loader.py        # Config loading utilities
│
├── data/                # Data storage
│   ├── data_store_main.py  # SQLite CRUD
│   ├── db_retry.py      # SQLite retry decorator
│   ├── change_detector.py
│   ├── bg-estate.db     # Main database
│   ├── checkpoints/     # Session recovery
│   ├── logs/            # Application logs
│   └── scrapling_selectors/  # Adaptive selectors
│
├── utils/               # Utilities
│   ├── log_config.py    # Logging configuration
│   └── utils.py         # Helper functions
│
├── tests/               # All tests
│   ├── test_*.py        # Unit tests
│   ├── debug/           # Debug/integration tests
│   ├── stress/          # Stress tests
│   ├── scrapers/        # Scraper-specific tests
│   └── unit/            # Pure unit tests
│
├── admin/               # Admin tools
│   ├── scripts/         # Admin scripts, hooks
│   └── config/          # Admin configuration
│
├── docs/                # Documentation
│   ├── architecture/    # This folder
│   ├── specs/           # Active specs
│   ├── research/        # Active research
│   ├── tasks/           # Task tracking (TASKS.md)
│   └── libs/            # Library documentation
│
└── archive/             # Historical files
    ├── browsers/        # Archived browser code
    ├── specs/           # Implemented specs
    └── research/        # Completed research
```

---

## Key Entry Points

| Purpose | Command |
|---------|---------|
| Run scraper | `python main.py` |
| Dashboard | `streamlit run app/streamlit_app.py` |
| Celery worker | `celery -A celery_app worker --beat` |
| Tests | `pytest tests/` |

---

## Key Files

| Purpose | File |
|---------|------|
| Entry point | `main.py` |
| Service management | `orchestrator.py` |
| Centralized settings | `config/settings.py` |
| Add new scraper | `websites/__init__.py` |
| Add URLs | `config/start_urls.yaml` |
| Database operations | `data/data_store_main.py` |
| Task tracking | `docs/tasks/TASKS.md` |
| Scraper guide | `websites/SCRAPER_GUIDE.md` |

---

## Module Quick Reference

| Module | Purpose | Key Pattern |
|--------|---------|-------------|
| `websites/` | Site-specific scraping | Template Method (see DESIGN_PATTERNS.md) |
| `resilience/` | Error handling, retry | Circuit Breaker, Retry (patterns 10-16) |
| `proxies/` | Proxy rotation | Facade, Pipeline |
| `scraping/` | Celery tasks, metrics | Async tasks |
| `llm/` | LLM extraction | Facade |
| `data/` | SQLite operations | DTO, Retry |

---

*Last updated: 2025-12-30*
