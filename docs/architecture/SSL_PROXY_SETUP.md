# SSL Certificate Setup for Mubeng Proxy

> **Purpose**: Configure SSL certificates for HTTPS scraping through mubeng proxy.
>
> **Last updated**: 2025-12-26

---

## Table of Contents

1. [Overview](#overview)
2. [Why SSL Certificates Are Needed](#why-ssl-certificates-are-needed)
3. [How It Works](#how-it-works)
4. [Installation](#installation)
5. [Usage in Code](#usage-in-code)
6. [Troubleshooting](#troubleshooting)
7. [Security Considerations](#security-considerations)

---

## Overview

When scraping HTTPS websites through mubeng (our proxy rotator), we need to install mubeng's CA certificate in the browser. Without this, Firefox/Camoufox will reject the connection with `SEC_ERROR_UNKNOWN_ISSUER`.

**Key files:**
| File | Purpose |
|------|---------|
| `data/certs/mubeng-ca.pem` | Mubeng CA certificate (PEM format) |
| `data/certs/mubeng-ca.der` | Mubeng CA certificate (DER format) |
| `websites/scrapling_base.py` | Uses certificate in `fetch_stealth()` |
| `setup.sh` | Automates certificate extraction |

---

## Why SSL Certificates Are Needed

### The Problem

```
[Firefox/Camoufox] --HTTPS--> [mubeng proxy] --HTTPS--> [imot.bg]
        |                           |
        |   SEC_ERROR_UNKNOWN_ISSUER |
        |<--------------------------|
        Firefox doesn't trust mubeng's certificate
```

When you request `https://imot.bg` through mubeng:
1. Firefox connects to mubeng proxy
2. Mubeng intercepts the HTTPS request (MITM)
3. Mubeng presents its own SSL certificate to Firefox
4. Firefox rejects it because it's not from a trusted CA

### The Solution

Install mubeng's CA certificate so Firefox trusts it:

```
[Firefox/Camoufox] --HTTPS (trusted)--> [mubeng] --HTTPS--> [imot.bg]
        |                                   |
        | Certificate trusted via           | Real certificate
        | certificatePaths config           | from imot.bg
```

### Important: Target Websites Don't See Our Certificate

The mubeng certificate is **only** for the internal connection:

```
Your machine                           Internet
┌─────────────────┐                   ┌─────────────┐
│ Firefox/Camoufox│ ←─mubeng cert─→  │   mubeng    │ ←─real cert─→ imot.bg
└─────────────────┘                   └─────────────┘
     You install                      mubeng handles     Website sees
     cert HERE                        this internally    normal HTTPS
```

**Target websites (imot.bg, bazar.bg) never see the mubeng certificate.** They only see:
- The proxy's IP address
- A normal HTTPS request

---

## How It Works

### Mubeng's MITM Proxy

Mubeng uses [GoProxy](https://github.com/elazarl/goproxy) internally, which:
1. Generates a CA certificate on first run
2. For each HTTPS request, creates a certificate signed by that CA
3. Presents the generated certificate to the client (Firefox)
4. Makes a separate HTTPS connection to the target server

### Certificate Chain

```
GoProxy CA (self-signed)
    └── *.imot.bg (generated on-the-fly)
    └── *.bazar.bg (generated on-the-fly)
    └── *.httpbin.org (generated on-the-fly)
    └── ... (any HTTPS domain)
```

### Camoufox Integration

Camoufox (our stealth Firefox) accepts custom CA certificates via the `certificatePaths` config option:

```python
from camoufox.sync_api import Camoufox

with Camoufox(
    config={"certificatePaths": ["/path/to/mubeng-ca.pem"]}
) as browser:
    # Firefox now trusts mubeng's certificates
    page = browser.new_page()
    page.goto("https://example.com")
```

---

## Installation

### Automatic (Recommended)

Run the setup script:

```bash
./setup.sh
```

This will:
1. Start mubeng temporarily
2. Download the CA certificate from `http://localhost:8089/cert`
3. Convert from DER to PEM format
4. Save to `data/certs/mubeng-ca.pem`
5. Stop mubeng

### Manual Installation

If you need to install manually:

#### Step 1: Start Mubeng

```bash
# Create a temporary proxy file
echo "http://httpbin.org:80" > /tmp/test_proxy.txt

# Start mubeng (needs at least one proxy to start)
./proxies/external/mubeng -a localhost:8089 -f /tmp/test_proxy.txt &
sleep 2
```

#### Step 2: Download Certificate

```bash
# Download DER format certificate
curl -s -o data/certs/mubeng-ca.der http://localhost:8089/cert

# Verify it downloaded
file data/certs/mubeng-ca.der
# Should output: "Certificate, Version=3, Serial=..."
```

#### Step 3: Convert to PEM Format

```bash
# Convert DER to PEM (required by Camoufox)
openssl x509 -inform DER \
    -in data/certs/mubeng-ca.der \
    -out data/certs/mubeng-ca.pem

# Verify conversion
openssl x509 -in data/certs/mubeng-ca.pem -text -noout | head -10
```

#### Step 4: Stop Mubeng

```bash
pkill mubeng
```

### Verify Installation

```bash
# Check certificate exists and is valid
ls -la data/certs/mubeng-ca.pem
openssl x509 -in data/certs/mubeng-ca.pem -noout -subject -dates
```

Expected output:
```
subject=C = IL, ST = Center, L = Lod, O = GoProxy, OU = GoProxy, CN = goproxy.github.io, emailAddress = elazarl@gmail.com
notBefore=Apr  5 20:00:10 2017 GMT
notAfter=Mar 31 20:00:10 2037 GMT
```

---

## Usage in Code

### ScraplingMixin (websites/scrapling_base.py)

The `fetch_stealth()` method automatically uses the certificate:

```python
from websites.scrapling_base import ScraplingMixin

class MyScraper(ScraplingMixin):
    site_name = "example"

    def scrape(self, url):
        # Automatically uses mubeng proxy + SSL certificate
        page = self.fetch_stealth(url)
        return page
```

### Direct Camoufox Usage

If using Camoufox directly:

```python
from camoufox.sync_api import Camoufox
from pathlib import Path

CERT_PATH = Path("data/certs/mubeng-ca.pem")
PROXY = "http://localhost:8089"

with Camoufox(
    headless=True,
    proxy={"server": PROXY},
    config={"certificatePaths": [str(CERT_PATH)]} if CERT_PATH.exists() else {}
) as browser:
    page = browser.new_page()
    page.goto("https://example.com")
    html = page.content()
```

### Without Proxy (skip_proxy=True)

If you need to bypass the proxy (e.g., for testing):

```python
# No proxy, no certificate needed
page = scraper.fetch_stealth(url, skip_proxy=True)
```

---

## Troubleshooting

### Error: SEC_ERROR_UNKNOWN_ISSUER

**Cause**: Certificate not installed or not found.

**Solution**:
```bash
# Check certificate exists
ls -la data/certs/mubeng-ca.pem

# If missing, reinstall
./setup.sh
```

### Error: Proxy server error

**Cause**: Upstream proxy failed (not an SSL issue).

**Solution**: This means the free proxies in `live_proxies.txt` are dead. Refresh proxies:
```bash
python -c "from proxies.proxies_main import refresh_proxy_pool; refresh_proxy_pool()"
```

### Error: Certificate file empty (0 bytes)

**Cause**: Tried to download cert via proxy instead of directly.

**Solution**: Access `http://localhost:8089/cert` **directly**, not through the proxy:
```bash
# WRONG - goes through proxy
curl --proxy http://localhost:8089 http://mubeng/cert

# CORRECT - direct access
curl http://localhost:8089/cert
```

### Error: UnknownProperty: certificatePaths

**Cause**: Old version of Camoufox.

**Solution**: Upgrade Camoufox:
```bash
pip install --upgrade camoufox
```

### Certificate Expired

**Cause**: The GoProxy CA certificate expires in 2037, but if regenerated, dates may differ.

**Solution**: Re-extract the certificate:
```bash
rm data/certs/mubeng-ca.*
./setup.sh
```

---

## Security Considerations

### What This Enables

Installing the mubeng CA certificate allows mubeng to:
- Decrypt HTTPS traffic between your browser and mubeng
- Re-encrypt traffic between mubeng and target websites
- Rotate through different upstream proxies for each request

### What This Does NOT Do

- Does **not** expose your traffic to target websites
- Does **not** weaken security of target website connections
- Does **not** affect other browsers or system-wide SSL

### Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| Certificate only trusted in Camoufox | Low | Isolated to scraping sessions |
| Mubeng can see decrypted traffic | Low | Mubeng runs locally, no external exposure |
| Certificate could be stolen | Low | Only valid for mubeng's CA, not general use |

### Best Practices

1. **Don't commit the certificate to public repos** (it's in `.gitignore`)
2. **Regenerate certificate on new machines** via `setup.sh`
3. **Don't use this certificate for other purposes**

---

## Technical Details

### Certificate Format

| Format | File | Used By |
|--------|------|---------|
| DER | `mubeng-ca.der` | Raw download from mubeng |
| PEM | `mubeng-ca.pem` | Camoufox `certificatePaths` |

### Camoufox Config Options

Available certificate-related options:

```python
config = {
    "certificatePaths": ["/path/to/cert.pem"],  # Array of PEM file paths
    "certificates": [...]  # Alternative: inline certificate data
}
```

### Mubeng Certificate Endpoint

| Endpoint | Method | Response |
|----------|--------|----------|
| `http://localhost:8089/cert` | GET (direct) | `goproxy-cacert.der` |
| `http://mubeng/cert` | GET (via proxy) | 403 Forbidden |

**Note**: Must access `/cert` endpoint directly, not through the proxy.

---

## Related Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System overview
- [websites/SCRAPER_GUIDE.md](../../websites/SCRAPER_GUIDE.md) - Scraper usage
- [Camoufox Documentation](https://camoufox.com/python/usage/)
- [Mubeng GitHub](https://github.com/kitabisa/mubeng)
- [GoProxy GitHub](https://github.com/elazarl/goproxy)

---

*Document created: 2025-12-26*
