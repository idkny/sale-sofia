---
id: nlp_competitor_intel
type: extraction
subject: nlp
source_repo: Competitor-Intel
description: "4-method NLP keyword extraction suite: KeyBERT, YAKE, RAKE, Gensim"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [nlp, keywords, keybert, yake, rake, gensim, seo, competitor-intel]
---

# NLP Extraction: Competitor-Intel

**Source**: `idkny/Competitor-Intel`
**Files**: `competitor_intel/nlp/main.py`, `phrases_keybert.py`, `phrases_yake.py`, `phrases_rake.py`, `phrases_gensim.py`, `tokenize.py`

---

## Overview

**UNIQUE IN CODEBASE** - Only repository with multi-method NLP keyword extraction.

4 extraction methods:
1. **KeyBERT** - Transformer-based (BERT embeddings)
2. **YAKE** - Statistical, unsupervised
3. **RAKE** - Rapid Automatic Keyword Extraction
4. **Gensim** - Phrase detection (bigrams + trigrams)

---

## Main Orchestrator

```python
import sqlite3
from typing import Dict, Tuple

from competitor_intel.nlp.phrases_gensim import mine_phrases_gensim
from competitor_intel.nlp.phrases_yake import mine_phrases_yake
from competitor_intel.nlp.phrases_rake import mine_phrases_rake
from competitor_intel.nlp.phrases_keybert import mine_phrases_keybert
from competitor_intel.nlp.tokenize import tokenize

def phrase_mining(
    conn: sqlite3.Connection,
    nlp_cfg: Dict[str, float | int] | None = None
) -> Tuple[int, int, int, int]:
    """Run all 4 NLP methods on extracted text."""

    nlp_cfg = nlp_cfg or {
        "gensim_min_count": 4,
        "gensim_threshold": 10.0,
        "yake_topk": 20,
        "rake_max_words": 4,
        "keybert_topk": 20
    }

    cur = conn.execute("SELECT page_url, text FROM texts")
    docs = cur.fetchall()
    if not docs:
        return (0, 0, 0, 0)

    # Prepare tokenized corpus for Gensim
    tokenized_docs = []
    doc_index = []
    for page_url, text in docs:
        tokens = tokenize(text or "")
        if tokens:
            tokenized_docs.append(tokens)
            doc_index.append(page_url)

    # Run all methods
    bigram_ct, trigram_ct = mine_phrases_gensim(conn, tokenized_docs, doc_index, nlp_cfg)
    yake_ct = mine_phrases_yake(conn, docs, nlp_cfg)
    rake_ct = mine_phrases_rake(conn, docs, nlp_cfg)
    kb_ct = mine_phrases_keybert(conn, docs, nlp_cfg)

    return bigram_ct, trigram_ct, yake_ct, rake_ct
```

---

## 1. KeyBERT - Transformer-Based Extraction

```python
import sqlite3
from typing import Dict, List

def mine_phrases_keybert(
    conn: sqlite3.Connection,
    docs: List,
    nlp_cfg: Dict[str, float | int]
) -> int:
    """Extract keywords using BERT embeddings."""
    kb_ct = 0
    try:
        from keybert import KeyBERT

        kb = KeyBERT()
        topk = int(nlp_cfg.get("keybert_topk", 20))

        for page_url, text in docs:
            if not text:
                continue
            try:
                kw = kb.extract_keywords(
                    text,
                    keyphrase_ngram_range=(1, 4),  # 1 to 4 word phrases
                    stop_words="english",
                    top_n=topk
                )
            except Exception:
                continue

            for phrase, score in kw:
                n = max(1, len(phrase.split()))
                conn.execute(
                    "INSERT INTO phrases(page_url, phrase, n, method, score, freq) VALUES(?,?,?,?,?,?)",
                    (page_url, phrase, n, "keybert", float(score), None)
                )
                kb_ct += 1
        conn.commit()
    except Exception:
        # Optional - if model not installed, skip silently
        pass
    return kb_ct
```

**Key Features**:
- Uses BERT embeddings for semantic similarity
- `keyphrase_ngram_range=(1, 4)` - extracts 1-4 word phrases
- Returns similarity scores (0-1 range)

---

## 2. YAKE - Statistical Keyword Extraction

```python
import sqlite3
from typing import Dict, List

def mine_phrases_yake(
    conn: sqlite3.Connection,
    docs: List,
    nlp_cfg: Dict[str, float | int]
) -> int:
    """Extract keywords using YAKE (unsupervised statistical method)."""
    yake_ct = 0
    try:
        import yake

        kw_extractor = yake.KeywordExtractor(top=int(nlp_cfg["yake_topk"]))

        for page_url, text in docs:
            if not text:
                continue
            try:
                kws = kw_extractor.extract_keywords(text)
            except Exception:
                continue

            for phrase, score in kws:
                n = max(1, len(phrase.split()))
                conn.execute(
                    "INSERT INTO phrases(page_url, phrase, n, method, score, freq) VALUES(?,?,?,?,?,?)",
                    (page_url, phrase, n, "yake", float(score), None)
                )
                yake_ct += 1
        conn.commit()
    except Exception:
        pass
    return yake_ct
```

**Key Features**:
- Unsupervised (no training data needed)
- Fast, language-agnostic
- Lower score = more relevant (inverted scoring)

---

## 3. RAKE - Rapid Automatic Keyword Extraction

