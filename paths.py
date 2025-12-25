from pathlib import Path

# 🧭 Absolute project root: ~/Projects/Bg-Estate
ROOT_DIR = Path(__file__).resolve().parent

# 📁 Data directory and DB path
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "bg-estate.db"  # Changed underscore to hyphen

# 📂 HTML source files (raw website dumps)
HTML_SITES_DIR = DATA_DIR / "html_sites"

# 🧠 Vector DBs for RAG/embedding
VECTOR_DB_DIR = DATA_DIR / "vector_dbs"

# 📄 .env location (loaded manually or via dotenv)
ENV_FILE = ROOT_DIR.parent / ".env"

# 🧹 Cleaned proxy lists directory (used by proxies.get_proxies)
CLEANED_PROXIES_DIR = ROOT_DIR / "proxies" / "free_proxies_lists"

# 🪵 Logs directory
LOGS_DIR = DATA_DIR / "logs"

# 🛠️ Proxy Scraper Checker tool paths
PROXY_CHECKER_DIR = ROOT_DIR / "proxies/external/proxy-scraper-checker"
PSC_EXECUTABLE_PATH = PROXY_CHECKER_DIR / "target/release/proxy-scraper-checker"

# Mubeng executable path
MUBENG_EXECUTABLE_PATH = ROOT_DIR / "proxies" / "external" / "mubeng"

# Proxies directory
PROXIES_DIR = ROOT_DIR / "proxies"

# Browsers directory
BROWSERS_DIR = ROOT_DIR / "browsers"
CHROMIUM_DIR = Path.home() / ".local" / "share" / "fingerprint-chromium"
CHROMIUM_EXECUTABLE_PATH = CHROMIUM_DIR / "chrome"
