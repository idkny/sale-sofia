"""
bazar.bg CSS selectors and regex patterns.

Centralizes all site-specific patterns for easier maintenance.
When bazar.bg changes their HTML structure, update patterns here.

Based on structure analysis performed on 2025-12-24.
"""

# =============================================================================
# URL PATTERNS
# =============================================================================

# Extract listing ID from URL: https://bazar.bg/obiava-52890419/prodawa-3-staen-gr-sofiia-tsentar
LISTING_ID_PATTERN = r"obiava-(\d+)"

# Extract neighborhood from URL slug: gr-sofiia-(.+)$
NEIGHBORHOOD_URL_PATTERN = r"gr-sofiia-(.+)$"

# Pagination pattern in URL: ?page=N
PAGE_URL_PATTERN = r"[?&]page=(\d+)"

# =============================================================================
# LISTING LINK PATTERNS (for search results)
# =============================================================================

# Links that are property listings contain /obiava-
LISTING_LINK_CONTAINS = ["/obiava-"]

# =============================================================================
# CSS SELECTORS (for search page)
# =============================================================================

# Search page listing selectors
LISTING_CONTAINER = ".listItemContainer.listItemContainerV2"
LISTING_LINK = "a.listItemLink"
LISTING_URL_ATTR = "href"
LISTING_ID_ATTR = "data-id"
TITLE = ".title span.title"
LOCATION = ".title .location"
DATE = ".title .date"
PRICE = ".title .price"
IMAGE = "img.cover.lazy"
IMAGE_URL_ATTR = "data-src"

# =============================================================================
# PAGINATION SELECTORS (for is_last_page detection)
# =============================================================================

# Pagination - detect max page from JavaScript variable
MAX_PAGE_JS_PATTERN = r"var maxPage = (\d+);"

# Next button text (Bulgarian)
NEXT_PAGE_SELECTORS = [
    "Следваща »",
    "следваща",
]

# Current page indicator (not specified in analysis, using general selector)
CURRENT_PAGE_SELECTOR = ".active"

# "No results" indicators
NO_RESULTS_PATTERNS = [
    "Няма намерени обяви",
    "няма резултати",
]

# =============================================================================
# PRICE PATTERNS
# =============================================================================

# JavaScript variables for price extraction
# Note: Handle both single and double quotes, and decimal numbers
AD_ID_JS = r"var adId = ['\"](\d+)['\"];"
AD_PRICE_JS = r"var adPrice = ['\"](\d+(?:\.\d+)?)['\"];"
AD_CURRENCY_JS = r"var adCurrency = ['\"]([€лв]+)['\"];"

# Price patterns - bazar.bg shows both EUR and BGN
PRICE_PATTERNS = [
    r"([\d\s]+)\s*€",  # EUR format: 389 998 €
    r"([\d\s]+)\s*EUR",  # EUR format: 150000 EUR
    r"([\d\s]+)\s*лв",  # BGN format: 762 769,79 лв
]

# =============================================================================
# SIZE PATTERNS (square meters)
# =============================================================================

# Square meter patterns - Bulgarian "кв. м." or "кв.м"
SQM_PATTERNS = [
    r"(?:Площ|Квадратура)[:\s]*(\d+(?:[.,]\d+)?)\s*(?:кв\.?\s*м\.?|m2|m²)",  # Площ: 100 кв.м or Квадратура: 100 кв. м.
    r"(\d+(?:[.,]\d+)?)\s*(?:кв\.?\s*м\.?|m2|m²)",  # General format: 100 кв.м, 100 m²
]

# =============================================================================
# FLOOR PATTERNS
# =============================================================================

# Floor patterns - extract floor number and total floors
# Note: [Ее] matches both Cyrillic Е and Latin E for resilience
FLOOR_PATTERNS = [
    # "Етаж: 4/8" or "Етаж 4/8" (colon optional, slash separator)
    r"[Ее]таж:?\s*(\d+)\s*/\s*(\d+)",
    # "Етаж 4 от 8" or "Етаж: 4 от 8"
    r"[Ее]таж:?\s*(\d+)\s*от\s*(\d+)",
    # "4 от 8 етаж" or "4/8 етаж"
    r"(\d+)\s*(?:от|/)\s*(\d+)\s*етаж",
]

