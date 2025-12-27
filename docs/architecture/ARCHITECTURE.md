# Sofia Apartment Search - Architecture

> **Core architecture overview.** For details, see linked documents.

---

## Quick Links

| Topic | Document |
|-------|----------|
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
| Browser | Playwright |
| Task Queue | Celery + Redis |
| Database | SQLite |
| Dashboard | Streamlit |
| Proxy Rotation | Mubeng (Go) |
| Proxy Scraping | proxy-scraper-checker (Rust) |

### Scrapling (HTML Parser)

We use [Scrapling](https://github.com/D4Vinci/Scrapling) instead of BeautifulSoup for:
- **774x faster** parsing performance
- **Auto-encoding** detection (windows-1251, UTF-8 for Bulgarian sites)
- **Adaptive selectors** that survive site HTML changes

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
│  main.py, orchestrator.py, celery_app.py                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER                            │
│  websites/ - scrapers    proxies/ - proxy management        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                       │
│  data/, browsers/, config/, Redis, Celery                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Layers Summary

| Layer | Location | Purpose |
|-------|----------|---------|
| Presentation | `app/` | Streamlit dashboard, scoring |
| Application | `main.py`, `orchestrator.py` | Workflows, service lifecycle |
| Domain | `websites/`, `proxies/`, `resilience/` | Business logic, error handling |
| Infrastructure | `data/`, `browsers/`, `config/` | External services, persistence |

---

## Project Structure

```
sale-sofia/
├── main.py              # Entry point
├── orchestrator.py      # Service lifecycle
├── celery_app.py        # Celery config
├── paths.py             # Path constants
│
├── app/                 # Dashboard
├── browsers/            # Browser automation
├── config/              # Configuration
├── data/                # SQLite, logs
├── proxies/             # Proxy management
├── resilience/          # Error handling, retry logic
├── websites/            # Scrapers
├── tests/               # Tests
├── docs/                # Documentation
├── admin/               # Admin scripts
└── archive/             # Historical files
```

---

## Key Entry Points

| Purpose | File |
|---------|------|
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
| Add new scraper | `websites/__init__.py` |
| Add URLs | `config/start_urls.yaml` |
| Database | `data/data_store_main.py` |
| Task tracking | `docs/tasks/TASKS.md` |

---

*Last updated: 2025-12-25*
