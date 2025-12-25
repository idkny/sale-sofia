# Sofia Apartment Search

Automated web scraping system for Bulgarian real estate listings. Scrapes apartment listings from imot.bg and bazar.bg to support apartment investment search in Sofia.

## Quick Start

```bash
# 1. Install dependencies
./setup.sh

# 2. Activate virtual environment
source venv/bin/activate

# 3. Run the scraper
python main.py
```

## Project Structure

```
sale-sofia/
├── main.py              # Entry point - runs automated scraping
├── orchestrator.py      # Manages Redis, Celery, proxy lifecycle
├── celery_app.py        # Celery configuration with Beat scheduler
├── paths.py             # Central path definitions
│
├── app/                 # Streamlit dashboard
│   ├── streamlit_app.py # Dashboard entry point
│   └── pages/           # Multi-page dashboard views
│
├── websites/            # Scraper implementations
│   ├── base_scraper.py  # Abstract base class
│   ├── imot_bg/         # imot.bg scraper
│   └── bazar_bg/        # bazar.bg scraper
│
├── proxies/             # Proxy management system
│   ├── proxies_main.py  # Proxy orchestration facade
│   ├── mubeng_manager.py# Proxy rotator control
│   ├── proxy_scorer.py  # Performance scoring
│   └── tasks.py         # Celery background tasks
│
├── browsers/            # Browser automation
│   ├── browsers_main.py # Browser factory
│   ├── strategies/      # Browser strategy implementations
│   └── profile/         # Stealth browser profiles
│
├── data/                # Data persistence
│   ├── data_store_main.py # SQLite listings database
│   └── bg-estate.db     # SQLite database file
│
├── config/              # Configuration
│   ├── loader.py        # YAML config loader
│   └── start_urls.yaml  # Target URLs per site
│
├── utils/               # Utilities
├── tests/               # Pytest test suite
│   └── stress/          # Stress tests
├── scripts/             # Utility scripts
├── docs/                # System documentation
│   └── tasks/           # Multi-instance coordination
│       ├── TASKS.md     # Task tracker (single source of truth)
│       ├── instance_001.md  # Instance 1 session file
│       └── instance_002.md  # Instance 2 session file
├── research/            # Apartment search research
└── archive/             # Historical sessions & reference material
```

## Architecture

### Scraping Pipeline

```
1. Start Redis (message broker)
2. Start Celery (background worker)
3. Setup Mubeng proxy rotator (port 8089)
4. Pre-flight proxy validation with 3-tier recovery
5. For each site/URL:
   - Collect listing URLs via pagination
   - Scrape each listing detail page
   - Track proxy performance
6. Save results to SQLite
7. Cleanup processes
```

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **Scrapers** | `websites/` | Site-specific scraping logic |
| **Proxy System** | `proxies/` | Multi-layer proxy validation, scoring, rotation |
| **Browsers** | `browsers/` | Stealth browser automation (Camoufox) |
| **Data Store** | `data/` | SQLite persistence with 25+ listing fields |
| **Dashboard** | `app/` | Streamlit UI for viewing/analyzing listings |

## Configuration

### Start URLs

Edit `config/start_urls.yaml` to configure which URLs to scrape:

```yaml
imot_bg:
  urls:
    - "https://www.imot.bg/obiavi/prodazhbi/grad-sofiya"
  limit: 100
  delay: 6.0
```

### Environment Variables

Create `.env` file for:
- `REDIS_HOST`, `REDIS_PORT` - Redis connection
- Log level and output directory

## Running

### Full Auto Mode
```bash
python main.py
```

### Dashboard Only
```bash
streamlit run app/streamlit_app.py
```

### Tests
```bash
pytest
```

## Dependencies

- **Python 3.12+**
- **Redis** - Message broker for Celery
- **Playwright** - Browser automation
- **Camoufox** - Stealth browser profiles
- **Celery** - Background task processing
- **Streamlit** - Dashboard UI

See `requirements.txt` for full list.
