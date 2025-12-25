---
id: 20251201_ai_llm_autobiz
type: extraction
subject: ai_llm
source_repo: Auto-Biz
description: "LLM model factory, URL classification from Auto-Biz"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [ai, llm, ollama, classification, auto-biz]
---

# SUBJECT: ai_llm/

**Source Repository**: Auto-Biz (https://github.com/idkny/Auto-Biz)
**Extracted From**: `rag/model_factory.py`, `rag/url_classifier.py`, `rag/rag_main.py`

---

## 1. EXTRACTED CODE

### 1.1 Model Factory (LangChain)

```python
"""Factory for creating LLM instances based on configuration."""

from typing import Any

from langchain_community.llms import Ollama
from langchain_openai import ChatOpenAI

from config import RAG_CONFIG


def get_model_for_task(task_name: str) -> Any:
    """Create and return a LangChain chat model instance."""
    task_config = RAG_CONFIG["tasks"].get(task_name)
    if not task_config:
        raise ValueError(f"No RAG configuration found for task: {task_name}")

    llm_provider = task_config.get("llm_provider")
    model_name = task_config.get("model_name")
    temperature = task_config.get("temperature", 0.7)

    if llm_provider == "openai":
        return ChatOpenAI(model_name=model_name, temperature=temperature)
    elif llm_provider == "ollama":
        return Ollama(model=model_name, temperature=temperature)
    else:
        raise ValueError(f"Unsupported LLM provider: {llm_provider}")
```

### 1.2 URL Classifier (Hybrid Rule + ML)

```python
"""URL classification logic for determining page types."""

import logging
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class RuleBasedClassifier:
    """Classifies URLs based on predefined rules, whitelists, blacklists."""

    def __init__(
        self,
        whitelist: Optional[Set[str]] = None,
        blacklist: Optional[Set[str]] = None,
        keywords: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        self.whitelist = whitelist if whitelist is not None else set()
        self.blacklist = blacklist if blacklist is not None else set()
        self.keywords = keywords if keywords is not None else {}

    def classify(self, url: str, html_content: str) -> tuple[Optional[str], Optional[str]]:
        """Applies rules to classify the URL. Returns (decision, rule_label)."""
        if any(whitelisted in url for whitelisted in self.whitelist):
            return "crawl_site", "whitelisted_domain"
        if any(blacklisted in url for blacklisted in self.blacklist):
            return "skip", "blacklisted_domain"

        for label, kws in self.keywords.items():
            if any(kw in html_content for kw in kws):
                return "single_page", f"keyword_match_{label}"

        return None, None


class FormatClassifier:
    """Classifies HTML content using a pre-trained model."""

    def __init__(self, token: Optional[str] = None) -> None:
        model_id = "KnutJaegersberg/website-classifier"
        # Placeholder for HuggingFace pipeline
        logger.warning("Hugging Face pipeline is a placeholder.")

    def classify(self, html_content: str) -> tuple[str, float]:
        """Classifies the HTML content. Returns (label, confidence)."""
        return "unknown", 0.5  # Placeholder


class PageTypeDecider:
    """Decides page type by combining rule-based and format-based classification."""

    def __init__(self, rule_clf: RuleBasedClassifier, format_clf: FormatClassifier) -> None:
        self.rule_clf = rule_clf
        self.format_clf = format_clf

    def decide_page_type(self, url: str, html_content: str) -> tuple[str, dict[str, Any]]:
        """Decides page type. Returns (final_decision, details_dict)."""
        rule_decision, rule_label = self.rule_clf.classify(url, html_content)
        format_label, format_confidence = self.format_clf.classify(html_content)

        details = {
            "rule_decision": rule_decision,
            "rule_label": rule_label,
            "format_label": format_label,
            "format_confidence": format_confidence,
        }

        if rule_decision:
            return rule_decision, details

        if format_confidence > 0.8:
            return format_label, details

        return "unknown", details
```

### 1.3 RAG Main Entry Point

```python
"""Main module for RAG functionalities."""

import logging
from typing import Any

from .url_classifier import FormatClassifier, PageTypeDecider, RuleBasedClassifier

logger = logging.getLogger(__name__)


def classify_url_type(url: str, html_content: str) -> dict[str, Any]:
    """Classifies the type of a URL based on its HTML content."""
    logger.info(f"Classifying URL: {url}")

    rule_classifier = RuleBasedClassifier()
    format_classifier = FormatClassifier()
    page_type_decider = PageTypeDecider(rule_classifier, format_classifier)

    decision, details = page_type_decider.decide_page_type(url, html_content)

    logger.info(f"Classification for {url}: {decision} - Details: {details}")
    return {"decision": decision, "details": details}
```

---

## 2. CONCLUSIONS

### What is Good / Usable

1. **Model Factory**: Clean task-based LLM provider switching
2. **Hybrid Classification**: Rules first, ML fallback with confidence threshold
3. **PageTypeDecider**: Separation of concerns

### What is Outdated

1. **FormatClassifier**: Placeholder, needs real implementation
2. **No JSON mode**: MarketIntel has Ollama JSON mode

### What Must Be Rewritten

1. **Add HuggingFace pipeline**: Real model loading
2. **Add JSON mode support**: For structured output

### Conflicts with Previous Repos

| Pattern | Auto-Biz | MarketIntel | Ollama-Rag | Best |
|---------|----------|-------------|------------|------|
| Model factory | LangChain | Direct Ollama | LangChain | **Auto-Biz** (task-based) |
| JSON mode | No | Yes | No | **MarketIntel** |
| Classification | Rule + ML | Confidence-based | N/A | **Auto-Biz** (hybrid) |
| RAG | Placeholder | No | Yes (hybrid) | **Ollama-Rag** |
| Embeddings | No | No | HuggingFace BGE | **Ollama-Rag** |

### Best Version Recommendation

**MERGE**: Auto-Biz model factory + MarketIntel JSON mode + Ollama-Rag RAG
- Auto-Biz: Model factory pattern, hybrid classification
- MarketIntel: JSON mode, confidence-based decisions
- Ollama-Rag: Actual RAG implementation with embeddings
