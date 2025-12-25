---
id: 20251201_ai_llm_marketintel
type: extraction
subject: ai_llm
description: "Ollama client and AI classification patterns from MarketIntel"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [ai, llm, ollama, classification, marketintel, extraction]
source_repo: idkny/MarketIntel
---

# AI/LLM Extraction: MarketIntel

**Source**: `idkny/MarketIntel`
**Files**: `src/ai_clients.py`, `src/keyword_classifier.py`

---

## Conclusions

### What's Good (HIGH PRIORITY)

| Pattern | Description | Use For |
|---------|-------------|---------|
| Abstract AIClient | Provider-agnostic interface | Swap LLM providers |
| OllamaClient | Local LLM with JSON mode | AutoBiz AI tools |
| Factory pattern | Get client by config | Multi-provider setup |
| Hybrid classification | Rules first, AI fallback | Efficient classification |
| Confidence scoring | Return (category, score) | Auto-approve decisions |

### What to Adapt

- Change system prompt for Zoho context
- Add more categories (Zoho entity types)
- Consider adding LangChain wrapper

---

## Pattern 1: Abstract AI Client

```python
import abc

class AIClient(abc.ABC):
    """Abstract base class for AI providers."""

    @abc.abstractmethod
    def classify(self, text: str) -> tuple[str, float]:
        """
        Classify text into a category.

        Returns:
            tuple: (category, confidence_score)
            Returns ('uncertain', 0.0) on failure.
        """
        pass
```

---

## Pattern 2: Ollama Client (LOCAL LLM)

```python
import json
import logging
import requests

class OllamaClient(AIClient):
    """Client for local Ollama LLM server."""

    def __init__(self, base_url: str, model: str, timeout: int = 60):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.api_url = f"{self.base_url.rstrip('/')}/api/chat"
        logging.info(f"Initialized OllamaClient: {model} at {base_url}")

    def classify(self, text: str) -> tuple[str, float]:
        """Send classification request to Ollama."""

        system_prompt = """
        You are an expert classification system.
        Classify the input into one of these categories:
        - "relevant": Directly related to the task
        - "indirect": Tangentially related
        - "irrelevant": Not related at all
        - "uncertain": Cannot determine

        Respond with JSON only:
        {"category": "...", "confidence": 0.0-1.0}
        """

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "stream": False,
            "format": "json"  # Force JSON output
        }

        try:
            response = requests.post(self.api_url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            content_str = response.json().get('message', {}).get('content', '')
            if not content_str:
                logging.error("Empty response from Ollama")
                return "uncertain", 0.0

            parsed = json.loads(content_str)
            category = parsed.get("category")
            confidence = parsed.get("confidence")

            if category and isinstance(confidence, (float, int)):
                logging.info(f"Classified '{text[:30]}...' as '{category}' ({confidence:.2f})")
                return category, float(confidence)
            else:
                logging.error(f"Malformed response: {parsed}")
                return "uncertain", 0.0

        except requests.RequestException as e:
            logging.error(f"Ollama request failed: {e}")
            return "uncertain", 0.0
        except json.JSONDecodeError as e:
            logging.error(f"JSON parse error: {e}")
            return "uncertain", 0.0
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return "uncertain", 0.0
```

**Key Features**:
- `format: "json"` forces structured output
- Graceful fallback to ("uncertain", 0.0)
- Timeout handling

---

## Pattern 3: Mock Client (Testing)

```python
class MockAIClient(AIClient):
    """Mock client for testing without LLM."""

    def __init__(self, model: str = "mock", **kwargs):
        self.model = model
        logging.info(f"Initialized MockAIClient")

    def classify(self, text: str) -> tuple[str, float]:
        """Rule-based mock classification."""
        text_lower = text.lower()

        if "cost" in text_lower or "price" in text_lower:
            return "relevant", 0.92
        if "weather" in text_lower or "movie" in text_lower:
            return "irrelevant", 0.95

        return "uncertain", 0.60
```

---

