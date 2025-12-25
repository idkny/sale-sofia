---
id: ai_llm_bg_estate
type: extraction
subject: ai_llm
source_repo: Bg-Estate
description: "Task-based LLM model factory with multi-provider support + URL classifier"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [ai, llm, langchain, classifier, multi-provider, bg-estate]
---

# AI/LLM Extraction: Bg-Estate

**Source**: `idkny/Bg-Estate`
**Files**: `rag/model_factory.py`, `rag/url_classifier.py`, `rag/rag_main.py`, `utils/wikipedia_enricher.py`

---

## Overview

Task-based LLM configuration with:
- **Model Factory** - Task → Provider → Model mapping
- **Multi-provider** - OpenAI, Google Gemini, Ollama
- **URL Classifier** - Rule-based + ML-based (HuggingFace)
- **Wikipedia Enricher** - Domain enrichment via Wikipedia API

---

## Task-Based Model Factory

```python
from langchain_community.chat_models import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from config import RAG_CONFIG

def get_model_for_task(task_name: str):
    """Create LangChain model based on task config."""
    task_config = RAG_CONFIG["tasks"].get(task_name)
    if not task_config:
        raise ValueError(f"No config for task: {task_name}")

    provider_name = task_config["provider"]
    model_name = task_config["model"]
    temperature = task_config["temperature"]

    provider_config = RAG_CONFIG["providers"].get(provider_name)

    if provider_name == "openai":
        return ChatOpenAI(model=model_name, temperature=temperature)
    elif provider_name == "google":
        return ChatGoogleGenerativeAI(model=model_name, temperature=temperature)
    elif provider_name == "ollama":
        return ChatOllama(
            base_url=provider_config["base_url"],
            model=model_name,
            temperature=temperature,
        )
    else:
        raise NotImplementedError(f"Provider '{provider_name}' not supported.")
```

---

## RAG Config Structure

```python
RAG_CONFIG = {
    "active_provider": "google",
    "providers": {
        "openai": {"api_key_env": "OPENAI_API_KEY"},
        "google": {"api_key_env": "GOOGLE_API_KEY"},
        "ollama": {"base_url": "http://localhost:11434"},
    },
    "tasks": {
        "url_classification": {
            "provider": "google",
            "model": "gemini-1.5-flash",
            "prompt_template": "rag/prompts/url_classification_prompt.txt",
            "temperature": 0.1,
        },
        "listing_normalization": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.3,
        },
        "another_task": {
            "provider": "ollama",
            "model": "llama3",
            "temperature": 0.5,
        },
    },
}
```

---

## URL Classifier (Rule + ML Hybrid)

```python
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

class RuleBasedClassifier:
    """URL classification via rules, whitelists, blacklists."""

    def __init__(self, whitelist=None, blacklist=None, keywords=None):
        self.whitelist = whitelist or set()
        self.blacklist = blacklist or set()
        self.keywords = keywords or {"estate", "apartments", "homes"}
        self.block_extensions = {".pdf", ".xml", ".rss", ".doc", ".zip"}

    def classify(self, url: str) -> str:
        domain = tldextract.extract(url).domain.lower()

        if domain in self.blacklist:
            return "skip"
        if domain in self.whitelist:
            return "crawl_site"
        if any(url.endswith(ext) for ext in self.block_extensions):
            return "skip"
        if any(k in url.lower() for k in self.keywords):
            return "maybe"
        return "skip"


class FormatClassifier:
    """ML-based HTML format classification using HuggingFace model."""

    def __init__(self):
        model_id = "KnutJaegersberg/website-classifier"
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_id)
        self.model.to(self.device)
        self.model.eval()

    def classify(self, html: str) -> tuple[str, float]:
        text = self._clean_html(html)[:5000]
        inputs = self.tokenizer(text, truncation=True, padding=True, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model(**inputs.to(self.device))
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1).squeeze()
        confidence, idx = torch.max(probs, dim=0)
        label = self.model.config.id2label[idx.item()]
        return label, confidence.item()


class PageTypeDecider:
    """Combines rule + ML classification."""

    def decide(self, url, html=None):
        rule_label = self.rule_clf.classify(url)
        if rule_label == "skip":
            return "skip", {"source": "rule"}

        if not html:
            return "single_page", {"source": "rule-fallback"}

        format_label, confidence = self.format_clf.classify(html)

        if format_label in ["Shopping", "Business", "Society"]:
            return "crawl_site", {...}
        elif format_label in ["News", "Arts", "Health"]:
            return "single_page", {...}
        else:
            return "skip", {...}
```

---

## Wikipedia Enricher

```python
class WikipediaEnricher:
    """Enriches domains with Wikipedia-derived labels."""

    def __init__(self, lang="en"):
        self.base_url = f"https://{lang}.wikipedia.org/w/api.php"

    def enrich_domain(self, url: str) -> str | None:
        domain = tldextract.extract(url).domain
        page_title = self._search_page(domain)
        if not page_title:
            return None

        summary = self._get_page_summary(page_title)
        if summary:
            if "real estate" in summary.lower():
                return "real estate portal"
            if "classifieds" in summary.lower():
                return "classifieds site"
            if "news" in summary.lower():
                return "news site"
        return None
```

---

## What's Good / Usable

1. **Task-based model selection** - Different models for different tasks
2. **Multi-provider support** - OpenAI, Google, Ollama
3. **Hybrid classification** - Rule + ML combination
4. **HuggingFace integration** - Pre-trained website classifier
5. **Wikipedia enrichment** - Domain context via API

---

## Cross-Repo Comparison

| Feature | Bg-Estate | Auto-Biz | Market_AI |
|---------|-----------|----------|-----------|
| Model factory | Task-based | Task-based | Model slots |
| Providers | 3 (OpenAI, Google, Ollama) | 1 (Ollama) | 1 (Ollama) |
| URL classifier | Rule + HuggingFace ML | None | None |
| Wikipedia | Yes | No | No |

**Recommendation**: Bg-Estate has the best task-based model factory. Use for AutoBiz multi-provider support.
