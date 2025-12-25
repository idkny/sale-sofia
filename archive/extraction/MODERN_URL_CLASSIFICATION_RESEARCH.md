---
id: 20251205_171745_MODERN_URL_CLASSIFICATION_RESEARCH
type: guide
subject: url-classification-techniques
description: |
  Comprehensive research on modern URL classification techniques (2023-2025).
  Covers LLM-based classification, embeddings, hybrid systems, content extraction,
  production patterns, and open-source tools. Includes practical recommendations
  for improving our 3-layer classifier (Rules → LLM → Chunked Voting) with
  Qwen2.5:0.5b on GTX 960M (4GB VRAM).
created_at: 2025-12-05
updated_at: 2025-12-05
tags: [classification, llm, embeddings, url-analysis, research, qwen, ollama, optimization]
---

# Modern URL Classification Techniques (2023-2025)

**Research Date:** December 5, 2025
**Target System:** AutoBiz URL Classifier (Rules → LLM → Chunked Voting)
**Current Model:** Qwen2.5:0.5b via Ollama on GTX 960M (4GB VRAM)

---

## Executive Summary

This document compiles state-of-the-art URL and webpage classification techniques from 2023-2025 research. Each technique is evaluated for:
- **Practical implementation** with our existing 3-layer system
- **Complexity** (Easy/Medium/Hard)
- **Compatibility** with small models (Qwen2.5:0.5b, 4GB VRAM)
- **Expected impact** on classification accuracy and efficiency

---

## 1. Modern LLM-Based Classification

### 1.1 Few-Shot vs Zero-Shot Prompting

#### How It Works
- **Zero-shot**: Direct task instruction without examples. Model relies purely on pre-training.
- **Few-shot**: Include 2-8 labeled examples in the prompt to guide the model.
- **Research Finding**: First 8 examples have the most impact; diminishing returns after that.

#### Best Practices ([Nyckel](https://www.nyckel.com/blog/llms-for-classification-best-practices-and-benchmarks/), [PromptingGuide](https://www.promptingguide.ai/techniques/zeroshot))
- Zero-shot accuracy is generally poor for classification tasks
- **Few-shot dramatically improves performance** with minimal data
- Include `text_type` context (e.g., "product listing page", "company homepage")
- Set temperature=0 for deterministic classification outputs
- Provide "Other" option for ambiguous cases

#### Implementation Complexity: **Easy**
```python
# Few-shot prompt template
prompt = """Classify the following webpage as: product_listing, company_info, blog, or other.

Examples:
- "Shop All Products | Auto Parts Store" → product_listing
- "About Us - Company History" → company_info
- "Latest Industry News - Blog" → blog

URL: {url}
Page Title: {title}
Main Headings: {headings}
Classification:"""
```

#### Impact on Our System
- **Replace zero-shot with 3-5 shot prompts** in Layer 2 (LLM classification)
- Store canonical examples per category in config
- Expected accuracy improvement: **+15-20%** for edge cases

#### Qwen2.5:0.5b Considerations
- Small models benefit MORE from few-shot than large models
- Keep examples concise (token limits)
- Use consistent formatting for all examples

---

### 1.2 Chain-of-Thought (CoT) Prompting

#### How It Works
Models perform better when they "think out loud" before classifying. Instead of direct classification, ask the model to:
1. Identify key features
2. Reason about what they indicate
3. Make final classification

#### Research Findings ([OpenAI](https://openai.com/index/introducing-structured-outputs-in-the-api/), [Dev.to](https://dev.to/aphanite/less-is-more-when-prompting-2ie4))
- CoT improves accuracy by **60% on complex tasks** (GSM8k benchmark)
- Combine CoT with JSON structured output for reliability
- Include `reasoning` field BEFORE final classification in JSON schema
- **Field naming matters**: "potential_answers" + "final_answer" performs better than "potential_final_choice" + "final_choice"

#### Implementation Complexity: **Medium**

```python
# CoT with structured JSON output (Ollama)
schema = {
    "type": "object",
    "properties": {
        "observations": {
            "type": "string",
            "description": "Key features noticed in URL/content"
        },
        "reasoning": {
            "type": "string",
            "description": "Step-by-step logic for classification"
        },
        "confidence": {
            "type": "number",
            "description": "Confidence score 0-100"
        },
        "final_classification": {
            "type": "string",
            "enum": ["product_listing", "company_info", "blog", "other"]
        }
    },
    "required": ["observations", "reasoning", "confidence", "final_classification"]
}

response = ollama.chat(
    model="qwen2.5:0.5b",
    messages=[{"role": "user", "content": prompt}],
    format=schema  # Ollama structured outputs
)
```

#### Impact on Our System
- Add CoT to Layer 2 (LLM) for high-uncertainty cases
- Use `observations` + `reasoning` to debug misclassifications
- Enables explainable classifications for human review

#### Qwen2.5:0.5b Considerations
- Small models can still benefit from CoT
- Keep reasoning concise (avoid verbose explanations)
- May add 20-30% inference time

---

### 1.3 Confidence Calibration

#### How It Works
LLMs report confidence scores that often don't match actual accuracy. Techniques to improve calibration:

