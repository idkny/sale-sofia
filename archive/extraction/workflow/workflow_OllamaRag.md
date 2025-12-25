---
id: extraction_ollamarag_workflow
type: extraction
subject: workflow
source_repo: Ollama-Rag
description: "RAG pipeline workflow and orchestration patterns from Ollama-Rag"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [extraction, workflow, rag, pipeline, ollamarag, llamaindex]
---

# Workflow Patterns - Ollama-Rag

**Source**: `rag_pipeline.py`, `save_to_md.py`, `benchmark.py`
**Purpose**: RAG query pipeline, data export, benchmarking
**Status**: PRODUCTION-READY patterns, but missing persistence

---

## 1. RAG Query Pipeline

### Main Entry Point

```python
# Source: rag_pipeline.py:41-44
def run_query_with_context(query):
    """
    Execute a query against the RAG pipeline.
    Returns: (answer_text, [source_contexts])
    """
    engine = setup_retriever()
    response = engine.query(query)
    return response.response, [node.node.text for node in response.source_nodes]
```

### Pipeline Setup (Hybrid Retrieval)

```python
# Source: rag_pipeline.py:11-39
def setup_retriever():
    config = load_config("config/config.yaml")

    # Health check with auto-restart
    try:
        check_ollama_health()
    except:
        print("Ollama not running. Attempting to start...")
        restart_ollama()
        check_ollama_health()

    llm = configure_llm(config)

    # Document ingestion
    documents = SimpleDirectoryReader("data").load_data()
    parser = SimpleNodeParser()
    nodes = parser.get_nodes_from_documents(documents)

    # Build BOTH retrievers (hybrid)
    vector_index = VectorStoreIndex(nodes)
    bm25_retriever = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=3)
    vector_retriever = VectorIndexRetriever(index=vector_index, similarity_top_k=3)

    # Combine with weights
    hybrid_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever],
        weights=[0.5, 0.5]  # Equal weight to keyword and semantic
    )

    # Create query engine
    query_engine = RetrieverQueryEngine.from_args(
        hybrid_retriever,
        llm=llm,
        response_mode="compact"  # Compact response synthesis
    )

    return query_engine
```

### Pipeline Flow Diagram

```
START
  │
  ▼
load_config("config/config.yaml")
  │
  ▼
check_ollama_health() ──► fail ──► restart_ollama() ──► check again
  │
  ▼
configure_llm(config) → ChatOllama instance
  │
  ▼
SimpleDirectoryReader("data").load_data()
  │
  ▼
SimpleNodeParser().get_nodes_from_documents(documents)
  │
  ▼
┌─────────────────────────────────────────┐
│           PARALLEL BUILD                │
│   VectorStoreIndex(nodes)               │
│   BM25Retriever.from_defaults(nodes)    │
│   VectorIndexRetriever(index)           │
└─────────────────────────────────────────┘
  │
  ▼
EnsembleRetriever([bm25, vector], weights=[0.5, 0.5])
  │
  ▼
RetrieverQueryEngine.from_args(retriever, llm)
  │
  ▼
engine.query(user_query)
  │
  ▼
(response.response, response.source_nodes)
```

---

## 2. Interactive CLI

```python
# Source: rag_pipeline.py:46-56
if __name__ == "__main__":
    while True:
        user_query = input("Enter your query (or 'exit'): ")
        if user_query.lower() in ["exit", "quit"]:
            break
        answer, context = run_query_with_context(user_query)
        print("\n--- Answer ---")
        print(answer)
        print("\n--- Source Context ---")
        for i, c in enumerate(context, 1):
            print(f"[{i}] {c[:200]}...\n")
```

### CLI Pattern

- Simple REPL loop
- Exit commands: "exit", "quit"
- Shows answer + truncated source contexts (200 chars)

---

## 3. Database to Markdown Export

```python
# Source: save_to_md.py (complete file)
from src.database import database_connection  # NOTE: Missing import!
import os
import yaml

def fetch_data_and_save_to_markdown():
    """
    Export database records to individual markdown files with YAML frontmatter.
    Creates ./data/{slug}.md for each repository.
    """
    try:
        with database_connection() as conn:
            cursor = conn.cursor()

            query = """
            SELECT
                r.full_name,
                r.description,
                r.language,
                r.readme_content,
                rs.forks,
                rs.stars,
                rs.date_last_push,
                GROUP_CONCAT(t.name, ', ') AS topics
            FROM
                repositories r
            LEFT JOIN
                repository_stats rs ON r.id = rs.repository_id
            LEFT JOIN
                repository_topics rt ON r.id = rt.repository_id
            LEFT JOIN
                topics t ON rt.topic_id = t.id
            GROUP BY
                r.id
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
            os.makedirs(data_dir, exist_ok=True)

            for row in rows:
                full_name, description, language, readme, forks, stars, last_push, topics = row
                slug = full_name.replace("/", "__").replace(" ", "_")

                metadata = {
                    'full_name': full_name,
                    'description': description,
                    'language': language,
                    'forks': forks,
                    'stars': stars,
                    'last_push_date': last_push,
                    'topics': topics
                }

                markdown_path = os.path.join(data_dir, f'{slug}.md')
                with open(markdown_path, 'w', encoding='utf-8') as f:
                    f.write('---\n')
                    yaml.dump(metadata, f, sort_keys=False)
                    f.write('---\n\n')
                    f.write(f'# {full_name}\n\n')
                    f.write(readme or '')

                print(f"Saved: {markdown_path}")
    except Exception as e:
        print(f"Error saving markdown files: {e}")
```