# Floor number only (no total)
FLOOR_NUMBER_ONLY_PATTERN = r"[Ее]таж:?\s*(\d+)(?:\s|$)"

# =============================================================================
# ROOM COUNT MAPPINGS
# =============================================================================

# Bulgarian room type words to count (same terminology as imot.bg)
ROOM_WORDS_BG = {
    "едностаен": 1,
    "двустаен": 2,
    "тристаен": 3,
    "четиристаен": 4,
    "многостаен": 5,
    "мезонет": 3,
}

# URL slug mappings (Latin transliteration used in URLs)
ROOM_SLUGS = {
    "ednostaen": 1,
    "dvustaen": 2,
    "2-staen": 2,
    "tristaen": 3,
    "3-staen": 3,
    "chetiristaen": 4,
    "4-staen": 4,
    "mnogostaen": 5,
    "mezonet": 3,
}

# Numeric pattern: "3-стаен"
ROOM_NUMERIC_PATTERN = r"(\d+)-стаен"

# Room type pattern from specifications
ROOM_TYPE_PATTERN = r"Тип апартамент:\s*(\d+-стаен|[А-Яа-я]+стаен|Мезонет)"

# =============================================================================
# BATHROOM PATTERNS
# =============================================================================

# Bathroom count patterns
BATHROOM_PATTERNS = [
    r"(\d+)\s*(?:бани|бан|санитарен възел|санитарни възела|тоалетн)",  # e.g., "2 бани", "2 санитарни възела"
]

# Keywords indicating 2+ bathrooms
TWO_BATHROOM_KEYWORDS = [
    "2 бани",
    "2 санитарни възела",
    "две бани",
    "два санитарни",
]

# =============================================================================
# BUILDING TYPE KEYWORDS
# =============================================================================

# Building type keywords - bazar.bg terminology
BUILDING_TYPES = {
    "panel": ["Панел", "ЕПК", "ПК"],
    "brick": ["Тухла", "Гредоред"],
    "new_construction": ["Ново строителство", "Ново"],
}

# Building type pattern from specifications
BUILDING_TYPE_PATTERN = r"Вид строителство:\s*(Тухла|Панел|Ново строителство|ЕПК|Гредоред)"

# Construction year pattern
CONSTRUCTION_YEAR_PATTERN = r"Година:\s*(\d{4})"

# =============================================================================
# ACT STATUS PATTERNS
# =============================================================================

# Act status patterns for new construction
ACT_STATUS_PATTERNS = {
    "act16": [
        r"Акт 16",
        r"Act 16",
        r"АКТ 16",
        r"акт\s*16",
    ],
    "act15": [
        r"Акт 15",
        r"Act 15",
        r"АКТ 15",
        r"акт\s*15",
    ],
    "act14": [
        r"Акт 14",
        r"Act 14",
        r"АКТ 14",
        r"акт\s*14",
    ],
}

# =============================================================================
# METRO / LOCATION PATTERNS
# =============================================================================

# Sofia metro stations (same as imot.bg, should be consistent)
SOFIA_METRO_STATIONS = [
    "сердика", "св. климент охридски", "опълченска", "западен парк",
    "вардар", "константин величков", "обеля", "люлин", "запад",
    "бизнес парк", "младост", "интер експо център", "цариградско шосе",
    "академик александър теодоров-балан", "г.м. димитров", "мусагеница",
    "жолио кюри", "надежда", "хан кубрат", "княгиня мария луиза",
    "централна гара", "лъвов мост", "орлов мост", "стадион васил левски",
    "джеймс баучер", "витоша", "хладилника", "околовръстен път",
]

# Metro distance patterns
METRO_DISTANCE_PATTERNS = [
    r"(\d+)\s*(?:м|метра)\s*(?:до|от)\s*метро",  # e.g., "300м до метро"
    r"метро\s*(\d+)\s*(?:м|метра)",  # e.g., "метро 300м"
]

# Location pattern from page text
LOCATION_PATTERN = r"гр\.\s*София,\s*([А-Яа-я\s\.]+)"

# =============================================================================
# FEATURE KEYWORDS
# =============================================================================