1. **Self-Consistency**: Generate multiple responses at higher temperature, select most common answer
2. **Redundancy + Confidence Threshold**: Only accept classifications with N repetitions above threshold
3. **Stable Explanations**: Measure consistency of reasoning across multiple runs

#### Research Findings ([NAACL 2024 Survey](https://aclanthology.org/2024.naacl-long.366/), [HDSR](https://hdsr.mitpress.mit.edu/pub/jaqt0vpb))
- LLMs are generally **overconfident** (report high confidence on incorrect answers)
- Self-consistency is most reliable calibration strategy
- Combining redundancy with confidence thresholds **increases accuracy** but has cost
- Better models show more aligned confidence, but even best models have minimal variation between correct/incorrect

#### Implementation Complexity: **Medium**

```python
def classify_with_calibration(url, title, content, num_samples=3, threshold=70):
    """Generate multiple classifications and measure consistency."""
    results = []

    for _ in range(num_samples):
        response = ollama.chat(
            model="qwen2.5:0.5b",
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.7}  # Higher temp for diversity
        )
        results.append(response['final_classification'])

    # Self-consistency: most common classification
    from collections import Counter
    vote_counts = Counter(results)
    winner, count = vote_counts.most_common(1)[0]
    confidence = (count / num_samples) * 100

    if confidence >= threshold:
        return winner, confidence
    else:
        return "uncertain", confidence
```

#### Impact on Our System
- Use in Layer 3 (Chunked Voting) as tie-breaker
- Route low-confidence cases to human review
- Expected: **Reduce false positives by 30-40%**

#### Qwen2.5:0.5b Considerations
- Small models benefit from self-consistency
- 3-5 samples is optimal (more is diminishing returns)
- Batch inference to minimize latency

---

### 1.4 Ollama Structured Outputs (JSON Schema)

#### How It Works
Ollama (v0.5+) uses GBNF grammars from llama.cpp to **constrain model outputs** to valid JSON matching your schema. Invalid tokens are masked during sampling.

#### Research Findings ([Ollama Blog](https://ollama.com/blog/structured-outputs), [Daniel Clayton](https://blog.danielclayton.co.uk/posts/ollama-structured-outputs/))
- Guarantees valid JSON structure (no parsing errors)
- Schema-specific grammar generation (not generic JSON)
- **Performance trade-off**: Grammar sampling adds overhead (not GPU-accelerated)
- Does NOT validate semantic correctness (model can still output nonsense that matches schema)

#### Implementation Complexity: **Easy**

```python
import ollama
from pydantic import BaseModel

class Classification(BaseModel):
    category: str  # One of: product_listing, company_info, blog, other
    confidence: float  # 0-100
    reasoning: str

response = ollama.chat(
    model='qwen2.5:0.5b',
    messages=[{'role': 'user', 'content': prompt}],
    format=Classification.model_json_schema()
)

# Parse with Pydantic for validation
result = Classification.model_validate_json(response['message']['content'])
```

#### Impact on Our System
- **Eliminate JSON parsing errors** in Layer 2 (currently ~5% failure rate?)
- Simplify error handling code
- Enable strict typing for downstream processing

#### Qwen2.5:0.5b Considerations
- Grammar sampling overhead is **model-agnostic** (same for all models)
- Keep schemas simple (fewer fields = faster)
- Use `temperature=0` for structured output (more deterministic)

---

## 2. Embedding-Based Approaches

### 2.1 URL/Content Embeddings for Semantic Similarity

#### How It Works
Convert URLs and page content into dense vector representations using embedding models. Similar pages have similar embeddings (measured by cosine similarity).

#### Research Findings ([Screaming Frog](https://www.screamingfrog.co.uk/seo-spider/tutorials/how-to-identify-semantically-similar-pages-outliers/), [MDPI](https://www.mdpi.com/2073-8994/15/2/395))
- BERT-based embeddings capture semantic meaning beyond keywords
- Can detect near-duplicate content and topical outliers
- Embeddings enable **clustering** of similar pages
- Pre-trained models (e.g., Sentence-BERT) work well without fine-tuning

#### Tools Available
- **sentence-transformers** (Python): Pre-trained models like `all-MiniLM-L6-v2`
- **FAISS** (Facebook AI Similarity Search): Efficient similarity search in millions of vectors
- **Chroma**: Lightweight vector DB for prototyping

#### Implementation Complexity: **Medium**

```python
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Load lightweight embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')  # 80MB, fast on CPU

# Create embeddings from labeled examples
labeled_texts = [
    "Shop All Auto Parts | Discount Store",  # product_listing
    "About Our Company - 50 Years of Service",  # company_info
    "Latest Industry Trends - Blog Post"  # blog
]
labels = ["product_listing", "company_info", "blog"]

embeddings = model.encode(labeled_texts)

# Build FAISS index
dimension = embeddings.shape[1]  # 384 for all-MiniLM-L6-v2
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# Classify new URL by finding nearest neighbor
new_url_text = "Automotive Tools Online Store | Buy Now"
new_embedding = model.encode([new_url_text])
distances, indices = index.search(new_embedding, k=1)

predicted_label = labels[indices[0][0]]
similarity_score = 1 / (1 + distances[0][0])  # Convert distance to similarity
```

