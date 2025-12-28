# Spec 116: Generic Scraper Template

**Status**: Active
**Created**: 2025-12-28
**Priority**: P1 (Future Enhancement)

---

## Overview

Create a configuration-driven scraper framework that allows adding new sites with **YAML config only** - no code changes required.

### The Universal Pattern

```
Category Page (filtered) → Grid of Items → Detail Page
         ↓                      ↓               ↓
E-commerce:  /shoes?gender=men     Product cards   Product page
Real Estate: /apartments?rooms=2   Listing cards   Listing page
```

Both e-commerce and real estate follow identical scraping patterns.

---

## Goals

1. **Zero code for new sites** - Just add a YAML config file
2. **Robust extraction** - Fallback selector chains (3-5 selectors per field)
3. **User provides starting URL** - Skip navigation (LLM not needed)
4. **Reuse existing infrastructure** - Scrapling, resilience, Celery integration

---

## Architecture

### Directory Structure

```
websites/
├── base_scraper.py           # Keep existing ListingData + BaseSiteScraper
├── scrapling_base.py         # Keep existing ScraplingMixin
├── generic/
│   ├── __init__.py
│   ├── config_loader.py      # Load + validate YAML configs
│   ├── selector_chain.py     # Fallback extraction engine
│   └── config_scraper.py     # Generic scraper using config
├── imot_bg/                  # Keep existing (migrate later)
└── bazar_bg/                 # Keep existing (migrate later)

config/sites/
├── imot_bg.yaml              # Existing
├── bazar_bg.yaml             # Existing
├── olx_bg.yaml               # NEW - just config!
└── homes_bg.yaml             # NEW - just config!
```

### YAML Config Schema

```yaml
# config/sites/olx_bg.yaml
site:
  name: olx.bg
  domain: www.olx.bg
  encoding: utf-8              # or windows-1251 for Bulgarian sites

urls:
  listing_pattern: "/ad/"      # Regex to identify listing URLs from search results
  id_pattern: "/ad/([^/]+)"    # Regex to extract listing ID from URL

pagination:
  type: numbered               # Options: numbered, infinite_scroll, load_more, next_link
  param: page                  # URL parameter for page number (?page=2)
  start: 1                     # First page number
  next_selector: "a[data-cy='pagination-forward']"  # For next_link type
  load_more_selector: null     # For load_more type
  max_pages: 50                # Safety limit

listing_page:
  container: "[data-cy='l-card']"           # CSS selector for each listing card
  link: "a[href*='/ad/']"                   # CSS selector for link to detail page
  # Optional: extract some fields from listing page (faster, less requests)
  quick_fields:
    price: ".price-label"
    title: "h6"

detail_page:
  selectors:
    # Each field has a fallback chain - try in order until one works
    price:
      - "[data-testid='ad-price-container'] h3"
      - ".price-label strong"
      - "h3.css-price"
    title:
      - "h1[data-cy='ad_title']"
      - "h1.title"
      - "h1"
    description:
      - "[data-cy='ad_description'] div"
      - ".description-content"
      - "div.text-body"
    sqm:
      - "li:contains('Квадратура') span"
      - "[data-code='m'] span"
    rooms:
      - "li:contains('Стаи') span"
      - "[data-code='rooms'] span"
    floor:
      - "li:contains('Етаж') span"
      - "[data-code='floor'] span"
    building_type:
      - "li:contains('Вид строителство') span"
    images:
      - "img[data-testid='swiper-image']"
      - "img.gallery-image"
      - "div.swiper-slide img"
    location:
      - "[data-testid='map-link-text']"
      - "address"
    contact_phone:
      - "[data-testid='phones'] span"
      - "a[href^='tel:']"

  # Field type hints for parsing
  field_types:
    price: currency_bgn_eur      # Parse BGN/EUR amounts
    sqm: number                  # Extract numeric value
    rooms: integer               # Extract integer
    floor: floor_pattern         # Parse "3/6" or "3 от 6"
    images: list                 # Collect all matches

extraction:
  # LLM fallback (disabled for weak hardware)
  llm_fallback: false
  llm_model: null

  # Text preprocessing
  clean_whitespace: true
  decode_html_entities: true

timing:
  delay_seconds: 2.0
  max_per_domain: 2

# Site-specific quirks
quirks:
  requires_js: false            # If true, use Playwright/Camoufox
  has_lazy_images: true         # If true, scroll to load images
  encoding_fallback: windows-1251
```

---

## 3-Tier Extraction Strategy

```
Tier 1: CSS Selector Chain (fast, free)
        ├── Try selector[0]
        ├── If empty, try selector[1]
        ├── If empty, try selector[2]
        └── Continue until match or exhausted

Tier 2: XPath Fallback (for complex DOM)
        └── Only if CSS chain fails and XPath defined

Tier 3: LLM Fallback (disabled by default)
        └── Only for problematic sites with unstable DOM
        └── Preprocess HTML → markdown to reduce tokens
```

