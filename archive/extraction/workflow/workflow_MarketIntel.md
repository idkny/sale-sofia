---
id: 20251201_workflow_marketintel
type: extraction
subject: workflow
description: "Pipeline orchestration and registry patterns from MarketIntel"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [workflow, pipeline, registry, orchestration, marketintel, extraction]
source_repo: idkny/MarketIntel
---

# Workflow/Pipeline Extraction: MarketIntel

**Source**: `idkny/MarketIntel`
**File**: `src/main.py`

---

## Conclusions

### What's Good (MEDIUM-HIGH PRIORITY)

| Pattern | Description | Use For |
|---------|-------------|---------|
| Registry pattern | Map endpoint names to functions | Zoho API routing |
| Discovery pipeline | Fetch → Extract → Classify → Save | Data ingestion |
| Resilient iteration | Try/except per item, continue | Batch processing |
| Dual-mode CLI | `cycle` vs `query` modes | Batch vs single ops |
| Key=value parser | Simple CLI arg parsing | Admin scripts |

### What to Skip

- SERP-specific discovery functions
- Location-based iteration

---

## Pattern 1: Endpoint Registry

```python
from typing import Callable

# Registry maps endpoint names to callable functions
REGISTRY: dict[str, Callable[..., dict]] = {
    # CRM endpoints
    "crm_contacts": api.get_contacts,
    "crm_deals": api.get_deals,
    "crm_leads": api.get_leads,

    # Books endpoints
    "books_invoices": api.get_invoices,
    "books_payments": api.get_payments,

    # Inventory endpoints
    "inventory_items": api.get_items,
    "inventory_orders": api.get_orders,

    # Composed endpoints
    "full_customer_view": api.get_customer_with_invoices,
}


def call_endpoint(endpoint: str, **params) -> dict:
    """Call registered endpoint by name."""
    if endpoint not in REGISTRY:
        raise ValueError(f"Unknown endpoint: {endpoint}. Available: {list(REGISTRY.keys())}")

    func = REGISTRY[endpoint]
    return func(**params)
```

**Benefits**:
- Decouples endpoint names from implementation
- Easy to add new endpoints
- Supports dynamic routing

---

## Pattern 2: Discovery Pipeline

```python
def process_discovered_item(conn, item_text: str, source: str, base_query: str):
    """
    Pipeline: Classify item -> Decide status -> Save to DB.
    """
    # 1. Classify using AI/rules
    category, confidence = classify_item(item_text)

    # 2. Decide status based on confidence
    THRESHOLD = 0.85

    if category in ["relevant", "core"] and confidence >= THRESHOLD:
        status = "approved"
    elif category == "irrelevant" and confidence >= THRESHOLD:
        status = "rejected"
    else:
        status = "pending_review"

    # 3. Save with classification metadata
    db.get_or_insert_item(
        conn=conn,
        text=item_text,
        category=category,
        confidence=confidence,
        status=status,
        source=source,
        base_query=base_query
    )

    logging.info(f"Processed: '{item_text[:30]}...' -> {status}")
```

---

## Pattern 3: Resilient Batch Processing

```python
def run_batch_cycle(conn, items: list, locations: list):
    """
    Process items in batch with error resilience.
    Errors on individual items don't stop the batch.
    """
    logging.info(f"Starting batch: {len(items)} items x {len(locations)} locations")

    success_count = 0
    error_count = 0

    for location in locations:
        if not location.active:
            continue

        logging.info(f"Processing location: {location.name}")

        for item in items:
            try:
                # Process single item
                result = process_item(conn, item, location)
                success_count += 1

            except Exception as e:
                # Log error but continue to next item
                logging.error(f"Error processing {item}: {e}")
                error_count += 1
                continue  # Don't fail entire batch

    logging.info(f"Batch complete: {success_count} success, {error_count} errors")
    return {"success": success_count, "errors": error_count}
```

**Key**: `continue` after error keeps batch running.

---

## Pattern 4: Multi-Source Discovery

