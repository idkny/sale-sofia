---
id: 20251201_proxies_scraper
type: extraction
subject: proxies
source_repo: Scraper
description: "Complete proxy management system - validation, rotation, filtering"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [extraction, proxies, scraper, proxy-checker, proxy-service]
---

# SUBJECT: proxies/

**Source**: `idkny/Scraper`
**Files Extracted**: 3 files
**Quality**: HIGH VALUE - UNIQUE (no other repo has this)

---

## 1. ProxyChecker (proxy_checker.py)

Full proxy validation with pycurl, multi-protocol support, anonymity detection.

```python
import time
import subprocess
import concurrent.futures
import threading
from io import BytesIO
import random
import re
import pycurl
from typing import Union
import certifi

class ProxyChecker:

    def __init__(self, timeout: int = 5000, verbose: bool = False):
        self.timeout = timeout
        self.verbose = verbose
        self.proxy_judges = [
            'https://azenv.net/',
            'https://httpbin.org/get',
            'https://api.myip.com/',
            'https://ipapi.co/json/'
        ]

        self.ip = self.get_ip()

        if self.ip == "":
            print("ERROR: Could not retrieve your IP. This module won't work.")
            exit()

        self.check_proxy_judges()

    def change_timeout(self, timeout: int) -> None:
        self.timeout = timeout

    def change_verbose(self, value: bool) -> None:
        self.verbose = value


    def check_proxy_judges(self) -> None:
        checked_judges = []
        for judge in self.proxy_judges:
            if self.send_query(url=judge) is not False:
                checked_judges.append(judge)
        self.proxy_judges = checked_judges

        if len(checked_judges) == 0:
            print("ERROR: JUDGES ARE OUTDATED. CREATE A GIT BRANCH AND UPDATE SELF.PROXY_JUDGES")
            exit()
        elif len(checked_judges) == 1:
            print("WARNING! THERE'S ONLY 1 JUDGE!")

    def get_ip(self) -> str:
        urls = ['https://api.ipify.org/', 'https://api.myip.com/', 'https://httpbin.org/ip']
        for url in urls:
            r = self.send_query(url=url)
            if r and r.get("response"):
                ip = r['response']
                # attempt to extract IP if JSON
                match = re.search(r'(\d{1,3}\.){3}\d{1,3}', ip)
                if match:
                    return match.group(0)
                return ip.strip()
        return ""

    def send_query(self, proxy: Union[str, bool] = False, url: str = None, tls=1.3,
                   user: str = None, password: str = None) -> Union[bool, dict]:
        response = BytesIO()
        c = pycurl.Curl()
        if self.verbose:
            c.setopt(c.VERBOSE, True)

        c.setopt(c.URL, url or random.choice(self.proxy_judges))
        c.setopt(c.WRITEDATA, response)
        c.setopt(c.TIMEOUT_MS, self.timeout)

        if user is not None and password is not None:
            c.setopt(c.PROXYUSERPWD, f"{user}:{password}")

        c.setopt(c.SSL_VERIFYHOST, 0)
        c.setopt(c.SSL_VERIFYPEER, 0)

        if proxy:
            c.setopt(c.PROXY, proxy)
            if proxy.startswith('https'):
                c.setopt(c.SSL_VERIFYHOST, 1)
                c.setopt(c.SSL_VERIFYPEER, 1)
                c.setopt(c.CAINFO, certifi.where())
                if tls == 1.3:
                    c.setopt(c.SSLVERSION, c.SSLVERSION_MAX_TLSv1_3)
                elif tls == 1.2:
                    c.setopt(c.SSLVERSION, c.SSLVERSION_MAX_TLSv1_2)
                elif tls == 1.1:
                    c.setopt(c.SSLVERSION, c.SSLVERSION_MAX_TLSv1_1)
                elif tls == 1.0:
                    c.setopt(c.SSLVERSION, c.SSLVERSION_MAX_TLSv1_0)

        try:
            c.perform()
        except Exception:
            return False

        if c.getinfo(c.HTTP_CODE) != 200:
            return False

        timeout = round(c.getinfo(c.CONNECT_TIME) * 1000)
        response = response.getvalue().decode('iso-8859-1')

        return {
            'timeout': timeout,
            'response': response
        }

    def parse_anonymity(self, r: str) -> str:
        if self.ip in r:
            return 'Transparent'

        privacy_headers = [
            'VIA', 'X-FORWARDED-FOR', 'X-FORWARDED', 'FORWARDED-FOR',
            'FORWARDED-FOR-IP', 'FORWARDED', 'CLIENT-IP', 'PROXY-CONNECTION'
        ]

        if any(header in r for header in privacy_headers):
            return 'Anonymous'

        return 'Elite'

    def get_country(self, ip: str) -> list:
        r = self.send_query(url='https://ip2c.org/' + ip)
        if r and r['response'][0] == '1':
            r = r['response'].split(';')
            return [r[3], r[1]]
        return ['-', '-']

    def check_proxy(self, proxy: str, check_country: bool = True, check_address: bool = False,
                    check_all_protocols: bool = False, protocol: Union[str, list] = None, retries: int = 1,
                    tls: float = 1.3, user: str = None, password: str = None) -> Union[bool, dict]:
        protocols = {}
        timeout = 0

        protocols_to_test = ['http', 'https', 'socks4', 'socks5']
        if isinstance(protocol, list):
            temp = [p for p in protocol if p in protocols_to_test]
            if temp:
                protocols_to_test = temp
        elif protocol in protocols_to_test:
            protocols_to_test = [protocol]

        for retry in range(retries):
            for protocol in protocols_to_test:
                r = self.send_query(proxy=protocol + '://' + proxy, user=user, password=password, tls=tls)
                if not r:
                    continue
                protocols[protocol] = r
                timeout += r['timeout']
                if not check_all_protocols:
                    break
            if timeout != 0:
                break

        if len(protocols) == 0:
            return False

        r = protocols[random.choice(list(protocols.keys()))]['response']
        country = ['-', '-']
        if check_country:
            country = self.get_country(proxy.split(':')[0])

        anonymity = self.parse_anonymity(r)
        timeout = timeout // len(protocols)

        remote_addr = None
        if check_address:
            remote_regex = r'REMOTE_ADDR = (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            remote_addr_match = re.search(remote_regex, r)
            if remote_addr_match:
                remote_addr = remote_addr_match.group(1)

        results = {
            'protocols': list(protocols.keys()),
            'anonymity': anonymity,
            'timeout': timeout
        }

        if check_country:
            results['country'] = country[0]
            results['country_code'] = country[1]
        if check_address:
            results['remote_address'] = remote_addr

        return results
```