#### Impact on Our System
- Add as **Layer 1.5** (between Rules and LLM)
- Use embeddings for **fast pre-filtering** before expensive LLM call
- Build reference embeddings from labeled examples
- If similarity > 0.85, skip LLM and return matched category

#### Qwen2.5:0.5b Considerations
- Embeddings run on CPU (no GPU memory needed)
- `all-MiniLM-L6-v2` is lightweight and fast
- Can complement small LLM without memory issues

---

### 2.2 Vector Databases (FAISS vs Chroma)

#### Comparison

| Feature | FAISS | Chroma |
|---------|-------|--------|
| **Speed** | Fastest (1.81s for 50 queries) | Slower (2.18s for 50 queries) |
| **GPU Support** | Yes (5-10x faster) | No |
| **Ease of Use** | Low-level API | High-level, beginner-friendly |
| **Persistence** | Manual save/load | Built-in (SQLite backend) |
| **Metadata** | Basic | Rich (store labels, timestamps, etc.) |
| **Best For** | Large-scale production | Prototyping, small-scale |

([RisingWave](https://risingwave.com/blog/chroma-db-vs-pinecone-vs-faiss-vector-database-showdown/), [MyScale](https://www.myscale.com/blog/faiss-vs-chroma-vector-storage-battle/))

#### Implementation Complexity: **Medium-Hard**

**FAISS**: Requires manual index management, but maximum performance.
**Chroma**: Drop-in replacement with persistence and metadata.

```python
# Chroma example (easier)
import chromadb
from sentence_transformers import SentenceTransformer

# Initialize Chroma with local persistence
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("url_classifications")

# Add labeled examples with metadata
model = SentenceTransformer('all-MiniLM-L6-v2')
texts = ["Shop Auto Parts", "About Company"]
embeddings = model.encode(texts).tolist()

collection.add(
    embeddings=embeddings,
    documents=texts,
    metadatas=[{"label": "product_listing"}, {"label": "company_info"}],
    ids=["1", "2"]
)

# Query for similar URLs
query_embedding = model.encode(["Buy Car Tools Online"]).tolist()
results = collection.query(
    query_embeddings=query_embedding,
    n_results=1
)
predicted_label = results['metadatas'][0][0]['label']
```

#### Impact on Our System
- Start with **Chroma for prototyping** (easier)
- Migrate to **FAISS if scaling** (1000s of URLs)
- Store classified URLs to improve future classifications
- Enable "did you mean this category?" suggestions

#### Qwen2.5:0.5b Considerations
- Vector DBs run independently of LLM
- No VRAM impact (CPU-based)
- Can cache classifications to reduce LLM calls by 40-60%

---

## 3. Hybrid Classification Systems

### 3.1 Cascading Classifiers (Cheap → Expensive)

#### How It Works
Use a multi-stage pipeline where fast/cheap methods filter before expensive methods:

1. **Stage 1: Rule-based** (regex, keywords) - Free, instant
2. **Stage 2: Embedding similarity** - Cheap (~10ms), no LLM
3. **Stage 3: Small LLM** (Qwen2.5:0.5b) - Moderate cost (~200ms)
4. **Stage 4: Large LLM** (GPT-4, optional) - Expensive, high accuracy

Only proceed to next stage if confidence is below threshold.

#### Research Findings ([Wikipedia](https://en.wikipedia.org/wiki/Cascading_classifiers), [Medium](https://medium.com/@lad.jai/the-hybrid-approach-combining-llms-and-non-llms-for-nlp-success-c07a1d0e14f8))
- Cascading enables "successive refinement" of classification
- Each stage adds complexity only when needed
- Combines **speed of rules** with **accuracy of LLMs**
- Non-LLM models (decision trees, logistic regression) are more interpretable

#### Implementation Complexity: **Medium**

```python
class CascadingClassifier:
    def __init__(self):
        self.rules = RuleBasedClassifier()
        self.embeddings = EmbeddingClassifier()
        self.llm = LLMClassifier()

    def classify(self, url, title, content):
        # Stage 1: Rule-based (instant)
        result, confidence = self.rules.classify(url, title)
        if confidence > 95:
            return result, confidence, "rules"

        # Stage 2: Embedding similarity (~10ms)
        result, confidence = self.embeddings.classify(title, content)
        if confidence > 85:
            return result, confidence, "embeddings"

        # Stage 3: Small LLM (~200ms)
        result, confidence = self.llm.classify(url, title, content)
        return result, confidence, "llm"
```

#### Impact on Our System
- **Exactly matches our current 3-layer architecture!**
- Add embeddings as intermediate stage (Layer 1.5)
- Set confidence thresholds per stage: Rules (95%), Embeddings (85%), LLM (70%)
- Expected: **60% of classifications bypass LLM** (faster + cheaper)

#### Qwen2.5:0.5b Considerations
- Small LLM is already efficient (good for Stage 3)
- Optimize Stages 1-2 to reduce LLM load
- Monitor stage distribution (should be: 40% rules, 30% embeddings, 30% LLM)

---

### 3.2 Ensemble Methods (Voting)

#### How It Works
Combine predictions from multiple classifiers using voting:

- **Hard Voting**: Each classifier votes for one class; majority wins
- **Soft Voting**: Average probabilities across classifiers; highest avg wins
- **Weighted Voting**: Assign higher weights to better-performing classifiers

#### Research Findings ([Towards Data Science](https://towardsdatascience.com/ensemble-of-classifiers-voting-classifier-ef7f6a5b7795/), [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0305054824002119))
- Ensembles reduce risk of poorly performing classifier
- Cross-efficiency weights (from DEA) outperform equal weights
- Self-consistency (single model, multiple runs) often beats multi-model ensembles
- **Veto voting** has better recall for security tasks (one "malicious" vote blocks)

#### Implementation Complexity: **Easy-Medium**

```python
from collections import Counter

def weighted_voting(classifiers, weights, url, title, content):
    """Combine multiple classifier predictions with weights."""
    votes = []

    for classifier, weight in zip(classifiers, weights):
        prediction = classifier.classify(url, title, content)
        # Add vote 'weight' times
        votes.extend([prediction] * weight)

    # Majority vote
    vote_counts = Counter(votes)
    winner, count = vote_counts.most_common(1)[0]
    confidence = (count / len(votes)) * 100

    return winner, confidence
```

#### Impact on Our System
- **Already using voting in Layer 3** (Chunked Voting)!
- Add weighted voting (weight by historical accuracy per chunk type)
- Consider "veto" rule for critical misclassifications
- Expected: **+5-10% accuracy** from optimal weighting

#### Qwen2.5:0.5b Considerations
- Voting requires multiple inference passes (3-5x slower)
- Use only for high-value classifications
- Batch inference to amortize cost

---

## 4. Content Extraction Best Practices

### 4.1 Trafilatura vs Readability

#### Performance Comparison

| Metric | Trafilatura | Readability |
|--------|-------------|-------------|
| **Mean F1** | **0.937 (best)** | 0.89 |
| **Precision** | **0.978 (best)** | 0.92 |
| **Recall** | 0.89 | **0.929 (best)** |
| **Consistency** | Good overall | Best predictability |
| **Speed** | Fast | Fast |

([Sandia Labs 2024](https://www.osti.gov/servlets/purl/2429881), [Chuniversiteit](https://chuniversiteit.nl/papers/comparison-of-web-content-extraction-algorithms))

**Key Finding**: Ensemble of Readability + Trafilatura + Goose3 (weighted voting) **outperforms any single extractor**.

#### When to Use Which

- **Trafilatura**: Best precision (removes nearly all boilerplate). Use for classification.
- **Readability**: Best recall + most robust across page types. Use for content analysis.
- **Ensemble**: Best overall. Vote between extractors or use Trafilatura as primary, fallback to Readability.

#### Implementation Complexity: **Easy**

```python
import trafilatura
from readability import Document

def extract_content(html):
    """Extract main content using Trafilatura with Readability fallback."""

    # Try Trafilatura first (best precision)
    content = trafilatura.extract(html, include_comments=False)

    if content and len(content) > 100:
        return content, "trafilatura"

    # Fallback to Readability (better recall)
    doc = Document(html)
    content = doc.summary(html_partial=True)
    text = trafilatura.extract(content)  # Clean Readability output with Trafilatura

    return text, "readability"
```

#### Impact on Our System
- **Use Trafilatura as primary** (already using?)
- Add Readability fallback for JS-heavy pages
- Expected: **+10-15% extraction success rate**

#### Qwen2.5:0.5b Considerations
- Extraction runs on CPU (no VRAM impact)
- Better extraction = better LLM input = higher accuracy
- Cleaner content = fewer tokens = faster inference

---

### 4.2 Optimal Content for Classification

#### What to Extract

Research shows these elements are most valuable for classification:

1. **Page Title** (highest signal-to-noise ratio)
2. **Main Headings** (H1, H2) - structure indicators
3. **First paragraph** - usually describes purpose
4. **Meta description** (if available)
5. **URL structure** (path segments, query params)

**Avoid**: Long paragraphs, footers, navigation, ads (add noise)

#### Optimal Text Length for LLM Classification

- **Minimum**: 50-100 words (title + headings + snippet)
- **Optimal**: 200-300 words (enough context, not overwhelming)
- **Maximum**: 500 words (token limits, diminishing returns)

#### Implementation Complexity: **Easy**

```python
def prepare_classification_input(html, url):
    """Extract optimal content for classification."""

    # Parse with BeautifulSoup
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Extract key elements
    title = soup.find('title').get_text() if soup.find('title') else ''
    h1 = [h.get_text() for h in soup.find_all('h1')]
    h2 = [h.get_text() for h in soup.find_all('h2')][:3]  # Top 3 H2s
    meta_desc = ''
    if soup.find('meta', attrs={'name': 'description'}):
        meta_desc = soup.find('meta', attrs={'name': 'description'})['content']

    # Main content (first 300 words)
    content = trafilatura.extract(html, include_comments=False)
    content_snippet = ' '.join(content.split()[:300]) if content else ''

    # Format for LLM
    formatted = f"""
URL: {url}
Title: {title}
H1: {', '.join(h1)}
H2: {', '.join(h2)}
Description: {meta_desc}
Content Preview: {content_snippet}
""".strip()

    return formatted
```

#### Impact on Our System
- **Reduce input tokens by 50-70%** (faster + cheaper)
- Focus LLM on high-signal content
- Expected: **+10% accuracy** from better input quality

---

## 5. Production Patterns

### 5.1 Caching Strategies

#### Types of Caching

1. **Exact Match Caching**: Cache by URL hash (fast, simple)
2. **Semantic Caching**: Cache by embedding similarity (handles variations)
3. **Prefix Caching**: Cache common prompt prefixes (system message, examples)
4. **KV Caching**: Cache LLM internal states (built into llama.cpp)

#### Research Findings ([Redis](https://redis.io/blog/what-is-semantic-caching/), [ML Journey](https://mljourney.com/batching-and-caching-strategies-for-high-throughput-llm-inference/))
- Semantic caching reduces computational demands by 40-60%
- Similarity threshold tuning is critical (too tight = low hit rate, too loose = wrong answers)
- Prefix caching saves 30-50% of prompt processing time
- KV caching is essential for multi-turn conversations (less relevant for classification)

#### Implementation Complexity: **Medium**

```python
import hashlib
import json
from datetime import datetime, timedelta

class SemanticCache:
    def __init__(self, similarity_threshold=0.92):
        self.cache = {}  # {embedding_hash: {result, timestamp}}
        self.embeddings = {}  # {embedding_hash: embedding_vector}
        self.threshold = similarity_threshold
        self.ttl = timedelta(days=30)  # Cache invalidation

    def get(self, embedding):
        """Check if similar classification exists in cache."""
        import numpy as np

        for cached_hash, cached_embedding in self.embeddings.items():
            # Compute cosine similarity
            similarity = np.dot(embedding, cached_embedding) / (
                np.linalg.norm(embedding) * np.linalg.norm(cached_embedding)
            )

            if similarity >= self.threshold:
                cached_data = self.cache[cached_hash]
                # Check TTL
                if datetime.now() - cached_data['timestamp'] < self.ttl:
                    return cached_data['result'], similarity

        return None, 0

    def set(self, embedding, result):
        """Store classification result with embedding."""
        embedding_hash = hashlib.sha256(embedding.tobytes()).hexdigest()
        self.embeddings[embedding_hash] = embedding
        self.cache[embedding_hash] = {
            'result': result,
            'timestamp': datetime.now()
        }
```

#### Impact on Our System
- Start with **simple URL hash caching** (Day 1)
- Add **semantic caching** for near-duplicate URLs (Week 2)
- Expected cache hit rate: 40-50% (2x speedup on cached requests)

#### Qwen2.5:0.5b Considerations
- Caching benefits smaller models MORE (inference is already slow)
- Store embeddings in SQLite for persistence
- Monitor cache hit rate (aim for 50%+)

---

### 5.2 Batch Processing

#### How It Works
Process multiple URLs in parallel to maximize GPU utilization. Techniques:

1. **Static Batching**: Fixed batch size (e.g., 8 URLs)
2. **Dynamic Batching**: Accumulate requests for N milliseconds, then process batch
3. **Continuous Batching**: Stream new requests into running batch (advanced)
4. **Priority-Based Batching**: Separate queues for high/low priority

#### Research Findings ([Latitude Blog](https://latitude-blog.ghost.io/blog/scaling-llms-with-batch-processing-ultimate-guide/))
- Batching increases throughput from 200 to 1,500 tokens/sec (LLaMA2-70B)
- Reduces cost by up to 40%
- Small models benefit less (already fast), but still 20-30% speedup
- Priority queues minimize latency for critical requests

#### Implementation Complexity: **Medium-Hard**

```python
import asyncio
from collections import deque

class BatchProcessor:
    def __init__(self, batch_size=8, timeout_ms=100):
        self.batch_size = batch_size
        self.timeout = timeout_ms / 1000
        self.queue = deque()
        self.processing = False

    async def add(self, url, title, content):
        """Add URL to batch queue."""
        future = asyncio.Future()
        self.queue.append((url, title, content, future))

        # Trigger batch if full or timeout
        if len(self.queue) >= self.batch_size:
            await self._process_batch()
        else:
            # Schedule timeout
            asyncio.create_task(self._timeout_handler())

        return await future

    async def _process_batch(self):
        """Process accumulated batch."""
        if self.processing or len(self.queue) == 0:
            return

        self.processing = True
        batch = [self.queue.popleft() for _ in range(min(self.batch_size, len(self.queue)))]

        # Batch inference
        prompts = [self._create_prompt(url, title, content) for url, title, content, _ in batch]
        results = await self._batch_classify(prompts)

        # Resolve futures
        for (_, _, _, future), result in zip(batch, results):
            future.set_result(result)

        self.processing = False

    async def _timeout_handler(self):
        """Process batch after timeout."""
        await asyncio.sleep(self.timeout)
        await self._process_batch()
```

#### Impact on Our System
- Implement for **bulk classification jobs** (e.g., 1000 URLs)
- For real-time (single URL), batching adds latency (skip)
- Expected: **2-3x throughput** for batch jobs

#### Qwen2.5:0.5b Considerations
- Small models have lower GPU utilization (benefit less from batching)
- Use batch_size=4-8 (larger batches = OOM on 4GB VRAM)
- Monitor VRAM usage with `nvidia-smi`

---

### 5.3 Confidence Thresholds & Human-in-the-Loop

#### How It Works
Route low-confidence classifications to human review instead of auto-deciding.

**Typical Thresholds**:
- **High confidence** (85-100%): Auto-approve
- **Medium confidence** (60-85%): Flag for review
- **Low confidence** (<60%): Reject, require human labeling

#### Research Findings ([ArXiv](https://arxiv.org/html/2406.12114v1), [IntuitionLabs](https://intuitionlabs.ai/articles/active-learning-hitl-llms))
- Active learning with uncertainty sampling reduces labeling costs by 50-70%
- Human-in-the-loop achieves optimal cost-accuracy balance
- Focus human effort on **uncertain cases** (steepest learning curve)
- Small models benefit MORE from human feedback (less prior knowledge)

#### Implementation Complexity: **Easy**

```python
def classify_with_review(url, title, content, confidence_threshold=75):
    """Classify with human review for low-confidence cases."""

    result, confidence, source = classifier.classify(url, title, content)

    if confidence >= confidence_threshold:
        # Auto-approve
        store_classification(url, result, confidence, auto=True)
        return result
    else:
        # Queue for human review
        review_queue.add({
            'url': url,
            'predicted': result,
            'confidence': confidence,
            'timestamp': datetime.now()
        })
        return "pending_review"
```

#### Impact on Our System
- Start with **threshold=75%** (adjust based on data)
- Build simple review queue (SQLite table)
- Use reviewed classifications to **improve model** (active learning)
- Expected: **90%+ accuracy** on auto-approved classifications

#### Qwen2.5:0.5b Considerations
- Small models have **lower calibration** (confidence less reliable)
- Use **self-consistency** to improve confidence estimates
- Monitor precision at different thresholds (calibration curve)

---

## 6. Open Source Tools & Libraries

### 6.1 Python Libraries for Text Classification

#### scikit-learn
**Use Case**: Traditional ML classifiers (baseline)

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

# Simple TF-IDF + Logistic Regression baseline
baseline = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=1000)),
    ('clf', LogisticRegression(max_iter=1000))
])

