# Sofia Apartment Search

Automated web scraping system for Bulgarian real estate listings with scoring, analytics, and a Streamlit dashboard.

---

## Quick Start

```bash
# 1. Install dependencies
./setup.sh

# 2. Activate virtual environment
source venv/bin/activate

# 3. Run the scraper
python main.py

# 4. View results in dashboard
streamlit run app/streamlit_app.py
```

The dashboard opens at **http://localhost:8501**

---

## What This System Does

1. **Scrapes** apartment listings from Bulgarian real estate sites (imot.bg, bazar.bg)
2. **Rotates proxies** to avoid IP blocking (scrapes ~5000 proxies, filters to ~50-100 working ones)
3. **Stores** 30+ fields per listing in SQLite database
4. **Scores** listings based on your criteria (location, price/sqm, condition, etc.)
5. **Detects** price changes and cross-site duplicates
6. **Displays** everything in a Streamlit dashboard

---

## Running the Scraper

### Basic Usage

```bash
python main.py
```

This runs the full automated pipeline:

```
1. Starts Redis (message broker)
2. Starts Celery (background worker)
3. Scrapes/validates proxies (takes 5-10 min on first run)
4. Starts Mubeng proxy rotator on localhost:8089
5. Runs pre-flight proxy check (3-tier recovery)
6. Crawls all URLs from config/start_urls.yaml
7. Saves listings to data/bg-estate.db
8. Generates session report in data/reports/
```

### Configuring What to Scrape

Edit `config/start_urls.yaml`:

```yaml
imot.bg:
  config:
    limit: 100      # Max listings per start URL
    delay: 6        # Seconds between requests
    timeout: 30     # Page load timeout
  urls:
    - https://www.imot.bg/obiavi/prodazhbi/grad-sofiya/tristaen/?priceBuy_min=200000&priceBuy_max=270000

bazar.bg:
  config:
    limit: 100
    delay: 6
    timeout: 30
  urls:
    - https://bazar.bg/obiavi/apartamenti/tristaini/sofia
```

### Session Reports

After each run, a session report is saved to `data/reports/`:
- Success/failure rates
- Response times
- Per-domain statistics
- Health status (healthy/degraded/critical)

---

## Viewing Results: The Dashboard

### Starting the Dashboard

```bash
streamlit run app/streamlit_app.py
```

Opens at **http://localhost:8501**

### Dashboard Pages

#### 1. Home (🏠)
- Quick stats: total listings, avg price, avg price/sqm
- Links to other pages

#### 2. Dashboard (📊)
- **Metrics row**: Total listings, shortlisted, viewed, avg price, avg €/sqm
- **Status distribution**: Chart showing New/Contacted/Viewed/Shortlist/Rejected counts
- **District breakdown**: Top 10 districts with listing counts and avg price/sqm
- **Shortlisted apartments**: Expandable cards with scores and deal breaker status
- **Price analysis**: Price range and price/sqm distribution charts

#### 3. Listings (🏢)
- **Filterable table**: Filter by district, price range, rooms, status
- **Deal breaker filter**: Show only apartments passing all deal breakers
- **Change detection filter**: Show recently changed listings (price drops!)
- **Detail view**: Click any listing to see:
  - Details tab: Price, size, building, location, features
  - Scoring tab: Score breakdown with bar chart
  - Price History tab: Price changes over time with chart
  - Deal Breakers tab: Pass/fail status for each criterion
  - Notes & Viewings tab: User notes and viewing history
  - Edit tab: Update status, decision, renovation estimate, add viewings

#### 4. Compare (⚖️)
- **Side-by-side comparison**: Select 2-3 apartments to compare
- **Comparison sections**: Price/budget, size/layout, location, building, scores, features
- **Recommendation**: Shows best choice based on scores and deal breakers

#### 5. Cross-Site (🔄)
- **Duplicate detection**: Properties listed on multiple sites
- **Price discrepancies**: Find the same property cheaper on another site
- **Recommendation**: Which site to contact for best price

#### 6. Scraper Health (🔧)
- **Health metrics**: Success rate, error rate, block rate, response time
- **Trend charts**: Success rate and response time over multiple runs
- **Run history**: Last 10 scraper runs with status
- **Domain health**: Per-site success rates

---

## Scoring System

Each listing is scored 0-5 on multiple criteria:

| Criterion | Weight | What It Measures |
|-----------|--------|------------------|
| Location | 25% | District quality, metro proximity |
| Price/sqm | 20% | Value for money |
| Condition | 15% | Renovation state |
| Layout | 15% | Rooms, size, floor |
| Building | 10% | Building type, year, elevator |
| Rental | 10% | Rental potential |
| Extras | 5% | Balcony, parking, storage, etc. |

**Total weighted score**: 0-5 (higher is better)

---

## Deal Breakers

Configurable criteria that must pass for a listing to be considered:

- **Budget**: Total investment (price + renovation) must be under limit
- **Rooms**: Minimum room count
- **Floor**: Not on first or last floor (configurable)
- **Metro**: Within walking distance to metro
- **Building type**: No panel buildings (configurable)

Listings failing any deal breaker are flagged with ❌

---

## Database Location

All data is stored in SQLite:

```
data/bg-estate.db
```

Contains:
- `listings` table: All scraped listings (30+ fields)
- `viewings` table: Viewing notes for visited apartments
- `properties` table: Cross-site property fingerprints

---

## Logs and Reports

| File | Purpose |
|------|---------|
| `data/logs/scraper.log` | Detailed scraping logs |
| `data/reports/*.json` | Session reports (per run) |
| `data/checkpoints/*.json` | Crash recovery checkpoints |

