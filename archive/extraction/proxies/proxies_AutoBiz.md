---
id: 20251201_proxies_autobiz
type: extraction
subject: proxies
source_repo: Auto-Biz
description: "Proxy management, Celery tasks, Mubeng integration from Auto-Biz"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [proxies, celery, mubeng, packetstream, auto-biz]
---

# SUBJECT: proxies/

**Source Repository**: Auto-Biz (https://github.com/idkny/Auto-Biz)
**Extracted From**: `proxies/proxies_main.py`, `proxies/get_paid_proxies.py`, `proxies/mubeng_manager.py`, `auto_biz/tasks/proxies.py`

---

## 1. EXTRACTED CODE

### 1.1 PaidProxyService (PacketStream Integration)

```python
"""Module for integrating with paid proxy services like PacketStream.io."""

import os
from typing import Literal, Optional

from dotenv import load_dotenv

load_dotenv()


class PaidProxyService:
    """Interface to the PacketStream.io paid proxy service."""

    def __init__(self) -> None:
        self.username = os.getenv("PROXY_USERNAME")
        self.password = os.getenv("PROXY_PASSWORD")
        if not self.username or not self.password:
            raise ValueError("Missing PacketStream credentials in .env file")

        self.base_host = "proxy.packetstream.io"
        self.port_map = {"http": 31112, "https": 31112, "socks5": 31113}

    def get_proxy_dict(
        self,
        protocol: Literal["http", "https", "socks5"] = "http",
        country: Optional[str] = None,
        session_type: Literal["sticky", "random"] = "sticky",
    ) -> dict[str, str]:
        """Generates a dictionary with proxy details for Playwright."""
        if protocol not in self.port_map:
            raise ValueError(f"Unsupported protocol: {protocol}")

        auth_user = self.username

        pass_parts = [self.password]
        if country:
            pass_parts.append(f"country-{country}")
        if session_type == "random":
            pass_parts.append("session-random")

        auth_pass = "_".join(pass_parts)
        port = self.port_map[protocol]

        if protocol == "socks5":
            server_url = f"socks5://{self.base_host}:{port}"
        else:
            server_url = f"{self.base_host}:{port}"

        return {
            "server": server_url,
            "username": auth_user,
            "password": auth_pass,
        }

    def get_proxy(
        self,
        protocol: Literal["http", "https", "socks5"] = "http",
        country: Optional[str] = None,
        session_type: Literal["sticky", "random"] = "sticky",
        as_dict: bool = False,
    ) -> str | dict[str, str]:
        """Generates a fully-formed PacketStream proxy URL."""
        if protocol not in self.port_map:
            raise ValueError(f"Unsupported protocol: {protocol}")

        auth_user = self.username
        pass_parts = [self.password]
        if country:
            pass_parts.append(f"country-{country}")
        if session_type == "random":
            pass_parts.append("session-random")

        auth_pass = "_".join(pass_parts)
        port = self.port_map[protocol]

        # Use 'socks5h' for SOCKS5 to ensure DNS resolves through the proxy
        scheme = "socks5h" if protocol == "socks5" else protocol

        proxy_url = f"{scheme}://{auth_user}:{auth_pass}@{self.base_host}:{port}"

        if as_dict:
            return {"http": proxy_url, "https": proxy_url}

        return proxy_url
```

### 1.2 Proxy Filtering and Management

```python
"""Main module for proxy management."""

import json
import logging
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Optional

import requests
from celery import chain

import config
from paths import MUBENG_EXECUTABLE_PATH, PROXIES_DIR
from utils.utils import free_port

logger = logging.getLogger(__name__)

MIN_LIVE_PROXIES_DEFAULT = 1
ANONYMITY_MAPPING = {
    "1": "Transparent",
    "2": "Anonymous",
    "3": "Elite",
}


def get_and_filter_proxies(
    protocols: Optional[list[str]] = None,
    anonymity_levels: Optional[list[str]] = None,
    country_codes: Optional[list[str]] = None,
    google_passed: Optional[bool] = None,
    source_file: str = "scraped_proxies.json",
) -> Optional[list[dict]]:
    """Filters proxies from a specified JSON file."""
    logger.info(
        f"Filtering proxies with: protocols={protocols}, "
        f"anonymity={anonymity_levels}, countries={country_codes}"
    )
    proxies_file = PROXIES_DIR / source_file
    if not proxies_file.exists():
        return None

    with open(proxies_file, "r") as f:
        try:
            all_proxies = json.load(f)
        except json.JSONDecodeError:
            return None

    filtered_proxies = all_proxies
    if protocols:
        filtered_proxies = [p for p in filtered_proxies if p.get("protocol") in protocols]
    if anonymity_levels:
        mapped_anonymity = [ANONYMITY_MAPPING.get(level, "") for level in anonymity_levels]
        if mapped_anonymity:
            filtered_proxies = [p for p in filtered_proxies if p.get("anonymity") in mapped_anonymity]
    if country_codes:
        filtered_proxies = [p for p in filtered_proxies if p.get("country_code") in country_codes]
    if google_passed is not None:
        filtered_proxies = [p for p in filtered_proxies if p.get("google_passed") is google_passed]

    return filtered_proxies


def get_live_free_proxies(
    protocols: Optional[list[str]] = None,
    anonymity_levels: Optional[list[str]] = None,
    country_codes: Optional[list[str]] = None,
    google_passed: Optional[bool] = None,
) -> list[str]:
    """Retrieves filtered list of high-quality, live proxies."""
    live_proxies = get_and_filter_proxies(
        protocols=protocols,
        anonymity_levels=anonymity_levels,
        country_codes=country_codes,
        google_passed=google_passed,
        source_file="live_proxies.json",
    )

    if not live_proxies:
        return []

    proxy_urls = [f"{p.get('protocol', 'http')}://{p['host']}:{p['port']}" for p in live_proxies]
    return proxy_urls
```

### 1.3 Mubeng Rotator Management

```python
"""Manages the Mubeng proxy checker and rotator executable."""

import logging
import socket
import subprocess
import time
from pathlib import Path
from typing import Optional

from paths import MUBENG_EXECUTABLE_PATH

logger = logging.getLogger(__name__)


def find_free_port() -> int:
    """Finds a free port on localhost."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("localhost", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def check_proxies_with_mubeng(
    candidate_proxy_file: Path,
    min_live_proxies: int = 1,
    mubeng_timeout: str = "5s",
) -> Optional[Path]:
    """Uses 'mubeng --check' to validate proxies."""
    timestamp = int(time.time() * 1000)
    output_file = candidate_proxy_file.parent / f"mubeng_check_output_{timestamp}.txt"

    mubeng_command = [
        str(MUBENG_EXECUTABLE_PATH),
        "--check",
        "-f", str(candidate_proxy_file),
        "-o", str(output_file),
        "-t", mubeng_timeout,
    ]

    try:
        process = subprocess.run(mubeng_command, capture_output=True, text=True, check=False)
        if process.returncode != 0:
            logger.error(f"Mubeng Check Failed: {process.stderr}")
            return None

        if not output_file.exists() or output_file.stat().st_size == 0:
            return None

        with open(output_file, "r") as f:
            live_proxies = [line.strip() for line in f if line.strip()]

        if len(live_proxies) < min_live_proxies:
            output_file.unlink(missing_ok=True)
            return None

        return output_file
    except FileNotFoundError:
        logger.error(f"Mubeng executable not found at {MUBENG_EXECUTABLE_PATH}")
        return None


def start_mubeng_rotator(
    live_proxy_file: Path,
    desired_port: int,
    mubeng_timeout: str = "15s",
    max_errors: int = 3
) -> Optional[subprocess.Popen]:
    """Starts the mubeng proxy rotator server as a background process."""
    if not live_proxy_file.exists() or live_proxy_file.stat().st_size == 0:
        return None

    mubeng_command = [
        str(MUBENG_EXECUTABLE_PATH),
        "-a", f"localhost:{desired_port}",
        "-f", str(live_proxy_file),
        "-t", mubeng_timeout,
        "--max-errors", str(max_errors),
    ]

    try:
        process = subprocess.Popen(mubeng_command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        time.sleep(1)

        if process.poll() is not None:
            stderr_output = process.stderr.read().decode("utf-8") if process.stderr else "N/A"
            logger.error(f"Mubeng Rotator failed: {stderr_output}")
            return None

        logger.info(f"Mubeng Rotator started on localhost:{desired_port}, PID: {process.pid}")
        return process
    except FileNotFoundError:
        return None


def stop_mubeng_rotator_server(process: subprocess.Popen) -> None:
    """Stops the mubeng proxy rotator server process."""
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
```

### 1.4 Celery Task Chain for Multi-Stage Validation

```python
"""Celery tasks for proxy scraping and checking."""

import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional

import time
import requests
from celery import group, chord, chain
from auto_biz.celery_app import app as celery_app
from paths import MUBENG_EXECUTABLE_PATH, PROXIES_DIR, PSC_EXECUTABLE_PATH

logger = logging.getLogger(__name__)


@celery_app.task
def scrape_new_proxies_task() -> Optional[str]:
    """Celery task to scrape a new list of potential proxies."""
    try:
        psc_output_file = PROXY_CHECKER_DIR / "out" / "proxies_pretty.json"
        psc_output_file.parent.mkdir(parents=True, exist_ok=True)

        cmd = [str(PSC_EXECUTABLE_PATH), "-o", str(psc_output_file)]
        subprocess.run(cmd, check=True, capture_output=True, text=True)

        with open(psc_output_file, "r") as f:
            proxies_found = len(json.load(f))

        # Auto-trigger checking
        check_scraped_proxies_task.delay()
        return f"Scraped {proxies_found} potential proxies."
    except Exception as e:
        logger.error(f"Proxy scraping task failed: {e}")
        raise


@celery_app.task
def check_scraped_proxies_task() -> str:
    """Dispatcher: Orchestrates multi-stage proxy validation."""
    psc_output_file = PROXY_CHECKER_DIR / "out" / "proxies_pretty.json"

    if not psc_output_file.exists():
        (scrape_new_proxies_task.s() | check_scraped_proxies_task.s()).delay()
        return "Chaining scrape before check"

    with open(psc_output_file, "r") as f:
        all_proxies = json.load(f)

    chunk_size = 100
    proxy_chunks = [all_proxies[i:i + chunk_size] for i in range(0, len(all_proxies), chunk_size)]

    # Celery chord: parallel mubeng checks -> combine -> dispatch quality checks
    header = group(mubeng_check_chunk_task.s(chunk) for chunk in proxy_chunks)
    callback_chain = chain(combine_mubeng_results_task.s(), dispatch_quality_checks_task.s())
    chord(header)(callback_chain)

    return f"Dispatched {len(proxy_chunks)} chunks for validation"


@celery_app.task
def mubeng_check_chunk_task(proxy_chunk: list[dict]) -> list[dict]:
    """Stage 1: Fast liveness check using mubeng."""
    live_proxies_in_chunk = []

    temp_input_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".txt")
    temp_output_file = tempfile.NamedTemporaryFile(mode='r', delete=False, suffix=".txt")

    try:
        for proxy in proxy_chunk:
            protocol = proxy.get("protocol", "http")
            temp_input_file.write(f"{protocol}://{proxy['host']}:{proxy['port']}\n")
        temp_input_file.close()

        cmd = [str(MUBENG_EXECUTABLE_PATH), "--check", "-f", temp_input_file.name, "-o", temp_output_file.name]
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=120)

        with open(temp_output_file.name, 'r') as f:
            live_proxy_urls = {line.strip() for line in f if line.strip()}

        proxy_data_map = {f"{p.get('protocol', 'http')}://{p['host']}:{p['port']}": p for p in proxy_chunk}

        for proxy_url in live_proxy_urls:
            if proxy_url in proxy_data_map:
                live_proxies_in_chunk.append(proxy_data_map[proxy_url])

    except Exception as e:
        logger.error(f"Mubeng check failed: {e}")
    finally:
        Path(temp_input_file.name).unlink(missing_ok=True)
        Path(temp_output_file.name).unlink(missing_ok=True)

    return live_proxies_in_chunk


@celery_app.task
def sequential_quality_check_task(proxy: dict) -> Optional[dict]:
    """Stage 2 & 3: Liveness + Google quality check."""
    proxy_url = f"{proxy.get('protocol', 'http')}://{proxy['host']}:{proxy['port']}"
    proxy["google_passed"] = False

    # Stage 2: Simple liveness check
    try:
        requests.get(
            "https://api.ipify.org?format=json",
            proxies={"http": proxy_url, "https": proxy_url},
            timeout=30
        ).raise_for_status()
    except requests.exceptions.RequestException:
        return None

    # Stage 3: Google quality check
    time.sleep(1)
    try:
        response = requests.get(
            "https://www.google.com",
            proxies={"http": proxy_url, "https": proxy_url},
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()
        if "<title>Google</title>" in response.text:
            proxy["google_passed"] = True
    except requests.exceptions.RequestException:
        pass

    return proxy


@celery_app.task
def process_final_results_task(results: list) -> str:
    """Final stage: Save validated proxies to JSON."""
    all_live_proxies = [proxy for proxy in results if proxy]

    if not all_live_proxies:
        return "No live proxies found"

    all_live_proxies.sort(key=lambda p: p.get("timeout", 999))

    json_output = PROXIES_DIR / "live_proxies.json"
    with open(json_output, "w") as f:
        json.dump(all_live_proxies, f, indent=2)

    return f"Saved {len(all_live_proxies)} validated proxies"
```

---

## 2. CONCLUSIONS

### What is Good / Usable

1. **PaidProxyService**: Clean PacketStream integration with sticky/random sessions
2. **Multi-stage validation**: mubeng -> ipify -> Google (comprehensive)
3. **Celery patterns**: chord/group/chain for parallel processing
4. **Filter system**: Protocol, anonymity, country, google_passed filters
5. **Mubeng integration**: Both checker and rotator modes
6. **Auto-refresh**: Background refresh when proxy count is low

### What is Outdated

1. **proxy-scraper-checker**: External Rust binary dependency

### What Must Be Rewritten

1. **Error handling**: Some tasks silently fail
2. **Chunking logic**: Hardcoded chunk_size=100

### How it Fits into AutoBiz

- **DIRECT PORT**: PaidProxyService, filter system, Celery patterns
- **MERGE with Scraper**: Combine ProxyChecker/ProxyOrchestrator from Scraper
- **KEEP**: Multi-stage validation workflow

### Conflicts or Duplicates with Previous Repos

| Pattern | Auto-Biz | Scraper | Best |
|---------|----------|---------|------|
| Paid proxy | PaidProxyService | PaidProxyService | **Same** |
| Free proxy | proxy-scraper-checker | ProxyService | **Scraper** (Python) |
| Validation | Celery chord | Sync loop | **Auto-Biz** (scalable) |
| Anonymity | Mapping dict | Enum | **Scraper** (type-safe) |
| Rotation | Mubeng | ProxyOrchestrator | **MERGE both** |

### Best Version Recommendation

**MERGE Auto-Biz + Scraper**:
- Auto-Biz: Celery task patterns, multi-stage validation workflow
- Scraper: ProxyChecker class (pycurl), ProxyService (pure Python), ProxyOrchestrator
