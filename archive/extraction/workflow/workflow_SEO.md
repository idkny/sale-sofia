---
id: workflow_seo
type: extraction
subject: workflow
source_repo: SEO
description: "Keyword discovery workflow with filtering and interactive approval CLI"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [workflow, keywords, cli, review, seo]
---

# Workflow Extraction: SEO

**Source**: `idkny/SEO`
**Files**: `src/review_cli.py`, `approve_keywords.py`, `serp_api/keyword_filter.py`

---

## Overview

Keyword discovery workflow:
1. **Discovery** - Extract keywords from SerpAPI responses
2. **Filtering** - Service-based relevance with seed/negative tokens
3. **Review** - Interactive CLI for approval/rejection
4. **Execution** - Run approved keywords through pipeline

---

## Keyword Filter

```python
SERVICE_SEEDS = {
    "air_duct_cleaning": [
        "air duct cleaning", "duct cleaning", "HVAC cleaning",
        "AC duct cleaning", "furnace cleaning", ...
    ],
    "dryer_vent_cleaning": ["dryer vent cleaning", "dryer duct cleaning", ...],
    # ... more services
}

SERVICE_NEGATIVES = {
    "air_duct_cleaning": ["diy", "vacuum", "rental", "machine", "kit", "cheap", "amazon", ...],
    # ... more services
}

def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", text.lower()))

def is_relevant(service: str, keyword: str, enforce_geo: bool = True) -> bool:
    """Token-based relevance check."""
    tokens = tokenize(keyword)
    seed_tokens = {token for phrase in SERVICE_SEEDS[service] for token in tokenize(phrase)}
    negative_tokens = set(SERVICE_NEGATIVES[service])
    geo_tokens = {"austin", "tx", "texas"}

    # Geographic enforcement
    if enforce_geo and not tokens & geo_tokens:
        return False

    # Must contain seed token
    if not tokens & seed_tokens:
        return False

    # Must not contain negative
    if tokens & negative_tokens:
        return False

    return True
```

---

## Review CLI

```python
def approve_keywords_interactively():
    """Interactive CLI for bulk keyword approval."""
    pending = get_pending_reviews(conn)

    print(f"--- Keyword Approval ({len(pending)} pending) ---")
    for i, kw in enumerate(pending, 1):
        print(f"{i}. {kw['keyword']}")

    print("\nInstructions:")
    print("  - 'y' approve all, 'n' reject all, 's' skip")
    print("  - Enter numbers/ranges: '1,3,5-7'")

    while True:
        user_input = input("\nChoice: ").lower()

        if user_input == 'y':
            # Approve all
            for kw in pending:
                cursor.execute(
                    "UPDATE discovered_keywords SET status = 'approved' WHERE id = ?",
                    (kw["id"],)
                )
            break
        elif user_input == 'n':
            # Reject all
            for kw in pending:
                cursor.execute(
                    "UPDATE discovered_keywords SET status = 'rejected' WHERE id = ?",
                    (kw["id"],)
                )
            break

        # Parse selection (1,3,5-7)
        selected = parse_selection(user_input, len(pending))
        if selected:
            action = input("Approve (a) or Reject (r)? ").lower()
            if action == 'a':
                for idx in selected:
                    # Approve selected
                    ...
            elif action == 'r':
                for idx in selected:
                    # Reject and add to negatives
                    ...
```

---

## Auto-Discovery Integration

```python
def google_autocomplete(q: str, service: str, conn, **kw):
    """Fetch autocomplete, save relevant keywords."""
    data = get_or_fetch(conn, "google_autocomplete", {"q": q, **kw})

    if "suggestions" in data:
        for suggestion in data["suggestions"]:
            phrase = suggestion["value"]
            if is_relevant(service, phrase, enforce_geo=False):
                save_discovered_keyword(conn, service, "google_autocomplete", q, phrase)
    return data

def google_related_questions(q: str, service: str, conn, **kw):
    """Fetch PAA, save relevant keywords."""
    data = get_or_fetch(conn, "google_related_questions", {"q": q, **kw})

    if "related_questions" in data:
        for question in data["related_questions"]:
            phrase = question.get("question", "")
            if is_relevant(service, phrase, enforce_geo=False):
                save_discovered_keyword(conn, service, "google_related_questions", q, phrase)
    return data
```

---

## What's Good / Usable

1. **Service-based filtering** - Seed + negative token matching
2. **Geographic enforcement** - Optional location filter
3. **Interactive CLI** - Bulk selection with ranges
4. **Rejected → Negatives** - Learning from rejections
5. **Auto-discovery** - Keywords saved during API calls

---

## Cross-Repo Comparison

| Feature | SEO | Market_AI | Others |
|---------|-----|-----------|--------|
| Keyword filter | Token-based | None | None |
| Review CLI | Interactive | HITL gate | None |
| Auto-discovery | Yes | None | None |
| Negatives learning | Yes | None | None |

**Recommendation**: UNIQUE - Only repo with keyword discovery workflow. Use for AutoBiz SEO features.
