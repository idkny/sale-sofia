# Local Package Documentation Reference

These packages have documentation in their source code (docstrings). Use the commands below to access them.

## How to Get Documentation

```bash
# Get module/class help
venv/bin/python -c "import <module>; help(<module>)"
venv/bin/python -c "from <module> import <class>; help(<class>)"

# Or use pydoc
venv/bin/pydoc <module>
venv/bin/pydoc <module>.<class>
```

---

## Celery (Task Queue)

**Location:** `venv/lib/python3.12/site-packages/celery/`

**Quick Reference:**
```bash
venv/bin/python -c "from celery import Celery; help(Celery)"
venv/bin/python -c "from celery import chain, group, chord; help(chain)"
```

**Key Modules:**
- `celery.Celery` - Main app class
- `celery.chain` - Chain tasks sequentially
- `celery.group` - Run tasks in parallel
- `celery.chord` - Group + callback
- `celery.Task` - Base task class

---

## Loguru (Logging)

**Location:** `venv/lib/python3.12/site-packages/loguru/`

**Quick Reference:**
```bash
venv/bin/python -c "from loguru import logger; help(logger)"
venv/bin/python -c "from loguru import logger; help(logger.add)"
```

**Key Methods:**
- `logger.add()` - Add handler/sink
- `logger.debug/info/warning/error/critical()` - Log levels
- `logger.bind()` - Add context
- `logger.catch()` - Exception decorator
- `logger.opt()` - Options for next log

---

## Streamlit (Dashboard)

**Location:** `venv/lib/python3.12/site-packages/streamlit/`

**Quick Reference:**
```bash
venv/bin/python -c "import streamlit as st; help(st)"
venv/bin/python -c "import streamlit as st; help(st.dataframe)"
```

**Key Functions:**
- `st.title/header/subheader/write` - Text
- `st.dataframe/table` - Data display
- `st.selectbox/multiselect/slider` - Inputs
- `st.columns/tabs/expander` - Layout
- `st.session_state` - State management

---

## Pandas (Data Analysis)

**Location:** `venv/lib/python3.12/site-packages/pandas/`

**Quick Reference:**
```bash
venv/bin/python -c "import pandas as pd; help(pd.DataFrame)"
venv/bin/python -c "import pandas as pd; help(pd.read_json)"
```

**Key Classes:**
- `pd.DataFrame` - Main data structure
- `pd.Series` - Single column
- `pd.read_json/read_csv` - Load data
- `df.groupby/merge/pivot` - Data operations

---

## Pytest (Testing)

**Location:** `venv/lib/python3.12/site-packages/pytest/`

**Quick Reference:**
```bash
venv/bin/python -c "import pytest; help(pytest)"
venv/bin/python -c "import pytest; help(pytest.fixture)"
```

**Key Decorators:**
- `@pytest.fixture` - Test fixtures
- `@pytest.mark.parametrize` - Parameterized tests
- `@pytest.mark.asyncio` - Async tests
- `pytest.raises()` - Exception testing

---

## Playwright (Browser Automation)

**Location:** `venv/lib/python3.12/site-packages/playwright/`

**Quick Reference:**
```bash
venv/bin/python -c "from playwright.sync_api import sync_playwright; help(sync_playwright)"
```

**Note:** Playwright docs are best accessed at https://playwright.dev/python/docs/intro

**Key Classes:**
- `sync_playwright()` - Sync API context
- `browser.new_page()` - Create page
- `page.goto/click/fill` - Page actions
- `page.locator()` - Element selection

---

## Reading Source Directly

For any package, read the source:
```bash
# Find main module
ls venv/lib/python3.12/site-packages/<package>/

# Read specific file
cat venv/lib/python3.12/site-packages/<package>/<file>.py
```