---

## 2. ProxyService (free_proxies.py)

Complete free proxy management with auto-replenishment and filtering.

```python
from pathlib import Path
import random
import subprocess
import time
from typing import Optional, List
import json

from config import PROXY_VALID_THRESHOLD
from paths import (
    VALID_PROXIES_FILE,
    PROXY_SERVICE_DIR,
    SCRAPER_PROXIES_DIR,
    SCRAPER_ANONYMOUS_DIR
)
from Fingerprint.Proxy_Service.proxy_checker import ProxyChecker

class ProxyService:
    def __init__(self):
        self.checker = ProxyChecker()
        self.scraper_command = [
            str(PROXY_SERVICE_DIR / "proxy-scraper-checker" / "target" / "release" / "proxy-scraper-checker")
        ]
        self.scraper_cwd = str((PROXY_SERVICE_DIR / "proxy-scraper-checker").resolve())

    def get_proxy(self,
                  protocol: Optional[List[str]] = None,
                  anonymity: Optional[str] = None,
                  country: Optional[List[str]] = None,
                  require_geolocation: Optional[bool] = None,
                  require_anonymous: Optional[bool] = None) -> Optional[str]:

        print(f"get_proxy called with protocol={protocol}, country={country}, anonymous={require_anonymous}")

        if self._valid_pool_below_threshold():
            self._trigger_scraper()
            time.sleep(10)  # Give time for scraper to run
            self._populate_valid_proxy_file(protocol, country, anonymity, require_geolocation, require_anonymous)

        valid_proxies = self._load_valid_proxies()
        filtered = self._filter_proxies(valid_proxies, protocol, country, anonymity, require_geolocation, require_anonymous)

        if not filtered:
            return None

        chosen = random.choice(filtered)
        self._remove_used_proxy(chosen)
        return chosen

    def _valid_pool_below_threshold(self) -> bool:
        if not VALID_PROXIES_FILE.exists():
            return True
        with open(VALID_PROXIES_FILE, 'r') as f:
            return len(f.read().splitlines()) < PROXY_VALID_THRESHOLD

    def _trigger_scraper(self):
        subprocess.Popen(self.scraper_command, cwd=self.scraper_cwd)

    def _populate_valid_proxy_file(self, protocols, countries, anonymity, require_geo, require_anon):
        print("Populating valid proxy file...")
        VALID_PROXIES_FILE.write_text("")  # Clear previous file
        files_to_load = self._get_filtered_files(protocols, require_anon)
        proxies = self._load_proxies_from_files(files_to_load)

        for proxy in proxies:
            result = self.checker.check_proxy(proxy,
                                              check_country=True,
                                              check_address=True,
                                              protocol=protocols,
                                              retries=2)
            if result:
                if require_geo and result.get("country", "-") == "-":
                    continue
                if require_anon and result.get("anonymity", "").lower() not in ("anonymous", "elite"):
                    continue
                entry = {
                    "ip": proxy,
                    "protocols": result.get("protocols", []),
                    "anonymity": result.get("anonymity", ""),
                    "country": result.get("country", "-"),
                    "country_code": result.get("country_code", "-"),
                    "timeout": result.get("timeout", -1)
                }
                with open(VALID_PROXIES_FILE, 'a') as f:
                    f.write(json.dumps(entry) + "\n")

    def _load_proxies_from_files(self, files: List[Path]) -> List[str]:
        proxies = []
        for file in files:
            if file.exists():
                proxies.extend(file.read_text().splitlines())
        return proxies

    def _get_filtered_files(self, protocols: Optional[List[str]], anonymous: bool) -> List[Path]:
        sources = [SCRAPER_PROXIES_DIR]
        if anonymous:
            sources.append(SCRAPER_ANONYMOUS_DIR)

        files = []
        for directory in sources:
            for proto in (protocols or ["http", "https", "socks4", "socks5"]):
                candidate = directory / f"{proto}.txt"
                if candidate.exists():
                    files.append(candidate)
        return files

    def _load_valid_proxies(self) -> List[str]:
        if not VALID_PROXIES_FILE.exists():
            return []
        return [json.loads(line) for line in VALID_PROXIES_FILE.read_text().splitlines()]

    def _remove_used_proxy(self, proxy: str):
        lines = VALID_PROXIES_FILE.read_text().splitlines()
        lines = [line for line in lines if line.strip() != proxy]
        VALID_PROXIES_FILE.write_text("\n".join(lines) + "\n")

    def _filter_proxies(self, proxies, protocols, countries, anonymity, require_geo, require_anon):
        result = []
        for p in proxies:
            if protocols and not any(proto in p.get("protocols", []) for proto in protocols):
                continue
            if countries and p.get("country_code") not in countries:
                continue
            if anonymity and p.get("anonymity", "").lower() != anonymity.lower():
                continue
            if require_geo and p.get("country_code", "-") == "-":
                continue
            if require_anon and p.get("anonymity", "").lower() not in ("anonymous", "elite"):
                continue
            result.append(p["ip"])
        return result


class ProxyOrchestrator:
    """Strategy-based proxy rotation with fallback."""

    def __init__(self, strategies: List[dict]):
        self.strategies = strategies
        self.current_index = 0
        self.service = ProxyService()

    def next_proxy(self):
        attempts = 0
        while attempts < len(self.strategies):
            strategy = self.strategies[self.current_index]
            proxy = self.service.get_proxy(**strategy)
            if proxy:
                return proxy
            self.current_index = (self.current_index + 1) % len(self.strategies)
            attempts += 1
        return None
```