baseline.fit(train_texts, train_labels)
predictions = baseline.predict(test_texts)
```

**Complexity**: Easy | **Speed**: Fast (10-50ms) | **Accuracy**: Moderate (70-80%)

---

#### SetFit (Sentence Transformers + sklearn)
**Use Case**: Few-shot learning with minimal labeled data

([HuggingFace](https://github.com/huggingface/setfit))

```python
from setfit import SetFitModel, SetFitTrainer

# Train with just 8 examples per class
model = SetFitModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

trainer = SetFitTrainer(
    model=model,
    train_dataset=train_dataset,  # Only 8 examples per class!
    eval_dataset=eval_dataset
)

trainer.train()
predictions = model.predict(test_texts)
```

**Complexity**: Medium | **Speed**: Fast (50-100ms) | **Accuracy**: High (85-90% with 8 examples)

**Why SetFit?**
- Achieves RoBERTa-Large accuracy with 8 examples vs 3000
- No prompts/verbalizers needed
- 10x faster than fine-tuning large models
- Multilingual support

---

#### Small-Text (Active Learning)
**Use Case**: Label only the most informative examples

([ArXiv](https://arxiv.org/html/2107.10314))

```python
from small_text import TransformerBasedClassificationFactory
from small_text.integrations.pytorch.classifiers import KimCNN
from small_text.query_strategies import RandomSampling, LeastConfidence

