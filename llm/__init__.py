"""LLM module for Ollama integration.

Exports:
    map_fields: Map page content to DB fields
    extract_description: Extract structured data from description
    ensure_ollama_ready: Ensure Ollama server is running
    get_confidence_threshold: Get min confidence from config
    get_metrics: Get extraction metrics
    reset_metrics: Reset metrics to zero
"""

from llm.llm_main import (
    map_fields,
    extract_description,
    ensure_ollama_ready,
    get_confidence_threshold,
    get_metrics,
    reset_metrics,
)

__all__ = [
    "map_fields",
    "extract_description",
    "ensure_ollama_ready",
    "get_confidence_threshold",
    "get_metrics",
    "reset_metrics",
]