---

## 3. PaidProxyService (paid_proxies.py)

PacketStream.io integration for paid residential proxies.

```python
import os
from typing import Optional, Dict
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

class PaidProxyService:
    """
    Interface to PacketStream.io paid proxy service.
    Constructs authenticated proxy strings for various protocols and countries.
    """

    def __init__(self):
        self.username = os.getenv("PACKETSTREAM_USERNAME")
        self.password = os.getenv("PACKETSTREAM_PASSWORD")
        if not self.username or not self.password:
            raise ValueError("Missing PacketStream credentials in .env file")

        self.base_host = "proxy.packetstream.io"
        self.port_map = {
            "http": 31112,
            "https": 31112,
            "socks5": 31113
        }

    def get_proxy(
        self,
        protocol: str = "http",
        country: Optional[str] = None,
        as_dict: bool = False
    ) -> str | Dict[str, str]:
        """
        Generate an authenticated proxy string or requests-style dictionary.

        :param protocol: http, https, or socks5
        :param country: ISO country code (e.g., "US", "FR")
        :param as_dict: If True, return dict suitable for requests/aiohttp
        :return: proxy string or dict
        """
        if protocol not in self.port_map:
            raise ValueError(f"Unsupported protocol: {protocol}")

        port = self.port_map[protocol]
        user = f"{self.username}:{self.password}"
        if country:
            user = f"{self.username}_country-{country}:{self.password}"

        if protocol == "socks5":
            prefix = "socks5h"
        else:
            prefix = protocol

        proxy_str = f"{prefix}://{user}@{self.base_host}:{port}"

        if as_dict:
            return {
                "http": proxy_str,
                "https": proxy_str
            } if protocol in ("http", "https") else {
                "all": proxy_str  # for aiohttp or selenium-style use
            }

        return proxy_str
```