### Markdown Export Pattern

```
Database Record
      ↓
YAML Frontmatter + README Content
      ↓
./data/{owner}__{repo}.md
      ↓
RAG VectorStoreIndex ingestion
```

### Output Format

```markdown
---
full_name: owner/repo-name
description: A cool project
language: Python
forks: 42
stars: 1337
last_push_date: 2024-01-15
topics: python, machine-learning
---

# owner/repo-name

[README content here...]
```

---

## 4. Benchmarking Pattern

```python
# Source: benchmark.py (complete file)
import argparse
import json
import time
from datetime import datetime
from rag_pipeline import run_query_with_context

# Test dataset with expected keywords
benchmark_set = [
    {"query": "What is Retrieval-Augmented Generation?", "expected_keywords": ["retrieval", "generation"]},
    {"query": "Explain how FAISS works.", "expected_keywords": ["vector", "similarity"]},
    {"query": "What is Ollama?", "expected_keywords": ["model", "local"]},
]

def run_benchmark():
    results = []
    total_start = time.time()

    for item in benchmark_set:
        query = item["query"]
        expected_keywords = item.get("expected_keywords", [])
        print(f"Running query: {query}")

        try:
            response, context = run_query_with_context(query)
            # Keyword-based validation
            passed = all(keyword.lower() in response.lower() for keyword in expected_keywords)

            results.append({
                "query": query,
                "response": response,
                "context_used": context,
                "keywords_checked": expected_keywords,
                "passed": passed
            })

        except Exception as e:
            results.append({
                "query": query,
                "response": None,
                "context_used": None,
                "keywords_checked": expected_keywords,
                "passed": False,
                "error": str(e)
            })

    duration = time.time() - total_start
    print(f"Benchmark completed in {duration:.2f} seconds.")

    # Save results with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"benchmark_results_{timestamp}.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved results to benchmark_results_{timestamp}.json")
```

### Benchmark Pattern

1. **Test cases** - Query + expected keywords
2. **Keyword validation** - Check if all keywords present in response
3. **Timing** - Total benchmark duration
4. **Results output** - JSON file with timestamp
5. **Error handling** - Captures failures per query

---

## 5. Shell Startup Script

```bash
# Source: run.sh
#!/bin/bash
echo "Starting Ollama model..."
ollama run mistral &

echo "Waiting for Ollama to warm up..."
sleep 5

echo "Starting RAG CLI..."
source rag_env/bin/activate
python rag_pipeline.py
```

---

## Conclusions

### ✅ Good / Usable

1. **Hybrid retrieval pattern** - BM25 + Vector is best practice
2. **Auto-restart Ollama** - Self-healing service management
3. **Markdown export with frontmatter** - Clean data format
4. **Benchmark framework** - Keyword-based validation
5. **CLI interface** - Simple interactive mode
6. **Context extraction** - Returns source nodes with answer

### ⚠️ Outdated / Missing

1. **No index persistence** - Rebuilds every query (MAJOR issue)
2. **Missing database module** - `from src.database import database_connection` fails
3. **No batch processing** - Single query at a time
4. **No async** - Synchronous only
5. **Basic error handling** - Bare except in health check

### 🔧 Must Rewrite for AutoBiz

1. **Add index persistence** - Save/load from disk
2. **Implement database_connection** - Context manager for SQLite
3. **Add batch query mode** - Process multiple queries
4. **Add proper async support** - For concurrent queries
5. **Improve benchmark** - Add latency metrics, accuracy scores

### 📊 Comparison with Previous Repos

| Pattern | MarketIntel | SerpApi | Ollama-Rag |
|---------|-------------|---------|------------|
| Pipeline Type | Sync batch | Discovery pipeline | RAG query |
| CLI | No | Yes (review workflow) | Yes (REPL) |
| Benchmarking | No | No | Yes (basic) |
| Data Export | No | No | Yes (markdown) |
| Auto-restart | No | No | Yes (Ollama) |
| Persistence | SQLite | None (planning) | None (!) |
| Hybrid Search | No | No | Yes (BM25+Vector) |

### 🎯 Fit for AutoBiz

- **Hybrid retrieval** → Direct port to AutoBiz RAG
- **Markdown export** → Useful for document preparation
- **Benchmark pattern** → Extend for pipeline testing
- **CLI pattern** → Too simple, need richer CLI from SerpApi

---

## Files

- `/tmp/Ollama-Rag/rag_pipeline.py` - Complete file
- `/tmp/Ollama-Rag/save_to_md.py` - Complete file
- `/tmp/Ollama-Rag/benchmark.py` - Complete file
- `/tmp/Ollama-Rag/run.sh` - Shell script