# Feature keywords - bazar.bg terminology
FEATURES = {
    "elevator": ["асансьор", "лифт", "elevator"],
    "balcony": ["балкон", "тераса", "balcony"],
    "parking": ["паркинг", "гараж", "паркомясто", "parking"],
    "storage": ["мазе", "избено помещение", "storage", "склад"],
    "garden": ["градина", "двор", "yard", "garden"],
    "furnished": ["обзаведен", "мебелиран", "furnished"],
    "ac": ["климатик", "AC", "въздушно"],
}

# =============================================================================
# ORIENTATION KEYWORDS
# =============================================================================

# Orientation mapping - Bulgarian terms to compass directions
ORIENTATION_MAPPING = {
    "изток": "E",
    "запад": "W",
    "север": "N",
    "юг": "S",
    "югоизток": "SE",
    "югозапад": "SW",
    "североизток": "NE",
    "северозапад": "NW",
}

# Orientation pattern from specifications
ORIENTATION_PATTERN = r"изположение:\s*(изток|запад|север|юг|югоизток|югозапад|североизток|северозапад)"

# =============================================================================
# HEATING KEYWORDS
# =============================================================================

# Heating type keywords
HEATING_TYPES = {
    "central": ["ТЕЦ", "ЦО", "Централно"],
    "gas": ["Газ", "газ"],
    "electric": ["Електричество", "ел."],
    "ac": ["Климатик", "AC"],
    "fireplace": ["Камина"],
}

# Heating pattern from specifications
HEATING_PATTERN = r"Отопление:\s*(ТЕЦ|ЦО|Газ|Електричество|Климатик)"

# =============================================================================
# CONDITION KEYWORDS
# =============================================================================

# Condition type keywords
CONDITION_TYPES = {
    "ready": ["завършен", "луксозно"],
    "renovation": ["за ремонт"],
    "bare_walls": ["на зелено", "зелено", "груб строеж"],
}

# =============================================================================
# IMAGE PATTERNS
# =============================================================================

# bazar.bg image hosting domains and pattern
IMAGE_HOST_PATTERN = r"//(cdn\d+|imotstatic\d+)\.focus\.bg/imot/photosimotbg/.*?/(big|med)/.*?\.(jpg|jpeg|png)"

# Valid image extensions (likely same across sites)
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]

# =============================================================================
# CONTACT PATTERNS
# =============================================================================

# Bulgarian phone number pattern (same as imot.bg)
PHONE_PATTERN = r"(\+?359|0)\s*\d{2,3}\s*\d{3}\s*\d{2,3}"

# Agency identification pattern (bazar.bg doesn't use agency subdomains)
AGENCY_SUBDOMAIN_PATTERN = None

# Agency keywords to identify agency listings
AGENCY_KEYWORDS = [
    "агенция",
    "имоти",
    "estates",
    "properties",
]

# =============================================================================
# NEIGHBORHOOD TRANSLITERATION MAPPING
# =============================================================================

# Map URL slugs (Latin) to Bulgarian Cyrillic neighborhood names
NEIGHBORHOOD_TRANSLITERATION = {
    "tsentar": "Център",
    "borowo": "Борово",
    "gr-bankia": "гр. Банкя",
    "mladost": "Младост",
    "lyulin": "Люлин",
    "druzhba": "Дружба",
    "nadejda": "Надежда",
    "oborishte": "Оборище",
    "lozenets": "Лозенец",
    "manastirski-livadi": "Манастирски ливади",
    "studentski-grad": "Студентски град",
    "ovcha-kupel": "Овча купел",
    "pavlovo": "Павлово",
    "poduyane": "Подуяне",
    "reduta": "Редута",
    "geo-milev": "Гео Милев",
    "hipodruma": "Хиподрума",
    "iztok": "Изток",
    "zapaden-park": "Западен парк",
    "krasna-polyana": "Красна поляна",
    "krasno-selo": "Красно село",
    "levski": "Левски",
}

# =============================================================================
# DESCRIPTION KEYWORDS (to identify description blocks)
# =============================================================================

# Description keywords - terms that indicate description content
DESCRIPTION_KEYWORDS = [
    "апартамент",
    "имот",
    "продава",
    "предлага",
    "разполага",
    "възможност",
    "ПАНОРАМЕН",
    "Unique Estates",
    "представя",
]