```python
import contextlib
import sqlite3
from typing import Dict, List

def mine_phrases_rake(
    conn: sqlite3.Connection,
    docs: List,
    nlp_cfg: Dict[str, float | int]
) -> int:
    """Extract keywords using RAKE algorithm."""
    rake_ct = 0
    try:
        from rake_nltk import Rake
        import nltk

        with contextlib.suppress(Exception):
            nltk.download("stopwords", quiet=True)

        rake = Rake()

        for page_url, text in docs:
            if not text:
                continue
            try:
                rake.extract_keywords_from_text(text)
                ranked = rake.get_ranked_phrases_with_scores()
            except Exception:
                continue

            for score, phrase in ranked[:50]:  # Limit to top 50
                n = max(1, len(phrase.split()))
                conn.execute(
                    "INSERT INTO phrases(page_url, phrase, n, method, score, freq) VALUES(?,?,?,?,?,?)",
                    (page_url, phrase, n, "rake", float(score), None)
                )
                rake_ct += 1
        conn.commit()
    except Exception:
        pass
    return rake_ct
```

**Key Features**:
- Uses word co-occurrence
- Higher score = more relevant
- NLTK stopwords integration

---

## 4. Gensim - Phrase Detection (Bigrams/Trigrams)

```python
import sqlite3
from typing import Dict, List, Tuple

def mine_phrases_gensim(
    conn: sqlite3.Connection,
    tokenized_docs: List[List[str]],
    doc_index: List[str],
    nlp_cfg: Dict[str, float | int]
) -> Tuple[int, int]:
    """Detect collocations using Gensim Phrases."""
    bigram_ct = trigram_ct = 0
    try:
        from gensim.models.phrases import Phrases, Phraser

        # Build bigram model
        phrases_bigram = Phrases(
            tokenized_docs,
            min_count=int(nlp_cfg["gensim_min_count"]),
            threshold=float(nlp_cfg["gensim_threshold"])
        )
        bigram_phraser = Phraser(phrases_bigram)
        bigrammed = [bigram_phraser[doc] for doc in tokenized_docs]

        # Build trigram model on bigrammed corpus
        phrases_trigram = Phrases(
            bigrammed,
            min_count=int(nlp_cfg["gensim_min_count"]),
            threshold=float(nlp_cfg["gensim_threshold"])
        )
        trigram_phraser = Phraser(phrases_trigram)

        # Extract phrases per document
        for page_url, doc in zip(doc_index, tokenized_docs):
            # Bigrams: words joined with underscore
            bi = [w for w in bigram_phraser[doc] if "_" in w]
            # Trigrams: 2+ underscores
            tri = [w for w in trigram_phraser[bigram_phraser[doc]] if w.count("_") >= 2]

            for p in bi:
                conn.execute(
                    "INSERT INTO phrases(page_url, phrase, n, method, score, freq) VALUES(?,?,?,?,?,?)",
                    (page_url, p.replace("_", " "), 2, "gensim", None, 1)
                )
                bigram_ct += 1

            for p in tri:
                conn.execute(
                    "INSERT INTO phrases(page_url, phrase, n, method, score, freq) VALUES(?,?,?,?,?,?)",
                    (page_url, p.replace("_", " "), 3, "gensim", None, 1)
                )
                trigram_ct += 1
        conn.commit()
    except Exception:
        pass
    return bigram_ct, trigram_ct
```

**Key Features**:
- Statistical collocation detection
- Builds hierarchical models (bigram → trigram)
- Uses underscore joining (`air_duct_cleaning`)

---

## Tokenizer

```python
import re
from typing import List

STOPWORDS = set("""
    a an the and or for with without to of in on at by from as is are was were be have has had
    this that these those it its it's we you they i our your their not more most other some any
    each every such can will just than then so if when while where how
""".split())

def tokenize(text: str) -> List[str]:
    """Simple tokenizer with stopword removal."""
    text = text.lower()
    # Keep alphanumeric with hyphens and apostrophes
    tokens = re.findall(r"[a-z0-9][a-z0-9\-']+", text)
    return [t for t in tokens if t not in STOPWORDS]
```

---

## What's Good / Usable

1. **Multi-method approach** - Different algorithms for different use cases
2. **Graceful degradation** - Silently skips unavailable libraries
3. **Configurable parameters** - `nlp_cfg` dict for tuning
4. **Database integration** - Results stored with method attribution
5. **N-gram tracking** - Stores phrase length for filtering

---

## What's Outdated

1. **No caching** - KeyBERT model loaded fresh each run
2. **No batch processing** - Processes one doc at a time
3. **Silent failures** - Swallows exceptions without logging

---

## What Must Be Rewritten

1. Add **model caching** for KeyBERT:
   ```python
   _kb_model = None
   def get_keybert():
       global _kb_model
       if _kb_model is None:
           _kb_model = KeyBERT()
       return _kb_model
   ```

2. Add **batch processing** for efficiency:
   ```python
   # KeyBERT supports batch extraction
   kb.extract_keywords(docs_list, ...)
   ```

3. Add **logging** for debugging:
   ```python
   logger.info(f"Extracted {kb_ct} keywords with KeyBERT")
   ```

---

## How It Fits AutoBiz

- **Content analysis** - Extract keywords from scraped business data
- **SEO optimization** - Identify target keywords
- **Topic modeling** - Understand what competitors focus on
- **Search enhancement** - Build keyword indexes

---

## Cross-Repo Comparison

| Feature | Competitor-Intel | Market_AI | Others |
|---------|------------------|-----------|--------|
| NLP methods | 4 (KeyBERT, YAKE, RAKE, Gensim) | None | None |
| Phrase storage | phrases table | None | None |
| Usage mapping | phrase_usage table | None | None |

**Recommendation**: UNIQUE - Use Competitor-Intel's NLP suite for all keyword extraction in AutoBiz. Only repo with this capability.

---

## Dependencies

```
keybert>=0.7.0
yake>=0.4.8
rake-nltk>=1.0.6
gensim>=4.3.0
nltk>=3.8.0
```
