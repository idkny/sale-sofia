---
id: extraction_utils_index
type: index
subject: extraction
description: "Index of utility function patterns extracted from repositories"
created_at: 2025-12-01
updated_at: 2025-12-01
created_by: cto
status: active
tags: [extraction, utils, index, utilities]
---

# Utility Patterns - Extraction Index

**Subject**: File handling, URL processing, helper functions

---

## Files

| File | Source Repo | Key Patterns |
|------|-------------|--------------|
| `utils_OllamaRag.md` | Ollama-Rag | URL deduplication, inbox pattern, file operations |

---

## Best-of-Breed

| Pattern | Best Version | Source |
|---------|--------------|--------|
| Deduplication | MarketIntel (DB) | get_or_insert is better than set() |
| Inbox pattern | Ollama-Rag | Process → append → clear |
| URL cleaning | Ollama-Rag | Needs generalization |

---

## Integration Target

`autobiz/tools/utils/` - General utilities

---

Last updated: 2025-12-01