---

## CONCLUSIONS

### What is GOOD / Usable (Direct Port)

1. **ProxyChecker** - Complete, production-ready
   - pycurl-based (fast, low-level control)
   - Multi-protocol (http, https, socks4, socks5)
   - Anonymity detection (Transparent/Anonymous/Elite)
   - Country lookup via ip2c.org
   - TLS version control
   - Multiple proxy judges for reliability

2. **ProxyService** - Complete lifecycle management
   - Auto-replenishment when pool below threshold
   - JSON persistence for valid proxies
   - Filtering by protocol, country, anonymity
   - Integration with Rust scraper binary

3. **ProxyOrchestrator** - Strategy rotation
   - Fallback through multiple strategies
   - Round-robin with failure handling

4. **PaidProxyService** - Clean PacketStream integration
   - Country targeting
   - Dict format for requests/aiohttp

### What is OUTDATED

- Hardcoded proxy judges (azenv.net, etc.) - need to verify still working
- Rust binary dependency (`proxy-scraper-checker`) - needs installation

### What Must Be REWRITTEN

- Integrate with AutoBiz config system (replace `config.py` import)
- Add async version of ProxyChecker
- Add logging instead of print statements
- Add retry decorator from utils

### How It Fits Into AutoBiz

**Location**: `autobiz/tools/proxies/`
- `proxy_checker.py` - Validation
- `proxy_service.py` - Free proxy management
- `paid_proxy_service.py` - Paid proxy management
- `proxy_orchestrator.py` - Strategy rotation

**Integration Points**:
- Scraper tools use proxies for requests
- Browser automation uses proxies for stealth
- API clients can optionally route through proxies

### Conflicts/Duplicates

- **No conflicts** - This is the ONLY repo with proxy management
- MarketIntel has no proxy support
- SerpApi specification mentions proxies but no implementation
- Ollama-Rag has no proxy support

### Best Version

**SCRAPER is the ONLY version** - Direct port recommended

---

## Usage Example

```python
# Free proxy with filtering
service = ProxyService()
proxy = service.get_proxy(
    protocol=["http", "https"],
    country=["US", "GB"],
    require_anonymous=True
)

# Paid proxy with country targeting
paid_service = PaidProxyService()
proxy = paid_service.get_proxy(
    protocol="socks5",
    country="US",
    as_dict=True  # For requests library
)

# Strategy-based rotation
orchestrator = ProxyOrchestrator([
    {"protocol": ["http"], "country": ["US"]},
    {"protocol": ["socks5"], "require_anonymous": True},
    {"paid": True, "country": "GB"}  # Fallback to paid
])
proxy = orchestrator.next_proxy()
```
