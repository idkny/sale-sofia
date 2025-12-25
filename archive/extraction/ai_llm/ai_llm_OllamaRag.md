---
id: extraction_ollamarag_ai_llm
type: extraction
subject: ai_llm
source_repo: Ollama-Rag
description: "LLM configuration, embeddings, and RAG patterns from Ollama-Rag"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [extraction, ai_llm, ollama, embeddings, rag, langchain, llamaindex]
---

# AI/LLM Patterns - Ollama-Rag

**Source**: `utils.py`, `rag_pipeline.py`
**Purpose**: Local RAG pipeline with hybrid retrieval
**Frameworks**: LangChain + LlamaIndex (hybrid approach)

---

## Overview

This repo uses **TWO frameworks**:
1. **LangChain** - For embeddings, summarization, clustering
2. **LlamaIndex** - For RAG retrieval (FAISS + BM25)

This is different from MarketIntel which uses only raw Ollama API.

---

## 1. LLM Configuration (ChatOllama)

```python
# Source: utils.py:228-266
from langchain_ollama import ChatOllama

def configure_llm(config: dict) -> ChatOllama:
    """
    Configures and returns a ChatOllama LLM instance based on the provided configuration.

    Args:
        config (dict): Configuration dictionary.

    Returns:
        ChatOllama: Configured language model.
    """
    try:
        # Extract LLM configuration
        llm_config = config.get("llm", {})
        logging.debug(f"LLM configuration: {llm_config}")

        # Validate and provide defaults for configuration fields
        model_name = llm_config.get("model_name")
        if not model_name:
            raise ValueError("The 'model_name' field is missing in the LLM configuration.")

        temperature = llm_config.get("temperature", 0)  # Default to 0 if not specified
        if not isinstance(temperature, (int, float)) or not (0 <= temperature <= 1):
            raise ValueError("The 'temperature' field must be a float between 0 and 1.")

        # Log the configured LLM details
        logging.info(f"Configuring ChatOllama LLM with model: {model_name}, temperature: {temperature}")

        # Create and return the LLM instance
        return ChatOllama(
            model=model_name,
            temperature=temperature,
        )

    except ValueError as ve:
        logging.error(f"ValueError in configure_llm: {ve}", exc_info=True)
        raise
    except Exception as e:
        logging.error(f"Unexpected error in configure_llm: {e}", exc_info=True)
        raise
```

### Comparison: ChatOllama vs MarketIntel OllamaClient

| Feature | Ollama-Rag (ChatOllama) | MarketIntel (OllamaClient) |
|---------|-------------------------|---------------------------|
| Library | langchain-ollama | Raw requests |
| JSON Mode | No | Yes (`format="json"`) |
| Streaming | Unknown | Yes |
| Retry Logic | No | Yes (exponential backoff) |
| Validation | Temperature only | Temperature + response format |
| Type Hints | Yes | Yes |

**Verdict**: MarketIntel's OllamaClient is **more complete** (JSON mode, retry, streaming).

---

## 2. Embeddings Configuration (HuggingFace BGE)

```python
# Source: utils.py:182-226
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
import torch

def configure_embeddings(config: dict) -> HuggingFaceBgeEmbeddings:
    """
    Configures and returns HuggingFace embeddings based on the provided configuration.

    Args:
        config (dict): Configuration dictionary.

    Returns:
        HuggingFaceBgeEmbeddings: Configured embedding model.
    """
    try:
        # Extract embedding configuration
        embedding_config = config.get("embeddings", {})
        logging.debug(f"Embedding configuration: {embedding_config}")

        # Validate required fields
        model_name = embedding_config.get("model_name")
        device = embedding_config.get("device", "auto")
        normalize_embeddings = embedding_config.get("normalize_embeddings", True)

        if not model_name:
            raise ValueError("The 'model_name' field is missing in the embeddings configuration.")
        if device not in ["auto", "cuda", "cpu"]:
            raise ValueError("The 'device' field must be 'auto', 'cuda', or 'cpu'.")

        # Determine the device
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"

        # Log the configured device and model
        logging.info(f"Configuring HuggingFace embeddings with model: {model_name}, device: {device}, normalize_embeddings: {normalize_embeddings}")

        # Create and return the embedding model
        return HuggingFaceBgeEmbeddings(
            model_name=model_name,
            model_kwargs={"device": device},
            encode_kwargs={"normalize_embeddings": normalize_embeddings},
        )

    except ValueError as ve:
        logging.error(f"ValueError in configure_embeddings: {ve}", exc_info=True)
        raise
    except Exception as e:
        logging.error(f"Unexpected error in configure_embeddings: {e}", exc_info=True)
        raise
```

### Key Features

1. **HuggingFace BGE** - Uses `BAAI/bge-small-en` by default (local, no API)
2. **Auto device detection** - CUDA if available, else CPU
3. **Normalization** - Configurable embeddings normalization
4. **Model kwargs** - Pass device to underlying model

### Why This Matters

- **Local embeddings** - No Ollama embeddings API needed
- **Fast** - BGE-small is lightweight
- **Standard** - Works with any LangChain/LlamaIndex component

