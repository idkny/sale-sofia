# File Structure Rules

> **For Agents**: Read this BEFORE creating any new file. Follow these rules exactly.

---

## Quick Decision Tree

```
Creating a new file? Ask yourself:

Is it a .md file?
├── README or CLAUDE? ────────────────→ ROOT/
├── Architecture documentation? ──────→ docs/architecture/
├── Active research? ─────────────────→ docs/research/
├── Active spec? ─────────────────────→ docs/specs/
├── Task-related? ────────────────────→ docs/tasks/
├── Completed research? ──────────────→ archive/research/
├── Implemented spec? ────────────────→ archive/specs/
└── Other? ───────────────────────────→ ASK USER

Is it a .py file?
├── Test file (test_*.py)? ───────────→ tests/
├── Scraper code? ────────────────────→ websites/<site>/
├── Browser automation? ──────────────→ browsers/
├── Proxy management? ────────────────→ proxies/
├── LLM integration? ─────────────────→ llm/
├── Dashboard/UI? ────────────────────→ app/
├── Utility script? ──────────────────→ scripts/
├── Data access? ─────────────────────→ data/
└── Core entry point? ────────────────→ ROOT/ (only main, orchestrator, celery_app, paths)

Is it a config file (.yaml, .json)?
├── Start URLs / site config? ────────→ config/
├── Claude Code settings? ────────────→ .claude/
└── Proxy lists? ─────────────────────→ proxies/

Is it test output / results?
└── Always ───────────────────────────→ tests/<type>/

Is it data / logs?
├── Database (.db)? ──────────────────→ data/
└── Logs (.log)? ─────────────────────→ data/logs/
```

---

## Allowed Root Files

**ONLY these files are allowed at project root:**

| File | Purpose |
|------|---------|
| `main.py` | Entry point |
| `orchestrator.py` | Service lifecycle management |
| `celery_app.py` | Celery configuration |
| `paths.py` | Centralized path constants |
| `requirements.txt` | Python dependencies |
| `README.md` | Project overview |
| `CLAUDE.md` | AI agent instructions |
| `.gitignore` | Git ignore patterns |
| `.env` | Environment variables (gitignored) |
| `pytest.ini` | Pytest configuration |
| `setup.sh` | Project setup script |

**Everything else goes in a subdirectory.**

---

## Directory Structure

```
sale-sofia/
│
├── [ROOT FILES - see above]
│
├── app/                      # PRESENTATION LAYER
│   ├── *.py                  # Streamlit code ONLY
│   └── pages/*.py            # Streamlit pages
│
├── browsers/                 # Browser automation
│   ├── *.py                  # Browser code
│   ├── strategies/*.py       # Strategy implementations
│   └── profile/              # Browser profiles
│
├── config/                   # Configuration files
│   ├── *.yaml                # YAML configs
│   └── *.json                # JSON configs
│
├── data/                     # Data storage
│   ├── *.db                  # SQLite databases
│   └── logs/                 # Application logs
│       └── *.log
│
├── proxies/                  # Proxy management
│   ├── *.py                  # Python code
│   ├── *.json                # Proxy lists (live_proxies.json)
│   ├── *.md                  # Module README only
│   └── external/             # External binaries
│
├── resilience/               # Error handling, circuit breaker, rate limiting
│   ├── __init__.py           # Exports
│   ├── exceptions.py         # Exception hierarchy
│   ├── error_classifier.py   # Error type classification
│   ├── retry.py              # Retry decorators with backoff
│   ├── circuit_breaker.py    # Domain circuit breaker (Phase 2)
│   ├── rate_limiter.py       # Token bucket rate limiter (Phase 2)
│   ├── checkpoint.py         # Session recovery checkpoint (Phase 3)
│   └── response_validator.py # Soft block detection (Phase 4)
│
├── llm/                      # LLM integration (Ollama)
│   ├── __init__.py           # Exports
│   ├── llm_main.py           # Facade (OllamaClient + public functions)
│   ├── prompts.py            # Prompt templates
│   └── schemas.py            # Pydantic models
│
├── websites/                 # Scrapers
│   ├── base_scraper.py       # Base class
│   └── <site_name>/          # Per-site folders
│       ├── *_scraper.py      # Scraper implementation
│       └── selectors.py      # CSS/regex selectors
│
├── tests/                    # ALL test files
│   ├── test_*.py             # Unit tests
│   ├── debug/                # Debug/integration tests
│   │   └── *.py
│   └── stress/               # Stress tests
│       ├── *.py              # Test scripts
│       ├── *.sh              # Shell test scripts
│       └── *.md              # Test results/reports
│
├── scripts/                  # Utility scripts
│   ├── *.py                  # Python scripts
│   └── *.sh                  # Shell scripts
│
├── docs/                     # Documentation (.md ONLY)
│   ├── architecture/         # Architecture docs
│   │   ├── ARCHITECTURE.md
│   │   └── FILE_STRUCTURE.md
│   ├── research/             # ACTIVE research
│   │   └── *.md              # (archive when done)
│   ├── specs/                # ACTIVE specs
│   │   └── *.md              # (archive when implemented)
│   └── tasks/                # Task management
│       ├── TASKS.md          # Single source of truth
│       ├── instance_001.md
│       └── instance_002.md
│
├── research/                 # Domain research (non-technical)
│   └── *.md                  # Neighborhoods, criteria, etc.
│
├── archive/                  # Historical files
│   ├── docs/                 # Old documentation
│   ├── research/             # Completed research
│   ├── specs/                # Implemented specs
│   ├── sessions/             # Old session histories
│   └── extraction/           # Reference code
│
└── .claude/                  # Claude Code config
    ├── settings.json
    └── commands/
```