---

## Configuration Files

| File | Purpose |
|------|---------|
| `config/start_urls.yaml` | URLs to scrape, limits, delays |
| `config/settings.py` | All system settings (timeouts, thresholds) |
| `config/scraping/` | Per-site scraping configs |

---

## Architecture Overview

```
PRESENTATION   → app/                  # Streamlit dashboard
APPLICATION    → main.py, orchestrator.py, celery_app.py
DOMAIN         → websites/, proxies/, resilience/
INFRASTRUCTURE → data/, browsers/, config/
```

**Data Flow**:
```
URLs → Mubeng Proxy → Browser → HTML → Scraper → SQLite → Dashboard
```

For full architecture details, see `docs/architecture/ARCHITECTURE.md`

---

## Key Commands

| Command | Purpose |
|---------|---------|
| `python main.py` | Run full scraping pipeline |
| `streamlit run app/streamlit_app.py` | Start dashboard |
| `pytest tests/` | Run test suite (900+ tests) |
| `celery -A celery_app worker --beat` | Start Celery worker manually |

---

## For Claude Code Instances

When asked to work on this project:

1. **Read this README first** for system overview
2. **Read `docs/tasks/TASKS.md`** for current work and backlog
3. **Read `docs/tasks/instance_XXX.md`** for your session file
4. **Read `docs/architecture/`** for detailed technical docs:
   - `ARCHITECTURE.md` - System overview
   - `DATA_FLOW.md` - How data moves through the system
   - `DESIGN_PATTERNS.md` - Patterns used (16 documented patterns)
   - `CONVENTIONS.md` - Code style and naming
   - `FILE_STRUCTURE.md` - Where to put files
   - `ADDING_COMPONENTS.md` - How to add scrapers/proxy sources

**Current Status**: All phases complete. 900+ tests passing. Future work in backlog (TASKS.md).

---

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
│   ├── scoring.py       # Scoring logic
│   └── pages/           # Dashboard pages (5 pages)
│
├── websites/            # Scraper implementations
│   ├── base_scraper.py  # Abstract base class
│   ├── scrapling_base.py# ScraplingMixin for fast parsing
│   ├── generic/         # NEW: Config-driven scraper framework
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
│   └── strategies/      # Browser strategy implementations
│
├── resilience/          # Error handling and recovery
│   ├── circuit_breaker.py  # Domain circuit breaker
│   ├── rate_limiter.py     # Token bucket rate limiter
│   ├── retry.py            # Retry with backoff
│   ├── checkpoint.py       # Crash recovery
│   └── response_validator.py # Soft block detection
│
├── data/                # Data persistence
│   ├── data_store_main.py # SQLite CRUD operations
│   ├── change_detector.py # Price change tracking
│   └── bg-estate.db     # SQLite database
│
├── config/              # Configuration
│   ├── start_urls.yaml  # Target URLs per site
│   ├── settings.py      # All settings
│   ├── scraping/        # Per-site configs
│   └── sites/           # NEW: Generic scraper YAML configs
│
├── scraping/            # Scraping infrastructure
│   ├── metrics.py       # Request metrics collection
│   └── session_report.py# Session report generation
│
├── tests/               # Test suite (900+ tests)
│   ├── test_*.py        # Unit tests
│   ├── debug/           # Debug tests
│   └── stress/          # Stress/benchmark tests
│
├── docs/                # Documentation
│   ├── architecture/    # Architecture docs (7 files)
│   └── tasks/           # Task tracking
│       ├── TASKS.md     # Single source of truth for tasks
│       └── instance_*.md # Instance session files
│
└── archive/             # Historical files
```

---

## Generic Scraper Framework (Experimental)

**Status**: Phase 1 Complete - Not Yet Production Ready

A new config-driven scraper framework that allows adding new sites with **YAML only** - no Python code required.

### How It Works

1. Create a YAML config file in `config/sites/` (e.g., `olx_bg.yaml`)
2. Define CSS selector chains for each field (with fallback order)
3. Use `ConfigScraper` to extract data using the config
4. No Python code needed for new sites

### Key Features

- **Fallback selector chains**: Define 3-5 selectors per field - if one breaks, the next takes over
- **Field type parsing**: Supports text, number, currency, floor patterns, lists
- **Reuses existing infrastructure**: ScraplingMixin, resilience, Celery integration
- **Zero code for new sites**: Just add YAML config

### Components

| File | Purpose |
|------|---------|
| `websites/generic/config_loader.py` | Load and validate YAML configs |
| `websites/generic/selector_chain.py` | Fallback extraction engine |
| `websites/generic/config_scraper.py` | Generic ConfigScraper class |
| `config/sites/*.yaml` | Site-specific selector configs |

### Example Config

```yaml
site:
  name: example.bg
  domain: www.example.bg

detail_page:
  selectors:
    price:
      - "span.price-main"      # Try first
      - ".price-label strong"   # Fallback 1
      - "h3.css-price"         # Fallback 2
    sqm:
      - "li:contains('Квадратура') span"
      - "[data-code='m'] span"
```

**Important**: This framework is experimental. Phase 1 implementation is complete (148 passing tests), but it has not been tested with real sites in production yet.

For detailed documentation, see:
- `docs/specs/116_GENERIC_SCRAPER_TEMPLATE.md` - Full specification
- `websites/SCRAPER_GUIDE.md` - Updated guide with generic scraper section

---

*Last updated: 2025-12-28*
