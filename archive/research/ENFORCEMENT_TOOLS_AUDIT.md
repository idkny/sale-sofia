# Enforcement Tools Audit

**Date:** 2025-12-25
**Purpose:** Identify tools to enforce coding guidelines (function length, complexity, etc.)

---

## Executive Summary

**Current State:** File placement is heavily enforced, code quality is NOT.

**Quick Win:** Create `pyproject.toml` with ruff config + extend file validator to check function length = ~2 hours of work, massive enforcement improvement.

---

## 1. Existing Enforcement Mechanisms

### A. File Placement Enforcement (ACTIVE)

| Component | Location |
|-----------|----------|
| Manifest | `admin/config/project_structure_manifest.json` |
| Validator | `admin/scripts/hooks/validate_file_placement.py` |
| Hook | `admin/scripts/hooks/pre_write_validate.sh` |
| Config | `.claude/settings.json` (PreToolUse hooks) |

**What it enforces:**
- File location rules
- Extension validation
- Directory depth (max 3)
- Implicit mkdir operations

**Status:** FULLY OPERATIONAL - blocks Write/Edit operations that violate rules.

### B. Claude Code Permissions (ACTIVE)

**Location:** `.claude/settings.json`
**Scope:** Git operations only (force push, hard reset denied)
**Code quality:** NOT enforced

### C. Testing Framework (INSTALLED)

**Location:** `pytest.ini`
**Current Config:** Markers for asyncio and integration tests only
**Quality plugins:** NOT configured

---

## 2. Available But Unused Tools

### A. Linting Tools in `requirements.txt`

| Tool | Status | Can Enforce |
|------|--------|-------------|
| **ruff** | Installed, NOT configured | Line length, complexity, imports |
| **black** | Installed, NOT configured | Code formatting |
| **isort** | Installed, NOT configured | Import sorting |

### B. Git Hooks Infrastructure

**Location:** `.git/hooks/`
**Status:** All standard .sample files, NONE activated
**Potential:** Pre-commit hooks for Python quality

### C. External Reference (Rust project)

**Location:** `proxies/external/proxy-scraper-checker/`
**Has:** Complete pre-commit config + GitHub Actions
**Note:** Different language, but shows pattern

---

## 3. What's Missing

**No Python config files at root:**
- No `pyproject.toml`
- No `.flake8`
- No `ruff.toml`
- No `.pre-commit-config.yaml`
- No `.pylintrc`
- No `setup.cfg`

---

## 4. Implementation Options

### Option A: Ruff Configuration Only (30 min)

**Create:** `pyproject.toml`

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = [
  "E501",    # Line too long
  "E302",    # Expected 2 blank lines
  "F",       # Pyflakes
  "I",       # isort
  "W",       # Warnings
]
```

**Enforcement:** Manual (`ruff check` before commit)

---

### Option B: Pre-commit Framework (1-2 hours)

**Create:** `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
```

**Enforcement:** Git pre-commit hook (blocks violating commits)

---

### Option C: GitHub Actions CI/CD (2-3 hours)

**Create:** `.github/workflows/python-quality.yml`

**Covers:** All of Option B + automated PR checks

---

### Option D: Custom Function Length Validator (RECOMMENDED)

**Why:** Ruff doesn't enforce function length directly.

**Create:** `admin/scripts/hooks/validate_function_length.py`

```python
import ast
import sys

MAX_FUNCTION_LINES = 50
WARNING_THRESHOLD = 30

def check_file(filepath):
    with open(filepath) as f:
        tree = ast.parse(f.read())

    violations = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lines = node.end_lineno - node.lineno + 1
            if lines > MAX_FUNCTION_LINES:
                violations.append({
                    'function': node.name,
                    'lines': lines,
                    'start': node.lineno,
                })
    return violations
```

**Integration:** Add to `pre_write_validate.sh`

**Enforcement:** Claude Code write hook (blocks edits creating long functions)

---

## 5. Recommended Approach (Hybrid)

### Immediate (Option B + D)

1. Create `.pre-commit-config.yaml` for standard linting
2. Create `validate_function_length.py` validator
3. Configure ruff in `pyproject.toml`

### Files to Create

| File | Purpose |
|------|---------|
| `pyproject.toml` | Ruff + tool configuration |
| `.pre-commit-config.yaml` | Pre-commit hooks |
| `admin/scripts/hooks/validate_function_length.py` | Function length check |

### Update Required

| File | Change |
|------|--------|
| `admin/scripts/hooks/pre_write_validate.sh` | Add function length check |
| `.claude/settings.json` | Already configured for hooks |

---

## 6. Enforcement Gap Analysis

| Rule from CONVENTIONS.md | Currently Enforced? | How to Enforce |
|--------------------------|---------------------|----------------|
| Functions <50 lines | NO | Custom validator |
| Functions target <30 lines | NO | Custom validator (warning) |
| Max 3 levels nesting | NO | Ruff C901 complexity |
| Single responsibility | NO | Code review only |
| No magic numbers | NO | Code review only |
| Helper functions with `_` | NO | Code review only |

---

## 7. Quick Win Recommendation

**Minimum viable enforcement (2 hours):**

1. Create `pyproject.toml` with ruff config
2. Create `validate_function_length.py`
3. Update hook to call validator

**Result:** Any Write/Edit creating a function >50 lines will be blocked.

---

*Report generated on 2025-12-25*