```python
def discover_new_items(conn, base_queries: list):
    """
    Discover items from multiple sources.
    Each source feeds into the classification pipeline.
    """
    sources = [
        ("api_endpoint_1", discover_from_source_1),
        ("api_endpoint_2", discover_from_source_2),
        ("api_endpoint_3", discover_from_source_3),
    ]

    for base_query in base_queries:
        for source_name, discover_func in sources:
            try:
                logging.info(f"Discovering from {source_name} for '{base_query}'")
                discover_func(conn, base_query)
            except Exception as e:
                logging.error(f"Discovery error ({source_name}): {e}")
                continue


def discover_from_source_1(conn, base_query: str):
    """Discover items from API source 1."""
    response = api.call_endpoint_1(query=base_query)

    if "items" in response:
        for item in response["items"]:
            process_discovered_item(
                conn=conn,
                item_text=item["text"],
                source="api_endpoint_1",
                base_query=base_query
            )
```

---

## Pattern 5: Dual-Mode CLI

```python
import sys
import json


def main():
    """Entry point with dual modes: batch cycle or single query."""

    if len(sys.argv) < 2:
        print("Usage: python main.py [cycle|query]")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "cycle":
        # Batch mode: run full processing cycle
        run_full_cycle()

    elif mode == "query":
        # Single query mode: call one endpoint
        endpoint, params = parse_query_args(sys.argv[2:])
        result = call_endpoint(endpoint, **params)
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)


def run_full_cycle():
    """Run complete batch processing cycle."""
    conn = get_db_connection()
    try:
        init_db(conn)

        # Get approved items from previous runs
        approved = db.get_items_by_status(conn, "approved")

        # Run batch processing
        run_batch_cycle(conn, approved, get_active_locations())

        # Discover new items
        discover_new_items(conn, get_base_queries())

    finally:
        conn.close()

    logging.info("Cycle complete")
```

---

## Pattern 6: Key=Value Argument Parser

```python
def _coerce(v: str):
    """Convert string to appropriate Python type."""
    # Boolean
    if v.lower() in ("true", "false"):
        return v.lower() == "true"

    # Integer
    if v.isdigit() or (v.startswith("-") and v[1:].isdigit()):
        try:
            return int(v)
        except:
            pass

    # Float
    try:
        if "." in v:
            return float(v)
    except:
        pass

    # Strip quotes
    if (v.startswith('"') and v.endswith('"')) or \
       (v.startswith("'") and v.endswith("'")):
        return v[1:-1]

    return v


def parse_query_args(argv: list) -> tuple[str, dict]:
    """
    Parse CLI args in format: endpoint key=value key=value ...

    Example:
        python main.py query crm_contacts per_page=100 modified_since=2024-01-01
    """
    if len(argv) < 1:
        raise ValueError("Missing endpoint name")

    endpoint = argv[0]
    params = {}

    for arg in argv[1:]:
        if "=" not in arg:
            raise ValueError(f"Bad arg '{arg}'. Use key=value format.")
        k, v = arg.split("=", 1)
        params[k] = _coerce(v)

    return endpoint, params


# Usage:
# python main.py query crm_contacts per_page=100 active=true
# -> endpoint="crm_contacts", params={"per_page": 100, "active": True}
```

---

## AutoBiz Adaptation

```python
# autobiz/pipelines/orchestrator.py

ZOHO_REGISTRY = {
    "sync_contacts": sync_crm_contacts,
    "sync_deals": sync_crm_deals,
    "sync_invoices": sync_books_invoices,
    "full_sync": run_full_sync,
}


def run_autobiz_cycle(conn):
    """AutoBiz batch processing cycle."""

    # 1. Sync from Zoho (fetch new/updated records)
    for sync_name, sync_func in ZOHO_REGISTRY.items():
        if sync_name.startswith("sync_"):
            try:
                sync_func(conn)
            except Exception as e:
                logging.error(f"Sync error ({sync_name}): {e}")
                continue

    # 2. Process pending items
    pending = db.get_items_by_status(conn, "pending_review")
    for item in pending:
        try:
            process_item(conn, item)
        except Exception as e:
            logging.error(f"Process error: {e}")
            continue

    # 3. Execute approved actions
    approved = db.get_items_by_status(conn, "approved")
    for item in approved:
        try:
            execute_action(conn, item)
        except Exception as e:
            logging.error(f"Action error: {e}")
            continue
```