# Start with small labeled set
classifier_factory = TransformerBasedClassificationFactory(
    'sentence-transformers/all-MiniLM-L6-v2',
    num_classes=4
)

# Use uncertainty sampling to select examples to label
query_strategy = LeastConfidence()
indices_to_label = query_strategy.query(unlabeled_pool, n=10)

# Human labels these 10, model retrains, repeats
```

**Complexity**: Hard | **Speed**: Medium | **Accuracy**: High (with iterative labeling)

---

### 6.2 HuggingFace Models

#### MarkupLM (Microsoft)
**Use Case**: Webpage classification using HTML structure + text

([HuggingFace](https://huggingface.co/docs/transformers/en/model_doc/markuplm))

```python
from transformers import MarkupLMProcessor, MarkupLMForSequenceClassification

processor = MarkupLMProcessor.from_pretrained("microsoft/markuplm-base")
model = MarkupLMForSequenceClassification.from_pretrained("microsoft/markuplm-base")

# Use HTML directly (no need to extract text)
inputs = processor(html=html_string, return_tensors="pt")
outputs = model(**inputs)
predicted_class = outputs.logits.argmax(-1)
```

**Complexity**: Hard (requires fine-tuning) | **Speed**: Slow (500ms+) | **Accuracy**: Very High (90%+)

**Trade-off**: More accurate than text-only models, but requires GPU and fine-tuning.

---

#### Pre-trained Classification Models on HuggingFace Hub

Search for `zero-shot-classification` or `text-classification` on [HuggingFace Models](https://huggingface.co/models):

- `facebook/bart-large-mnli`: Zero-shot classification (no training needed)
- `typeform/distilbert-base-uncased-mnli`: Faster zero-shot alternative
- Domain-specific models (search by your domain)

**Warning**: Most require 8GB+ VRAM (won't run on GTX 960M).

---

### 6.3 URL Classification Datasets

- **[snats/url-classifications](https://huggingface.co/datasets/snats/url-classifications)**: 400k URLs classified with Llama3.1 8B
- **Use for**: Bootstrapping labeled data, benchmarking, few-shot examples

---

## 7. Practical Recommendations for Your System

### 7.1 Quick Wins (1-2 Days Implementation)

| Improvement | Expected Impact | Complexity |
|-------------|----------------|------------|
| **Few-shot prompts** (3-5 examples per category) | +15-20% accuracy | Easy |
| **Ollama structured outputs** (JSON schema) | Eliminate parsing errors | Easy |
| **Simple URL caching** (SQLite) | 2x speedup on repeated URLs | Easy |
| **Trafilatura + Readability fallback** | +10% extraction success | Easy |
| **Optimal content extraction** (title + headings + 300 words) | +10% accuracy, 50% faster | Easy |

**Total Expected Impact**: +30-40% accuracy, 1.5-2x speedup

---

### 7.2 Medium-Term Improvements (1-2 Weeks)

| Improvement | Expected Impact | Complexity |
|-------------|----------------|------------|
| **Embedding-based pre-filtering** (Layer 1.5) | 40-60% LLM calls bypassed | Medium |
| **Chain-of-Thought for edge cases** | +10-15% on hard cases | Medium |
| **Semantic caching** | +30-40% cache hit rate | Medium |
| **Confidence thresholds + review queue** | 90%+ precision on auto-approved | Easy-Medium |
| **Weighted voting** (optimize chunk weights) | +5-10% accuracy | Medium |

**Total Expected Impact**: 50-70% cost reduction, +20-30% accuracy

---

### 7.3 Advanced Features (1-2 Months)

| Improvement | Expected Impact | Complexity |
|-------------|----------------|------------|
| **SetFit few-shot classifier** | Match/exceed current LLM accuracy at 10x speed | Hard |
| **Active learning pipeline** | 50-70% reduction in labeling costs | Hard |
| **Batch processing for bulk jobs** | 2-3x throughput | Medium-Hard |
| **Vector DB (Chroma)** | Persistent similarity search, clustering | Medium |
| **MarkupLM fine-tuning** | +10-20% accuracy (if GPU available) | Hard |

**Total Expected Impact**: 10x speedup, approach 95% accuracy

---

### 7.4 Architecture Recommendation

**Proposed 4-Stage Cascading Classifier**:

```
Input (URL + HTML)
    ↓
