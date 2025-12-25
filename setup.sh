#!/bin/bash
set -e  # Exit immediately if any command fails

# Resolve project root based on script location (works from any pwd)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[INFO] Starting setup..."

# --- Helpers ---
is_installed() {
  dpkg -s "$1" &>/dev/null
}

is_command() {
  command -v "$1" &>/dev/null
}

# --- System Dependencies (e.g., xvfb) ---
if ! is_installed xvfb; then
  echo "[INFO] xvfb not found. Installing with sudo..."
  sudo apt-get update -y && sudo apt-get install -y xvfb
else
  echo "[OK] xvfb is already installed."
fi

# --- Python Dependencies ---
echo "[INFO] Installing Python dependencies..."
pip install -r requirements.txt

# --- Camoufox ---
if ! python -m camoufox --help &>/dev/null; then
  echo "[WARN] camoufox module not available. Please verify it's installed in your environment."
else
  echo "[INFO] Downloading browser engine with Camoufox..."
  python -m camoufox fetch
fi

# --- Directory Structure ---
echo "[INFO] Setting up folders..."
mkdir -p proxies/external/proxy-scraper-checker

# --- Rust Proxy Checker Permissions ---
if [ -f proxies/external/proxy-scraper-checker/target/release/proxy-scraper-checker ]; then
  echo "[INFO] Setting execute permissions for Rust proxy checker..."
  chmod +x proxies/external/proxy-scraper-checker/target/release/proxy-scraper-checker
else
  echo "[WARN] Rust proxy checker not built yet, skipping chmod."
fi

# --- Mubeng Binary ---
MUBENG_VERSION="0.22.0"
MUBENG_DIR="proxies/external"
MUBENG_PATH="$MUBENG_DIR/mubeng"

if [ ! -f "$MUBENG_PATH" ]; then
  echo "[INFO] Installing Mubeng (Linux binary v$MUBENG_VERSION)..."
  mkdir -p "$MUBENG_DIR"
  wget -q "https://github.com/mubeng/mubeng/releases/download/v$MUBENG_VERSION/mubeng_${MUBENG_VERSION}_linux_amd64" -O "$MUBENG_PATH"
  chmod +x "$MUBENG_PATH"
else
  echo "[OK] Mubeng already exists at $MUBENG_PATH."
fi

echo "[INFO] Verifying Mubeng..."
"$MUBENG_PATH" --help


# --- Ungoogled Chromium from fingerprint-chromium ---

FPC_REPO="https://github.com/adryfish/fingerprint-chromium"
INSTALL_BASE="$HOME/.local/share/fingerprint-chromium"
INSTALL_DIR="$INSTALL_BASE/ungoogled-chromium"

echo "[INFO] Checking for latest fingerprint-chromium release..."

LATEST_URL=$(curl -s https://api.github.com/repos/adryfish/fingerprint-chromium/releases/latest \
  | grep "browser_download_url.*linux.tar.xz" \
  | cut -d '"' -f 4)

if [ -z "$LATEST_URL" ]; then
  echo "[ERROR] Could not find latest fingerprint-chromium Linux release URL."
  exit 1
fi

ARCHIVE_NAME=$(basename "$LATEST_URL")

if [ ! -d "$INSTALL_DIR" ]; then
  echo "[INFO] Chromium not found at $INSTALL_DIR. Downloading and installing..."

  mkdir -p "$INSTALL_BASE"
  wget -q "$LATEST_URL" -O "$INSTALL_BASE/$ARCHIVE_NAME"

  echo "[INFO] Extracting $ARCHIVE_NAME..."
  tar -xf "$INSTALL_BASE/$ARCHIVE_NAME" -C "$INSTALL_BASE"

  EXTRACTED_FOLDER=$(tar -tf "$INSTALL_BASE/$ARCHIVE_NAME" | head -1 | cut -f1 -d"/")
  mv "$INSTALL_BASE/$EXTRACTED_FOLDER" "$INSTALL_DIR"

  rm "$INSTALL_BASE/$ARCHIVE_NAME"

  echo "[OK] Chromium is ready at $INSTALL_DIR"
else
  echo "[OK] Chromium already installed at $INSTALL_DIR"
fi

echo "[✅ DONE] Setup completed successfully."