### Selector Chain Implementation

```python
# websites/generic/selector_chain.py

def extract_field(page: Adaptor, selectors: list[str], field_type: str = "text") -> Optional[str]:
    """
    Try selectors in order until one returns a value.

    Args:
        page: Scrapling Adaptor
        selectors: List of CSS selectors to try in order
        field_type: How to parse the result (text, number, currency, list)

    Returns:
        Extracted and parsed value, or None if all selectors fail
    """
    for selector in selectors:
        try:
            if field_type == "list":
                elements = page.css(selector)
                if elements:
                    return [get_attr(el, "src") or get_text(el) for el in elements]
            else:
                element = page.css_first(selector)
                if element:
                    raw_value = get_text(element)
                    return parse_field(raw_value, field_type)
        except Exception:
            continue
    return None
```

---

## Implementation Phases

### Phase 1: Core Framework

1. **1.1** Create `websites/generic/__init__.py`
2. **1.2** Create `config_loader.py` - YAML loading with validation
3. **1.3** Create `selector_chain.py` - Fallback extraction engine
4. **1.4** Create `config_scraper.py` - Generic ConfigScraper class
5. **1.5** Write unit tests for config loading and selector chains

### Phase 2: Field Parsers

1. **2.1** Create field type parsers (currency, number, floor_pattern, etc.)
2. **2.2** Support Bulgarian-specific patterns (BGN/EUR, кв.м, етаж)
3. **2.3** Write unit tests for all parsers

### Phase 3: Pagination Support

1. **3.1** Implement numbered pagination
2. **3.2** Implement next_link pagination
3. **3.3** Implement load_more pagination (click simulation)
4. **3.4** Implement infinite_scroll pagination
5. **3.5** Write pagination detection tests

### Phase 4: OLX.bg Pilot

1. **4.1** Research OLX.bg HTML structure (inspect manually)
2. **4.2** Create `config/sites/olx_bg.yaml`
3. **4.3** Test extraction with sample pages
4. **4.4** Verify pagination works
5. **4.5** Integration test: full scrape of test category

### Phase 5: Homes.bg

1. **5.1** Research homes.bg HTML structure
2. **5.2** Create `config/sites/homes_bg.yaml`
3. **5.3** Test and verify

### Phase 6: Migration (Optional)

1. **6.1** Create YAML configs for imot.bg and bazar.bg
2. **6.2** Validate against existing scraper output
3. **6.3** Deprecate old scraper code (keep as fallback)

---

## Integration with Existing Code

### Reuse from Current Codebase

| Component | Location | How to Reuse |
|-----------|----------|--------------|
| `ListingData` | `websites/base_scraper.py` | Use as-is for output |
| `ScraplingMixin` | `websites/scrapling_base.py` | Inherit for parsing |
| Rate limiting | `resilience/rate_limiter.py` | Use existing |
| Circuit breaker | `resilience/circuit_breaker.py` | Use existing |
| Celery tasks | `scraping/tasks.py` | Extend for new sites |
| Site config | `config/scraping_config.py` | Extend loader |

### ConfigScraper Class

```python
# websites/generic/config_scraper.py

class ConfigScraper(ScraplingMixin, BaseSiteScraper):
    """
    Generic scraper that uses YAML configuration instead of hardcoded selectors.
    """

    def __init__(self, config_path: str):
        super().__init__()
        self.config = load_config(config_path)
        self.site_name = self.config["site"]["name"]
        self.base_url = f"https://{self.config['site']['domain']}"

    def extract_listing(self, html: str, url: str) -> Optional[ListingData]:
        """Extract listing using selector chains from config."""
        page = self.parse(html, url)

        # Extract each field using fallback chain
        data = {}
        for field, selectors in self.config["detail_page"]["selectors"].items():
            field_type = self.config["detail_page"].get("field_types", {}).get(field, "text")
            data[field] = extract_field(page, selectors, field_type)

        # Extract ID from URL
        external_id = self._extract_id(url)

        return ListingData(
            external_id=external_id,
            url=url,
            source_site=self.site_name,
            price_eur=data.get("price"),
            sqm_total=data.get("sqm"),
            rooms_count=data.get("rooms"),
            # ... map all fields
        )

    def extract_search_results(self, html: str) -> List[str]:
        """Extract listing URLs from search page using config."""
        page = self.parse(html)
        container_sel = self.config["listing_page"]["container"]
        link_sel = self.config["listing_page"]["link"]

        urls = []
        for card in page.css(container_sel):
            link = card.css_first(link_sel)
            if link:
                href = self.get_attr(link, "href")
                urls.append(self._normalize_url(href))
        return urls
```

