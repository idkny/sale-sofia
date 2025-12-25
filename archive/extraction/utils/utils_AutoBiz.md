---
id: 20251201_utils_autobiz
type: extraction
subject: utils
source_repo: Auto-Biz
description: "Utility functions, logging, token tracking from Auto-Biz"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [utils, logging, loguru, port, xvfb, auto-biz]
---

# SUBJECT: utils/

**Source Repository**: Auto-Biz (https://github.com/idkny/Auto-Biz)
**Extracted From**: `utils/utils.py`, `utils/log_config.py`, `browsers/utils.py`

---

## 1. EXTRACTED CODE

### 1.1 Port Management

```python
"""General utility functions."""

import logging
import os
import socket
import subprocess
import time

logger = logging.getLogger(__name__)


def is_port_in_use(port: int) -> bool:
    """Check if a local port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def free_port(port: int) -> bool:
    """Check if a port is in use and attempt to free it by killing the process."""
    if is_port_in_use(port):
        logger.warning(f"Port {port} is already in use. Attempting to free it.")
        try:
            if os.name == "posix":
                process = subprocess.run(
                    ["lsof", "-t", f"-i:{port}"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                pid = process.stdout.strip()
                if pid:
                    subprocess.run(["kill", "-9", pid], check=True)
                    time.sleep(2)
                    if not is_port_in_use(port):
                        logger.info(f"Successfully freed port {port}.")
                        return True
                    else:
                        logger.error(f"Failed to free port {port}.")
                        return False
            else:
                logger.warning("Port freeing is not implemented for this OS.")
                return False
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"Failed to kill process on port {port}: {e}")
            return False
    else:
        return True
```

### 1.2 Proxy Validation

```python
from urllib.parse import urlparse


def validate_proxy(proxy: str | dict | None) -> dict | None:
    """Validates and formats the proxy input for Playwright."""
    if isinstance(proxy, str) and proxy:
        parsed = urlparse(proxy)
        if not parsed.hostname:
            return None
        proxy_dict = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
        if parsed.username:
            proxy_dict["username"] = parsed.username
        if parsed.password:
            proxy_dict["password"] = parsed.password
        return proxy_dict
    elif isinstance(proxy, dict):
        return proxy
    return None
```

### 1.3 Virtual Display Manager

```python
from contextlib import contextmanager
from typing import Any

from pyvirtualdisplay import Display


@contextmanager
def xvfb_manager(width: int = 1920, height: int = 1080) -> Any:
    """A context manager to run code within a virtual X display."""
    display = None
    try:
        display = Display(visible=0, size=(width, height))
        display.start()
        logger.info(f"Started virtual display: {display.display}")
        yield
    except Exception as e:
        logger.error(f"Failed to start virtual display: {e}")
        raise
    finally:
        if display:
            display.stop()
            logger.info("Stopped virtual display.")
```

### 1.4 Token Usage Tracker

```python
from typing import Any


class TokenUsageTracker:
    """Callback handler for tracking token usage from LLM calls."""

    def __init__(self) -> None:
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.llm_provider_type = None

    def on_llm_start(self, serialized: dict[str, Any], prompts: list[str], **kwargs: Any) -> None:
        if "invocation_params" in serialized:
            inv_params = serialized["invocation_params"]
            self.llm_provider_type = inv_params.get("_type", self.llm_provider_type)

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        if hasattr(response, "llm_output") and response.llm_output is not None:
            token_usage_data = response.llm_output.get("token_usage")
            if token_usage_data:
                self.total_tokens += token_usage_data.get("total_tokens", 0)
                self.prompt_tokens += token_usage_data.get("prompt_tokens", 0)
                self.completion_tokens += token_usage_data.get("completion_tokens", 0)

    def get_usage_dict(self) -> dict[str, Any]:
        return {
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "llm_provider_type": self.llm_provider_type,
        }
```

### 1.5 Loguru Configuration

```python
"""Configures logging using Loguru."""

import logging
import sys
from pathlib import Path

from loguru import logger


def setup_logging(log_dir: Path) -> None:
    """Sets up Loguru logging to console and a file."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    logger.remove()

    # Console logging
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # File logging
    logger.add(
        log_file,
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        enqueue=True,
    )

    # Redirect standard logging to Loguru
    logging.basicConfig(handlers=[LoguruHandler()], level=0, force=True)
    logger.info("Logging initialized. Console: INFO, File: DEBUG, Log file: {}", log_file)


class LoguruHandler(logging.Handler):
    """A handler that redirects standard logging messages to Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelname

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())
```

---

## 2. CONCLUSIONS

### What is Good / Usable

1. **Port management**: is_port_in_use + free_port
2. **Proxy validation**: URL parsing for Playwright format
3. **Xvfb manager**: Context manager for headless servers
4. **TokenUsageTracker**: LLM callback for token accounting
5. **Loguru setup**: Rotation, retention, colorized output, stdlib redirect

### What is Outdated

Nothing - all patterns are current

### What Must Be Rewritten

Nothing - ready for direct use

### Conflicts with Previous Repos

| Pattern | Auto-Biz | Ollama-Rag | Best |
|---------|----------|------------|------|
| Xvfb | Yes | No | **Auto-Biz** |
| URL cleaning | Proxy validation | GitHub URL | **Both useful** |
| Token tracking | Yes | No | **Auto-Biz** |
| Logging | Loguru | Basic | **Auto-Biz** |

### Best Version Recommendation

**Auto-Biz is BEST for utilities**:
- Most comprehensive set of helper functions
- Loguru setup is production-ready
- Xvfb manager is unique and essential
