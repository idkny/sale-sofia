---
id: extraction_ollamarag_automation
type: extraction
subject: automation
source_repo: Ollama-Rag
description: "Ollama server management and automation patterns from Ollama-Rag"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [extraction, automation, ollama, server, health-check, ollamarag]
---

# Automation Patterns - Ollama-Rag

**Source**: `utils.py`
**Purpose**: Ollama server health checks and auto-restart
**Status**: PRODUCTION-READY - Direct port to AutoBiz

---

## 1. Ollama Health Check

```python
# Source: utils.py:147-158
import requests

def check_ollama_health(base_url="http://localhost:11434"):
    """
    Check if Ollama server is running and healthy.
    Raises exception on failure.
    """
    print(f"Checking Ollama server at {base_url}...")
    try:
        response = requests.get(f"{base_url}/", timeout=2)
        print(f"Ollama server response: {response.status_code}")
        if response.status_code == 200:
            print("Ollama server is healthy and running.")
        else:
            print("Ollama server is not healthy. Response:", response.status_code)
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to Ollama server: {e}")
        raise  # Re-throw for caller to handle
```

### Key Features

- **Timeout** - 2 second timeout prevents hanging
- **Simple endpoint** - Just checks root `/` responds with 200
- **Raises on failure** - Allows caller to handle retry

---

## 2. Ollama Auto-Restart

```python
# Source: utils.py:160-180
import socket
import time
from subprocess import run, Popen

def restart_ollama():
    """
    Stop any running Ollama server and restart it.
    Includes port binding check to avoid conflicts.
    """
    try:
        print("Stopping any running Ollama server...")
        run(["pkill", "-f", "ollama"])
        time.sleep(3)

        # Check if port 11434 is free before starting
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", 11434))
            s.close()
            print("Port 11434 is free. Starting Ollama server...")
            Popen(["ollama", "serve"])
            time.sleep(2)
        except OSError:
            s.close()
            print("Port 11434 is still in use. Skipping start and waiting for Ollama health check.")
            return  # Skip restart, let health check retry handle it
    except Exception as e:
        print(f"Error in restart_ollama: {e}")
        raise RuntimeError("Failed to restart Ollama server.")
```

### Key Features

1. **Kill existing process** - `pkill -f ollama`
2. **Wait for cleanup** - 3 second sleep
3. **Port binding check** - Verify port is free before start
4. **Background start** - `Popen(["ollama", "serve"])`
5. **Warmup delay** - 2 second sleep after start
6. **Graceful degradation** - If port busy, skip restart

### Port Binding Pattern

```python
# Check if port is available
import socket

def is_port_free(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((host, port))
        s.close()
        return True
    except OSError:
        s.close()
        return False
```

---

## 3. GPU Memory Cleanup

```python
# Source: utils.py:35-44
import torch
import sys
import logging

def cleanup_gpu_memory(signal_received=None, frame=None):
    """
    Cleans up GPU memory when the script exits.
    Can be used as signal handler or called directly.
    """
    logging.info("Received termination signal. Cleaning up GPU memory.")
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        print("GPU memory cleared.")
        logging.info("GPU memory cleared.")
    sys.exit(0)
```

### Usage as Signal Handler

```python
import signal

# Register for graceful shutdown
signal.signal(signal.SIGTERM, cleanup_gpu_memory)
signal.signal(signal.SIGINT, cleanup_gpu_memory)
```

---

## 4. Dynamic Batch Size Calculator

```python
# Source: utils.py:46-83
import psutil

def calculate_dynamic_batch_size(config: dict) -> int:
    """
    Calculates a dynamic batch size based on system memory availability.

    Args:
        config (dict): Configuration settings.

    Returns:
        int: Optimal batch size.
    """
    try:
        # Get available memory
        available_memory = psutil.virtual_memory().available
        logging.debug(f"Available memory: {available_memory / (1024 ** 2):.2f} MB")

        # Estimate memory usage per document
        memory_per_document = config.get("memory_per_document", 50 * 1024 * 1024)  # Default 50 MB
        if memory_per_document <= 0:
            raise ValueError("Memory per document must be greater than zero.")
        logging.debug(f"Memory per document: {memory_per_document / (1024 ** 2):.2f} MB")

        # Calculate max batch size based on available memory
        max_batch_size = available_memory // memory_per_document
        logging.debug(f"Calculated max batch size based on memory: {max_batch_size}")

        # Get user-defined maximum batch size from the configuration
        user_max_batch_size = config.get("batch_settings", {}).get("max_batch_size", 20)
        if user_max_batch_size <= 0:
            raise ValueError("User-defined max batch size must be greater than zero.")
        logging.debug(f"User-defined max batch size: {user_max_batch_size}")

        # Return the smaller of the calculated and user-defined max batch size
        optimal_batch_size = max(1, min(max_batch_size, user_max_batch_size))
        logging.debug(f"Optimal batch size: {optimal_batch_size}")
        return optimal_batch_size
    except Exception as e:
        logging.error(f"Error in calculate_dynamic_batch_size: {e}", exc_info=True)
        raise
```

### Key Features

- **Memory-aware** - Uses `psutil.virtual_memory().available`
- **Config-bounded** - Respects user-defined max
- **Safe minimum** - Always returns at least 1
- **Configurable per-doc memory** - 50MB default

---

## 5. Integration Pattern (Auto-Heal on Failure)

```python
# Source: rag_pipeline.py:12-18
def setup_retriever():
    config = load_config("config/config.yaml")

    # Self-healing pattern
    try:
        check_ollama_health()
    except:
        print("Ollama not running. Attempting to start...")
        restart_ollama()
        check_ollama_health()  # Verify restart worked

    llm = configure_llm(config)
    # ... rest of setup
```

---

## Conclusions

### ✅ Good / Usable - DIRECT PORT

1. **Health check with timeout** - Essential for LLM services
2. **Port binding check** - Avoids address-in-use errors
3. **Auto-restart pattern** - Self-healing services
4. **GPU cleanup** - Proper resource management
5. **Dynamic batch sizing** - Memory-aware processing
6. **Self-healing integration** - Try → Fail → Restart → Retry

### ⚠️ Missing / Could Improve

1. **No retry count limit** - Could loop forever
2. **No exponential backoff** - Just fixed sleeps
3. **No health check interval** - Only checks on demand
4. **Basic logging** - Could use structured logging

### 🔧 Improvements for AutoBiz

```python
# Enhanced version with retry limits
def check_ollama_health_with_retry(base_url="http://localhost:11434", max_retries=3):
    for attempt in range(max_retries):
        try:
            check_ollama_health(base_url)
            return True
        except:
            if attempt < max_retries - 1:
                restart_ollama()
                time.sleep(5 * (attempt + 1))  # Increasing delay
    raise RuntimeError(f"Ollama failed after {max_retries} attempts")
```

### 📊 Comparison Matrix

| Feature | MarketIntel | SerpApi | Ollama-Rag |
|---------|-------------|---------|------------|
| Health Checks | No | No | Yes |
| Auto-restart | No | No | Yes |
| Port Binding | No | No | Yes |
| GPU Cleanup | No | No | Yes |
| Dynamic Batching | No | No | Yes |
| Signal Handlers | No | No | Yes |

### 🎯 Fit for AutoBiz

- **DIRECT PORT** - All patterns are production-ready
- **Unique value** - Only repo with server management
- **Critical for local LLM** - AutoBiz needs this

---

## Files

- `/tmp/Ollama-Rag/utils.py:35-83` - GPU cleanup, batch sizing
- `/tmp/Ollama-Rag/utils.py:147-180` - Health check, restart