[Stage 1: Rule-Based]
    95%+ confidence? → DONE (40% of cases)
    ↓ No
[Stage 2: Embedding Similarity]
    85%+ confidence? → DONE (30% of cases)
    ↓ No
[Stage 3: Qwen2.5:0.5b + Few-Shot + CoT]
    75%+ confidence? → DONE (25% of cases)
    ↓ No
[Stage 4: Human Review Queue]
    Manual labeling → Retrain model (5% of cases)
```

**Expected Performance**:
- **Accuracy**: 90%+ (auto-approved), 95%+ (after review)
- **Speed**: 20ms (Stage 1), 50ms (Stage 2), 200ms (Stage 3)
- **Cost**: 70% reduction in LLM calls

---

## 8. Qwen2.5:0.5b Specific Optimizations

### 8.1 Memory Optimizations

**Current Constraints**: 4GB VRAM (GTX 960M)

**Qwen2.5:0.5b Memory Footprint**:
- **FP16**: ~1GB VRAM
- **INT8 (quantized)**: ~500MB VRAM
- **INT4 (aggressive quant)**: ~250MB VRAM

**Recommendations**:
- Use **INT8 quantization** (minimal accuracy loss, 50% memory savings)
- Load model once, keep in VRAM (avoid reload overhead)
- Batch size = 4-8 (monitor with `nvidia-smi`)

```bash
# Quantize Qwen2.5:0.5b to INT8
ollama pull qwen2.5:0.5b-q8_0

