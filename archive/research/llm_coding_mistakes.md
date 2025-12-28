# LLM/Claude Code Common Mistakes - Pre-Production Audit Research

**Created**: 2025-12-28
**Purpose**: Document known LLM coding mistakes to check before production deployment

---

## Executive Summary

Research from multiple sources (2024-2025) shows AI-generated code has **1.7x more issues** than human-written code. This document catalogs specific patterns to audit in our codebase.

---

## 1. Duplicate/Similar Code (DRY Violations)

**The Problem**: LLMs optimize for local correctness, not global architecture. They copy-paste solutions rather than reuse existing functions.

**What to check**:
- Functions with similar names in different files
- Identical logic implemented multiple times
- Helper functions that could be consolidated
- Retry/backoff logic duplicated across modules

**Sources**: [AI-Generated Code Creates New Wave of Technical Debt](https://www.infoq.com/news/2025/11/ai-code-technical-debt/)

---

## 2. Security Vulnerabilities

**The Problem**: AI code is 1.88x more likely to have password issues, 2.74x more likely to have XSS, 1.82x more likely to have insecure deserialization.

**What to check**:
- SQL injection (even with SQLite)
- Command injection in subprocess calls
- Improper input validation
- Secrets/credentials in code
- Unsafe file path handling

**Sources**: [AI-authored code needs more attention](https://www.theregister.com/2025/12/17/ai_code_bugs/)

---

## 3. Error Handling Gaps

**The Problem**: LLMs generate happy-path code. Error handling exists but doesn't meaningfully handle edge cases.

**What to check**:
- Empty try/except blocks or bare `except:`
- Missing null/None checks
- Errors that are caught but not properly logged/handled
- Missing validation at system boundaries
- Database connection error handling

**Sources**: [8 Failure Patterns & Fixes](https://www.augmentcode.com/guides/debugging-ai-generated-code-8-failure-patterns-and-fixes)

---

## 4. Performance Anti-Patterns

**The Problem**: LLMs optimize for correctness, not performance. Code works in dev but degrades at scale.

**What to check**:
- String concatenation in loops (use join())
- Nested iterations creating O(n²) complexity
- N+1 query patterns in database code
- Loading entire datasets into memory
- Repeated file I/O in loops

**Sources**: [8 Failure Patterns & Fixes](https://www.augmentcode.com/guides/debugging-ai-generated-code-8-failure-patterns-and-fixes)

---

## 5. Dead Code & Unused Imports

**The Problem**: LLMs leave artifacts - old code with "New" prefixes, unused imports, commented-out blocks.

**What to check**:
- Imports that are never used
- Functions that are never called
- Variables assigned but never read
- Commented-out code blocks
- Files that are orphaned

**Sources**: [Claude Code Gotchas](https://www.dolthub.com/blog/2025-06-30-claude-code-gotchas/)

---

## 6. Test Quality Issues

**The Problem**: LLM tests look correct but are often flawed. Tests get modified to match buggy code instead of vice versa.

**What to check**:
- Tests that pass but don't actually test anything meaningful
- Hardcoded expected values that hide bugs
- Missing edge case tests (empty, null, boundary)
- Tests that mock too much (test the mock, not the code)
- Assertions that are too weak

**Sources**: [Claude Code Gotchas](https://www.dolthub.com/blog/2025-06-30-claude-code-gotchas/)

---

## 7. Configuration Inconsistencies

**The Problem**: LLMs don't maintain global consistency. Same value hardcoded in multiple places.

**What to check**:
- Hardcoded timeouts, limits, thresholds (should be in settings.py)
- Duplicate constant definitions
- Environment variables referenced but not documented
- Config values that should match but don't

---

## 8. Hallucinated APIs/Dependencies

**The Problem**: LLMs generate plausible-sounding but non-existent imports and methods.

**What to check**:
- Imports that reference non-existent packages
- Method calls to functions that don't exist
- Outdated API usage from deprecated libraries

**Sources**: [8 Failure Patterns & Fixes](https://www.augmentcode.com/guides/debugging-ai-generated-code-8-failure-patterns-and-fixes)

---

## 9. Context Compaction Artifacts

**The Problem**: After context limits, Claude forgets previous work and re-introduces fixed bugs.

**What to check**:
- Inconsistent patterns across files (some files follow pattern, others don't)
- Partially implemented features
- Mixed coding styles within same module

**Sources**: [Claude Code Gotchas](https://www.dolthub.com/blog/2025-06-30-claude-code-gotchas/)

---

## 10. Missing Edge Cases

**The Problem**: Training data biases toward common scenarios. Edge cases get missed.

**What to check**:
- Empty list/dict handling
- None/null value handling
- Unicode/special character handling
- Boundary values (0, -1, MAX_INT)
- Concurrent access scenarios

---

## Audit Checklist for This Project

| Category | Agent Assigned | Status |
|----------|---------------|--------|
| Duplicate functions | code-reviewer | Pending |
| Security vulnerabilities | backend-security-coder | Pending |
| Error handling gaps | code-reviewer | Pending |
| Dead code/unused imports | code-reviewer | Pending |
| Configuration consistency | architect-review | Pending |
| Test quality | tdd-orchestrator | Pending |

---

## References

- [Claude Code Gotchas - DoltHub](https://www.dolthub.com/blog/2025-06-30-claude-code-gotchas/)
- [8 Failure Patterns & Fixes - Augment Code](https://www.augmentcode.com/guides/debugging-ai-generated-code-8-failure-patterns-and-fixes)
- [AI-Generated Code Creates Technical Debt - InfoQ](https://www.infoq.com/news/2025/11/ai-code-technical-debt/)
- [AI-authored code needs more attention - The Register](https://www.theregister.com/2025/12/17/ai_code_bugs/)
- [Hallucinations in code - Simon Willison](https://simonwillison.net/2025/Mar/2/hallucinations-in-code/)