---

## 3. Document Clustering (KMeans)

```python
# Source: utils.py:85-145
from langchain_community.document_transformers import EmbeddingsClusteringFilter
from sklearn.cluster import KMeans

def generate_embeddings_clustering(documents, embeddings, num_clusters, use_kmeans=False):
    """
    Clusters documents based on embeddings using either LangChain's EmbeddingsClusteringFilter
    or manual KMeans clustering.

    Args:
        documents (list[Document]): List of LangChain Document objects.
        embeddings: The embedding model.
        num_clusters (int): Number of clusters to create.
        use_kmeans (bool): Whether to use manual KMeans clustering (default is False).

    Returns:
        list: List of clustered documents.
    """
    try:
        # Validate input arguments
        if not documents:
            raise ValueError("No documents provided for clustering.")
        if num_clusters <= 0:
            raise ValueError("Number of clusters must be greater than zero.")
        if num_clusters > len(documents):
            logging.warning(f"Requested {num_clusters} clusters, but only {len(documents)} documents are available.")
            num_clusters = len(documents)  # Adjust clusters to the number of available documents

        logging.debug(f"Number of documents: {len(documents)}")
        logging.debug(f"Number of clusters: {num_clusters}")
        logging.debug(f"Clustering method: {'KMeans' if use_kmeans else 'EmbeddingsClusteringFilter'}")

        # Extract text content for embedding
        texts = [doc.page_content for doc in documents]
        logging.debug(f"Extracted text content for {len(texts)} documents.")

        # Generate embeddings for the document content
        doc_embeddings = embeddings.embed_documents(texts)
        logging.debug(f"Generated embeddings for documents.")

        if use_kmeans:
            # Manual KMeans clustering
            logging.info("Using KMeans for clustering.")
            kmeans = KMeans(n_clusters=num_clusters, random_state=42)
            labels = kmeans.fit_predict(doc_embeddings)

            # Group documents by cluster
            clustered_docs = [[] for _ in range(num_clusters)]
            for doc, label in zip(documents, labels):
                clustered_docs[label].append(doc)
        else:
            # LangChain's EmbeddingsClusteringFilter
            logging.info("Using EmbeddingsClusteringFilter for clustering.")
            filter = EmbeddingsClusteringFilter(embeddings=embeddings, num_clusters=num_clusters)
            clustered_docs = filter.transform_documents(documents)

        logging.debug(f"Clustering completed successfully.")
        return clustered_docs

    except ValueError as ve:
        logging.error(f"ValueError in generate_embeddings_clustering: {ve}", exc_info=True)
        raise
    except Exception as e:
        logging.error(f"Unexpected error in generate_embeddings_clustering: {e}", exc_info=True)
        raise
```

### Use Case

- **Pre-processing for summarization** - Cluster docs before LLM summary
- **Representative sampling** - Pick one doc per cluster
- **Two methods** - LangChain filter or manual KMeans

---

## 4. Summarization Chain

```python
# Source: utils.py:269-333
from langchain.chains.summarize import load_summarize_chain
from langchain.schema import Document

def summarize_doc(readme_content, llm, embeddings, num_clusters=10):
    """
    Summarizes the README content of a single repository or document.

    Args:
        readme_content (str): The content of the README or document to summarize.
        llm: The language model to use for summarization.
        embeddings: The embeddings model to use for clustering.
        num_clusters (int): Maximum number of clusters for summarization.

    Returns:
        str: The generated summary of the document or a fallback message.
    """
    try:
        if not readme_content or len(readme_content.strip()) == 0:
            logging.warning("No README content provided. Skipping summarization.")
            return "No content to summarize."

        if embeddings is None:
            raise ValueError("Embeddings model is not loaded.")

        logging.debug(f"Length of README content: {len(readme_content)} characters.")
        texts = [Document(page_content=readme_content)]
        n_samples = len(texts)

        if n_samples == 0:
            logging.warning("No data to process in the document.")
            return "No data to process in the document."

        summarize_chain = load_summarize_chain(llm, chain_type="stuff")

        # Short content: skip clustering
        if len(readme_content) < 500:
            logging.info("README content is short. Bypassing clustering.")
            summary_result = summarize_chain.invoke(texts)
        else:
            # Long content: use clustering
            clusters = min(n_samples, num_clusters)
            logging.debug(f"Number of clusters: {clusters}")
            clustered_documents = generate_embeddings_clustering(texts, embeddings, clusters)
            logging.debug(f"Clustered documents: {clustered_documents}")
            summary_result = summarize_chain.invoke(clustered_documents)

        # Handle result types
        if isinstance(summary_result, dict):
            summary = summary_result.get("output_text", "")
        elif isinstance(summary_result, str):
            summary = summary_result
        else:
            logging.error(f"Unexpected summary result type: {type(summary_result)}")
            summary = str(summary_result)

        if not summary.strip():
            logging.warning("Generated empty summary.")
            return "Generated summary is empty."

        logging.debug(f"Generated summary: {summary}")
        return summary

    except ValueError as ve:
        logging.error(f"ValueError in summarize_doc: {ve}", exc_info=True)
        raise
    except Exception as e:
        logging.error(f"Unexpected error in summarize_doc: {e}", exc_info=True)
        raise
```

