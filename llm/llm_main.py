"""Ollama LLM client facade for real estate data extraction.

This module provides:
- OllamaClient: Health check, server management, API calls
- map_fields(): Extract DB fields from page content
- extract_description(): Extract structured data from descriptions
- ensure_ollama_ready(): Ensure Ollama server is running

Reference: ZohoCentral's implementation at /home/wow/Documents/ZohoCentral/autobiz/tools/ai/_llm.py
"""

import hashlib
import json
import logging
import re
import socket
import subprocess
import time
from pathlib import Path
from typing import Optional, Type, TypeVar

import redis
import requests
import yaml

from llm.prompts import FIELD_MAPPING_PROMPT, build_extraction_prompt
from llm.schemas import MappedFields, ExtractedDescription
from llm.dictionary import scan_and_build_hints

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent / "config" / "ollama.yaml"

T = TypeVar("T", MappedFields, ExtractedDescription)

# Metrics tracking
_metrics = {
    "extractions_total": 0,
    "extractions_success": 0,
    "extractions_failed": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "total_time_ms": 0.0,
    "total_confidence": 0.0,
}


class OllamaClient:
    """Ollama LLM client with health check and auto-restart."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize client with config from ollama.yaml."""
        self.config = self._load_config(config_path or CONFIG_PATH)
        self.port = self.config["ollama"]["port"]
        self.host = self.config["ollama"]["host"]
        self.base_url = f"http://{self.host}:{self.port}"

    def _load_config(self, path: Path) -> dict:
        """Load config from YAML file."""
        with open(path) as f:
            return yaml.safe_load(f)

    def check_health(self, timeout: int = 2) -> bool:
        """Check if Ollama server is running via HTTP GET."""
        try:
            response = requests.get(f"{self.base_url}/", timeout=timeout)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def is_port_free(self, port: Optional[int] = None) -> bool:
        """Check if port is available for binding."""
        port = port or self.port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", port))
            s.close()
            return True
        except OSError:
            s.close()
            return False

    def kill_port_holder(self, port: int = 11434) -> bool:
        """Kill process holding the specified port."""
        try:
            result = subprocess.run(
                ["lsof", "-t", f"-i:{port}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            pid = result.stdout.strip()

            if pid:
                logger.warning(f"Killing process {pid} holding port {port}")
                subprocess.run(["kill", "-9", pid], timeout=5)

                # Wait for port to be free (max 5 seconds)
                for _ in range(10):
                    if self.is_port_free(port):
                        return True
                    time.sleep(0.5)

            return self.is_port_free(port)

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error(f"Failed to kill port holder: {e}")
            return False

    def start_server(self) -> bool:
        """Start ollama serve as detached process."""
        if self.check_health():
            logger.info("Ollama server already running")
            return True

        if not self.is_port_free(self.port):
            logger.warning(f"Port {self.port} busy, killing holder")
            if not self.kill_port_holder(self.port):
                logger.error("Failed to free port")
                return False

        try:
            logger.info("Starting Ollama server...")
            subprocess.Popen(
                ["ollama", "serve"],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return self.wait_for_healthy()

        except FileNotFoundError:
            logger.error("ollama command not found - is Ollama installed?")
            return False
        except Exception as e:
            logger.error(f"Failed to start Ollama: {e}")
            return False

    def wait_for_healthy(self, timeout: int = 10) -> bool:
        """Poll until server becomes healthy or timeout."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.check_health():
                logger.info("Ollama server is healthy")
                return True
            time.sleep(1)
        logger.error(f"Ollama did not become healthy within {timeout}s")
        return False

    def ensure_ready(self) -> bool:
        """Self-healing: check health, restart if needed."""
        if self.check_health():
            return True

        max_attempts = self.config["ollama"]["max_restart_attempts"]
        for attempt in range(1, max_attempts + 1):
            logger.warning(f"Ollama not healthy, restart attempt {attempt}/{max_attempts}")
            if self.start_server():
                return True
            if attempt < max_attempts:
                time.sleep(2)

        logger.error(f"Failed to start Ollama after {max_attempts} attempts")
        return False

    def _call_ollama(
        self, prompt: str, task: str, schema_class: Optional[Type[T]] = None
    ) -> str:
        """Call Ollama REST API for generation.

        Args:
            prompt: The formatted prompt to send
            task: Task key from config (field_mapping or description_extraction)
            schema_class: Optional Pydantic model for JSON schema enforcement.
                         If provided, uses model_json_schema() for grammar-level
                         enum enforcement. Otherwise falls back to "json".

        Returns:
            Raw response string from Ollama
        """
        task_config = self.config["tasks"][task]
        model = task_config["primary_model"]

        # Use full JSON schema if provided, else just "json" for syntax-only
        format_value = (
            schema_class.model_json_schema() if schema_class else "json"
        )

        try:
            # Get keep_alive from config (default 5m if not set)
            keep_alive = self.config["ollama"].get("keep_alive", "5m")

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "format": format_value,
                    "keep_alive": keep_alive,  # Keep model loaded for batch processing
                    "options": {
                        "temperature": task_config["temperature"],
                        "num_predict": task_config["max_tokens"],
                    },
                },
                timeout=task_config["timeout_seconds"],
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            return ""

    def _parse_response(
        self, response: str, schema_class: Type[T]
    ) -> T:
        """Parse JSON response into Pydantic model.

        Args:
            response: Raw response string from Ollama
            schema_class: Pydantic model class to parse into

        Returns:
            Instance of schema_class, with confidence=0.0 if parsing fails
        """
        if not response:
            return schema_class(confidence=0.0)

        try:
            # Try to extract JSON from response
            json_match = re.search(r"\{[^{}]*\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                # Translate Bulgarian values to English
                data = self._translate_values(data)
                return schema_class(**data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse LLM response: {e}")

        return schema_class(confidence=0.0)

    def _translate_values(self, data: dict) -> dict:
        """Translate Bulgarian enum values to English.

        The LLM sometimes returns Bulgarian words despite instructions.
        This maps common Bulgarian values to their English equivalents.
        """
        translations = {
            # construction types
            "tuhla": "brick",
            "тухла": "brick",
            "panel": "panel",
            "панел": "panel",
            "epk": "epk",
            "епк": "epk",
            # heating types
            "tec": "district",
            "тец": "district",
            "centralno": "district",
            "централно": "district",
            "gas": "gas",
            "газ": "gas",
            "gazovo": "gas",
            "газово": "gas",
            "tok": "electric",
            "ток": "electric",
            "elektricherstvo": "electric",
            "електричество": "electric",
            "klimatik": "air_conditioner",
            "климатик": "air_conditioner",
            # furnishing
            "obzaveden": "furnished",
            "обзаведен": "furnished",
            "napalno obzaveden": "furnished",
            "напълно обзаведен": "furnished",
            "full": "furnished",
            "neobzaveden": "unfurnished",
            "необзаведен": "unfurnished",
            "chastichno": "partially",
            "частично": "partially",
            "chastichno obzaveden": "partially",
            "частично обзаведен": "partially",
            "partial": "partially",
            # condition
            "nov": "new",
            "нов": "new",
            "nova": "new",
            "нова": "new",
            "novo": "new",
            "ново": "new",
            "new": "new",
            "remontiран": "renovated",
            "remontiran": "renovated",
            "renovated": "renovated",
            "za remont": "needs_renovation",
            "за ремонт": "needs_renovation",
            "needs repair": "needs_renovation",
            # orientation
            "yug": "south",
            "юг": "south",
            "sever": "north",
            "север": "north",
            "iztok": "east",
            "изток": "east",
            "zapad": "west",
            "запад": "west",
            # view type
            "grad": "city",
            "град": "city",
            "city": "city",
            "planina": "mountain",
            "планина": "mountain",
            "vitosha": "mountain",
            "витоша": "mountain",
            "park": "park",
            "парк": "park",
            # parking type
            "podzemen": "underground",
            "подземен": "underground",
            "underground": "underground",
            "garazh": "garage",
            "гараж": "garage",
            "garage": "garage",
            "dvor": "outdoor",
            "двор": "outdoor",
            "outdoor": "outdoor",
        }

        for key, value in data.items():
            if isinstance(value, str):
                lower_val = value.lower()
                if lower_val in translations:
                    data[key] = translations[lower_val]

        return data


# Module-level singletons
_client: Optional[OllamaClient] = None
_redis_client: Optional[redis.Redis] = None


def _get_client() -> OllamaClient:
    """Get or create singleton OllamaClient instance."""
    global _client
    if _client is None:
        _client = OllamaClient()
    return _client


def _get_redis_client() -> Optional[redis.Redis]:
    """Get or create singleton Redis client. Returns None on connection failure."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
            _redis_client.ping()
        except redis.RedisError as e:
            logger.warning(f"Redis connection failed, cache disabled: {e}")
            return None
    return _redis_client


def _cache_key(text: str) -> str:
    """Generate cache key from text using MD5 hash."""
    config = _get_client().config["ollama"].get("cache", {})
    prefix = config.get("key_prefix", "llm:extract:")
    text_hash = hashlib.md5(text.encode()).hexdigest()
    return f"{prefix}{text_hash}"


def _get_cached(key: str) -> Optional[dict]:
    """Get cached extraction result. Returns None if not found or error."""
    client = _get_redis_client()
    if not client:
        return None
    try:
        data = client.get(key)
        return json.loads(data) if data else None
    except (redis.RedisError, json.JSONDecodeError):
        return None


def _set_cached(key: str, data: dict, ttl_days: int) -> None:
    """Store extraction result in cache with TTL."""
    client = _get_redis_client()
    if not client:
        return
    try:
        client.setex(key, ttl_days * 86400, json.dumps(data))
    except redis.RedisError:
        pass  # Fail silently, cache is optional


def ensure_ollama_ready() -> bool:
    """Ensure Ollama server is running and ready.

    Returns:
        True if server is healthy, False otherwise
    """
    return _get_client().ensure_ready()


def get_confidence_threshold() -> float:
    """Get minimum confidence threshold from config.

    Returns:
        Confidence threshold (default 0.7)
    """
    return _get_client().config["ollama"].get("confidence_threshold", 0.7)


def get_metrics() -> dict:
    """Get extraction metrics.

    Returns:
        Dict with:
        - extractions_total: Total extraction calls
        - extractions_success: Successful extractions (confidence > 0)
        - extractions_failed: Failed extractions
        - cache_hits: Cache hit count
        - cache_misses: Cache miss count
        - avg_time_ms: Average extraction time
        - avg_confidence: Average confidence score
        - cache_hit_rate: Cache hit percentage
    """
    total = _metrics["extractions_total"]
    cache_total = _metrics["cache_hits"] + _metrics["cache_misses"]

    return {
        **_metrics,
        "avg_time_ms": _metrics["total_time_ms"] / max(1, total),
        "avg_confidence": _metrics["total_confidence"] / max(1, _metrics["extractions_success"]),
        "cache_hit_rate": _metrics["cache_hits"] / max(1, cache_total),
    }


def reset_metrics() -> None:
    """Reset all metrics to zero."""
    for key in _metrics:
        _metrics[key] = 0.0 if "time" in key or "confidence" in key else 0


def map_fields(content: str) -> MappedFields:
    """Map page content to database fields using LLM.

    Args:
        content: Raw text content from scraped page

    Returns:
        MappedFields with extracted data, confidence=0.0 if failed
    """
    client = _get_client()

    if not client.ensure_ready():
        logger.error("Ollama not available for field mapping")
        return MappedFields(confidence=0.0)

    prompt = FIELD_MAPPING_PROMPT.format(content=content)
    response = client._call_ollama(prompt, "field_mapping", schema_class=MappedFields)
    return client._parse_response(response, MappedFields)


def extract_description(description: str) -> ExtractedDescription:
    """Extract structured data from free-text description.

    Uses dynamic Bulgarian dictionary to:
    1. Pre-scan text for known Bulgarian keywords
    2. Inject only relevant hints into the prompt
    3. Pre-extract numeric values with regex (more reliable than LLM)

    Args:
        description: Free-text description from listing

    Returns:
        ExtractedDescription with extracted data, confidence=0.0 if failed
    """
    start_time = time.time()
    _metrics["extractions_total"] += 1

    client = _get_client()
    cache_config = client.config["ollama"].get("cache", {})

    # Check cache first
    if cache_config.get("enabled", False):
        cache_key = _cache_key(description)
        cached = _get_cached(cache_key)
        if cached:
            _metrics["cache_hits"] += 1
            _metrics["extractions_success"] += 1
            _metrics["total_confidence"] += cached.get("confidence", 0.0)
            logger.debug(f"Cache hit for extraction: {cache_key[:20]}...")
            return ExtractedDescription(**cached)
        _metrics["cache_misses"] += 1

    if not client.ensure_ready():
        logger.error("Ollama not available for description extraction")
        _metrics["extractions_failed"] += 1
        return ExtractedDescription(confidence=0.0)

    # Scan text for Bulgarian keywords and build dynamic hints
    hints, pre_extracted = scan_and_build_hints(description)

    # Build prompt with injected hints
    prompt = build_extraction_prompt(description, hints)

    response = client._call_ollama(
        prompt, "description_extraction", schema_class=ExtractedDescription
    )
    result = client._parse_response(response, ExtractedDescription)

    # Override with pre-extracted numeric values (regex is more reliable than LLM)
    for field, value in pre_extracted.items():
        if value is not None and hasattr(result, field):
            setattr(result, field, value)

    # Track metrics
    elapsed_ms = (time.time() - start_time) * 1000
    _metrics["total_time_ms"] += elapsed_ms
    if result.confidence > 0:
        _metrics["extractions_success"] += 1
        _metrics["total_confidence"] += result.confidence
    else:
        _metrics["extractions_failed"] += 1

    # Cache successful extractions
    if cache_config.get("enabled", False) and result.confidence > 0:
        ttl_days = cache_config.get("ttl_days", 7)
        _set_cached(cache_key, result.model_dump(), ttl_days)

    return result