---

## Validation & Testing

### Config Validation

```python
# Validate YAML against schema before use
def validate_config(config: dict) -> List[str]:
    errors = []

    # Required fields
    if "site" not in config:
        errors.append("Missing 'site' section")
    if "detail_page" not in config or "selectors" not in config["detail_page"]:
        errors.append("Missing 'detail_page.selectors'")

    # Selector format
    for field, selectors in config.get("detail_page", {}).get("selectors", {}).items():
        if not isinstance(selectors, list):
            errors.append(f"Field '{field}' selectors must be a list")
        if len(selectors) < 2:
            errors.append(f"Field '{field}' should have at least 2 fallback selectors")

    return errors
```

### Test Strategy

1. **Unit tests**: Config loading, selector chains, field parsers
2. **Integration tests**: Full extraction from saved HTML samples
3. **Regression tests**: Compare ConfigScraper output vs hardcoded scraper output

---

## Success Criteria

1. **New site in <1 hour**: Adding olx.bg or homes.bg requires only YAML
2. **No code changes**: Generic engine handles all sites
3. **Extraction accuracy**: ≥95% field extraction rate
4. **Fallback working**: If selector[0] breaks, selector[1] takes over

---

## Research Sources

### Real Estate Scraping

- [fgrillo89/real-estate-scraper](https://github.com/fgrillo89/real-estate-scraper) - WebsiteConfig pattern
- [Sqrap - JSON Schema Web Scraper](https://github.com/dinostheo/sqrap)
- [SelectorLib - YAML Scraper Definitions](https://selectorlib.com/)
- [ScrapeGraphAI - LLM-powered scraping](https://scrapegraphai.com/blog/llm-web-scraping)
- [Scraping Real Estate Data With Python](https://oxylabs.io/blog/scraping-real-estate-data)
- [How to Scrape Real Estate Data from Zillow](https://dev.to/eunit/how-to-scrape-real-estate-data-from-zillow-in-2026-step-by-step-guide-j13)
- [Building a Real Estate Web Scraper](https://www.scrapingbee.com/blog/real-estate-web-scraping/)

### E-commerce & Generic Scraping

- [Crawlee for Python](https://github.com/apify/crawlee-python) - Full framework
- [Crawlee One](https://github.com/JuroOravec/crawlee-one) - Config-driven builder
- [llm-scraper](https://github.com/mishushakov/llm-scraper) - LLM extraction
- [Firecrawl](https://github.com/firecrawl/firecrawl) - Web Data API
- [Building a Generic Scraper for Multiple Websites](https://substack.thewebscraping.club/p/building-a-generic-scraper-for-multiple)
- [Scrapy Architecture Overview](https://docs.scrapy.org/en/latest/topics/architecture.html)
- [scrapy-settings YAML integration](https://github.com/taicaile/scrapy-settings)

### Selector Strategies

- [CSS Selector Cheat Sheet for Web Scraping](https://rebrowser.net/blog/css-selector-cheat-sheet-for-web-scraping-a-complete-guide)
- [Scrapy Selectors & Chaining](https://docs.scrapy.org/en/latest/topics/selectors.html)
- [CSS vs XPath for Web Scraping](https://www.scrapingbee.com/blog/xpath-vs-css-selector/)
- [Web Scraping XPATH and CSS Selectors](https://substack.thewebscraping.club/p/xpath-css-selectors-web-scraping)

### Pagination

- [Pagination Strategies in Web Scraping](https://brightdata.com/blog/web-data/pagination-web-scraping)
- [Pagination Techniques in JavaScript Web Scraping](https://scrapingant.com/blog/javascript-pagination-web-scraping)
- [How to Master Web Scraping Pagination](https://www.scrapingbee.com/blog/web-scraping-pagination/)

### Anti-Bot & Architecture

- [Top 7 Anti-Scraping Techniques in 2025](https://medium.com/@datajournal/most-popular-anti-scraping-techniques-in-2024-765473ea0451)
- [Large-Scale Web Scraping Architecture](https://www.scrapehero.com/how-to-build-and-run-scrapers-on-a-large-scale/)
- [Setting up Large-Scale Scraping Architecture with Python](https://sia-ai.medium.com/setting-up-a-large-scale-scraping-architecture-with-python-3b26cb6571a6)
- [Web Scraping With Scrapy: Complete Guide 2025](https://scrapfly.io/blog/posts/web-scraping-with-scrapy)

---

## Notes

- **LLM fallback disabled** by default due to hardware constraints
- **User provides filtered starting URL** - no navigation needed
- **Migrate existing scrapers later** - new sites first, then optional migration