### Key Features

1. **Chain type: "stuff"** - Concatenates all docs into single prompt
2. **Adaptive clustering** - Only clusters if content > 500 chars
3. **Error handling** - Handles empty content, dict/str results

---

## 5. RAG Pipeline (LlamaIndex Hybrid)

```python
# Source: rag_pipeline.py (complete file)
import os
from utils import load_config, check_ollama_health, restart_ollama, configure_llm
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.retrievers import BM25Retriever, VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.indices.composability import ComposableGraph
from llama_index.core.schema import TextNode

def setup_retriever():
    config = load_config("config/config.yaml")
    try:
        check_ollama_health()
    except:
        print("Ollama not running. Attempting to start...")
        restart_ollama()
        check_ollama_health()

    llm = configure_llm(config)

    # Load documents
    documents = SimpleDirectoryReader("data").load_data()
    parser = SimpleNodeParser()
    nodes = parser.get_nodes_from_documents(documents)

    # Build both retrievers
    vector_index = VectorStoreIndex(nodes)
    bm25_retriever = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=3)
    vector_retriever = VectorIndexRetriever(index=vector_index, similarity_top_k=3)

    # Combine both
    from llama_index.core.retrievers import EnsembleRetriever
    hybrid_retriever = EnsembleRetriever(retrievers=[bm25_retriever, vector_retriever], weights=[0.5, 0.5])

    # Create query engine
    query_engine = RetrieverQueryEngine.from_args(hybrid_retriever, llm=llm, response_mode="compact")

    return query_engine

def run_query_with_context(query):
    engine = setup_retriever()
    response = engine.query(query)
    return response.response, [node.node.text for node in response.source_nodes]

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

### Key RAG Architecture

```
./data/*.md files
       ↓
SimpleDirectoryReader (LlamaIndex)
       ↓
SimpleNodeParser → nodes
       ↓
┌──────────────────────────────────┐
│   HYBRID RETRIEVAL               │
│  ┌────────────┐ ┌─────────────┐  │
│  │ BM25       │ │ Vector      │  │
│  │ (keyword)  │ │ (semantic)  │  │
│  └────────────┘ └─────────────┘  │
│         ↓             ↓          │
│     EnsembleRetriever            │
│     weights=[0.5, 0.5]           │
└──────────────────────────────────┘
       ↓
RetrieverQueryEngine
response_mode="compact"
       ↓
(answer, source_nodes)
```

---

## Conclusions

### ✅ Good / Usable

1. **Hybrid retrieval pattern** - BM25 + Vector is state-of-the-art for RAG
2. **HuggingFace embeddings** - Local, no API dependency
3. **Auto device detection** - CUDA/CPU automatic
4. **Document clustering** - Useful for summarization at scale
5. **Config-driven** - All settings in YAML
6. **Summarization chain** - Ready-to-use LangChain pattern

### ⚠️ Outdated / Missing

1. **No persistent index** - Rebuilds VectorStoreIndex every query (!)
2. **No vector DB** - Uses in-memory only (no FAISS persistence despite requirements.txt)
3. **No caching** - Every query re-loads documents
4. **ChatOllama basic** - No JSON mode, no retry, no streaming
5. **No RAG evaluation** - Benchmark.py is basic

### 🔧 Must Rewrite for AutoBiz

1. **Add index persistence** - Save/load VectorStoreIndex to disk
2. **Add ChromaDB or FAISS persistence** - Not just in-memory
3. **Merge with MarketIntel OllamaClient** - Get JSON mode + retry
4. **Add streaming** - For long responses

### 🎯 Best-of-Breed Recommendations

| Component | Best Version | Source |
|-----------|-------------|--------|
| LLM Client | OllamaClient | MarketIntel |
| Embeddings | HuggingFaceBgeEmbeddings | Ollama-Rag |
| RAG Retrieval | EnsembleRetriever (hybrid) | Ollama-Rag |
| Summarization | summarize_doc + clustering | Ollama-Rag |
| Config | Pydantic Settings | MarketIntel |
| Caching | SHA256 + TTL | MarketIntel |

### 📊 Cross-Repo Comparison

| Feature | MarketIntel | Ollama-Rag |
|---------|-------------|------------|
| LLM Library | Raw requests | langchain-ollama |
| Embeddings | None | HuggingFace BGE |
| RAG | None | LlamaIndex hybrid |
| Caching | SQLite+TTL | None |
| Config | Pydantic | YAML |
| Retry | Exponential backoff | None |
| JSON Mode | Yes | No |
| Summarization | No | Yes (LangChain) |
| Clustering | No | Yes (KMeans) |

---

## Files

- `/tmp/Ollama-Rag/utils.py` - Lines 182-333
- `/tmp/Ollama-Rag/rag_pipeline.py` - Complete file
- `/tmp/Ollama-Rag/config/config.yaml` - Configuration