## Pattern 4: Factory with Registry

```python
# Config
ACTIVE_AI_PROVIDER = "ollama"

AI_PROVIDERS = {
    "mock": {
        "model": "mock"
    },
    "ollama": {
        "base_url": "http://localhost:11434",
        "model": "gemma:2b",
        "timeout": 60
    }
}

# Registry
CLIENT_MAP = {
    "mock": MockAIClient,
    "ollama": OllamaClient,
}


def get_ai_client() -> AIClient:
    """Factory function to get configured AI client."""
    provider_name = ACTIVE_AI_PROVIDER
    client_class = CLIENT_MAP.get(provider_name)

    if not client_class:
        raise ValueError(f"Unknown provider: {provider_name}")

    config = AI_PROVIDERS.get(provider_name)
    if not config:
        raise ValueError(f"Missing config for: {provider_name}")

    return client_class(**config)


# Singleton instance (reuse across calls)
try:
    ai_client = get_ai_client()
except ValueError as e:
    logging.error(f"Failed to init AI client: {e}")
    ai_client = None
```

---

## Pattern 5: Hybrid Classification

```python
# Rule-based keywords (fast, high confidence)
CORE_KEYWORDS = ["invoice", "payment", "customer", "order"]
INDIRECT_KEYWORDS = ["report", "analytics", "dashboard"]

CONFIDENCE_THRESHOLD = 0.85


def classify_item(text: str) -> tuple[str, float]:
    """
    Hybrid classification: rules first, AI fallback.
    """
    text_lower = text.lower()

    # 1. Rule-based (fast, deterministic)
    for phrase in CORE_KEYWORDS:
        if phrase in text_lower:
            logging.info(f"Rule match: '{phrase}' -> relevant")
            return "relevant", 0.99

    for phrase in INDIRECT_KEYWORDS:
        if phrase in text_lower:
            logging.info(f"Rule match: '{phrase}' -> indirect")
            return "indirect", 0.95

    # 2. AI fallback (slower, flexible)
    if ai_client is None:
        logging.warning("AI client unavailable")
        return "uncertain", 0.0

    logging.info(f"No rule match, using AI for: '{text[:30]}...'")
    category, confidence = ai_client.classify(text)

    # Validate category
    valid_categories = {"relevant", "indirect", "irrelevant", "uncertain"}
    if category not in valid_categories:
        logging.warning(f"Unexpected category: {category}")
        return "uncertain", 0.0

    return category, confidence
```

---

## Pattern 6: Confidence-Based Automation

```python
def process_item(conn, item_text: str, source: str):
    """
    Classify item and auto-decide status based on confidence.
    """
    category, confidence = classify_item(item_text)

    # Auto-approve if high confidence + relevant
    if category in ["relevant", "indirect"] and confidence >= CONFIDENCE_THRESHOLD:
        status = "approved"

    # Auto-reject if high confidence + irrelevant
    elif category == "irrelevant" and confidence >= CONFIDENCE_THRESHOLD:
        status = "rejected"

    # Manual review for everything else
    else:
        status = "pending_review"

    # Save with classification metadata
    save_item(
        conn=conn,
        text=item_text,
        category=category,
        confidence=confidence,
        status=status,
        source=source
    )

    logging.info(f"'{item_text[:30]}...' -> {category} ({confidence:.2f}) -> {status}")
```

---

## AutoBiz Adaptation

```python
# Zoho-specific classification

ZOHO_SYSTEM_PROMPT = """
You are an expert Zoho data classifier.
Classify the input into one of these categories:
- "crm_contact": Customer or lead data
- "crm_deal": Sales opportunity data
- "books_invoice": Invoice or billing data
- "books_payment": Payment transaction
- "inventory_item": Product or stock data
- "uncertain": Cannot determine

Respond with JSON only:
{"category": "...", "confidence": 0.0-1.0}
"""

class ZohoClassifier(OllamaClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.system_prompt = ZOHO_SYSTEM_PROMPT
```