---

## File Type Rules

### Markdown Files (.md)

| If the file is... | Put it in... |
|-------------------|--------------|
| Project overview | `README.md` (root) |
| AI instructions | `CLAUDE.md` (root) |
| Architecture documentation | `docs/architecture/` |
| Active research | `docs/research/` |
| Active spec | `docs/specs/` |
| Task tracking | `docs/tasks/` |
| Completed research | `archive/research/` |
| Implemented spec | `archive/specs/` |
| Module README | In the module folder |
| Test results/reports | `tests/stress/` or `tests/debug/` |

### Python Files (.py)

| If the file is... | Put it in... |
|-------------------|--------------|
| Entry point (main) | Root |
| Test file | `tests/` |
| Scraper | `websites/<site>/` |
| Browser code | `browsers/` |
| Proxy code | `proxies/` |
| Resilience/error handling | `resilience/` |
| LLM code | `llm/` |
| Dashboard code | `app/` |
| Data access | `data/` |
| Utility script | `scripts/` |
| Config loader | `config/` |

### Config Files (.yaml, .json)

| If the file is... | Put it in... |
|-------------------|--------------|
| Start URLs | `config/` |
| Site settings | `config/` |
| Proxy lists | `proxies/` |
| Claude settings | `.claude/` |

### Data Files

| If the file is... | Put it in... |
|-------------------|--------------|
| SQLite database | `data/` |
| Application logs | `data/logs/` |
| Test output | `tests/<type>/` |

---

## Forbidden Patterns

**NEVER do these:**

| Pattern | Why Wrong | Correct Location |
|---------|-----------|------------------|
| `ROOT/*.md` (except README, CLAUDE) | Clutters root | `docs/<folder>/` |
| `ROOT/*_results.*` | Test output in root | `tests/stress/` |
| `ROOT/*.json` | Config in root | `config/` or module folder |
| `ROOT/*.log` | Logs in root | `data/logs/` |
| `ROOT/test_*.py` | Tests in root | `tests/` |
| `docs/**/*.py` | Code in docs | Appropriate code folder |
| `*.md` in code folders (except README) | Docs mixed with code | `docs/` |

---

## Workflow Reminders

### Research → Specs → Code

```
docs/research/  →  docs/specs/  →  TASKS.md  →  code
(discovery)        (blueprint)     (tracking)    (truth)
     ↓                 ↓                           ↓
archive/research/  archive/specs/          (code supersedes)
```

1. **Research done** → Create spec in `docs/specs/`, archive research to `archive/research/`
2. **Spec implemented** → Archive spec to `archive/specs/`, code is now source of truth
3. **Never update archived files** → Write new specs for new features

### Before Creating Any File

1. Check this document for correct location
2. If unsure, ASK USER
3. Never create files at root unless listed in "Allowed Root Files"

---

## Common Mistakes

| Mistake | Why It Happens | Fix |
|---------|----------------|-----|
| Creating `stress_test_results.md` at root | Running tests from root | Use `tests/stress/stress_test_results.md` |
| Creating research in root | Quick notes | Use `docs/research/` |
| Creating specs outside docs/ | Forgetting workflow | Use `docs/specs/` |
| Putting test results in docs/ | Confusion | Use `tests/<type>/` |

---

*Last updated: 2025-12-25*
