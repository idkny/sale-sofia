---
id: 20251201_utils_market_ai
type: extraction
subject: utils
source_repo: Market_AI
description: "PII masking utility for email and phone redaction"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [utils, pii, privacy, redaction, compliance]
---

# SUBJECT: utils/

**Source Repository**: Market_AI (https://github.com/idkny/Market_AI)
**Extracted From**: `utils.py` (27 lines)

---

## 1. EXTRACTED CODE

### 1.1 PII Masking Function

```python
import re
from typing import Any, Dict, List

def mask_pii(data: Any) -> Any:
    """
    Recursively traverses a data structure (like a dict or list) and masks
    strings that look like email addresses or phone numbers.

    Args:
        data: The data to process (can be a dict, list, or primitive).

    Returns:
        The processed data with PII masked.
    """
    if isinstance(data, dict):
        return {k: mask_pii(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [mask_pii(item) for item in data]
    elif isinstance(data, str):
        # Mask emails
        data = re.sub(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '[EMAIL_REDACTED]',
            data
        )
        # Mask U.S. phone numbers (various formats)
        data = re.sub(
            r'(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})',
            '[PHONE_REDACTED]',
            data
        )
        return data
    else:
        return data
```

---

## 2. WHAT'S GOOD / USABLE

| Component | Value | Notes |
|-----------|-------|-------|
| **Recursive traversal** | HIGH | Works on nested dicts/lists |
| **Email regex** | HIGH | Standard email pattern |
| **Phone regex** | HIGH | Multiple US formats supported |
| **Type-safe** | HIGH | Handles dict, list, str, other |
| **Non-destructive** | HIGH | Returns new data, doesn't modify input |

---

## 3. WHAT'S OUTDATED

| Component | Issue | Fix |
|-----------|-------|-----|
| US phone only | Doesn't handle international | Add international patterns |
| No SSN masking | Missing | Add SSN regex |
| No credit card masking | Missing | Add CC regex |
| No address masking | Missing | Add address detection |

---

## 4. HOW IT FITS INTO AUTOBIZ

**Direct Port Candidates:**
1. mask_pii function for compliance
2. Recursive traversal pattern

**Integration Points:**
- `autobiz/core/utils/privacy.py` - Privacy utilities
- `autobiz/tools/data/` - Pre-insert data sanitization
- `autobiz/pipelines/` - Output sanitization before logging

---

## 5. CONFLICTS WITH EXISTING EXTRACTIONS

| Pattern | Market_AI | Existing | Resolution |
|---------|-----------|----------|------------|
| PII masking | mask_pii | None | **USE Market_AI** - unique |
| Utils | mask_pii only | Auto-Biz (Loguru, Xvfb) | **MERGE** - both |

---

## 6. BEST VERSION RECOMMENDATION

**Market_AI's mask_pii is UNIQUE** - no other repo has PII handling.

**Recommended enhancements:**
1. Add SSN pattern: `\b\d{3}-\d{2}-\d{4}\b`
2. Add credit card pattern (Luhn checksum)
3. Add international phone support
4. Add configurable replacement strings
5. Add whitelist for allowed patterns

---

## 7. EXTENDED VERSION (Recommended)

```python
import re
from typing import Any

PII_PATTERNS = {
    'email': (
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '[EMAIL_REDACTED]'
    ),
    'phone_us': (
        r'(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4})',
        '[PHONE_REDACTED]'
    ),
    'ssn': (
        r'\b\d{3}-\d{2}-\d{4}\b',
        '[SSN_REDACTED]'
    ),
    'credit_card': (
        r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
        '[CC_REDACTED]'
    ),
}

def mask_pii(data: Any, patterns: dict = None) -> Any:
    """
    Recursively masks PII in data structures.

    Args:
        data: Data to process
        patterns: Optional custom patterns dict
    """
    patterns = patterns or PII_PATTERNS

    if isinstance(data, dict):
        return {k: mask_pii(v, patterns) for k, v in data.items()}
    elif isinstance(data, list):
        return [mask_pii(item, patterns) for item in data]
    elif isinstance(data, str):
        for name, (pattern, replacement) in patterns.items():
            data = re.sub(pattern, replacement, data)
        return data
    else:
        return data
```