# Use in Python
ollama.chat(model='qwen2.5:0.5b-q8_0', ...)
```

---

### 8.2 Inference Optimizations

**Techniques from Research**:
- **vLLM**: Optimized inference engine (requires installation)
- **llama.cpp optimizations**: Built into Ollama (already active)
- **Prefix caching**: Cache common prompt prefixes (system message + examples)

**Implementation**:
```python
# Use consistent system message for prefix caching
SYSTEM_MESSAGE = """You are a URL classifier. Classify webpages into:
- product_listing: Pages selling products
- company_info: About pages, company information
- blog: Blog posts, articles, news
- other: Everything else"""

# Ollama caches this automatically (prefix caching)
response = ollama.chat(
    model='qwen2.5:0.5b',
    messages=[
        {'role': 'system', 'content': SYSTEM_MESSAGE},
        {'role': 'user', 'content': f'Classify: {url}'}
    ]
)
```

**Expected Speedup**: 30-50% on repeated prompts

---

### 8.3 Small Model Best Practices

**Research Findings**: Small models (<1B params) perform better with:

1. **More structure** (few-shot > zero-shot)
2. **Explicit instructions** (step-by-step > implicit)
3. **Constrained outputs** (JSON schema > free-form)
4. **Self-consistency** (multiple runs > single)
5. **Human feedback** (active learning > batch training)

**Anti-patterns for Small Models**:
- ❌ Long prompts (token limits)
- ❌ Complex reasoning (hallucination risk)
- ❌ Open-ended generation (low quality)
- ❌ Zero-shot on rare categories (poor accuracy)

---

## 9. Evaluation & Monitoring

### 9.1 Metrics to Track

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Overall Accuracy** | 90%+ | Precision across all categories |
| **Per-Category Precision** | 85%+ | TP / (TP + FP) per category |
| **Per-Category Recall** | 80%+ | TP / (TP + FN) per category |
| **Confidence Calibration** | ECE < 0.1 | Expected Calibration Error |
| **Average Latency** | <200ms | P50, P95, P99 response times |
| **Cache Hit Rate** | 50%+ | Cached / Total requests |
| **LLM Call Rate** | <40% | LLM calls / Total requests |
| **Review Queue Rate** | <10% | Low-confidence / Total |

---

### 9.2 A/B Testing Framework

```python
class ClassifierExperiment:
    def __init__(self):
        self.variants = {
            'control': CurrentClassifier(),
            'few_shot': FewShotClassifier(),
            'embeddings': EmbeddingClassifier()
        }

    def classify(self, url, title, content, user_id):
        # Assign variant based on user_id hash
        variant = self.get_variant(user_id)
        result = self.variants[variant].classify(url, title, content)

        # Log for analysis
        self.log_result(variant, url, result)
        return result

    def get_variant(self, user_id):
        # 80% control, 10% each variant
        hash_val = hash(user_id) % 100
        if hash_val < 80:
            return 'control'
        elif hash_val < 90:
            return 'few_shot'
        else:
            return 'embeddings'
```

---

## 10. References & Further Reading

### Academic Papers
- [LLMs are One-Shot URL Classifiers and Explainers](https://arxiv.org/html/2409.14306v1) (2024)
- [A Survey of Confidence Estimation and Calibration in Large Language Models](https://aclanthology.org/2024.naacl-long.366/) (NAACL 2024)
- [Enhancing Text Classification through LLM-Driven Active Learning](https://arxiv.org/html/2406.12114v1) (2024)
- [MiniLLM: Knowledge Distillation of Large Language Models](https://arxiv.org/abs/2306.08543) (2024)

### Industry Blogs
- [Classification using LLMs: Best Practices - Nyckel](https://www.nyckel.com/blog/llms-for-classification-best-practices-and-benchmarks/)
- [Structured Outputs in Ollama](https://ollama.com/blog/structured-outputs)
- [Batching and Caching Strategies - ML Journey](https://mljourney.com/batching-and-caching-strategies-for-high-throughput-llm-inference/)
- [Semantic Caching - Redis](https://redis.io/blog/what-is-semantic-caching/)

### Tools & Libraries
- [Trafilatura](https://github.com/adbar/trafilatura): Web content extraction
- [SetFit](https://github.com/huggingface/setfit): Few-shot text classification
- [Chroma](https://www.trychroma.com/): Vector database
- [FAISS](https://github.com/facebookresearch/faiss): Similarity search
- [small-text](https://github.com/webis-de/small-text): Active learning library

### Comparison Studies
- [Comparing HTML Extraction Algorithms - Chuniversiteit](https://chuniversiteit.nl/papers/comparison-of-web-content-extraction-algorithms)
- [FAISS vs Chroma - MyScale](https://www.myscale.com/blog/faiss-vs-chroma-vector-storage-battle/)
- [Main Content Extraction Evaluation - Sandia Labs 2024](https://www.osti.gov/servlets/purl/2429881)

---

## Appendix A: Implementation Checklist

### Phase 1: Quick Wins (Week 1)
- [ ] Convert zero-shot to few-shot prompts (3-5 examples per category)
- [ ] Add Ollama structured outputs (JSON schema)
- [ ] Implement simple URL caching (SQLite)
- [ ] Add Readability fallback for Trafilatura
- [ ] Optimize content extraction (title + headings + 300 words)
- [ ] Add confidence thresholds + review queue
- [ ] Track metrics: accuracy, latency, cache hit rate

### Phase 2: Embedding Layer (Week 2-3)
- [ ] Install sentence-transformers (`all-MiniLM-L6-v2`)
- [ ] Generate embeddings for labeled examples
- [ ] Implement embedding similarity classifier (Layer 1.5)
- [ ] Set up Chroma vector DB (optional)
- [ ] Add semantic caching
- [ ] Tune similarity thresholds (85% for bypass, 92% for cache)

### Phase 3: Advanced Techniques (Week 4+)
- [ ] Implement Chain-of-Thought for low-confidence cases
- [ ] Add self-consistency voting (3-5 samples)
- [ ] Optimize weighted voting in Layer 3
- [ ] Build active learning pipeline
- [ ] Set up batch processing for bulk jobs
- [ ] Fine-tune SetFit model (if needed)

### Phase 4: Monitoring & Iteration (Ongoing)
- [ ] Build evaluation dashboard (accuracy, latency, costs)
- [ ] Set up A/B testing framework
- [ ] Monitor per-category performance
- [ ] Calibrate confidence thresholds
- [ ] Collect human feedback
- [ ] Retrain models monthly

---

**End of Research Document**

*For questions or implementation support, refer to the original research sources linked throughout this document.*
