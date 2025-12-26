# scrapling Documentation

Source: https://github.com/D4Vinci/Scrapling
Branch: main
Synced: 2025-12-26T14:31:17.108337

============================================================


## File: README.md
<!-- Source: docs/README.md -->

Automated translations: [العربيه](README_AR.md) | [Español](README_ES.md) | [Deutsch](README_DE.md) | [简体中文](README_CN.md) | [日本語](README_JP.md) | [Русский](README_RU.md)


<p align=center>
  <br>
  <a href="https://scrapling.readthedocs.io/en/latest/" target="_blank"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/poster.png" style="width: 50%; height: 100%;" alt="main poster"/></a>
  <br>
  <i><code>Easy, effortless Web Scraping as it should be!</code></i>
</p>
<p align="center">
    <a href="https://github.com/D4Vinci/Scrapling/actions/workflows/tests.yml" alt="Tests">
        <img alt="Tests" src="https://github.com/D4Vinci/Scrapling/actions/workflows/tests.yml/badge.svg"></a>
    <a href="https://badge.fury.io/py/Scrapling" alt="PyPI version">
        <img alt="PyPI version" src="https://badge.fury.io/py/Scrapling.svg"></a>
    <a href="https://pepy.tech/project/scrapling" alt="PyPI Downloads">
        <img alt="PyPI Downloads" src="https://static.pepy.tech/personalized-badge/scrapling?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=GREEN&left_text=Downloads"></a>
    <br/>
    <a href="https://discord.gg/EMgGbDceNQ" alt="Discord" target="_blank">
      <img alt="Discord" src="https://img.shields.io/discord/1360786381042880532?style=social&logo=discord&link=https%3A%2F%2Fdiscord.gg%2FEMgGbDceNQ">
    </a>
    <a href="https://x.com/Scrapling_dev" alt="X (formerly Twitter)">
      <img alt="X (formerly Twitter) Follow" src="https://img.shields.io/twitter/follow/Scrapling_dev?style=social&logo=x&link=https%3A%2F%2Fx.com%2FScrapling_dev">
    </a>
    <br/>
    <a href="https://pypi.org/project/scrapling/" alt="Supported Python versions">
        <img alt="Supported Python versions" src="https://img.shields.io/pypi/pyversions/scrapling.svg"></a>
</p>

<p align="center">
    <a href="https://scrapling.readthedocs.io/en/latest/parsing/selection/">
        Selection methods
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/fetching/choosing/">
        Choosing a fetcher
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/cli/overview/">
        CLI
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/ai/mcp-server/">
        MCP mode
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/tutorials/migrating_from_beautifulsoup/">
        Migrating from Beautifulsoup
    </a>
</p>

**Stop fighting anti-bot systems. Stop rewriting selectors after every website update.**

Scrapling isn't just another Web Scraping library. It's the first **adaptive** scraping library that learns from website changes and evolves with them. While other libraries break when websites update their structure, Scrapling automatically relocates your elements and keeps your scrapers running.

Built for the modern Web, Scrapling features **its own rapid parsing engine** and fetchers to handle all Web Scraping challenges you face or will face. Built by Web Scrapers for Web Scrapers and regular users, there's something for everyone.

```python
>> from scrapling.fetchers import Fetcher, AsyncFetcher, StealthyFetcher, DynamicFetcher
>> StealthyFetcher.adaptive = True
# Fetch websites' source under the radar!
>> page = StealthyFetcher.fetch('https://example.com', headless=True, network_idle=True)
>> print(page.status)
200
>> products = page.css('.product', auto_save=True)  # Scrape data that survives website design changes!
>> # Later, if the website structure changes, pass `adaptive=True`
>> products = page.css('.product', adaptive=True)  # and Scrapling still finds them!
```

# Sponsors 

<!-- sponsors -->

<a href="https://www.scrapeless.com/en?utm_source=official&utm_term=scrapling" target="_blank" title="Effortless Web Scraping Toolkit for Business and Developers"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/scrapeless.jpg"></a>
<a href="https://www.thordata.com/?ls=github&lk=github" target="_blank" title="Unblockable proxies and scraping infrastructure, delivering real-time, reliable web data to power AI models and workflows."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/thordata.jpg"></a>
<a href="https://evomi.com?utm_source=github&utm_medium=banner&utm_campaign=d4vinci-scrapling" target="_blank" title="Evomi is your Swiss Quality Proxy Provider, starting at $0.49/GB"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/evomi.png"></a>
<a href="https://serpapi.com/?utm_source=scrapling" target="_blank" title="Scrape Google and other search engines with SerpApi"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/SerpApi.png"></a>
<a href="https://visit.decodo.com/Dy6W0b" target="_blank" title="Try the Most Efficient Residential Proxies for Free"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/decodo.png"></a>
<a href="https://petrosky.io/d4vinci" target="_blank" title="PetroSky delivers cutting-edge VPS hosting."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/petrosky.png"></a>
<a href="https://www.swiftproxy.net/" target="_blank" title="Unlock Reliable Proxy Services with Swiftproxy!"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/swiftproxy.png"></a>
<a href="https://www.rapidproxy.io/?ref=d4v" target="_blank" title="Affordable Access to the Proxy World – bypass CAPTCHAs blocks, and avoid additional costs."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/rapidproxy.jpg"></a>
<a href="https://browser.cash/?utm_source=D4Vinci&utm_medium=referral" target="_blank" title="Browser Automation & AI Browser Agent Platform"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/browserCash.png"></a>

<!-- /sponsors -->

<i><sub>Do you want to show your ad here? Click [here](https://github.com/sponsors/D4Vinci) and choose the tier that suites you!</sub></i>

---

## Key Features

### Advanced Websites Fetching with Session Support
- **HTTP Requests**: Fast and stealthy HTTP requests with the `Fetcher` class. Can impersonate browsers' TLS fingerprint, headers, and use HTTP3.
- **Dynamic Loading**: Fetch dynamic websites with full browser automation through the `DynamicFetcher` class supporting Playwright's Chromium, real Chrome, and custom stealth mode.
- **Anti-bot Bypass**: Advanced stealth capabilities with `StealthyFetcher` using a modified version of Firefox and fingerprint spoofing. Can bypass all types of Cloudflare's Turnstile and Interstitial with automation easily.
- **Session Management**: Persistent session support with `FetcherSession`, `StealthySession`, and `DynamicSession` classes for cookie and state management across requests.
- **Async Support**: Complete async support across all fetchers and dedicated async session classes.

### Adaptive Scraping & AI Integration
- 🔄 **Smart Element Tracking**: Relocate elements after website changes using intelligent similarity algorithms.
- 🎯 **Smart Flexible Selection**: CSS selectors, XPath selectors, filter-based search, text search, regex search, and more. 
- 🔍 **Find Similar Elements**: Automatically locate elements similar to found elements.
- 🤖 **MCP Server to be used with AI**: Built-in MCP server for AI-assisted Web Scraping and data extraction. The MCP server features custom, powerful capabilities that utilize Scrapling to extract targeted content before passing it to the AI (Claude/Cursor/etc), thereby speeding up operations and reducing costs by minimizing token usage. ([demo video](https://www.youtube.com/watch?v=qyFk3ZNwOxE))

### High-Performance & battle-tested Architecture
- 🚀 **Lightning Fast**: Optimized performance outperforming most Python scraping libraries.
- 🔋 **Memory Efficient**: Optimized data structures and lazy loading for a minimal memory footprint.
- ⚡ **Fast JSON Serialization**: 10x faster than the standard library.
- 🏗️ **Battle tested**: Not only does Scrapling have 92% test coverage and full type hints coverage, but it has been used daily by hundreds of Web Scrapers over the past year.

### Developer/Web Scraper Friendly Experience
- 🎯 **Interactive Web Scraping Shell**: Optional built-in IPython shell with Scrapling integration, shortcuts, and new tools to speed up Web Scraping scripts development, like converting curl requests to Scrapling requests and viewing requests results in your browser.
- 🚀 **Use it directly from the Terminal**: Optionally, you can use Scrapling to scrape a URL without writing a single code!
- 🛠️ **Rich Navigation API**: Advanced DOM traversal with parent, sibling, and child navigation methods.
- 🧬 **Enhanced Text Processing**: Built-in regex, cleaning methods, and optimized string operations.
- 📝 **Auto Selector Generation**: Generate robust CSS/XPath selectors for any element.
- 🔌 **Familiar API**: Similar to Scrapy/BeautifulSoup with the same pseudo-elements used in Scrapy/Parsel.
- 📘 **Complete Type Coverage**: Full type hints for excellent IDE support and code completion.
- 🔋 **Ready Docker image**: With each release, a Docker image containing all browsers is automatically built and pushed.

## Getting Started

### Basic Usage
```python
from scrapling.fetchers import Fetcher, StealthyFetcher, DynamicFetcher
from scrapling.fetchers import FetcherSession, StealthySession, DynamicSession

# HTTP requests with session support
with FetcherSession(impersonate='chrome') as session:  # Use latest version of Chrome's TLS fingerprint
    page = session.get('https://quotes.toscrape.com/', stealthy_headers=True)
    quotes = page.css('.quote .text::text')

# Or use one-off requests
page = Fetcher.get('https://quotes.toscrape.com/')
quotes = page.css('.quote .text::text')

# Advanced stealth mode (Keep the browser open until you finish)
with StealthySession(headless=True, solve_cloudflare=True) as session:
    page = session.fetch('https://nopecha.com/demo/cloudflare', google_search=False)
    data = page.css('#padded_content a')

# Or use one-off request style, it opens the browser for this request, then closes it after finishing
page = StealthyFetcher.fetch('https://nopecha.com/demo/cloudflare')
data = page.css('#padded_content a')
    
# Full browser automation (Keep the browser open until you finish)
with DynamicSession(headless=True, disable_resources=False, network_idle=True) as session:
    page = session.fetch('https://quotes.toscrape.com/', load_dom=False)
    data = page.xpath('//span[@class="text"]/text()')  # XPath selector if you prefer it

# Or use one-off request style, it opens the browser for this request, then closes it after finishing
page = DynamicFetcher.fetch('https://quotes.toscrape.com/')
data = page.css('.quote .text::text')
```

> [!NOTE]
> There's a wonderful guide to get you started quickly with Scraping [here](https://substack.thewebscraping.club/p/scrapling-hands-on-guide) written by The Web Scraping Club. In case you find it easier to get you started than the [documentation website](https://scrapling.readthedocs.io/en/latest/).

### Advanced Parsing & Navigation
```python
from scrapling.fetchers import Fetcher

# Rich element selection and navigation
page = Fetcher.get('https://quotes.toscrape.com/')

# Get quotes with multiple selection methods
quotes = page.css('.quote')  # CSS selector
quotes = page.xpath('//div[@class="quote"]')  # XPath
quotes = page.find_all('div', {'class': 'quote'})  # BeautifulSoup-style
# Same as
quotes = page.find_all('div', class_='quote')
quotes = page.find_all(['div'], class_='quote')
quotes = page.find_all(class_='quote')  # and so on...
# Find element by text content
quotes = page.find_by_text('quote', tag='div')

# Advanced navigation
first_quote = page.css_first('.quote')
quote_text = first_quote.css('.text::text')
quote_text = page.css('.quote').css_first('.text::text')  # Chained selectors
quote_text = page.css_first('.quote .text').text  # Using `css_first` is faster than `css` if you want the first element
author = first_quote.next_sibling.css('.author::text')
parent_container = first_quote.parent

# Element relationships and similarity
similar_elements = first_quote.find_similar()
below_elements = first_quote.below_elements()
```
You can use the parser right away if you don't want to fetch websites like below:
```python
from scrapling.parser import Selector

page = Selector("<html>...</html>")
```
And it works precisely the same way!

### Async Session Management Examples
```python
import asyncio
from scrapling.fetchers import FetcherSession, AsyncStealthySession, AsyncDynamicSession

async with FetcherSession(http3=True) as session:  # `FetcherSession` is context-aware and can work in both sync/async patterns
    page1 = session.get('https://quotes.toscrape.com/')
    page2 = session.get('https://quotes.toscrape.com/', impersonate='firefox135')

# Async session usage
async with AsyncStealthySession(max_pages=2) as session:
    tasks = []
    urls = ['https://example.com/page1', 'https://example.com/page2']
    
    for url in urls:
        task = session.fetch(url)
        tasks.append(task)
    
    print(session.get_pool_stats())  # Optional - The status of the browser tabs pool (busy/free/error)
    results = await asyncio.gather(*tasks)
    print(session.get_pool_stats())
```

## CLI & Interactive Shell

Scrapling v0.3 includes a powerful command-line interface:

[![asciicast](https://asciinema.org/a/736339.svg)](https://asciinema.org/a/736339)

```bash
# Launch interactive Web Scraping shell
scrapling shell

# Extract pages to a file directly without programming (Extracts the content inside `body` tag by default)
# If the output file ends with `.txt`, then the text content of the target will be extracted.
# If ended with `.md`, it will be a markdown representation of the HTML content, and `.html` will be the HTML content right away.
scrapling extract get 'https://example.com' content.md
scrapling extract get 'https://example.com' content.txt --css-selector '#fromSkipToProducts' --impersonate 'chrome'  # All elements matching the CSS selector '#fromSkipToProducts'
scrapling extract fetch 'https://example.com' content.md --css-selector '#fromSkipToProducts' --no-headless
scrapling extract stealthy-fetch 'https://nopecha.com/demo/cloudflare' captchas.html --css-selector '#padded_content a' --solve-cloudflare
```

> [!NOTE]
> There are many additional features, but we want to keep this page concise, such as the MCP server and the interactive Web Scraping Shell. Check out the full documentation [here](https://scrapling.readthedocs.io/en/latest/)

## Performance Benchmarks

Scrapling isn't just powerful—it's also blazing fast, and the updates since version 0.3 have delivered exceptional performance improvements across all operations.

### Text Extraction Speed Test (5000 nested elements)

| # |      Library      | Time (ms) | vs Scrapling | 
|---|:-----------------:|:---------:|:------------:|
| 1 |     Scrapling     |   1.99    |     1.0x     |
| 2 |   Parsel/Scrapy   |   2.01    |    1.01x     |
| 3 |     Raw Lxml      |    2.5    |    1.256x    |
| 4 |      PyQuery      |   22.93   |    ~11.5x    |
| 5 |    Selectolax     |   80.57   |    ~40.5x    |
| 6 |   BS4 with Lxml   |  1541.37  |   ~774.6x    |
| 7 |  MechanicalSoup   |  1547.35  |   ~777.6x    |
| 8 | BS4 with html5lib |  3410.58  |   ~1713.9x   |


### Element Similarity & Text Search Performance

Scrapling's adaptive element finding capabilities significantly outperform alternatives:

|   Library   | Time (ms) | vs Scrapling |
|-------------|:---------:|:------------:|
| Scrapling   |   2.46    |     1.0x     |
| AutoScraper |   13.3    |    5.407x    |


> All benchmarks represent averages of 100+ runs. See [benchmarks.py](https://github.com/D4Vinci/Scrapling/blob/main/benchmarks.py) for methodology.

## Installation

Scrapling requires Python 3.10 or higher:

```bash
pip install scrapling
```

Starting with v0.3.2, this installation only includes the parser engine and its dependencies, without any fetchers or commandline dependencies.

### Optional Dependencies

1. If you are going to use any of the extra features below, the fetchers, or their classes, then you need to install fetchers' dependencies and then install their browser dependencies with
    ```bash
    pip install "scrapling[fetchers]"
    
    scrapling install
    ```

    This downloads all browsers with their system dependencies and fingerprint manipulation dependencies.

2. Extra features:
   - Install the MCP server feature:
       ```bash
       pip install "scrapling[ai]"
       ```
   - Install shell features (Web Scraping shell and the `extract` command): 
       ```bash
       pip install "scrapling[shell]"
       ```
   - Install everything: 
       ```bash
       pip install "scrapling[all]"
       ```
   Remember that you need to install the browser dependencies with `scrapling install` after any of these extras (if you didn't already)

### Docker
You can also install a Docker image with all extras and browsers with the following command from DockerHub:
```bash
docker pull pyd4vinci/scrapling
```
Or download it from the GitHub registry:
```bash
docker pull ghcr.io/d4vinci/scrapling:latest
```
This image is automatically built and pushed through GitHub actions on the repository's main branch.

## Contributing

We welcome contributions! Please read our [contributing guidelines](https://github.com/D4Vinci/Scrapling/blob/main/CONTRIBUTING.md) before getting started.

## Disclaimer

> [!CAUTION]
> This library is provided for educational and research purposes only. By using this library, you agree to comply with local and international data scraping and privacy laws. The authors and contributors are not responsible for any misuse of this software. Always respect the terms of service of websites and robots.txt files.

## License

This work is licensed under the BSD-3-Clause License.

## Acknowledgments

This project includes code adapted from:
- Parsel (BSD License)—Used for [translator](https://github.com/D4Vinci/Scrapling/blob/main/scrapling/core/translator.py) submodule

## Thanks and References

- [Daijro](https://github.com/daijro)'s brilliant work on [BrowserForge](https://github.com/daijro/browserforge) and [Camoufox](https://github.com/daijro/camoufox)
- [Vinyzu](https://github.com/Vinyzu)'s brilliant work on [Botright](https://github.com/Vinyzu/Botright) and [PatchRight](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright)
- [brotector](https://github.com/kaliiiiiiiiii/brotector) for browser detection bypass techniques
- [fakebrowser](https://github.com/kkoooqq/fakebrowser) and [BotBrowser](https://github.com/botswin/BotBrowser) for fingerprinting research

---
<div align="center"><small>Designed & crafted with ❤️ by Karim Shoair.</small></div><br>

----------------------------------------


## File: README_AR.md
<!-- Source: docs/README_AR.md -->

<p align=center>
  <br>
  <a href="https://scrapling.readthedocs.io/en/latest/" target="_blank"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/poster.png" style="width: 50%; height: 100%;" alt="main poster"/></a>
  <br>
  <i><code>استخراج بيانات الويب بسهولة ويسر كما يجب أن يكون!</code></i>
</p>
<p align="center">
    <a href="https://github.com/D4Vinci/Scrapling/actions/workflows/tests.yml" alt="Tests">
        <img alt="Tests" src="https://github.com/D4Vinci/Scrapling/actions/workflows/tests.yml/badge.svg"></a>
    <a href="https://badge.fury.io/py/Scrapling" alt="PyPI version">
        <img alt="PyPI version" src="https://badge.fury.io/py/Scrapling.svg"></a>
    <a href="https://pepy.tech/project/scrapling" alt="PyPI Downloads">
        <img alt="PyPI Downloads" src="https://static.pepy.tech/personalized-badge/scrapling?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=GREEN&left_text=Downloads"></a>
    <br/>
    <a href="https://discord.gg/EMgGbDceNQ" alt="Discord" target="_blank">
      <img alt="Discord" src="https://img.shields.io/discord/1360786381042880532?style=social&logo=discord&link=https%3A%2F%2Fdiscord.gg%2FEMgGbDceNQ">
    </a>
    <a href="https://x.com/Scrapling_dev" alt="X (formerly Twitter)">
      <img alt="X (formerly Twitter) Follow" src="https://img.shields.io/twitter/follow/Scrapling_dev?style=social&logo=x&link=https%3A%2F%2Fx.com%2FScrapling_dev">
    </a>
    <br/>
    <a href="https://pypi.org/project/scrapling/" alt="Supported Python versions">
        <img alt="Supported Python versions" src="https://img.shields.io/pypi/pyversions/scrapling.svg"></a>
</p>

<p align="center">
    <a href="https://scrapling.readthedocs.io/en/latest/parsing/selection/">
        طرق الاختيار
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/fetching/choosing/">
        اختيار الجالب
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/cli/overview/">
        واجهة سطر الأوامر
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/ai/mcp-server/">
        وضع MCP
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/tutorials/migrating_from_beautifulsoup/">
        الانتقال من Beautifulsoup
    </a>
</p>

**توقف عن محاربة أنظمة مكافحة الروبوتات. توقف عن إعادة كتابة المحددات بعد كل تحديث للموقع.**

Scrapling ليست مجرد مكتبة أخرى لاستخراج بيانات الويب. إنها أول مكتبة استخراج **تكيفية** تتعلم من تغييرات المواقع وتتطور معها. بينما تتعطل المكتبات الأخرى عندما تحدث المواقع بنيتها، يعيد Scrapling تحديد موقع عناصرك تلقائياً ويحافظ على عمل أدوات الاستخراج الخاصة بك.

مبني للويب الحديث، يتميز Scrapling **بمحرك تحليل سريع خاص به** وجوالب للتعامل مع جميع تحديات استخراج بيانات الويب التي تواجهها أو ستواجهها. مبني بواسطة مستخرجي الويب لمستخرجي الويب والمستخدمين العاديين، هناك شيء للجميع.

```python
>> from scrapling.fetchers import Fetcher, AsyncFetcher, StealthyFetcher, DynamicFetcher
>> StealthyFetcher.adaptive = True
# احصل على كود المصدر للمواقع بشكل خفي!
>> page = StealthyFetcher.fetch('https://example.com', headless=True, network_idle=True)
>> print(page.status)
200
>> products = page.css('.product', auto_save=True)  # استخرج البيانات التي تنجو من تغييرات تصميم الموقع!
>> # لاحقاً، إذا تغيرت بنية الموقع، مرر `adaptive=True`
>> products = page.css('.product', adaptive=True)  # و Scrapling لا يزال يجدها!
```

# الرعاة 

<!-- sponsors -->

<a href="https://www.scrapeless.com/en?utm_source=official&utm_term=scrapling" target="_blank" title="Effortless Web Scraping Toolkit for Business and Developers"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/scrapeless.jpg"></a>
<a href="https://www.thordata.com/?ls=github&lk=github" target="_blank" title="Unblockable proxies and scraping infrastructure, delivering real-time, reliable web data to power AI models and workflows."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/thordata.jpg"></a>
<a href="https://evomi.com?utm_source=github&utm_medium=banner&utm_campaign=d4vinci-scrapling" target="_blank" title="Evomi is your Swiss Quality Proxy Provider, starting at $0.49/GB"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/evomi.png"></a>
<a href="https://serpapi.com/?utm_source=scrapling" target="_blank" title="Scrape Google and other search engines with SerpApi"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/SerpApi.png"></a>
<a href="https://visit.decodo.com/Dy6W0b" target="_blank" title="Try the Most Efficient Residential Proxies for Free"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/decodo.png"></a>
<a href="https://petrosky.io/d4vinci" target="_blank" title="PetroSky delivers cutting-edge VPS hosting."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/petrosky.png"></a>
<a href="https://www.swiftproxy.net/" target="_blank" title="Unlock Reliable Proxy Services with Swiftproxy!"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/swiftproxy.png"></a>
<a href="https://www.rapidproxy.io/?ref=d4v" target="_blank" title="Affordable Access to the Proxy World – bypass CAPTCHAs blocks, and avoid additional costs."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/rapidproxy.jpg"></a>
<a href="https://browser.cash/?utm_source=D4Vinci&utm_medium=referral" target="_blank" title="Browser Automation & AI Browser Agent Platform"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/browserCash.png"></a>

<!-- /sponsors -->

<i><sub>هل تريد عرض إعلانك هنا؟ انقر [هنا](https://github.com/sponsors/D4Vinci) واختر المستوى الذي يناسبك!</sub></i>

---

## الميزات الرئيسية

### جلب متقدم للمواقع مع دعم الجلسات
- **طلبات HTTP**: طلبات HTTP سريعة وخفية مع فئة `Fetcher`. يمكنها تقليد بصمة TLS للمتصفح والرؤوس واستخدام HTTP3.
- **التحميل الديناميكي**: جلب المواقع الديناميكية مع أتمتة كاملة للمتصفح من خلال فئة `DynamicFetcher` التي تدعم Chromium من Playwright، وChrome الحقيقي، ووضع التخفي المخصص.
- **تجاوز مكافحة الروبوتات**: قدرات تخفي متقدمة مع `StealthyFetcher` باستخدام نسخة معدلة من Firefox وانتحال البصمات. يمكنه تجاوز جميع أنواع Turnstile وInterstitial من Cloudflare بسهولة بالأتمتة.
- **إدارة الجلسات**: دعم الجلسات المستمرة مع فئات `FetcherSession` و`StealthySession` و`DynamicSession` لإدارة ملفات تعريف الارتباط والحالة عبر الطلبات.
- **دعم Async**: دعم async كامل عبر جميع الجوالب وفئات الجلسات async المخصصة.

### الاستخراج التكيفي والتكامل مع الذكاء الاصطناعي
- 🔄 **تتبع العناصر الذكي**: إعادة تحديد موقع العناصر بعد تغييرات الموقع باستخدام خوارزميات التشابه الذكية.
- 🎯 **الاختيار المرن الذكي**: محددات CSS، محددات XPath، البحث القائم على الفلاتر، البحث النصي، البحث بالتعبيرات العادية والمزيد.
- 🔍 **البحث عن عناصر مشابهة**: تحديد العناصر المشابهة للعناصر الموجودة تلقائياً.
- 🤖 **خادم MCP للاستخدام مع الذكاء الاصطناعي**: خادم MCP مدمج لاستخراج بيانات الويب بمساعدة الذكاء الاصطناعي واستخراج البيانات. يتميز خادم MCP بقدرات مخصصة قوية تستخدم Scrapling لاستخراج المحتوى المستهدف قبل تمريره إلى الذكاء الاصطناعي (Claude/Cursor/إلخ)، وبالتالي تسريع العمليات وتقليل التكاليف عن طريق تقليل استخدام الرموز. ([فيديو توضيحي](https://www.youtube.com/watch?v=qyFk3ZNwOxE))

### بنية عالية الأداء ومختبرة في المعارك
- 🚀 **سريع كالبرق**: أداء محسّن يتفوق على معظم مكتبات استخراج Python.
- 🔋 **فعال في استخدام الذاكرة**: هياكل بيانات محسّنة وتحميل كسول لأقل استخدام للذاكرة.
- ⚡ **تسلسل JSON سريع**: أسرع 10 مرات من المكتبة القياسية.
- 🏗️ **مُختبر في المعارك**: لا يمتلك Scrapling فقط تغطية اختبار بنسبة 92٪ وتغطية كاملة لتلميحات الأنواع، ولكن تم استخدامه يومياً من قبل مئات مستخرجي الويب خلال العام الماضي.

### تجربة صديقة للمطورين/مستخرجي الويب
- 🎯 **غلاف استخراج ويب تفاعلي**: غلاف IPython مدمج اختياري مع تكامل Scrapling، واختصارات، وأدوات جديدة لتسريع تطوير سكريبتات استخراج الويب، مثل تحويل طلبات curl إلى طلبات Scrapling وعرض نتائج الطلبات في متصفحك.
- 🚀 **استخدمه مباشرة من الطرفية**: اختيارياً، يمكنك استخدام Scrapling لاستخراج عنوان URL دون كتابة سطر واحد من الكود!
- 🛠️ **واجهة برمجة تطبيقات التنقل الغنية**: اجتياز DOM متقدم مع طرق التنقل بين الوالدين والأشقاء والأطفال.
- 🧬 **معالجة نصوص محسّنة**: تعبيرات عادية مدمجة وطرق تنظيف وعمليات سلسلة محسّنة.
- 📝 **إنشاء محدد تلقائي**: إنشاء محددات CSS/XPath قوية لأي عنصر.
- 🔌 **واجهة برمجة تطبيقات مألوفة**: مشابه لـ Scrapy/BeautifulSoup مع نفس العناصر الزائفة المستخدمة في Scrapy/Parsel.
- 📘 **تغطية كاملة للأنواع**: تلميحات نوع كاملة لدعم IDE ممتاز وإكمال الكود.
- 🔋 **صورة Docker جاهزة**: مع كل إصدار، يتم بناء ودفع صورة Docker تحتوي على جميع المتصفحات تلقائياً.

## البدء

### الاستخدام الأساسي
```python
from scrapling.fetchers import Fetcher, StealthyFetcher, DynamicFetcher
from scrapling.fetchers import FetcherSession, StealthySession, DynamicSession

# طلبات HTTP مع دعم الجلسات
with FetcherSession(impersonate='chrome') as session:  # استخدم أحدث إصدار من بصمة TLS لـ Chrome
    page = session.get('https://quotes.toscrape.com/', stealthy_headers=True)
    quotes = page.css('.quote .text::text')

# أو استخدم طلبات لمرة واحدة
page = Fetcher.get('https://quotes.toscrape.com/')
quotes = page.css('.quote .text::text')

# وضع التخفي المتقدم (احتفظ بالمتصفح مفتوحاً حتى تنتهي)
with StealthySession(headless=True, solve_cloudflare=True) as session:
    page = session.fetch('https://nopecha.com/demo/cloudflare', google_search=False)
    data = page.css('#padded_content a')

# أو استخدم نمط الطلب لمرة واحدة، يفتح المتصفح لهذا الطلب، ثم يغلقه بعد الانتهاء
page = StealthyFetcher.fetch('https://nopecha.com/demo/cloudflare')
data = page.css('#padded_content a')
    
# أتمتة المتصفح الكاملة (احتفظ بالمتصفح مفتوحاً حتى تنتهي)
with DynamicSession(headless=True) as session:
    page = session.fetch('https://quotes.toscrape.com/', network_idle=True)
    quotes = page.css('.quote .text::text')

# أو استخدم نمط الطلب لمرة واحدة
page = DynamicFetcher.fetch('https://quotes.toscrape.com/', network_idle=True)
quotes = page.css('.quote .text::text')
```

### اختيار العناصر
```python
# محددات CSS
page.css('a::text')                      # استخراج النص
page.css('a::attr(href)')                # استخراج السمات
page.css('a', recursive=False)           # العناصر المباشرة فقط
page.css('a', auto_save=True)            # حفظ مواضع العناصر تلقائياً

# XPath
page.xpath('//a/text()')

# بحث مرن
page.find_by_text('Python', first_match=True)  # البحث بالنص
page.find_by_regex(r'\d{4}')                   # البحث بنمط التعبير العادي
page.find('div', {'class': 'container'})       # البحث بالسمات

# التنقل
element.parent                           # الحصول على العنصر الوالد
element.next_sibling                     # الحصول على الشقيق التالي
element.children                         # الحصول على الأطفال

# عناصر مشابهة
similar = page.get_similar(element)      # البحث عن عناصر مشابهة

# الاستخراج التكيفي
saved_elements = page.css('.product', auto_save=True)
# لاحقاً، عندما يتغير الموقع:
page.css('.product', adaptive=True)      # البحث عن العناصر باستخدام المواضع المحفوظة
```

### استخدام الجلسة
```python
from scrapling.fetchers import FetcherSession, AsyncFetcherSession

# جلسة متزامنة
with FetcherSession() as session:
    # يتم الاحتفاظ بملفات تعريف الارتباط تلقائياً
    page1 = session.get('https://quotes.toscrape.com/login')
    page2 = session.post('https://quotes.toscrape.com/login', data={'username': 'admin', 'password': 'admin'})
    
    # تبديل بصمة المتصفح إذا لزم الأمر
    page2 = session.get('https://quotes.toscrape.com/', impersonate='firefox135')

# استخدام جلسة async
async with AsyncStealthySession(max_pages=2) as session:
    tasks = []
    urls = ['https://example.com/page1', 'https://example.com/page2']
    
    for url in urls:
        task = session.fetch(url)
        tasks.append(task)
    
    print(session.get_pool_stats())  # اختياري - حالة مجموعة علامات تبويب المتصفح (مشغول/حر/خطأ)
    results = await asyncio.gather(*tasks)
    print(session.get_pool_stats())
```

## واجهة سطر الأوامر والغلاف التفاعلي

يتضمن Scrapling v0.3 واجهة سطر أوامر قوية:

[![asciicast](https://asciinema.org/a/736339.svg)](https://asciinema.org/a/736339)

```bash
# تشغيل غلاف استخراج الويب التفاعلي
scrapling shell

# استخراج الصفحات إلى ملف مباشرة دون برمجة (يستخرج المحتوى داخل وسم `body` افتراضياً)
# إذا انتهى ملف الإخراج بـ `.txt`، فسيتم استخراج محتوى النص للهدف.
# إذا انتهى بـ `.md`، فسيكون تمثيل markdown لمحتوى HTML، و`.html` سيكون محتوى HTML مباشرة.
scrapling extract get 'https://example.com' content.md
scrapling extract get 'https://example.com' content.txt --css-selector '#fromSkipToProducts' --impersonate 'chrome'  # جميع العناصر المطابقة لمحدد CSS '#fromSkipToProducts'
scrapling extract fetch 'https://example.com' content.md --css-selector '#fromSkipToProducts' --no-headless
scrapling extract stealthy-fetch 'https://nopecha.com/demo/cloudflare' captchas.html --css-selector '#padded_content a' --solve-cloudflare
```

> [!NOTE]
> هناك العديد من الميزات الإضافية، لكننا نريد إبقاء هذه الصفحة موجزة، مثل خادم MCP وغلاف استخراج الويب التفاعلي. تحقق من الوثائق الكاملة [هنا](https://scrapling.readthedocs.io/en/latest/)

## معايير الأداء

Scrapling ليس قوياً فقط - إنه أيضاً سريع بشكل مذهل، والتحديثات منذ الإصدار 0.3 قدمت تحسينات أداء استثنائية عبر جميع العمليات.

### اختبار سرعة استخراج النص (5000 عنصر متداخل)

| # |      المكتبة      | الوقت (ms) | vs Scrapling | 
|---|:-----------------:|:----------:|:------------:|
| 1 |     Scrapling     |    1.99    |     1.0x     |
| 2 |   Parsel/Scrapy   |    2.01    |    1.01x     |
| 3 |     Raw Lxml      |    2.5     |    1.256x    |
| 4 |      PyQuery      |   22.93    |    ~11.5x    |
| 5 |    Selectolax     |   80.57    |    ~40.5x    |
| 6 |   BS4 with Lxml   |  1541.37   |   ~774.6x    |
| 7 |  MechanicalSoup   |  1547.35   |   ~777.6x    |
| 8 | BS4 with html5lib |  3410.58   |   ~1713.9x   |


### أداء تشابه العناصر والبحث النصي

قدرات العثور على العناصر التكيفية لـ Scrapling تتفوق بشكل كبير على البدائل:

| المكتبة     | الوقت (ms) | vs Scrapling |
|-------------|:----------:|:------------:|
| Scrapling   |    2.46    |     1.0x     |
| AutoScraper |    13.3    |    5.407x    |


> تمثل جميع المعايير متوسطات أكثر من 100 تشغيل. انظر [benchmarks.py](https://github.com/D4Vinci/Scrapling/blob/main/benchmarks.py) للمنهجية.

## التثبيت

يتطلب Scrapling Python 3.10 أو أعلى:

```bash
pip install scrapling
```

بدءاً من v0.3.2، يتضمن هذا التثبيت فقط محرك المحلل وتبعياته، بدون أي جوالب أو تبعيات سطر أوامر.

### التبعيات الاختيارية

1. إذا كنت ستستخدم أياً من الميزات الإضافية أدناه، أو الجوالب، أو فئاتها، فأنت بحاجة إلى تثبيت تبعيات الجوالب ثم تثبيت تبعيات المتصفح الخاصة بها بـ
    ```bash
    pip install "scrapling[fetchers]"
    
    scrapling install
    ```

    يقوم هذا بتنزيل جميع المتصفحات مع تبعيات النظام وتبعيات معالجة البصمات الخاصة بها.

2. ميزات إضافية:
   - تثبيت ميزة خادم MCP:
       ```bash
       pip install "scrapling[ai]"
       ```
   - تثبيت ميزات الغلاف (غلاف استخراج الويب وأمر `extract`):
       ```bash
       pip install "scrapling[shell]"
       ```
   - تثبيت كل شيء:
       ```bash
       pip install "scrapling[all]"
       ```
   تذكر أنك تحتاج إلى تثبيت تبعيات المتصفح مع `scrapling install` بعد أي من هذه الإضافات (إذا لم تكن قد فعلت ذلك بالفعل)

### Docker
يمكنك أيضاً تثبيت صورة Docker مع جميع الإضافات والمتصفحات باستخدام الأمر التالي من DockerHub:
```bash
docker pull pyd4vinci/scrapling
```
أو تنزيلها من سجل GitHub:
```bash
docker pull ghcr.io/d4vinci/scrapling:latest
```
يتم بناء هذه الصورة ودفعها تلقائياً من خلال إجراءات GitHub على الفرع الرئيسي للمستودع.

## المساهمة

نرحب بالمساهمات! يرجى قراءة [إرشادات المساهمة](https://github.com/D4Vinci/Scrapling/blob/main/CONTRIBUTING.md) قبل البدء.

## إخلاء المسؤولية

> [!CAUTION]
> يتم توفير هذه المكتبة للأغراض التعليمية والبحثية فقط. باستخدام هذه المكتبة، فإنك توافق على الامتثال لقوانين استخراج البيانات والخصوصية المحلية والدولية. المؤلفون والمساهمون غير مسؤولين عن أي إساءة استخدام لهذا البرنامج. احترم دائماً شروط خدمة المواقع وملفات robots.txt.

## الترخيص

هذا العمل مرخص بموجب ترخيص BSD-3-Clause.

## الشكر والتقدير

يتضمن هذا المشروع كوداً معدلاً من:
- Parsel (ترخيص BSD) - يستخدم للوحدة الفرعية [translator](https://github.com/D4Vinci/Scrapling/blob/main/scrapling/core/translator.py)

## الشكر والمراجع

- العمل الرائع لـ [Daijro](https://github.com/daijro) على [BrowserForge](https://github.com/daijro/browserforge) و[Camoufox](https://github.com/daijro/camoufox)
- العمل الرائع لـ [Vinyzu](https://github.com/Vinyzu) على [Botright](https://github.com/Vinyzu/Botright) و[PatchRight](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright)
- [brotector](https://github.com/kaliiiiiiiiii/brotector) لتقنيات تجاوز اكتشاف المتصفح
- [fakebrowser](https://github.com/kkoooqq/fakebrowser) و[BotBrowser](https://github.com/botswin/BotBrowser) لأبحاث البصمات

---
<div align="center"><small>مصمم ومصنوع بـ ❤️ بواسطة كريم شعير.</small></div><br>

----------------------------------------


## File: README_CN.md
<!-- Source: docs/README_CN.md -->

<p align=center>
  <br>
  <a href="https://scrapling.readthedocs.io/en/latest/" target="_blank"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/poster.png" style="width: 50%; height: 100%;" alt="main poster"/></a>
  <br>
  <i><code>简单、轻松的网页抓取，本该如此！</code></i>
</p>
<p align="center">
    <a href="https://github.com/D4Vinci/Scrapling/actions/workflows/tests.yml" alt="Tests">
        <img alt="Tests" src="https://github.com/D4Vinci/Scrapling/actions/workflows/tests.yml/badge.svg"></a>
    <a href="https://badge.fury.io/py/Scrapling" alt="PyPI version">
        <img alt="PyPI version" src="https://badge.fury.io/py/Scrapling.svg"></a>
    <a href="https://pepy.tech/project/scrapling" alt="PyPI Downloads">
        <img alt="PyPI Downloads" src="https://static.pepy.tech/personalized-badge/scrapling?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=GREEN&left_text=Downloads"></a>
    <br/>
    <a href="https://discord.gg/EMgGbDceNQ" alt="Discord" target="_blank">
      <img alt="Discord" src="https://img.shields.io/discord/1360786381042880532?style=social&logo=discord&link=https%3A%2F%2Fdiscord.gg%2FEMgGbDceNQ">
    </a>
    <a href="https://x.com/Scrapling_dev" alt="X (formerly Twitter)">
      <img alt="X (formerly Twitter) Follow" src="https://img.shields.io/twitter/follow/Scrapling_dev?style=social&logo=x&link=https%3A%2F%2Fx.com%2FScrapling_dev">
    </a>
    <br/>
    <a href="https://pypi.org/project/scrapling/" alt="Supported Python versions">
        <img alt="Supported Python versions" src="https://img.shields.io/pypi/pyversions/scrapling.svg"></a>
</p>

<p align="center">
    <a href="https://scrapling.readthedocs.io/en/latest/parsing/selection/">
        选择方法
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/fetching/choosing/">
        选择获取器
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/cli/overview/">
        命令行界面
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/ai/mcp-server/">
        MCP模式
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/tutorials/migrating_from_beautifulsoup/">
        从Beautifulsoup迁移
    </a>
</p>

**停止与反机器人系统斗争。停止在每次网站更新后重写选择器。**

Scrapling不仅仅是另一个网页抓取库。它是第一个**自适应**抓取库，能够从网站变化中学习并与之共同进化。当其他库在网站更新结构时失效，Scrapling会自动重新定位您的元素并保持抓取器运行。

为现代网络而构建，Scrapling具有**自己的快速解析引擎**和获取器来处理您面临或将要面临的所有网页抓取挑战。由网页抓取者为网页抓取者和普通用户构建，适合每个人。

```python
>> from scrapling.fetchers import Fetcher, AsyncFetcher, StealthyFetcher, DynamicFetcher
>> StealthyFetcher.adaptive = True
# 隐秘地获取网站源代码！
>> page = StealthyFetcher.fetch('https://example.com', headless=True, network_idle=True)
>> print(page.status)
200
>> products = page.css('.product', auto_save=True)  # 抓取在网站设计变更后仍能存活的数据！
>> # 之后，如果网站结构改变，传递 `adaptive=True`
>> products = page.css('.product', adaptive=True)  # Scrapling仍然能找到它们！
```

# 赞助商 

<!-- sponsors -->

<a href="https://www.scrapeless.com/en?utm_source=official&utm_term=scrapling" target="_blank" title="Effortless Web Scraping Toolkit for Business and Developers"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/scrapeless.jpg"></a>
<a href="https://www.thordata.com/?ls=github&lk=github" target="_blank" title="Unblockable proxies and scraping infrastructure, delivering real-time, reliable web data to power AI models and workflows."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/thordata.jpg"></a>
<a href="https://evomi.com?utm_source=github&utm_medium=banner&utm_campaign=d4vinci-scrapling" target="_blank" title="Evomi is your Swiss Quality Proxy Provider, starting at $0.49/GB"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/evomi.png"></a>
<a href="https://serpapi.com/?utm_source=scrapling" target="_blank" title="Scrape Google and other search engines with SerpApi"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/SerpApi.png"></a>
<a href="https://visit.decodo.com/Dy6W0b" target="_blank" title="Try the Most Efficient Residential Proxies for Free"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/decodo.png"></a>
<a href="https://petrosky.io/d4vinci" target="_blank" title="PetroSky delivers cutting-edge VPS hosting."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/petrosky.png"></a>
<a href="https://www.swiftproxy.net/" target="_blank" title="Unlock Reliable Proxy Services with Swiftproxy!"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/swiftproxy.png"></a>
<a href="https://www.rapidproxy.io/?ref=d4v" target="_blank" title="Affordable Access to the Proxy World – bypass CAPTCHAs blocks, and avoid additional costs."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/rapidproxy.jpg"></a>
<a href="https://browser.cash/?utm_source=D4Vinci&utm_medium=referral" target="_blank" title="Browser Automation & AI Browser Agent Platform"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/browserCash.png"></a>

<!-- /sponsors -->

<i><sub>想在这里展示您的广告吗？点击[这里](https://github.com/sponsors/D4Vinci)并选择适合您的级别！</sub></i>

---

## 主要特性

### 支持会话的高级网站获取
- **HTTP请求**：使用`Fetcher`类进行快速和隐秘的HTTP请求。可以模拟浏览器的TLS指纹、标头并使用HTTP3。
- **动态加载**：通过`DynamicFetcher`类使用完整的浏览器自动化获取动态网站，支持Playwright的Chromium、真实Chrome和自定义隐秘模式。
- **反机器人绕过**：使用`StealthyFetcher`的高级隐秘功能，使用修改版Firefox和指纹伪装。可以轻松自动绕过所有类型的Cloudflare的Turnstile和Interstitial。
- **会话管理**：使用`FetcherSession`、`StealthySession`和`DynamicSession`类持久化会话支持，用于跨请求的cookie和状态管理。
- **异步支持**：所有获取器和专用异步会话类的完整异步支持。

### 自适应抓取和AI集成
- 🔄 **智能元素跟踪**：使用智能相似性算法在网站更改后重新定位元素。
- 🎯 **智能灵活选择**：CSS选择器、XPath选择器、基于过滤器的搜索、文本搜索、正则表达式搜索等。
- 🔍 **查找相似元素**：自动定位与找到的元素相似的元素。
- 🤖 **与AI一起使用的MCP服务器**：内置MCP服务器用于AI辅助网页抓取和数据提取。MCP服务器具有自定义的强大功能，利用Scrapling在将内容传递给AI（Claude/Cursor等）之前提取目标内容，从而加快操作并通过最小化令牌使用来降低成本。（[演示视频](https://www.youtube.com/watch?v=qyFk3ZNwOxE)）

### 高性能和经过实战测试的架构
- 🚀 **闪电般快速**：优化性能超越大多数Python抓取库。
- 🔋 **内存高效**：优化的数据结构和延迟加载，最小内存占用。
- ⚡ **快速JSON序列化**：比标准库快10倍。
- 🏗️ **经过实战测试**：Scrapling不仅拥有92%的测试覆盖率和完整的类型提示覆盖率，而且在过去一年中每天被数百名网页抓取者使用。

### 对开发者/网页抓取者友好的体验
- 🎯 **交互式网页抓取Shell**：可选的内置IPython shell，具有Scrapling集成、快捷方式和新工具，可加快网页抓取脚本开发，例如将curl请求转换为Scrapling请求并在浏览器中查看请求结果。
- 🚀 **直接从终端使用**：可选地，您可以使用Scrapling抓取URL而无需编写任何代码！
- 🛠️ **丰富的导航API**：使用父级、兄弟级和子级导航方法进行高级DOM遍历。
- 🧬 **增强的文本处理**：内置正则表达式、清理方法和优化的字符串操作。
- 📝 **自动选择器生成**：为任何元素生成强大的CSS/XPath选择器。
- 🔌 **熟悉的API**：类似于Scrapy/BeautifulSoup，使用与Scrapy/Parsel相同的伪元素。
- 📘 **完整的类型覆盖**：完整的类型提示，出色的IDE支持和代码补全。
- 🔋 **现成的Docker镜像**：每次发布时，包含所有浏览器的Docker镜像会自动构建和推送。

## 入门

### 基本用法
```python
from scrapling.fetchers import Fetcher, StealthyFetcher, DynamicFetcher
from scrapling.fetchers import FetcherSession, StealthySession, DynamicSession

# 支持会话的HTTP请求
with FetcherSession(impersonate='chrome') as session:  # 使用Chrome的最新版本TLS指纹
    page = session.get('https://quotes.toscrape.com/', stealthy_headers=True)
    quotes = page.css('.quote .text::text')

# 或使用一次性请求
page = Fetcher.get('https://quotes.toscrape.com/')
quotes = page.css('.quote .text::text')

# 高级隐秘模式（保持浏览器打开直到完成）
with StealthySession(headless=True, solve_cloudflare=True) as session:
    page = session.fetch('https://nopecha.com/demo/cloudflare', google_search=False)
    data = page.css('#padded_content a')

# 或使用一次性请求样式，为此请求打开浏览器，完成后关闭
page = StealthyFetcher.fetch('https://nopecha.com/demo/cloudflare')
data = page.css('#padded_content a')
    
# 完整的浏览器自动化（保持浏览器打开直到完成）
with DynamicSession(headless=True) as session:
    page = session.fetch('https://quotes.toscrape.com/', network_idle=True)
    quotes = page.css('.quote .text::text')

# 或使用一次性请求样式
page = DynamicFetcher.fetch('https://quotes.toscrape.com/', network_idle=True)
quotes = page.css('.quote .text::text')
```

### 元素选择
```python
# CSS选择器
page.css('a::text')                      # 提取文本
page.css('a::attr(href)')                # 提取属性
page.css('a', recursive=False)           # 仅直接元素
page.css('a', auto_save=True)            # 自动保存元素位置

# XPath
page.xpath('//a/text()')

# 灵活搜索
page.find_by_text('Python', first_match=True)  # 按文本查找
page.find_by_regex(r'\d{4}')                   # 按正则表达式模式查找
page.find('div', {'class': 'container'})       # 按属性查找

# 导航
element.parent                           # 获取父元素
element.next_sibling                     # 获取下一个兄弟元素
element.children                         # 获取子元素

# 相似元素
similar = page.get_similar(element)      # 查找相似元素

# 自适应抓取
saved_elements = page.css('.product', auto_save=True)
# 之后，当网站更改时：
page.css('.product', adaptive=True)      # 使用保存的位置查找元素
```

### 会话使用
```python
from scrapling.fetchers import FetcherSession, AsyncFetcherSession

# 同步会话
with FetcherSession() as session:
    # Cookie自动保持
    page1 = session.get('https://quotes.toscrape.com/login')
    page2 = session.post('https://quotes.toscrape.com/login', data={'username': 'admin', 'password': 'admin'})
    
    # 如需要，切换浏览器指纹
    page2 = session.get('https://quotes.toscrape.com/', impersonate='firefox135')

# 异步会话使用
async with AsyncStealthySession(max_pages=2) as session:
    tasks = []
    urls = ['https://example.com/page1', 'https://example.com/page2']
    
    for url in urls:
        task = session.fetch(url)
        tasks.append(task)
    
    print(session.get_pool_stats())  # 可选 - 浏览器标签池的状态（忙/空闲/错误）
    results = await asyncio.gather(*tasks)
    print(session.get_pool_stats())
```

## CLI和交互式Shell

Scrapling v0.3包含强大的命令行界面：

[![asciicast](https://asciinema.org/a/736339.svg)](https://asciinema.org/a/736339)

```bash
# 启动交互式网页抓取shell
scrapling shell

# 直接将页面提取到文件而无需编程（默认提取`body`标签内的内容）
# 如果输出文件以`.txt`结尾，则将提取目标的文本内容。
# 如果以`.md`结尾，它将是HTML内容的markdown表示，`.html`将直接是HTML内容。
scrapling extract get 'https://example.com' content.md
scrapling extract get 'https://example.com' content.txt --css-selector '#fromSkipToProducts' --impersonate 'chrome'  # 所有匹配CSS选择器'#fromSkipToProducts'的元素
scrapling extract fetch 'https://example.com' content.md --css-selector '#fromSkipToProducts' --no-headless
scrapling extract stealthy-fetch 'https://nopecha.com/demo/cloudflare' captchas.html --css-selector '#padded_content a' --solve-cloudflare
```

> [!NOTE]
> 还有许多其他功能，但我们希望保持此页面简洁，例如MCP服务器和交互式网页抓取Shell。查看完整文档[这里](https://scrapling.readthedocs.io/en/latest/)

## 性能基准

Scrapling不仅功能强大——它还速度极快，自0.3版本以来的更新在所有操作中都提供了卓越的性能改进。

### 文本提取速度测试（5000个嵌套元素）

| # |         库         | 时间(ms)  | vs Scrapling | 
|---|:-----------------:|:-------:|:------------:|
| 1 |     Scrapling     |  1.99   |     1.0x     |
| 2 |   Parsel/Scrapy   |  2.01   |    1.01x     |
| 3 |     Raw Lxml      |   2.5   |    1.256x    |
| 4 |      PyQuery      |  22.93  |    ~11.5x    |
| 5 |    Selectolax     |  80.57  |    ~40.5x    |
| 6 |   BS4 with Lxml   | 1541.37 |   ~774.6x    |
| 7 |  MechanicalSoup   | 1547.35 |   ~777.6x    |
| 8 | BS4 with html5lib | 3410.58 |   ~1713.9x   |


### 元素相似性和文本搜索性能

Scrapling的自适应元素查找功能明显优于替代方案：

| 库           | 时间(ms) | vs Scrapling |
|-------------|:------:|:------------:|
| Scrapling   |  2.46  |     1.0x     |
| AutoScraper |  13.3  |    5.407x    |


> 所有基准测试代表100+次运行的平均值。请参阅[benchmarks.py](https://github.com/D4Vinci/Scrapling/blob/main/benchmarks.py)了解方法。

## 安装

Scrapling需要Python 3.10或更高版本：

```bash
pip install scrapling
```

从v0.3.2开始，此安装仅包括解析器引擎及其依赖项，没有任何获取器或命令行依赖项。

### 可选依赖项

1. 如果您要使用以下任何额外功能、获取器或它们的类，那么您需要安装获取器的依赖项，然后使用以下命令安装它们的浏览器依赖项
    ```bash
    pip install "scrapling[fetchers]"
    
    scrapling install
    ```

    这会下载所有浏览器及其系统依赖项和指纹操作依赖项。

2. 额外功能：
   - 安装MCP服务器功能：
       ```bash
       pip install "scrapling[ai]"
       ```
   - 安装shell功能（网页抓取shell和`extract`命令）：
       ```bash
       pip install "scrapling[shell]"
       ```
   - 安装所有内容：
       ```bash
       pip install "scrapling[all]"
       ```
   请记住，在安装任何这些额外功能后（如果您还没有安装），您需要使用`scrapling install`安装浏览器依赖项

### Docker
您还可以使用以下命令从DockerHub安装包含所有额外功能和浏览器的Docker镜像：
```bash
docker pull pyd4vinci/scrapling
```
或从GitHub注册表下载：
```bash
docker pull ghcr.io/d4vinci/scrapling:latest
```
此镜像通过仓库主分支上的GitHub actions自动构建和推送。

## 贡献

我们欢迎贡献！在开始之前，请阅读我们的[贡献指南](https://github.com/D4Vinci/Scrapling/blob/main/CONTRIBUTING.md)。

## 免责声明

> [!CAUTION]
> 此库仅用于教育和研究目的。使用此库即表示您同意遵守本地和国际数据抓取和隐私法律。作者和贡献者对本软件的任何滥用不承担责任。始终尊重网站的服务条款和robots.txt文件。

## 许可证

本作品根据BSD-3-Clause许可证授权。

## 致谢

此项目包含改编自以下内容的代码：
- Parsel（BSD许可证）——用于[translator](https://github.com/D4Vinci/Scrapling/blob/main/scrapling/core/translator.py)子模块

## 感谢和参考

- [Daijro](https://github.com/daijro)在[BrowserForge](https://github.com/daijro/browserforge)和[Camoufox](https://github.com/daijro/camoufox)上的出色工作
- [Vinyzu](https://github.com/Vinyzu)在[Botright](https://github.com/Vinyzu/Botright)和[PatchRight](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright)上的出色工作
- [brotector](https://github.com/kaliiiiiiiiii/brotector)提供的浏览器检测绕过技术
- [fakebrowser](https://github.com/kkoooqq/fakebrowser)和[BotBrowser](https://github.com/botswin/BotBrowser)提供的指纹识别研究

---
<div align="center"><small>由Karim Shoair用❤️设计和制作。</small></div><br>

----------------------------------------


## File: README_DE.md
<!-- Source: docs/README_DE.md -->

<p align=center>
  <br>
  <a href="https://scrapling.readthedocs.io/en/latest/" target="_blank"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/poster.png" style="width: 50%; height: 100%;" alt="main poster"/></a>
  <br>
  <i><code>Einfaches, müheloses Web Scraping, wie es sein sollte!</code></i>
</p>
<p align="center">
    <a href="https://github.com/D4Vinci/Scrapling/actions/workflows/tests.yml" alt="Tests">
        <img alt="Tests" src="https://github.com/D4Vinci/Scrapling/actions/workflows/tests.yml/badge.svg"></a>
    <a href="https://badge.fury.io/py/Scrapling" alt="PyPI version">
        <img alt="PyPI version" src="https://badge.fury.io/py/Scrapling.svg"></a>
    <a href="https://pepy.tech/project/scrapling" alt="PyPI Downloads">
        <img alt="PyPI Downloads" src="https://static.pepy.tech/personalized-badge/scrapling?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=GREEN&left_text=Downloads"></a>
    <br/>
    <a href="https://discord.gg/EMgGbDceNQ" alt="Discord" target="_blank">
      <img alt="Discord" src="https://img.shields.io/discord/1360786381042880532?style=social&logo=discord&link=https%3A%2F%2Fdiscord.gg%2FEMgGbDceNQ">
    </a>
    <a href="https://x.com/Scrapling_dev" alt="X (formerly Twitter)">
      <img alt="X (formerly Twitter) Follow" src="https://img.shields.io/twitter/follow/Scrapling_dev?style=social&logo=x&link=https%3A%2F%2Fx.com%2FScrapling_dev">
    </a>
    <br/>
    <a href="https://pypi.org/project/scrapling/" alt="Supported Python versions">
        <img alt="Supported Python versions" src="https://img.shields.io/pypi/pyversions/scrapling.svg"></a>
</p>

<p align="center">
    <a href="https://scrapling.readthedocs.io/en/latest/parsing/selection/">
        Auswahlmethoden
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/fetching/choosing/">
        Fetcher wählen
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/cli/overview/">
        CLI
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/ai/mcp-server/">
        MCP-Modus
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/tutorials/migrating_from_beautifulsoup/">
        Migration von Beautifulsoup
    </a>
</p>

**Hören Sie auf, gegen Anti-Bot-Systeme zu kämpfen. Hören Sie auf, Selektoren nach jedem Website-Update neu zu schreiben.**

Scrapling ist nicht nur eine weitere Web-Scraping-Bibliothek. Es ist die erste **adaptive** Scraping-Bibliothek, die von Website-Änderungen lernt und sich mit ihnen weiterentwickelt. Während andere Bibliotheken brechen, wenn Websites ihre Struktur aktualisieren, lokalisiert Scrapling Ihre Elemente automatisch neu und hält Ihre Scraper am Laufen.

Für das moderne Web entwickelt, bietet Scrapling **seine eigene schnelle Parsing-Engine** und Fetcher, um alle Web-Scraping-Herausforderungen zu bewältigen, denen Sie begegnen oder begegnen werden. Von Web Scrapern für Web Scraper und normale Benutzer entwickelt, ist für jeden etwas dabei.

```python
>> from scrapling.fetchers import Fetcher, AsyncFetcher, StealthyFetcher, DynamicFetcher
>> StealthyFetcher.adaptive = True
# Holen Sie sich Website-Quellcode unter dem Radar!
>> page = StealthyFetcher.fetch('https://example.com', headless=True, network_idle=True)
>> print(page.status)
200
>> products = page.css('.product', auto_save=True)  # Scrapen Sie Daten, die Website-Designänderungen überleben!
>> # Später, wenn sich die Website-Struktur ändert, übergeben Sie `adaptive=True`
>> products = page.css('.product', adaptive=True)  # und Scrapling findet sie trotzdem!
```

# Sponsoren 

<!-- sponsors -->

<a href="https://www.scrapeless.com/en?utm_source=official&utm_term=scrapling" target="_blank" title="Effortless Web Scraping Toolkit for Business and Developers"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/scrapeless.jpg"></a>
<a href="https://www.thordata.com/?ls=github&lk=github" target="_blank" title="Unblockable proxies and scraping infrastructure, delivering real-time, reliable web data to power AI models and workflows."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/thordata.jpg"></a>
<a href="https://evomi.com?utm_source=github&utm_medium=banner&utm_campaign=d4vinci-scrapling" target="_blank" title="Evomi is your Swiss Quality Proxy Provider, starting at $0.49/GB"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/evomi.png"></a>
<a href="https://serpapi.com/?utm_source=scrapling" target="_blank" title="Scrape Google and other search engines with SerpApi"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/SerpApi.png"></a>
<a href="https://visit.decodo.com/Dy6W0b" target="_blank" title="Try the Most Efficient Residential Proxies for Free"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/decodo.png"></a>
<a href="https://petrosky.io/d4vinci" target="_blank" title="PetroSky delivers cutting-edge VPS hosting."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/petrosky.png"></a>
<a href="https://www.swiftproxy.net/" target="_blank" title="Unlock Reliable Proxy Services with Swiftproxy!"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/swiftproxy.png"></a>
<a href="https://www.rapidproxy.io/?ref=d4v" target="_blank" title="Affordable Access to the Proxy World – bypass CAPTCHAs blocks, and avoid additional costs."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/rapidproxy.jpg"></a>
<a href="https://browser.cash/?utm_source=D4Vinci&utm_medium=referral" target="_blank" title="Browser Automation & AI Browser Agent Platform"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/browserCash.png"></a>

<!-- /sponsors -->

<i><sub>Möchten Sie Ihre Anzeige hier zeigen? Klicken Sie [hier](https://github.com/sponsors/D4Vinci) und wählen Sie die Stufe, die zu Ihnen passt!</sub></i>

---

## Hauptmerkmale

### Erweiterte Website-Abruf mit Sitzungsunterstützung
- **HTTP-Anfragen**: Schnelle und heimliche HTTP-Anfragen mit der `Fetcher`-Klasse. Kann Browser-TLS-Fingerabdrücke, Header imitieren und HTTP3 verwenden.
- **Dynamisches Laden**: Abrufen dynamischer Websites mit vollständiger Browser-Automatisierung über die `DynamicFetcher`-Klasse, die Playwrights Chromium, echtes Chrome und benutzerdefinierten Stealth-Modus unterstützt.
- **Anti-Bot-Umgehung**: Erweiterte Stealth-Fähigkeiten mit `StealthyFetcher` unter Verwendung einer modifizierten Firefox-Version und Fingerabdruck-Spoofing. Kann alle Arten von Cloudflares Turnstile und Interstitial einfach mit Automatisierung umgehen.
- **Sitzungsverwaltung**: Persistente Sitzungsunterstützung mit den Klassen `FetcherSession`, `StealthySession` und `DynamicSession` für Cookie- und Zustandsverwaltung über Anfragen hinweg.
- **Async-Unterstützung**: Vollständige Async-Unterstützung über alle Fetcher und dedizierte Async-Sitzungsklassen hinweg.

### Adaptives Scraping & KI-Integration
- 🔄 **Intelligente Element-Verfolgung**: Elemente nach Website-Änderungen mit intelligenten Ähnlichkeitsalgorithmen neu lokalisieren.
- 🎯 **Intelligente flexible Auswahl**: CSS-Selektoren, XPath-Selektoren, filterbasierte Suche, Textsuche, Regex-Suche und mehr.
- 🔍 **Ähnliche Elemente finden**: Elemente, die gefundenen Elementen ähnlich sind, automatisch lokalisieren.
- 🤖 **MCP-Server für die Verwendung mit KI**: Integrierter MCP-Server für KI-unterstütztes Web Scraping und Datenextraktion. Der MCP-Server verfügt über benutzerdefinierte, leistungsstarke Funktionen, die Scrapling nutzen, um gezielten Inhalt zu extrahieren, bevor er an die KI (Claude/Cursor/etc.) übergeben wird, wodurch Vorgänge beschleunigt und Kosten durch Minimierung der Token-Nutzung gesenkt werden. ([Demo-Video](https://www.youtube.com/watch?v=qyFk3ZNwOxE))

### Hochleistungs- und praxiserprobte Architektur
- 🚀 **Blitzschnell**: Optimierte Leistung, die die meisten Python-Scraping-Bibliotheken übertrifft.
- 🔋 **Speichereffizient**: Optimierte Datenstrukturen und Lazy Loading für einen minimalen Speicher-Footprint.
- ⚡ **Schnelle JSON-Serialisierung**: 10x schneller als die Standardbibliothek.
- 🏗️ **Praxiserprobt**: Scrapling hat nicht nur eine Testabdeckung von 92% und eine vollständige Type-Hints-Abdeckung, sondern wird seit dem letzten Jahr täglich von Hunderten von Web Scrapern verwendet.

### Entwickler/Web-Scraper-freundliche Erfahrung
- 🎯 **Interaktive Web-Scraping-Shell**: Optionale integrierte IPython-Shell mit Scrapling-Integration, Shortcuts und neuen Tools zur Beschleunigung der Web-Scraping-Skriptentwicklung, wie das Konvertieren von Curl-Anfragen in Scrapling-Anfragen und das Anzeigen von Anfrageergebnissen in Ihrem Browser.
- 🚀 **Direkt vom Terminal aus verwenden**: Optional können Sie Scrapling verwenden, um eine URL zu scrapen, ohne eine einzige Codezeile zu schreiben!
- 🛠️ **Umfangreiche Navigations-API**: Erweiterte DOM-Traversierung mit Eltern-, Geschwister- und Kind-Navigationsmethoden.
- 🧬 **Verbesserte Textverarbeitung**: Integrierte Regex, Bereinigungsmethoden und optimierte String-Operationen.
- 📝 **Automatische Selektorgenerierung**: Robuste CSS/XPath-Selektoren für jedes Element generieren.
- 🔌 **Vertraute API**: Ähnlich wie Scrapy/BeautifulSoup mit denselben Pseudo-Elementen, die in Scrapy/Parsel verwendet werden.
- 📘 **Vollständige Typabdeckung**: Vollständige Type Hints für hervorragende IDE-Unterstützung und Code-Vervollständigung.
- 🔋 **Fertiges Docker-Image**: Mit jeder Veröffentlichung wird automatisch ein Docker-Image erstellt und gepusht, das alle Browser enthält.

## Erste Schritte

### Grundlegende Verwendung
```python
from scrapling.fetchers import Fetcher, StealthyFetcher, DynamicFetcher
from scrapling.fetchers import FetcherSession, StealthySession, DynamicSession

# HTTP-Anfragen mit Sitzungsunterstützung
with FetcherSession(impersonate='chrome') as session:  # Verwenden Sie die neueste Version von Chromes TLS-Fingerabdruck
    page = session.get('https://quotes.toscrape.com/', stealthy_headers=True)
    quotes = page.css('.quote .text::text')

# Oder verwenden Sie einmalige Anfragen
page = Fetcher.get('https://quotes.toscrape.com/')
quotes = page.css('.quote .text::text')

# Erweiterter Stealth-Modus (Browser offen halten, bis Sie fertig sind)
with StealthySession(headless=True, solve_cloudflare=True) as session:
    page = session.fetch('https://nopecha.com/demo/cloudflare', google_search=False)
    data = page.css('#padded_content a')

# Oder verwenden Sie den einmaligen Anfragenstil, öffnet den Browser für diese Anfrage und schließt ihn dann nach Abschluss
page = StealthyFetcher.fetch('https://nopecha.com/demo/cloudflare')
data = page.css('#padded_content a')
    
# Vollständige Browser-Automatisierung (Browser offen halten, bis Sie fertig sind)
with DynamicSession(headless=True) as session:
    page = session.fetch('https://quotes.toscrape.com/', network_idle=True)
    quotes = page.css('.quote .text::text')

# Oder verwenden Sie den einmaligen Anfragenstil
page = DynamicFetcher.fetch('https://quotes.toscrape.com/', network_idle=True)
quotes = page.css('.quote .text::text')
```

### Elementauswahl
```python
# CSS-Selektoren
page.css('a::text')                      # Text extrahieren
page.css('a::attr(href)')                # Attribute extrahieren
page.css('a', recursive=False)           # Nur direkte Elemente
page.css('a', auto_save=True)            # Elementpositionen automatisch speichern

# XPath
page.xpath('//a/text()')

# Flexible Suche
page.find_by_text('Python', first_match=True)  # Nach Text suchen
page.find_by_regex(r'\d{4}')                   # Nach Regex-Muster suchen
page.find('div', {'class': 'container'})       # Nach Attributen suchen

# Navigation
element.parent                           # Elternelement abrufen
element.next_sibling                     # Nächstes Geschwister abrufen
element.children                         # Kindelemente abrufen

# Ähnliche Elemente
similar = page.get_similar(element)      # Ähnliche Elemente finden

# Adaptives Scraping
saved_elements = page.css('.product', auto_save=True)
# Später, wenn sich die Website ändert:
page.css('.product', adaptive=True)      # Elemente mithilfe gespeicherter Positionen finden
```

### Sitzungsverwendung
```python
from scrapling.fetchers import FetcherSession, AsyncFetcherSession

# Synchrone Sitzung
with FetcherSession() as session:
    # Cookies werden automatisch beibehalten
    page1 = session.get('https://quotes.toscrape.com/login')
    page2 = session.post('https://quotes.toscrape.com/login', data={'username': 'admin', 'password': 'admin'})
    
    # Bei Bedarf Browser-Fingerabdruck wechseln
    page2 = session.get('https://quotes.toscrape.com/', impersonate='firefox135')

# Async-Sitzungsverwendung
async with AsyncStealthySession(max_pages=2) as session:
    tasks = []
    urls = ['https://example.com/page1', 'https://example.com/page2']
    
    for url in urls:
        task = session.fetch(url)
        tasks.append(task)
    
    print(session.get_pool_stats())  # Optional - Der Status des Browser-Tab-Pools (beschäftigt/frei/Fehler)
    results = await asyncio.gather(*tasks)
    print(session.get_pool_stats())
```

## CLI & Interaktive Shell

Scrapling v0.3 enthält eine leistungsstarke Befehlszeilenschnittstelle:

[![asciicast](https://asciinema.org/a/736339.svg)](https://asciinema.org/a/736339)

```bash
# Interaktive Web-Scraping-Shell starten
scrapling shell

# Seiten direkt ohne Programmierung in eine Datei extrahieren (Extrahiert standardmäßig den Inhalt im `body`-Tag)
# Wenn die Ausgabedatei mit `.txt` endet, wird der Textinhalt des Ziels extrahiert.
# Wenn sie mit `.md` endet, ist es eine Markdown-Darstellung des HTML-Inhalts, und `.html` ist direkt der HTML-Inhalt.
scrapling extract get 'https://example.com' content.md
scrapling extract get 'https://example.com' content.txt --css-selector '#fromSkipToProducts' --impersonate 'chrome'  # Alle Elemente, die dem CSS-Selektor '#fromSkipToProducts' entsprechen
scrapling extract fetch 'https://example.com' content.md --css-selector '#fromSkipToProducts' --no-headless
scrapling extract stealthy-fetch 'https://nopecha.com/demo/cloudflare' captchas.html --css-selector '#padded_content a' --solve-cloudflare
```

> [!NOTE]
> Es gibt viele zusätzliche Funktionen, aber wir möchten diese Seite prägnant halten, wie den MCP-Server und die interaktive Web-Scraping-Shell. Schauen Sie sich die vollständige Dokumentation [hier](https://scrapling.readthedocs.io/en/latest/) an

## Leistungsbenchmarks

Scrapling ist nicht nur leistungsstark – es ist auch blitzschnell, und die Updates seit Version 0.3 haben außergewöhnliche Leistungsverbesserungen bei allen Operationen gebracht.

### Textextraktions-Geschwindigkeitstest (5000 verschachtelte Elemente)

| # |    Bibliothek     | Zeit (ms) | vs Scrapling | 
|---|:-----------------:|:---------:|:------------:|
| 1 |     Scrapling     |   1.99    |     1.0x     |
| 2 |   Parsel/Scrapy   |   2.01    |    1.01x     |
| 3 |     Raw Lxml      |    2.5    |    1.256x    |
| 4 |      PyQuery      |   22.93   |    ~11.5x    |
| 5 |    Selectolax     |   80.57   |    ~40.5x    |
| 6 |   BS4 with Lxml   |  1541.37  |   ~774.6x    |
| 7 |  MechanicalSoup   |  1547.35  |   ~777.6x    |
| 8 | BS4 with html5lib |  3410.58  |   ~1713.9x   |


### Element-Ähnlichkeit & Textsuche-Leistung

Scraplings adaptive Element-Finding-Fähigkeiten übertreffen Alternativen deutlich:

| Bibliothek  | Zeit (ms) | vs Scrapling |
|-------------|:---------:|:------------:|
| Scrapling   |   2.46    |     1.0x     |
| AutoScraper |   13.3    |    5.407x    |


> Alle Benchmarks stellen Durchschnittswerte von über 100 Durchläufen dar. Siehe [benchmarks.py](https://github.com/D4Vinci/Scrapling/blob/main/benchmarks.py) für die Methodik.

## Installation

Scrapling erfordert Python 3.10 oder höher:

```bash
pip install scrapling
```

Ab v0.3.2 enthält diese Installation nur die Parser-Engine und ihre Abhängigkeiten, ohne Fetcher oder Kommandozeilenabhängigkeiten.

### Optionale Abhängigkeiten

1. Wenn Sie eine der folgenden zusätzlichen Funktionen, die Fetcher oder ihre Klassen verwenden möchten, müssen Sie die Abhängigkeiten der Fetcher installieren und dann ihre Browser-Abhängigkeiten mit
    ```bash
    pip install "scrapling[fetchers]"
    
    scrapling install
    ```

    Dies lädt alle Browser mit ihren Systemabhängigkeiten und Fingerabdruck-Manipulationsabhängigkeiten herunter.

2. Zusätzliche Funktionen:
   - MCP-Server-Funktion installieren:
       ```bash
       pip install "scrapling[ai]"
       ```
   - Shell-Funktionen installieren (Web-Scraping-Shell und der `extract`-Befehl):
       ```bash
       pip install "scrapling[shell]"
       ```
   - Alles installieren:
       ```bash
       pip install "scrapling[all]"
       ```
   Denken Sie daran, dass Sie nach einem dieser Extras (falls noch nicht geschehen) die Browser-Abhängigkeiten mit `scrapling install` installieren müssen

### Docker
Sie können auch ein Docker-Image mit allen Extras und Browsern mit dem folgenden Befehl von DockerHub installieren:
```bash
docker pull pyd4vinci/scrapling
```
Oder laden Sie es aus der GitHub-Registry herunter:
```bash
docker pull ghcr.io/d4vinci/scrapling:latest
```
Dieses Image wird automatisch über GitHub Actions im Hauptzweig des Repositorys erstellt und gepusht.

## Beitragen

Wir freuen uns über Beiträge! Bitte lesen Sie unsere [Beitragsrichtlinien](https://github.com/D4Vinci/Scrapling/blob/main/CONTRIBUTING.md), bevor Sie beginnen.

## Haftungsausschluss

> [!CAUTION]
> Diese Bibliothek wird nur zu Bildungs- und Forschungszwecken bereitgestellt. Durch die Nutzung dieser Bibliothek erklären Sie sich damit einverstanden, lokale und internationale Gesetze zum Daten-Scraping und Datenschutz einzuhalten. Die Autoren und Mitwirkenden sind nicht verantwortlich für Missbrauch dieser Software. Respektieren Sie immer die Nutzungsbedingungen von Websites und robots.txt-Dateien.

## Lizenz

Diese Arbeit ist unter der BSD-3-Clause-Lizenz lizenziert.

## Danksagungen

Dieses Projekt enthält angepassten Code von:
- Parsel (BSD-Lizenz) – Verwendet für [translator](https://github.com/D4Vinci/Scrapling/blob/main/scrapling/core/translator.py)-Submodul

## Dank und Referenzen

- [Daijros](https://github.com/daijro) brillante Arbeit an [BrowserForge](https://github.com/daijro/browserforge) und [Camoufox](https://github.com/daijro/camoufox)
- [Vinyzus](https://github.com/Vinyzu) brillante Arbeit an [Botright](https://github.com/Vinyzu/Botright) und [PatchRight](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright)
- [brotector](https://github.com/kaliiiiiiiiii/brotector) für Browser-Erkennungs-Umgehungstechniken
- [fakebrowser](https://github.com/kkoooqq/fakebrowser) und [BotBrowser](https://github.com/botswin/BotBrowser) für Fingerprinting-Forschung

---
<div align="center"><small>Entworfen und hergestellt mit ❤️ von Karim Shoair.</small></div><br>

----------------------------------------


## File: README_ES.md
<!-- Source: docs/README_ES.md -->

<p align=center>
  <br>
  <a href="https://scrapling.readthedocs.io/en/latest/" target="_blank"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/poster.png" style="width: 50%; height: 100%;" alt="main poster"/></a>
  <br>
  <i><code>¡Web Scraping fácil y sin esfuerzo como debería ser!</code></i>
</p>
<p align="center">
    <a href="https://github.com/D4Vinci/Scrapling/actions/workflows/tests.yml" alt="Tests">
        <img alt="Tests" src="https://github.com/D4Vinci/Scrapling/actions/workflows/tests.yml/badge.svg"></a>
    <a href="https://badge.fury.io/py/Scrapling" alt="PyPI version">
        <img alt="PyPI version" src="https://badge.fury.io/py/Scrapling.svg"></a>
    <a href="https://pepy.tech/project/scrapling" alt="PyPI Downloads">
        <img alt="PyPI Downloads" src="https://static.pepy.tech/personalized-badge/scrapling?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=GREEN&left_text=Downloads"></a>
    <br/>
    <a href="https://discord.gg/EMgGbDceNQ" alt="Discord" target="_blank">
      <img alt="Discord" src="https://img.shields.io/discord/1360786381042880532?style=social&logo=discord&link=https%3A%2F%2Fdiscord.gg%2FEMgGbDceNQ">
    </a>
    <a href="https://x.com/Scrapling_dev" alt="X (formerly Twitter)">
      <img alt="X (formerly Twitter) Follow" src="https://img.shields.io/twitter/follow/Scrapling_dev?style=social&logo=x&link=https%3A%2F%2Fx.com%2FScrapling_dev">
    </a>
    <br/>
    <a href="https://pypi.org/project/scrapling/" alt="Supported Python versions">
        <img alt="Supported Python versions" src="https://img.shields.io/pypi/pyversions/scrapling.svg"></a>
</p>

<p align="center">
    <a href="https://scrapling.readthedocs.io/en/latest/parsing/selection/">
        Métodos de selección
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/fetching/choosing/">
        Elegir un fetcher
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/cli/overview/">
        CLI
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/ai/mcp-server/">
        Modo MCP
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/tutorials/migrating_from_beautifulsoup/">
        Migrar desde Beautifulsoup
    </a>
</p>

**Deja de luchar contra sistemas anti-bot. Deja de reescribir selectores después de cada actualización del sitio web.**

Scrapling no es solo otra biblioteca de Web Scraping. Es la primera biblioteca de scraping **adaptativa** que aprende de los cambios de los sitios web y evoluciona con ellos. Mientras que otras bibliotecas se rompen cuando los sitios web actualizan su estructura, Scrapling relocaliza automáticamente tus elementos y mantiene tus scrapers funcionando.

Construido para la Web moderna, Scrapling presenta **su propio motor de análisis rápido** y fetchers para manejar todos los desafíos de Web Scraping que enfrentas o enfrentarás. Construido por Web Scrapers para Web Scrapers y usuarios regulares, hay algo para todos.

```python
>> from scrapling.fetchers import Fetcher, AsyncFetcher, StealthyFetcher, DynamicFetcher
>> StealthyFetcher.adaptive = True
# ¡Obtén el código fuente de sitios web bajo el radar!
>> page = StealthyFetcher.fetch('https://example.com', headless=True, network_idle=True)
>> print(page.status)
200
>> products = page.css('.product', auto_save=True)  # ¡Extrae datos que sobreviven a cambios de diseño del sitio web!
>> # Más tarde, si la estructura del sitio web cambia, pasa `adaptive=True`
>> products = page.css('.product', adaptive=True)  # ¡y Scrapling aún los encuentra!
```

# Patrocinadores 

<!-- sponsors -->

<a href="https://www.scrapeless.com/en?utm_source=official&utm_term=scrapling" target="_blank" title="Effortless Web Scraping Toolkit for Business and Developers"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/scrapeless.jpg"></a>
<a href="https://www.thordata.com/?ls=github&lk=github" target="_blank" title="Unblockable proxies and scraping infrastructure, delivering real-time, reliable web data to power AI models and workflows."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/thordata.jpg"></a>
<a href="https://evomi.com?utm_source=github&utm_medium=banner&utm_campaign=d4vinci-scrapling" target="_blank" title="Evomi is your Swiss Quality Proxy Provider, starting at $0.49/GB"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/evomi.png"></a>
<a href="https://serpapi.com/?utm_source=scrapling" target="_blank" title="Scrape Google and other search engines with SerpApi"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/SerpApi.png"></a>
<a href="https://visit.decodo.com/Dy6W0b" target="_blank" title="Try the Most Efficient Residential Proxies for Free"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/decodo.png"></a>
<a href="https://petrosky.io/d4vinci" target="_blank" title="PetroSky delivers cutting-edge VPS hosting."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/petrosky.png"></a>
<a href="https://www.swiftproxy.net/" target="_blank" title="Unlock Reliable Proxy Services with Swiftproxy!"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/swiftproxy.png"></a>
<a href="https://www.rapidproxy.io/?ref=d4v" target="_blank" title="Affordable Access to the Proxy World – bypass CAPTCHAs blocks, and avoid additional costs."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/rapidproxy.jpg"></a>
<a href="https://browser.cash/?utm_source=D4Vinci&utm_medium=referral" target="_blank" title="Browser Automation & AI Browser Agent Platform"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/browserCash.png"></a>

<!-- /sponsors -->

<i><sub>¿Quieres mostrar tu anuncio aquí? ¡Haz clic [aquí](https://github.com/sponsors/D4Vinci) y elige el nivel que te convenga!</sub></i>

---

## Características Principales

### Obtención Avanzada de Sitios Web con Soporte de Sesión
- **Solicitudes HTTP**: Solicitudes HTTP rápidas y sigilosas con la clase `Fetcher`. Puede imitar la huella TLS de los navegadores, encabezados y usar HTTP3.
- **Carga Dinámica**: Obtén sitios web dinámicos con automatización completa del navegador a través de la clase `DynamicFetcher` compatible con Chromium de Playwright, Chrome real y modo sigiloso personalizado.
- **Evasión Anti-bot**: Capacidades de sigilo avanzadas con `StealthyFetcher` usando una versión modificada de Firefox y falsificación de huellas digitales. Puede evadir todos los tipos de Turnstile e Interstitial de Cloudflare con automatización fácilmente.
- **Gestión de Sesión**: Soporte de sesión persistente con las clases `FetcherSession`, `StealthySession` y `DynamicSession` para la gestión de cookies y estado entre solicitudes.
- **Soporte Async**: Soporte async completo en todos los fetchers y clases de sesión async dedicadas.

### Scraping Adaptativo e Integración con IA
- 🔄 **Seguimiento Inteligente de Elementos**: Relocaliza elementos después de cambios en el sitio web usando algoritmos inteligentes de similitud.
- 🎯 **Selección Flexible Inteligente**: Selectores CSS, selectores XPath, búsqueda basada en filtros, búsqueda de texto, búsqueda regex y más.
- 🔍 **Encontrar Elementos Similares**: Localiza automáticamente elementos similares a los elementos encontrados.
- 🤖 **Servidor MCP para usar con IA**: Servidor MCP integrado para Web Scraping asistido por IA y extracción de datos. El servidor MCP presenta capacidades personalizadas y poderosas que utilizan Scrapling para extraer contenido específico antes de pasarlo a la IA (Claude/Cursor/etc), acelerando así las operaciones y reduciendo costos al minimizar el uso de tokens. ([video demo](https://www.youtube.com/watch?v=qyFk3ZNwOxE))

### Arquitectura de Alto Rendimiento y Probada en Batalla
- 🚀 **Ultrarrápido**: Rendimiento optimizado que supera a la mayoría de las bibliotecas de scraping de Python.
- 🔋 **Eficiente en Memoria**: Estructuras de datos optimizadas y carga diferida para una huella de memoria mínima.
- ⚡ **Serialización JSON Rápida**: 10 veces más rápido que la biblioteca estándar.
- 🏗️ **Probado en batalla**: Scrapling no solo tiene una cobertura de prueba del 92% y cobertura completa de type hints, sino que ha sido utilizado diariamente por cientos de Web Scrapers durante el último año.

### Experiencia Amigable para Desarrolladores/Web Scrapers
- 🎯 **Shell Interactivo de Web Scraping**: Shell IPython integrado opcional con integración de Scrapling, atajos y nuevas herramientas para acelerar el desarrollo de scripts de Web Scraping, como convertir solicitudes curl a solicitudes Scrapling y ver resultados de solicitudes en tu navegador.
- 🚀 **Úsalo directamente desde la Terminal**: Opcionalmente, ¡puedes usar Scrapling para hacer scraping de una URL sin escribir ni una sola línea de código!
- 🛠️ **API de Navegación Rica**: Recorrido avanzado del DOM con métodos de navegación de padres, hermanos e hijos.
- 🧬 **Procesamiento de Texto Mejorado**: Métodos integrados de regex, limpieza y operaciones de cadena optimizadas.
- 📝 **Generación Automática de Selectores**: Genera selectores CSS/XPath robustos para cualquier elemento.
- 🔌 **API Familiar**: Similar a Scrapy/BeautifulSoup con los mismos pseudo-elementos usados en Scrapy/Parsel.
- 📘 **Cobertura Completa de Tipos**: Type hints completos para excelente soporte de IDE y autocompletado de código.
- 🔋 **Imagen Docker Lista**: Con cada lanzamiento, se construye y publica automáticamente una imagen Docker que contiene todos los navegadores.

## Empezando

### Uso Básico
```python
from scrapling.fetchers import Fetcher, StealthyFetcher, DynamicFetcher
from scrapling.fetchers import FetcherSession, StealthySession, DynamicSession

# Solicitudes HTTP con soporte de sesión
with FetcherSession(impersonate='chrome') as session:  # Usa la última versión de la huella TLS de Chrome
    page = session.get('https://quotes.toscrape.com/', stealthy_headers=True)
    quotes = page.css('.quote .text::text')

# O usa solicitudes de una sola vez
page = Fetcher.get('https://quotes.toscrape.com/')
quotes = page.css('.quote .text::text')

# Modo sigiloso avanzado (Mantén el navegador abierto hasta que termines)
with StealthySession(headless=True, solve_cloudflare=True) as session:
    page = session.fetch('https://nopecha.com/demo/cloudflare', google_search=False)
    data = page.css('#padded_content a')

# O usa el estilo de solicitud de una sola vez, abre el navegador para esta solicitud, luego lo cierra después de terminar
page = StealthyFetcher.fetch('https://nopecha.com/demo/cloudflare')
data = page.css('#padded_content a')
    
# Automatización completa del navegador (Mantén el navegador abierto hasta que termines)
with DynamicSession(headless=True) as session:
    page = session.fetch('https://quotes.toscrape.com/', network_idle=True)
    quotes = page.css('.quote .text::text')

# O usa el estilo de solicitud de una sola vez
page = DynamicFetcher.fetch('https://quotes.toscrape.com/', network_idle=True)
quotes = page.css('.quote .text::text')
```

### Selección de Elementos
```python
# CSS selectors
page.css('a::text')                      # Extracta texto
page.css('a::attr(href)')                # Extracta atributos
page.css('a', recursive=False)           # Solo elementos directos
page.css('a', auto_save=True)            # Guarda posiciones de los elementos automáticamente

# XPath
page.xpath('//a/text()')

# Búsqueda flexible
page.find_by_text('Python', first_match=True)  # Encuentra por texto
page.find_by_regex(r'\d{4}')                   # Encuentra por patrón regex
page.find('div', {'class': 'container'})       # Encuentra por atributos

# Navegación
element.parent                           # Obtener elemento padre
element.next_sibling                     # Obtener siguiente hermano
element.children                         # Obtener hijos

# Elementos similares
similar = page.get_similar(element)      # Encuentra elementos similares

# Scraping adaptativo
saved_elements = page.css('.product', auto_save=True)
# Más tarde, cuando el sitio web cambia:
page.css('.product', adaptive=True)      # Encuentra elementos usando posiciones guardadas
```

### Uso de Sesión
```python
from scrapling.fetchers import FetcherSession, AsyncFetcherSession

# Sesión sincrónica
with FetcherSession() as session:
    # Las cookies se mantienen automáticamente
    page1 = session.get('https://quotes.toscrape.com/login')
    page2 = session.post('https://quotes.toscrape.com/login', data={'username': 'admin', 'password': 'admin'})
    
    # Cambiar fingerprint del navegador si es necesario
    page2 = session.get('https://quotes.toscrape.com/', impersonate='firefox135')

# Uso de sesión async
async with AsyncStealthySession(max_pages=2) as session:
    tasks = []
    urls = ['https://example.com/page1', 'https://example.com/page2']
    
    for url in urls:
        task = session.fetch(url)
        tasks.append(task)
    
    print(session.get_pool_stats())  # Opcional - El estado del pool de pestañas del navegador (ocupado/libre/error)
    results = await asyncio.gather(*tasks)
    print(session.get_pool_stats())
```

## CLI y Shell Interactivo

Scrapling v0.3 incluye una poderosa interfaz de línea de comandos:

[![asciicast](https://asciinema.org/a/736339.svg)](https://asciinema.org/a/736339)

```bash
# Lanzar shell interactivo de Web Scraping
scrapling shell

# Extraer páginas a un archivo directamente sin programar (Extrae el contenido dentro de la etiqueta `body` por defecto)
# Si el archivo de salida termina con `.txt`, entonces se extraerá el contenido de texto del objetivo.
# Si termina con `.md`, será una representación markdown del contenido HTML, y `.html` será el contenido HTML directamente.
scrapling extract get 'https://example.com' content.md
scrapling extract get 'https://example.com' content.txt --css-selector '#fromSkipToProducts' --impersonate 'chrome'  # Todos los elementos que coinciden con el selector CSS '#fromSkipToProducts'
scrapling extract fetch 'https://example.com' content.md --css-selector '#fromSkipToProducts' --no-headless
scrapling extract stealthy-fetch 'https://nopecha.com/demo/cloudflare' captchas.html --css-selector '#padded_content a' --solve-cloudflare
```

> [!NOTE]
> Hay muchas características adicionales, pero queremos mantener esta página concisa, como el servidor MCP y el Shell Interactivo de Web Scraping. Consulta la documentación completa [aquí](https://scrapling.readthedocs.io/en/latest/)

## Benchmarks de Rendimiento

Scrapling no solo es poderoso, también es increíblemente rápido, y las actualizaciones desde la versión 0.3 han brindado mejoras de rendimiento excepcionales en todas las operaciones.

### Prueba de Velocidad de Extracción de Texto (5000 elementos anidados)

| # |    Biblioteca     | Tiempo (ms) | vs Scrapling | 
|---|:-----------------:|:-----------:|:------------:|
| 1 |     Scrapling     |    1.99     |     1.0x     |
| 2 |   Parsel/Scrapy   |    2.01     |    1.01x     |
| 3 |     Raw Lxml      |     2.5     |    1.256x    |
| 4 |      PyQuery      |    22.93    |    ~11.5x    |
| 5 |    Selectolax     |    80.57    |    ~40.5x    |
| 6 |   BS4 with Lxml   |   1541.37   |   ~774.6x    |
| 7 |  MechanicalSoup   |   1547.35   |   ~777.6x    |
| 8 | BS4 with html5lib |   3410.58   |   ~1713.9x   |


### Rendimiento de Similitud de Elementos y Búsqueda de Texto

Las capacidades de búsqueda adaptativa de elementos de Scrapling superan significativamente a las alternativas:

| Biblioteca  | Tiempo (ms) | vs Scrapling |
|-------------|:-----------:|:------------:|
| Scrapling   |    2.46     |     1.0x     |
| AutoScraper |    13.3     |    5.407x    |


> Todos los benchmarks representan promedios de más de 100 ejecuciones. Ver [benchmarks.py](https://github.com/D4Vinci/Scrapling/blob/main/benchmarks.py) para la metodología.

## Instalación

Scrapling requiere Python 3.10 o superior:

```bash
pip install scrapling
```

A partir de v0.3.2, esta instalación solo incluye el motor de análisis y sus dependencias, sin ningún fetcher o dependencias de línea de comandos.

### Dependencias Opcionales

1. Si vas a usar alguna de las características adicionales a continuación, los fetchers, o sus clases, entonces necesitas instalar las dependencias de los fetchers y luego instalar sus dependencias del navegador con
    ```bash
    pip install "scrapling[fetchers]"
    
    scrapling install
    ```

    Esto descarga todos los navegadores con sus dependencias del sistema y dependencias de manipulación de huellas digitales.

2. Características adicionales:
   - Instalar la característica del servidor MCP:
       ```bash
       pip install "scrapling[ai]"
       ```
   - Instalar características del shell (shell de Web Scraping y el comando `extract`): 
       ```bash
       pip install "scrapling[shell]"
       ```
   - Instalar todo: 
       ```bash
       pip install "scrapling[all]"
       ```
   Recuerda que necesitas instalar las dependencias del navegador con `scrapling install` después de cualquiera de estos extras (si no lo hiciste ya)

### Docker
También puedes instalar una imagen Docker con todos los extras y navegadores con el siguiente comando desde DockerHub:
```bash
docker pull pyd4vinci/scrapling
```
O descárgala desde el registro de GitHub:
```bash
docker pull ghcr.io/d4vinci/scrapling:latest
```
Esta imagen se construye y publica automáticamente a través de GitHub actions en la rama principal del repositorio.

## Contribuir

¡Damos la bienvenida a las contribuciones! Por favor lee nuestras [pautas de contribución](https://github.com/D4Vinci/Scrapling/blob/main/CONTRIBUTING.md) antes de comenzar.

## Descargo de Responsabilidad

> [!CAUTION]
> Esta biblioteca se proporciona solo con fines educativos y de investigación. Al usar esta biblioteca, aceptas cumplir con las leyes locales e internacionales de scraping de datos y privacidad. Los autores y contribuyentes no son responsables de ningún mal uso de este software. Respeta siempre los términos de servicio de los sitios web y los archivos robots.txt.

## Licencia

Este trabajo está licenciado bajo la Licencia BSD-3-Clause.

## Agradecimientos

Este proyecto incluye código adaptado de:
- Parsel (Licencia BSD)—Usado para el submódulo [translator](https://github.com/D4Vinci/Scrapling/blob/main/scrapling/core/translator.py)

## Agradecimientos y Referencias

- El brillante trabajo de [Daijro](https://github.com/daijro) en [BrowserForge](https://github.com/daijro/browserforge) y [Camoufox](https://github.com/daijro/camoufox)
- El brillante trabajo de [Vinyzu](https://github.com/Vinyzu) en [Botright](https://github.com/Vinyzu/Botright) y [PatchRight](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright)
- [brotector](https://github.com/kaliiiiiiiiii/brotector) por técnicas de evasión de detección de navegador
- [fakebrowser](https://github.com/kkoooqq/fakebrowser) y [BotBrowser](https://github.com/botswin/BotBrowser) por investigación de huellas digitales

---
<div align="center"><small>Diseñado y elaborado con ❤️ por Karim Shoair.</small></div><br>

----------------------------------------


## File: README_JP.md
<!-- Source: docs/README_JP.md -->

<p align=center>
  <br>
  <a href="https://scrapling.readthedocs.io/en/latest/" target="_blank"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/poster.png" style="width: 50%; height: 100%;" alt="main poster"/></a>
  <br>
  <i><code>簡単で効率的なウェブスクレイピング、あるべき姿！</code></i>
</p>
<p align="center">
    <a href="https://github.com/D4Vinci/Scrapling/actions/workflows/tests.yml" alt="Tests">
        <img alt="Tests" src="https://github.com/D4Vinci/Scrapling/actions/workflows/tests.yml/badge.svg"></a>
    <a href="https://badge.fury.io/py/Scrapling" alt="PyPI version">
        <img alt="PyPI version" src="https://badge.fury.io/py/Scrapling.svg"></a>
    <a href="https://pepy.tech/project/scrapling" alt="PyPI Downloads">
        <img alt="PyPI Downloads" src="https://static.pepy.tech/personalized-badge/scrapling?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=GREEN&left_text=Downloads"></a>
    <br/>
    <a href="https://discord.gg/EMgGbDceNQ" alt="Discord" target="_blank">
      <img alt="Discord" src="https://img.shields.io/discord/1360786381042880532?style=social&logo=discord&link=https%3A%2F%2Fdiscord.gg%2FEMgGbDceNQ">
    </a>
    <a href="https://x.com/Scrapling_dev" alt="X (formerly Twitter)">
      <img alt="X (formerly Twitter) Follow" src="https://img.shields.io/twitter/follow/Scrapling_dev?style=social&logo=x&link=https%3A%2F%2Fx.com%2FScrapling_dev">
    </a>
    <br/>
    <a href="https://pypi.org/project/scrapling/" alt="Supported Python versions">
        <img alt="Supported Python versions" src="https://img.shields.io/pypi/pyversions/scrapling.svg"></a>
</p>

<p align="center">
    <a href="https://scrapling.readthedocs.io/en/latest/parsing/selection/">
        選択メソッド
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/fetching/choosing/">
        フェッチャーの選択
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/cli/overview/">
        CLI
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/ai/mcp-server/">
        MCPモード
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/tutorials/migrating_from_beautifulsoup/">
        Beautifulsoupからの移行
    </a>
</p>

**アンチボットシステムとの戦いをやめましょう。ウェブサイトが更新されるたびにセレクタを書き直すのをやめましょう。**

Scraplingは単なるウェブスクレイピングライブラリではありません。ウェブサイトの変更から学習し、それとともに進化する最初の**適応型**スクレイピングライブラリです。他のライブラリがウェブサイトの構造が更新されると壊れる一方で、Scraplingは自動的に要素を再配置し、スクレイパーを稼働し続けます。

モダンウェブ向けに構築されたScraplingは、**独自の高速パースエンジン**とフェッチャーを備えており、あなたが直面する、または直面するであろうすべてのウェブスクレイピングの課題に対応します。ウェブスクレイパーによってウェブスクレイパーと一般ユーザーのために構築され、誰にでも何かがあります。

```python
>> from scrapling.fetchers import Fetcher, AsyncFetcher, StealthyFetcher, DynamicFetcher
>> StealthyFetcher.adaptive = True
# レーダーの下でウェブサイトのソースを取得！
>> page = StealthyFetcher.fetch('https://example.com', headless=True, network_idle=True)
>> print(page.status)
200
>> products = page.css('.product', auto_save=True)  # ウェブサイトのデザイン変更に耐えるデータをスクレイプ！
>> # 後でウェブサイトの構造が変わったら、`adaptive=True`を渡す
>> products = page.css('.product', adaptive=True)  # そしてScraplingはまだそれらを見つけます！
```

# スポンサー 

<!-- sponsors -->

<a href="https://www.scrapeless.com/en?utm_source=official&utm_term=scrapling" target="_blank" title="Effortless Web Scraping Toolkit for Business and Developers"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/scrapeless.jpg"></a>
<a href="https://www.thordata.com/?ls=github&lk=github" target="_blank" title="Unblockable proxies and scraping infrastructure, delivering real-time, reliable web data to power AI models and workflows."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/thordata.jpg"></a>
<a href="https://evomi.com?utm_source=github&utm_medium=banner&utm_campaign=d4vinci-scrapling" target="_blank" title="Evomi is your Swiss Quality Proxy Provider, starting at $0.49/GB"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/evomi.png"></a>
<a href="https://serpapi.com/?utm_source=scrapling" target="_blank" title="Scrape Google and other search engines with SerpApi"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/SerpApi.png"></a>
<a href="https://visit.decodo.com/Dy6W0b" target="_blank" title="Try the Most Efficient Residential Proxies for Free"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/decodo.png"></a>
<a href="https://petrosky.io/d4vinci" target="_blank" title="PetroSky delivers cutting-edge VPS hosting."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/petrosky.png"></a>
<a href="https://www.swiftproxy.net/" target="_blank" title="Unlock Reliable Proxy Services with Swiftproxy!"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/swiftproxy.png"></a>
<a href="https://www.rapidproxy.io/?ref=d4v" target="_blank" title="Affordable Access to the Proxy World – bypass CAPTCHAs blocks, and avoid additional costs."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/rapidproxy.jpg"></a>
<a href="https://browser.cash/?utm_source=D4Vinci&utm_medium=referral" target="_blank" title="Browser Automation & AI Browser Agent Platform"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/browserCash.png"></a>

<!-- /sponsors -->

<i><sub>ここに広告を表示したいですか？[こちら](https://github.com/sponsors/D4Vinci)をクリックして、あなたに合ったティアを選択してください！</sub></i>

---

## 主な機能

### セッションサポート付き高度なウェブサイト取得
- **HTTPリクエスト**：`Fetcher`クラスで高速でステルスなHTTPリクエスト。ブラウザのTLSフィンガープリント、ヘッダーを模倣し、HTTP3を使用できます。
- **動的読み込み**：Playwright's Chromium、実際のChrome、カスタムステルスモードをサポートする`DynamicFetcher`クラスを通じた完全なブラウザ自動化で動的ウェブサイトを取得。
- **アンチボット回避**：修正されたFirefoxとフィンガープリント偽装を使用した`StealthyFetcher`による高度なステルス機能。自動化でCloudflareのTurnstileとInterstitialのすべてのタイプを簡単に回避できます。
- **セッション管理**：リクエスト間でCookieと状態を管理するための`FetcherSession`、`StealthySession`、`DynamicSession`クラスによる永続的なセッションサポート。
- **非同期サポート**：すべてのフェッチャーと専用非同期セッションクラス全体での完全な非同期サポート。

### 適応型スクレイピングとAI統合
- 🔄 **スマート要素追跡**：インテリジェントな類似性アルゴリズムを使用してウェブサイトの変更後に要素を再配置。
- 🎯 **スマート柔軟選択**：CSSセレクタ、XPathセレクタ、フィルタベース検索、テキスト検索、正規表現検索など。
- 🔍 **類似要素を見つける**：見つかった要素に類似した要素を自動的に特定。
- 🤖 **AIと使用するMCPサーバー**：AI支援ウェブスクレイピングとデータ抽出のための組み込みMCPサーバー。MCPサーバーは、AI（Claude/Cursorなど）に渡す前にScraplingを利用してターゲットコンテンツを抽出するカスタムで強力な機能を備えており、操作を高速化し、トークン使用量を最小限に抑えることでコストを削減します。（[デモビデオ](https://www.youtube.com/watch?v=qyFk3ZNwOxE)）

### 高性能で実戦テスト済みのアーキテクチャ
- 🚀 **高速**：ほとんどのPythonスクレイピングライブラリを上回る最適化されたパフォーマンス。
- 🔋 **メモリ効率**：最小のメモリフットプリントのための最適化されたデータ構造と遅延読み込み。
- ⚡ **高速JSONシリアル化**：標準ライブラリの10倍の速度。
- 🏗️ **実戦テスト済み**：Scraplingは92%のテストカバレッジと完全な型ヒントカバレッジを備えているだけでなく、過去1年間に数百人のウェブスクレイパーによって毎日使用されてきました。

### 開発者/ウェブスクレイパーにやさしい体験
- 🎯 **インタラクティブウェブスクレイピングシェル**：Scraping統合、ショートカット、curlリクエストをScraplingリクエストに変換したり、ブラウザでリクエスト結果を表示したりするなどの新しいツールを備えたオプションの組み込みIPythonシェルで、ウェブスクレイピングスクリプトの開発を加速します。
- 🚀 **ターミナルから直接使用**：オプションで、コードを一行も書かずにScraplingを使用してURLをスクレイプできます！
- 🛠️ **豊富なナビゲーションAPI**：親、兄弟、子のナビゲーションメソッドによる高度なDOMトラバーサル。
- 🧬 **強化されたテキスト処理**：組み込みの正規表現、クリーニングメソッド、最適化された文字列操作。
- 📝 **自動セレクタ生成**：任意の要素に対して堅牢なCSS/XPathセレクタを生成。
- 🔌 **馴染みのあるAPI**：Scrapy/Parselで使用されている同じ疑似要素を持つScrapy/BeautifulSoupに似ています。
- 📘 **完全な型カバレッジ**：優れたIDEサポートとコード補完のための完全な型ヒント。
- 🔋 **すぐに使えるDockerイメージ**：各リリースで、すべてのブラウザを含むDockerイメージが自動的にビルドおよびプッシュされます。

## はじめに

### 基本的な使い方
```python
from scrapling.fetchers import Fetcher, StealthyFetcher, DynamicFetcher
from scrapling.fetchers import FetcherSession, StealthySession, DynamicSession

# セッションサポート付きHTTPリクエスト
with FetcherSession(impersonate='chrome') as session:  # ChromeのTLSフィンガープリントの最新バージョンを使用
    page = session.get('https://quotes.toscrape.com/', stealthy_headers=True)
    quotes = page.css('.quote .text::text')

# または一回限りのリクエストを使用
page = Fetcher.get('https://quotes.toscrape.com/')
quotes = page.css('.quote .text::text')

# 高度なステルスモード（完了するまでブラウザを開いたままにする）
with StealthySession(headless=True, solve_cloudflare=True) as session:
    page = session.fetch('https://nopecha.com/demo/cloudflare', google_search=False)
    data = page.css('#padded_content a')

# または一回限りのリクエストスタイルを使用、このリクエストのためにブラウザを開き、完了後に閉じる
page = StealthyFetcher.fetch('https://nopecha.com/demo/cloudflare')
data = page.css('#padded_content a')
    
# 完全なブラウザ自動化（完了するまでブラウザを開いたままにする）
with DynamicSession(headless=True) as session:
    page = session.fetch('https://quotes.toscrape.com/', network_idle=True)
    quotes = page.css('.quote .text::text')

# または一回限りのリクエストスタイルを使用
page = DynamicFetcher.fetch('https://quotes.toscrape.com/', network_idle=True)
quotes = page.css('.quote .text::text')
```

### 要素の選択
```python
# CSSセレクタ
page.css('a::text')                      # テキストを抽出
page.css('a::attr(href)')                # 属性を抽出
page.css('a', recursive=False)           # 直接の要素のみ
page.css('a', auto_save=True)            # 要素の位置を自動保存

# XPath
page.xpath('//a/text()')

# 柔軟な検索
page.find_by_text('Python', first_match=True)  # テキストで検索
page.find_by_regex(r'\d{4}')                   # 正規表現パターンで検索
page.find('div', {'class': 'container'})       # 属性で検索

# ナビゲーション
element.parent                           # 親要素を取得
element.next_sibling                     # 次の兄弟を取得
element.children                         # 子要素を取得

# 類似要素
similar = page.get_similar(element)      # 類似要素を見つける

# 適応型スクレイピング
saved_elements = page.css('.product', auto_save=True)
# 後でウェブサイトが変更されたとき：
page.css('.product', adaptive=True)      # 保存された位置を使用して要素を見つける
```

### セッションの使用
```python
from scrapling.fetchers import FetcherSession, AsyncFetcherSession

# 同期セッション
with FetcherSession() as session:
    # Cookieは自動的に維持されます
    page1 = session.get('https://quotes.toscrape.com/login')
    page2 = session.post('https://quotes.toscrape.com/login', data={'username': 'admin', 'password': 'admin'})
    
    # 必要に応じてブラウザのフィンガープリントを切り替え
    page2 = session.get('https://quotes.toscrape.com/', impersonate='firefox135')

# 非同期セッションの使用
async with AsyncStealthySession(max_pages=2) as session:
    tasks = []
    urls = ['https://example.com/page1', 'https://example.com/page2']
    
    for url in urls:
        task = session.fetch(url)
        tasks.append(task)
    
    print(session.get_pool_stats())  # オプション - ブラウザタブプールのステータス（ビジー/フリー/エラー）
    results = await asyncio.gather(*tasks)
    print(session.get_pool_stats())
```

## CLIとインタラクティブシェル

Scrapling v0.3には強力なコマンドラインインターフェースが含まれています：

[![asciicast](https://asciinema.org/a/736339.svg)](https://asciinema.org/a/736339)

```bash
# インタラクティブウェブスクレイピングシェルを起動
scrapling shell

# プログラミングせずに直接ページをファイルに抽出（デフォルトで`body`タグ内のコンテンツを抽出）
# 出力ファイルが`.txt`で終わる場合、ターゲットのテキストコンテンツが抽出されます。
# `.md`で終わる場合、HTMLコンテンツのMarkdown表現になり、`.html`は直接HTMLコンテンツになります。
scrapling extract get 'https://example.com' content.md
scrapling extract get 'https://example.com' content.txt --css-selector '#fromSkipToProducts' --impersonate 'chrome'  # CSSセレクタ'#fromSkipToProducts'に一致するすべての要素
scrapling extract fetch 'https://example.com' content.md --css-selector '#fromSkipToProducts' --no-headless
scrapling extract stealthy-fetch 'https://nopecha.com/demo/cloudflare' captchas.html --css-selector '#padded_content a' --solve-cloudflare
```

> [!NOTE]
> MCPサーバーやインタラクティブウェブスクレイピングシェルなど、他にも多くの追加機能がありますが、このページは簡潔に保ちたいと思います。完全なドキュメントは[こちら](https://scrapling.readthedocs.io/en/latest/)をご覧ください

## パフォーマンスベンチマーク

Scraplingは強力であるだけでなく、驚くほど高速で、バージョン0.3以降のアップデートはすべての操作で優れたパフォーマンス向上を実現しています。

### テキスト抽出速度テスト（5000個のネストされた要素）

| # |       ライブラリ       | 時間(ms)  | vs Scrapling | 
|---|:-----------------:|:-------:|:------------:|
| 1 |     Scrapling     |  1.99   |     1.0x     |
| 2 |   Parsel/Scrapy   |  2.01   |    1.01x     |
| 3 |     Raw Lxml      |   2.5   |    1.256x    |
| 4 |      PyQuery      |  22.93  |    ~11.5x    |
| 5 |    Selectolax     |  80.57  |    ~40.5x    |
| 6 |   BS4 with Lxml   | 1541.37 |   ~774.6x    |
| 7 |  MechanicalSoup   | 1547.35 |   ~777.6x    |
| 8 | BS4 with html5lib | 3410.58 |   ~1713.9x   |


### 要素類似性とテキスト検索のパフォーマンス

Scraplingの適応型要素検索機能は代替手段を大幅に上回ります：

| ライブラリ       | 時間(ms) | vs Scrapling |
|-------------|:------:|:------------:|
| Scrapling   |  2.46  |     1.0x     |
| AutoScraper |  13.3  |    5.407x    |


> すべてのベンチマークは100回以上の実行の平均を表します。方法論については[benchmarks.py](https://github.com/D4Vinci/Scrapling/blob/main/benchmarks.py)を参照してください。

## インストール

ScraplingにはPython 3.10以上が必要です：

```bash
pip install scrapling
```

v0.3.2以降、このインストールにはパーサーエンジンとその依存関係のみが含まれており、フェッチャーやコマンドライン依存関係は含まれていません。

### オプションの依存関係

1. 以下の追加機能、フェッチャー、またはそれらのクラスのいずれかを使用する場合は、フェッチャーの依存関係をインストールしてから、次のコマンドでブラウザの依存関係をインストールする必要があります
    ```bash
    pip install "scrapling[fetchers]"
    
    scrapling install
    ```

    これにより、すべてのブラウザとそのシステム依存関係およびフィンガープリント操作依存関係がダウンロードされます。

2. 追加機能：
   - MCPサーバー機能をインストール：
       ```bash
       pip install "scrapling[ai]"
       ```
   - シェル機能（ウェブスクレイピングシェルと`extract`コマンド）をインストール：
       ```bash
       pip install "scrapling[shell]"
       ```
   - すべてをインストール：
       ```bash
       pip install "scrapling[all]"
       ```
   これらの追加機能のいずれかの後（まだインストールしていない場合）、`scrapling install`でブラウザの依存関係をインストールする必要があることを忘れないでください

### Docker
DockerHubから次のコマンドですべての追加機能とブラウザを含むDockerイメージをインストールすることもできます：
```bash
docker pull pyd4vinci/scrapling
```
またはGitHubレジストリからダウンロード：
```bash
docker pull ghcr.io/d4vinci/scrapling:latest
```
このイメージは、リポジトリのメインブランチでGitHub actionsを通じて自動的にビルドおよびプッシュされます。

## 貢献

貢献を歓迎します！始める前に[貢献ガイドライン](https://github.com/D4Vinci/Scrapling/blob/main/CONTRIBUTING.md)をお読みください。

## 免責事項

> [!CAUTION]
> このライブラリは教育および研究目的のみで提供されています。このライブラリを使用することにより、地域および国際的なデータスクレイピングおよびプライバシー法に準拠することに同意したものとみなされます。著者および貢献者は、このソフトウェアの誤用について責任を負いません。常にウェブサイトの利用規約とrobots.txtファイルを尊重してください。

## ライセンス

この作品はBSD-3-Clauseライセンスの下でライセンスされています。

## 謝辞

このプロジェクトには次から適応されたコードが含まれています：
- Parsel（BSDライセンス）— [translator](https://github.com/D4Vinci/Scrapling/blob/main/scrapling/core/translator.py)サブモジュールに使用

## 感謝と参考文献

- [Daijro](https://github.com/daijro)の[BrowserForge](https://github.com/daijro/browserforge)と[Camoufox](https://github.com/daijro/camoufox)における素晴らしい仕事
- [Vinyzu](https://github.com/Vinyzu)の[Botright](https://github.com/Vinyzu/Botright)と[PatchRight](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright)における素晴らしい仕事
- ブラウザ検出回避技術を提供する[brotector](https://github.com/kaliiiiiiiiii/brotector)
- フィンガープリント研究を提供する[fakebrowser](https://github.com/kkoooqq/fakebrowser)と[BotBrowser](https://github.com/botswin/BotBrowser)

---
<div align="center"><small>Karim Shoairによって❤️でデザインおよび作成されました。</small></div><br>

----------------------------------------


## File: README_RU.md
<!-- Source: docs/README_RU.md -->

<p align=center>
  <br>
  <a href="https://scrapling.readthedocs.io/en/latest/" target="_blank"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/poster.png" style="width: 50%; height: 100%;" alt="main poster"/></a>
  <br>
  <i><code>Простой, легкий веб-скрапинг, каким он и должен быть!</code></i>
</p>
<p align="center">
    <a href="https://github.com/D4Vinci/Scrapling/actions/workflows/tests.yml" alt="Tests">
        <img alt="Tests" src="https://github.com/D4Vinci/Scrapling/actions/workflows/tests.yml/badge.svg"></a>
    <a href="https://badge.fury.io/py/Scrapling" alt="PyPI version">
        <img alt="PyPI version" src="https://badge.fury.io/py/Scrapling.svg"></a>
    <a href="https://pepy.tech/project/scrapling" alt="PyPI Downloads">
        <img alt="PyPI Downloads" src="https://static.pepy.tech/personalized-badge/scrapling?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=GREEN&left_text=Downloads"></a>
    <br/>
    <a href="https://discord.gg/EMgGbDceNQ" alt="Discord" target="_blank">
      <img alt="Discord" src="https://img.shields.io/discord/1360786381042880532?style=social&logo=discord&link=https%3A%2F%2Fdiscord.gg%2FEMgGbDceNQ">
    </a>
    <a href="https://x.com/Scrapling_dev" alt="X (formerly Twitter)">
      <img alt="X (formerly Twitter) Follow" src="https://img.shields.io/twitter/follow/Scrapling_dev?style=social&logo=x&link=https%3A%2F%2Fx.com%2FScrapling_dev">
    </a>
    <br/>
    <a href="https://pypi.org/project/scrapling/" alt="Supported Python versions">
        <img alt="Supported Python versions" src="https://img.shields.io/pypi/pyversions/scrapling.svg"></a>
</p>

<p align="center">
    <a href="https://scrapling.readthedocs.io/en/latest/parsing/selection/">
        Методы выбора
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/fetching/choosing/">
        Выбор фетчера
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/cli/overview/">
        CLI
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/ai/mcp-server/">
        Режим MCP
    </a>
    ·
    <a href="https://scrapling.readthedocs.io/en/latest/tutorials/migrating_from_beautifulsoup/">
        Миграция с Beautifulsoup
    </a>
</p>

**Прекратите бороться с анти-ботовыми системами. Прекратите переписывать селекторы после каждого обновления сайта.**

Scrapling - это не просто очередная библиотека для веб-скрапинга. Это первая **адаптивная** библиотека для скрапинга, которая учится на изменениях сайтов и развивается вместе с ними. В то время как другие библиотеки ломаются, когда сайты обновляют свою структуру, Scrapling автоматически перемещает ваши элементы и поддерживает работу ваших скраперов.

Созданный для современного веба, Scrapling имеет **собственный быстрый движок парсинга** и фетчеры для решения всех задач веб-скрапинга, с которыми вы сталкиваетесь или столкнетесь. Созданный веб-скраперами для веб-скраперов и обычных пользователей, здесь есть что-то для каждого.

```python
>> from scrapling.fetchers import Fetcher, AsyncFetcher, StealthyFetcher, DynamicFetcher
>> StealthyFetcher.adaptive = True
# Получайте исходный код сайтов незаметно!
>> page = StealthyFetcher.fetch('https://example.com', headless=True, network_idle=True)
>> print(page.status)
200
>> products = page.css('.product', auto_save=True)  # Скрапьте данные, которые переживут изменения дизайна сайта!
>> # Позже, если структура сайта изменится, передайте `adaptive=True`
>> products = page.css('.product', adaptive=True)  # и Scrapling все равно их найдет!
```

# Спонсоры 

<!-- sponsors -->

<a href="https://www.scrapeless.com/en?utm_source=official&utm_term=scrapling" target="_blank" title="Effortless Web Scraping Toolkit for Business and Developers"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/scrapeless.jpg"></a>
<a href="https://www.thordata.com/?ls=github&lk=github" target="_blank" title="Unblockable proxies and scraping infrastructure, delivering real-time, reliable web data to power AI models and workflows."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/thordata.jpg"></a>
<a href="https://evomi.com?utm_source=github&utm_medium=banner&utm_campaign=d4vinci-scrapling" target="_blank" title="Evomi is your Swiss Quality Proxy Provider, starting at $0.49/GB"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/evomi.png"></a>
<a href="https://serpapi.com/?utm_source=scrapling" target="_blank" title="Scrape Google and other search engines with SerpApi"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/SerpApi.png"></a>
<a href="https://visit.decodo.com/Dy6W0b" target="_blank" title="Try the Most Efficient Residential Proxies for Free"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/decodo.png"></a>
<a href="https://petrosky.io/d4vinci" target="_blank" title="PetroSky delivers cutting-edge VPS hosting."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/petrosky.png"></a>
<a href="https://www.swiftproxy.net/" target="_blank" title="Unlock Reliable Proxy Services with Swiftproxy!"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/swiftproxy.png"></a>
<a href="https://www.rapidproxy.io/?ref=d4v" target="_blank" title="Affordable Access to the Proxy World – bypass CAPTCHAs blocks, and avoid additional costs."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/rapidproxy.jpg"></a>
<a href="https://browser.cash/?utm_source=D4Vinci&utm_medium=referral" target="_blank" title="Browser Automation & AI Browser Agent Platform"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/browserCash.png"></a>

<!-- /sponsors -->

<i><sub>Хотите показать здесь свою рекламу? Нажмите [здесь](https://github.com/sponsors/D4Vinci) и выберите подходящий вам уровень!</sub></i>

---

## Ключевые особенности

### Продвинутая загрузка сайтов с поддержкой сессий
- **HTTP-запросы**: Быстрые и скрытные HTTP-запросы с классом `Fetcher`. Может имитировать TLS-отпечаток браузера, заголовки и использовать HTTP3.
- **Динамическая загрузка**: Загрузка динамических сайтов с полной автоматизацией браузера через класс `DynamicFetcher`, поддерживающий Chromium от Playwright, настоящий Chrome и пользовательский режим скрытности.
- **Обход анти-ботов**: Расширенные возможности скрытности с `StealthyFetcher`, использующим модифицированную версию Firefox и подмену отпечатков. Может легко обойти все типы Turnstile и Interstitial от Cloudflare с помощью автоматизации.
- **Управление сессиями**: Поддержка постоянных сессий с классами `FetcherSession`, `StealthySession` и `DynamicSession` для управления cookie и состоянием между запросами.
- **Поддержка асинхронности**: Полная асинхронная поддержка во всех фетчерах и выделенных асинхронных классах сессий.

### Адаптивный скрапинг и интеграция с ИИ
- 🔄 **Умное отслеживание элементов**: Перемещайте элементы после изменений сайта с помощью интеллектуальных алгоритмов подобия.
- 🎯 **Умный гибкий выбор**: CSS-селекторы, XPath-селекторы, поиск на основе фильтров, текстовый поиск, поиск по регулярным выражениям и многое другое.
- 🔍 **Поиск похожих элементов**: Автоматически находите элементы, похожие на найденные элементы.
- 🤖 **MCP-сервер для использования с ИИ**: Встроенный MCP-сервер для веб-скрапинга с помощью ИИ и извлечения данных. MCP-сервер обладает пользовательскими, мощными возможностями, которые используют Scrapling для извлечения целевого контента перед передачей его ИИ (Claude/Cursor/и т.д.), тем самым ускоряя операции и снижая затраты за счет минимизации использования токенов. ([демо-видео](https://www.youtube.com/watch?v=qyFk3ZNwOxE))

### Высокопроизводительная и проверенная в боях архитектура
- 🚀 **Молниеносно быстро**: Оптимизированная производительность превосходит большинство библиотек скрапинга Python.
- 🔋 **Эффективное использование памяти**: Оптимизированные структуры данных и ленивая загрузка для минимального потребления памяти.
- ⚡ **Быстрая сериализация JSON**: В 10 раз быстрее, чем стандартная библиотека.
- 🏗️ **Проверено в боях**: Scrapling имеет не только 92% покрытия тестами и полное покрытие type hints, но и ежедневно использовался сотнями веб-скраперов в течение последнего года.

### Удобный для разработчиков/веб-скраперов опыт
- 🎯 **Интерактивная оболочка веб-скрапинга**: Опциональная встроенная оболочка IPython с интеграцией Scrapling, ярлыками и новыми инструментами для ускорения разработки скриптов веб-скрапинга, такими как преобразование curl-запросов в Scrapling-запросы и просмотр результатов запросов в вашем браузере.
- 🚀 **Используйте прямо из терминала**: При желании вы можете использовать Scrapling для скрапинга URL без написания ни одной строки кода!
- 🛠️ **Богатый API навигации**: Расширенный обход DOM с методами навигации по родителям, братьям и детям.
- 🧬 **Улучшенная обработка текста**: Встроенные регулярные выражения, методы очистки и оптимизированные операции со строками.
- 📝 **Автоматическая генерация селекторов**: Генерация надежных CSS/XPath селекторов для любого элемента.
- 🔌 **Знакомый API**: Похож на Scrapy/BeautifulSoup с теми же псевдоэлементами, используемыми в Scrapy/Parsel.
- 📘 **Полное покрытие типами**: Полные подсказки типов для отличной поддержки IDE и автодополнения кода.
- 🔋 **Готовый Docker-образ**: С каждым релизом автоматически создается и отправляется Docker-образ, содержащий все браузеры.

## Начало работы

### Базовое использование
```python
from scrapling.fetchers import Fetcher, StealthyFetcher, DynamicFetcher
from scrapling.fetchers import FetcherSession, StealthySession, DynamicSession

# HTTP-запросы с поддержкой сессий
with FetcherSession(impersonate='chrome') as session:  # Используйте последнюю версию TLS-отпечатка Chrome
    page = session.get('https://quotes.toscrape.com/', stealthy_headers=True)
    quotes = page.css('.quote .text::text')

# Или используйте одноразовые запросы
page = Fetcher.get('https://quotes.toscrape.com/')
quotes = page.css('.quote .text::text')

# Расширенный режим скрытности (Держите браузер открытым до завершения)
with StealthySession(headless=True, solve_cloudflare=True) as session:
    page = session.fetch('https://nopecha.com/demo/cloudflare', google_search=False)
    data = page.css('#padded_content a')

# Или используйте стиль одноразового запроса, открывает браузер для этого запроса, затем закрывает его после завершения
page = StealthyFetcher.fetch('https://nopecha.com/demo/cloudflare')
data = page.css('#padded_content a')
    
# Полная автоматизация браузера (Держите браузер открытым до завершения)
with DynamicSession(headless=True) as session:
    page = session.fetch('https://quotes.toscrape.com/', network_idle=True)
    quotes = page.css('.quote .text::text')

# Или используйте стиль одноразового запроса
page = DynamicFetcher.fetch('https://quotes.toscrape.com/', network_idle=True)
quotes = page.css('.quote .text::text')
```

### Выбор элементов
```python
# CSS-селекторы
page.css('a::text')                      # Извлечь текст
page.css('a::attr(href)')                # Извлечь атрибуты
page.css('a', recursive=False)           # Только прямые элементы
page.css('a', auto_save=True)            # Автоматически сохранять позиции элементов

# XPath
page.xpath('//a/text()')

# Гибкий поиск
page.find_by_text('Python', first_match=True)  # Найти по тексту
page.find_by_regex(r'\d{4}')                   # Найти по паттерну regex
page.find('div', {'class': 'container'})       # Найти по атрибутам

# Навигация
element.parent                           # Получить родительский элемент
element.next_sibling                     # Получить следующего брата
element.children                         # Получить дочерние элементы

# Похожие элементы
similar = page.get_similar(element)      # Найти похожие элементы

# Адаптивный скрапинг
saved_elements = page.css('.product', auto_save=True)
# Позже, когда сайт изменится:
page.css('.product', adaptive=True)      # Найти элементы используя сохраненные позиции
```

### Использование сессий
```python
from scrapling.fetchers import FetcherSession, AsyncFetcherSession

# Синхронная сессия
with FetcherSession() as session:
    # Cookie автоматически сохраняются
    page1 = session.get('https://quotes.toscrape.com/login')
    page2 = session.post('https://quotes.toscrape.com/login', data={'username': 'admin', 'password': 'admin'})
    
    # При необходимости переключите отпечаток браузера
    page2 = session.get('https://quotes.toscrape.com/', impersonate='firefox135')

# Использование асинхронной сессии
async with AsyncStealthySession(max_pages=2) as session:
    tasks = []
    urls = ['https://example.com/page1', 'https://example.com/page2']
    
    for url in urls:
        task = session.fetch(url)
        tasks.append(task)
    
    print(session.get_pool_stats())  # Опционально - Статус пула вкладок браузера (занят/свободен/ошибка)
    results = await asyncio.gather(*tasks)
    print(session.get_pool_stats())
```

## CLI и интерактивная оболочка

Scrapling v0.3 включает мощный интерфейс командной строки:

[![asciicast](https://asciinema.org/a/736339.svg)](https://asciinema.org/a/736339)

```bash
# Запустить интерактивную оболочку веб-скрапинга
scrapling shell

# Извлечь страницы в файл напрямую без программирования (Извлекает содержимое внутри тега `body` по умолчанию)
# Если выходной файл заканчивается на `.txt`, то будет извлечено текстовое содержимое цели.
# Если заканчивается на `.md`, это будет markdown-представление HTML-содержимого, а `.html` будет непосредственно HTML-содержимым.
scrapling extract get 'https://example.com' content.md
scrapling extract get 'https://example.com' content.txt --css-selector '#fromSkipToProducts' --impersonate 'chrome'  # Все элементы, соответствующие CSS-селектору '#fromSkipToProducts'
scrapling extract fetch 'https://example.com' content.md --css-selector '#fromSkipToProducts' --no-headless
scrapling extract stealthy-fetch 'https://nopecha.com/demo/cloudflare' captchas.html --css-selector '#padded_content a' --solve-cloudflare
```

> [!NOTE]
> Есть много дополнительных функций, но мы хотим сохранить эту страницу краткой, например, MCP-сервер и интерактивная оболочка веб-скрапинга. Ознакомьтесь с полной документацией [здесь](https://scrapling.readthedocs.io/en/latest/)

## Тесты производительности

Scrapling не только мощный - он также невероятно быстрый, и обновления с версии 0.3 обеспечили исключительные улучшения производительности во всех операциях.

### Тест скорости извлечения текста (5000 вложенных элементов)

| # |    Библиотека     | Время (мс) | vs Scrapling | 
|---|:-----------------:|:----------:|:------------:|
| 1 |     Scrapling     |    1.99    |     1.0x     |
| 2 |   Parsel/Scrapy   |    2.01    |    1.01x     |
| 3 |     Raw Lxml      |    2.5     |    1.256x    |
| 4 |      PyQuery      |   22.93    |    ~11.5x    |
| 5 |    Selectolax     |   80.57    |    ~40.5x    |
| 6 |   BS4 with Lxml   |  1541.37   |   ~774.6x    |
| 7 |  MechanicalSoup   |  1547.35   |   ~777.6x    |
| 8 | BS4 with html5lib |  3410.58   |   ~1713.9x   |


### Производительность подобия элементов и текстового поиска

Возможности адаптивного поиска элементов Scrapling значительно превосходят альтернативы:

| Библиотека  | Время (мс) | vs Scrapling |
|-------------|:----------:|:------------:|
| Scrapling   |    2.46    |     1.0x     |
| AutoScraper |    13.3    |    5.407x    |


> Все тесты производительности представляют собой средние значения более 100 запусков. См. [benchmarks.py](https://github.com/D4Vinci/Scrapling/blob/main/benchmarks.py) для методологии.

## Установка

Scrapling требует Python 3.10 или выше:

```bash
pip install scrapling
```

Начиная с v0.3.2, эта установка включает только движок парсера и его зависимости, без каких-либо фетчеров или зависимостей командной строки.

### Опциональные зависимости

1. Если вы собираетесь использовать какие-либо из дополнительных функций ниже, фетчеры или их классы, то вам нужно установить зависимости фетчеров, а затем установить их зависимости браузера с помощью
    ```bash
    pip install "scrapling[fetchers]"
    
    scrapling install
    ```

    Это загрузит все браузеры с их системными зависимостями и зависимостями манипуляции отпечатками.

2. Дополнительные функции:
   - Установить функцию MCP-сервера:
       ```bash
       pip install "scrapling[ai]"
       ```
   - Установить функции оболочки (оболочка веб-скрапинга и команда `extract`):
       ```bash
       pip install "scrapling[shell]"
       ```
   - Установить все:
       ```bash
       pip install "scrapling[all]"
       ```
   Помните, что вам нужно установить зависимости браузера с помощью `scrapling install` после любого из этих дополнений (если вы еще этого не сделали)

### Docker
Вы также можете установить Docker-образ со всеми дополнениями и браузерами с помощью следующей команды из DockerHub:
```bash
docker pull pyd4vinci/scrapling
```
Или скачайте его из реестра GitHub:
```bash
docker pull ghcr.io/d4vinci/scrapling:latest
```
Этот образ автоматически создается и отправляется через GitHub actions в основной ветке репозитория.

## Вклад

Мы приветствуем вклад! Пожалуйста, прочитайте наши [руководства по внесению вклада](https://github.com/D4Vinci/Scrapling/blob/main/CONTRIBUTING.md) перед началом работы.

## Отказ от ответственности

> [!CAUTION]
> Эта библиотека предоставляется только в образовательных и исследовательских целях. Используя эту библиотеку, вы соглашаетесь соблюдать местные и международные законы о скрапинге данных и конфиденциальности. Авторы и участники не несут ответственности за любое неправомерное использование этого программного обеспечения. Всегда уважайте условия обслуживания веб-сайтов и файлы robots.txt.

## Лицензия

Эта работа лицензирована по лицензии BSD-3-Clause.

## Благодарности

Этот проект включает код, адаптированный из:
- Parsel (лицензия BSD) — Используется для подмодуля [translator](https://github.com/D4Vinci/Scrapling/blob/main/scrapling/core/translator.py)

## Благодарности и ссылки

- Блестящая работа [Daijro](https://github.com/daijro) над [BrowserForge](https://github.com/daijro/browserforge) и [Camoufox](https://github.com/daijro/camoufox)
- Блестящая работа [Vinyzu](https://github.com/Vinyzu) над [Botright](https://github.com/Vinyzu/Botright) и [PatchRight](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright)
- [brotector](https://github.com/kaliiiiiiiiii/brotector) за техники обхода обнаружения браузера
- [fakebrowser](https://github.com/kkoooqq/fakebrowser) и [BotBrowser](https://github.com/botswin/BotBrowser) за исследование отпечатков

---
<div align="center"><small>Разработано и создано с ❤️ Карим Шоаир.</small></div><br>

----------------------------------------


## File: ai/mcp-server.md
<!-- Source: docs/ai/mcp-server.md -->

# Scrapling MCP Server Guide

<iframe width="560" height="315" src="https://www.youtube.com/embed/qyFk3ZNwOxE?si=3FHzgcYCb66iJ6e3" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

The **Scrapling MCP Server** is a new feature that brings Scrapling's powerful Web Scraping capabilities directly to your favorite AI chatbot or AI agent. This integration allows you to scrape websites, extract data, and bypass anti-bot protections conversationally through Claude's AI interface or any other chatbot that supports MCP.

## Features

The Scrapling MCP Server provides six powerful tools for web scraping:

### 🚀 Basic HTTP Scraping
- **`get`**: Fast HTTP requests with browser fingerprint impersonation, generating real browser headers matching the TLS version, HTTP/3, and more!
- **`bulk_get`**: An async version of the above tool that allows scraping of multiple URLs at the same time!

### 🌐 Dynamic Content Scraping  
- **`fetch`**: Rapidly fetch dynamic content with Chromium/Chrome browser with complete control over the request/browser, stealth mode, and more!
- **`bulk_fetch`**: An async version of the above tool that allows scraping of multiple URLs in different browser tabs at the same time!

### 🔒 Stealth Scraping
- **`stealthy_fetch`**: Uses our modified version of Camoufox browser to bypass Cloudflare Turnstile/Interstitial and other anti-bot systems with complete control over the request/browser! 
- **`bulk_stealthy_fetch`**: An async version of the above tool that allows stealth scraping of multiple URLs in different browser tabs at the same time!

### Key Capabilities
- **Smart Content Extraction**: Convert web pages/elements to Markdown, HTML, or extract a clean version of the text content
- **CSS Selector Support**: Use the Scrapling engine to target specific elements with precision before handing the content to the AI
- **Anti-Bot Bypass**: Handle Cloudflare Turnstile, Interstitial, and other protections
- **Proxy Support**: Use proxies for anonymity and geo-targeting
- **Browser Impersonation**: Mimic real browsers with TLS fingerprinting, real browser headers matching that version, and more
- **Parallel Processing**: Scrape multiple URLs concurrently for efficiency

#### But why use Scrapling MCP Server instead of other available tools?

Aside from its stealth capabilities and ability to bypass Cloudflare Turnstile/Interstitial, Scrapling's server is the only one that allows you to pass a CSS selector in the prompt to extract specific elements before handing the content to the AI.

The way other servers work is that they extract the content, then pass it all to the AI to extract the fields you want. This causes the AI to consume a lot more tokens that are not needed (from irrelevant content). Scrapling solves this problem by allowing you to pass a CSS selector to narrow down the content you want before passing it to the AI, which makes the whole process much faster and more efficient.

If you don't know how to write/use CSS selectors, don't worry. You can tell the AI in the prompt to write selectors to match possible fields for you and watch it try different combinations until it finds the right one, as we will show in the examples section.

## Installation

Install Scrapling with MCP Support, then double-check that the browser dependencies are installed.

```bash
# Install Scrapling with MCP server dependencies
pip install "scrapling[ai]"

# Install browser dependencies
scrapling install
```

Or use the Docker image directly:
```bash
docker pull pyd4vinci/scrapling
```

## Setting up the MCP Server

Here we will explain how to add Scrapling MCP Server to [Claude Desktop](https://claude.ai/download) and [Claude Code](https://www.anthropic.com/claude-code), but the same logic applies to any other chatbot that supports MCP:

### Claude Desktop

1. Open Claude Desktop
2. Click the hamburger menu (☰) at the top left → Settings → Developer → Edit Config
3. Add the Scrapling MCP server configuration:
```json
"ScraplingServer": {
  "command": "scrapling",
  "args": [
    "mcp"
  ]
}
```
If that's the first MCP server you're adding, set the content of the file to this: 
```json
{
  "mcpServers": {
    "ScraplingServer": {
      "command": "scrapling",
      "args": [
        "mcp"
      ]
    }
  }
}
```
As per the [official article](https://modelcontextprotocol.io/quickstart/user), this action creates a new configuration file if one doesn’t exist or opens your existing configuration. The file is located at

1. **MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
2. **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

To ensure it's working, it's best to use the full path to the `scrapling` executable. Open the terminal and execute the following command:

1. **MacOS**: `which scrapling`
2. **Windows**: `where scrapling`

For me, on my Mac, it returned `/Users/<MyUsername>/.venv/bin/scrapling`, so the config I used in the end is:
```json
{
  "mcpServers": {
    "ScraplingServer": {
      "command": "/Users/<MyUsername>/.venv/bin/scrapling",
      "args": [
        "mcp"
      ]
    }
  }
}
```
#### Docker
If you are using the Docker image, then it would be something like
```json
{
  "mcpServers": {
    "ScraplingServer": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm", "scrapling", "mcp"
      ]
    }
  }
}
```

The same logic applies to [Cursor](https://docs.cursor.com/en/context/mcp), [WindSurf](https://windsurf.com/university/tutorials/configuring-first-mcp-server), and others.

### Claude Code
Here it's much simpler to do. If you have [Claude Code](https://www.anthropic.com/claude-code) installed, open the terminal and execute the following command:

```bash
claude mcp add ScraplingServer "/Users/<MyUsername>/.venv/bin/scrapling" mcp
```
Same as above, to get Scrapling's executable path, open the terminal and execute the following command:

1. **MacOS**: `which scrapling`
2. **Windows**: `where scrapling`

Here's the main article from Anthropic on [how to add MCP servers to Claude code](https://docs.anthropic.com/en/docs/claude-code/mcp#option-1%3A-add-a-local-stdio-server) for further details.


Then, after you've added the server, you need to completely quit and restart the app you used above. In Claude Desktop, you should see an MCP server indicator (🔧) in the bottom-right corner of the chat input or see `ScraplingServer` in the `Search and tools` dropdown in the chat input box.

### Streamable HTTP
As per version 0.3.6, we have added the ability to make the MCP server use the 'Streamable HTTP' transport mode instead of the traditional 'stdio' transport.

So instead of using the following command (the 'stdio' one):
```bash
scrapling mcp
```
Use the following to enable 'Streamable HTTP' transport mode:
```bash
scrapling mcp --http
```
Hence, the default value for the host the server is listening on is '0.0.0.0' and the port is 8000, which both can be configured as below:
```bash
scrapling mcp --http --host '127.0.0.1' --port 8000
```

## Examples

Now we will show you some examples of prompts we used while testing the MCP server, but you are probably more creative than we are and better at prompt engineering than we are :)

We will gradually go from simple prompts to more complex ones. We will use Claude Desktop for the examples, but the same logic applies to the rest, of course.

1. **Basic Web Scraping**

    Extract the main content from a webpage as Markdown:
    
    ```
    Scrape the main content from https://example.com and convert it to markdown format.
    ```
    
    Claude will use the `get` tool to fetch the page and return clean, readable content. If it fails, it will continue retrying every second for three attempts, unless you instruct it to do otherwise. If it fails to retrieve content for any reason, such as protection or if it's a dynamic website, it will automatically try the other tools. If Claude didn't do that automatically for some reason, you can add that to the prompt.
    
    A more optimized version of the same prompt would be:
    ```
    Use regular requests to scrape the main content from https://example.com and convert it to markdown format.
    ```
    This tells Claude about the right tool to use here, so it doesn't have to guess. Sometimes it will start using normal requests on its own, and at other times, it will assume browsers are better suited for this website without any apparent reason. As a general rule of thumb, you should always tell Claude what tool to use if you want to save time, money, and get consistent results.

2. **Targeted Data Extraction**

    Extract specific elements using CSS selectors:
    
    ```
    Get all product titles from https://shop.example.com using the CSS selector '.product-title'. If the request fails, retry up to 5 times every 10 seconds.
    ```
    
    The server will extract only the elements matching your selector and return them as a structured list. Notice I told it to set the tool to only try three times in case the website has connection issues, but the default setting should be fine for most cases.

3. **E-commerce Data Collection**

    Another example of a bit more complex prompt:
    ```
    Extract product information from these e-commerce URLs using bulk browser fetches:
    - https://shop1.com/product-a
    - https://shop2.com/product-b  
    - https://shop3.com/product-c
    
    Get the product names, prices, and descriptions from each page.
    ```
    
    Claude will use `bulk_fetch` to scrape all URLs concurrently, then analyze the extracted data.

4. **More advanced workflow**

    Let's say I want to get all the action games available on PlayStation's store first page right now. I can use the following prompt to do that:
    ```
    Extract the URLs of all games in this page, then do a bulk request to them and return a list of all action games: https://store.playstation.com/en-us/pages/browse
    ```
    Note that I instructed it to use a bulk request for all the URLs collected. If I hadn't mentioned it, sometimes it works as intended, and other times it makes a separate request to each URL, which takes significantly longer. This prompt takes approximately one minute to complete.
    
    However, because I wasn't specific enough, it actually used the `stealthy_fetch` here and the `bulk_stealthy_fetch` in the second step, which unnecessarily consumed a large number of tokens. A better prompt would be:
    ```
    Use normal requests to extract the URLs of all games in this page, then do a bulk request to them and return a list of all action games: https://store.playstation.com/en-us/pages/browse
    ```
    And if you know how to write CSS selectors, you can instruct Claude to apply the selectors to the elements you want, and it will nearly complete the task immediately.
    ```
    Use normal requests to extract the URLs of all games on the page below, then perform a bulk request to them and return a list of all action games.
    The selector for games in the first page is `[href*="/concept/"]` and the selector for the genre in the second request is `[data-qa="gameInfo#releaseInformation#genre-value"]`
    
    URL: https://store.playstation.com/en-us/pages/browse
    ```

5. **Get data from a website with Cloudflare protection**

    If you think the website you are targeting has Cloudflare protection, you should tell Claude instead of letting it discover that on its own.
    ```
    What's the price of this product? Be cautious, as it utilizes Cloudflare's Turnstile protection. Make the browser visible while you work.

    https://ao.com/product/oo101uk-ninja-woodfire-outdoor-pizza-oven-brown-99357-685.aspx
    ```

6. **Long workflow**

    You can, for example, use a prompt like this:
    ```
    Extract all the product URLs in the following category, then return the prices and the details of the first three products.
    
    https://www.arnotts.ie/furniture/bedroom/bed-frames/
    ```
    But a better prompt would be:
    ```
    Go to the following category URL and extract all product URLs using the CSS selector "a". Then, fetch the first 3 product pages in parallel and extract each product’s price and details.
    
    Keep the output in markdown format to reduce irrelevant content.
    
    Category URL:
    https://www.arnotts.ie/furniture/bedroom/bed-frames/
    ```

And so on, you get the idea. Your creativity is the key here.

## Best Practices

Here is some technical advice for you.

### 1. Choose the Right Tool
- **`get`**: Fast, simple websites
- **`fetch`**: Sites with JavaScript/dynamic content  
- **`stealthy_fetch`**: Protected sites, Cloudflare, anti-bot systems

### 2. Optimize Performance
- Use bulk tools for multiple URLs
- Disable unnecessary resources
- Set appropriate timeouts
- Use CSS selectors for targeted extraction

### 3. Handle Dynamic Content
- Use `network_idle` for SPAs
- Set `wait_selector` for specific elements
- Increase timeout for slow-loading sites

### 4. Data Quality
- Use `main_content_only=true` to avoid navigation/ads
- Choose an appropriate `extraction_type` for your use case

## Legal and Ethical Considerations

⚠️ **Important Guidelines:**

- **Check robots.txt**: Visit `https://website.com/robots.txt` to see scraping rules
- **Respect rate limits**: Don't overwhelm servers with requests
- **Terms of Service**: Read and comply with website terms
- **Copyright**: Respect intellectual property rights
- **Privacy**: Be mindful of personal data protection laws
- **Commercial use**: Ensure you have permission for business purposes

---

*Built with ❤️ by the Scrapling team. Happy scraping!*

----------------------------------------


## File: api-reference/custom-types.md
<!-- Source: docs/api-reference/custom-types.md -->

---
search:
  exclude: true
---

# Custom Types API Reference

Here's the reference information for all custom types of classes Scrapling implemented, with all their parameters, attributes, and methods.

You can import all of them directly like below:

```python
from scrapling.core.custom_types import TextHandler, TextHandlers, AttributesHandler
```

## ::: scrapling.core.custom_types.TextHandler
    handler: python
    :docstring:

## ::: scrapling.core.custom_types.TextHandlers
    handler: python
    :docstring:

## ::: scrapling.core.custom_types.AttributesHandler
    handler: python
    :docstring:


----------------------------------------


## File: api-reference/fetchers.md
<!-- Source: docs/api-reference/fetchers.md -->

---
search:
  exclude: true
---

# Fetchers Classes

Here's the reference information for all fetcher-type classes' parameters, attributes, and methods.

You can import all of them directly like below:

```python
from scrapling.fetchers import (
    Fetcher, AsyncFetcher, StealthyFetcher, DynamicFetcher,
    FetcherSession, AsyncStealthySession, StealthySession, DynamicSession, AsyncDynamicSession
)
```

## ::: scrapling.fetchers.Fetcher
    handler: python
    :docstring:

## ::: scrapling.fetchers.AsyncFetcher
    handler: python
    :docstring:

## ::: scrapling.fetchers.DynamicFetcher
    handler: python
    :docstring:

## ::: scrapling.fetchers.StealthyFetcher
    handler: python
    :docstring:


## Session Classes

### HTTP Sessions

## ::: scrapling.fetchers.FetcherSession
    handler: python
    :docstring:

### Stealth Sessions

## ::: scrapling.fetchers.StealthySession
    handler: python
    :docstring:

## ::: scrapling.fetchers.AsyncStealthySession
    handler: python
    :docstring:

### Dynamic Sessions

## ::: scrapling.fetchers.DynamicSession
    handler: python
    :docstring:

## ::: scrapling.fetchers.AsyncDynamicSession
    handler: python
    :docstring:



----------------------------------------


## File: api-reference/mcp-server.md
<!-- Source: docs/api-reference/mcp-server.md -->

---
search:
  exclude: true
---

# MCP Server API Reference

The **Scrapling MCP Server** provides six powerful tools for web scraping through the Model Context Protocol (MCP). This server integrates Scrapling's capabilities directly into AI chatbots and agents, allowing conversational web scraping with advanced anti-bot bypass features.

You can start the MCP server by running:

```bash
scrapling mcp
```

Or import the server class directly:

```python
from scrapling.core.ai import ScraplingMCPServer

server = ScraplingMCPServer()
server.serve()
```

## Response Model

The standardized response structure that's returned by all MCP server tools:

## ::: scrapling.core.ai.ResponseModel
    handler: python
    :docstring:

## MCP Server Class

The main MCP server class that provides all web scraping tools:

## ::: scrapling.core.ai.ScraplingMCPServer
    handler: python
    :docstring:

----------------------------------------


## File: api-reference/selector.md
<!-- Source: docs/api-reference/selector.md -->

---
search:
  exclude: true
---

# Selector Class

The `Selector` class is the core parsing engine in Scrapling that provides HTML parsing and element selection capabilities.

Here's the reference information for the `Selector` class, with all its parameters, attributes, and methods.

You can import the `Selector` class directly from `scrapling`:

```python
from scrapling.parser import Selector
```

## ::: scrapling.parser.Selector
    handler: python
    :docstring:

## ::: scrapling.parser.Selectors
    handler: python
    :docstring:



----------------------------------------


## File: benchmarks.md
<!-- Source: docs/benchmarks.md -->

# Performance Benchmarks

Scrapling isn't just powerful—it's also blazing fast, and the updates since version 0.3 deliver exceptional performance improvements across all operations!

## Benchmark Results

### Text Extraction Speed Test (5000 nested elements)

| # |      Library      | Time (ms) | vs Scrapling | 
|---|:-----------------:|:---------:|:------------:|
| 1 |     Scrapling     |   1.99    |     1.0x     |
| 2 |   Parsel/Scrapy   |   2.01    |    1.01x     |
| 3 |     Raw Lxml      |    2.5    |    1.256x    |
| 4 |      PyQuery      |   22.93   |    ~11.5x    |
| 5 |    Selectolax     |   80.57   |    ~40.5x    |
| 6 |   BS4 with Lxml   |  1541.37  |   ~774.6x    |
| 7 |  MechanicalSoup   |  1547.35  |   ~777.6x    |
| 8 | BS4 with html5lib |  3410.58  |   ~1713.9x   |

### Element Similarity & Text Search Performance

Scrapling's adaptive element finding capabilities significantly outperform alternatives:

| Library     | Time (ms) | vs Scrapling |
|-------------|:---------:|:------------:|
| Scrapling   |   2.46    |     1.0x     |
| AutoScraper |   13.3    |    5.407x    |


----------------------------------------


## File: cli/extract-commands.md
<!-- Source: docs/cli/extract-commands.md -->

# Scrapling Extract Command Guide

**Web Scraping through the terminal without requiring any programming!**

The `scrapling extract` Command lets you download and extract content from websites directly from your terminal without writing any code. Ideal for beginners, researchers, and anyone requiring rapid web data extraction.

> 💡 **Prerequisites:**
> 
> 1. You’ve completed or read the [Fetchers basics](../fetching/choosing.md) page to understand what the [Response object](../fetching/choosing.md#response-object) is and which fetcher to use.
> 2. You’ve completed or read the [Querying elements](../parsing/selection.md) page to understand how to find/extract elements from the [Selector](../parsing/main_classes.md#selector)/[Response](../fetching/choosing.md#response-object) object.
> 3. You’ve completed or read the [Main classes](../parsing/main_classes.md) page to know what properties/methods the [Response](../fetching/choosing.md#response-object) class is inheriting from the [Selector](../parsing/main_classes.md#selector) class.
> 4. You’ve completed or read at least one page from the fetchers section to use here for requests: [HTTP requests](../fetching/static.md), [Dynamic websites](../fetching/dynamic.md), or [Dynamic websites with hard protections](../fetching/stealthy.md).


## What is the Extract Command group?

The extract command is a set of simple terminal tools that:

- **Downloads web pages** and saves their content to files.
- **Converts HTML to readable formats** like Markdown, keeps it as HTML, or just extracts the text content of the page.
- **Supports custom CSS selectors** to extract specific parts of the page.
- **Handles HTTP requests and fetching through browsers**
- **Highly customizable** with custom headers, cookies, proxies, and the rest of the options. Almost all the options available through the code are also accessible through the command line.

## Quick Start

- **Basic Website Download**

    Download a website's text content as clean, readable text:
    ```bash
    scrapling extract get "https://example.com" page_content.txt
    ```
    This does an HTTP GET request and saves the text content of the webpage to `page_content.txt`.

- **Save as Different Formats**

    Choose your output format by changing the file extension:
    ```bash
    # Convert the HTML content to Markdown, then save it to the file (great for documentation)
    scrapling extract get "https://blog.example.com" article.md
    
    # Save the HTML content as it is to the file
    scrapling extract get "https://example.com" page.html
    
    # Save a clean version of the text content of the webpage to the file
    scrapling extract get "https://example.com" content.txt
  
    # Or use the Docker image with something like this:
    docker run -v $(pwd)/output:/output scrapling extract get "https://blog.example.com" /output/article.md 
    ```

- **Extract Specific Content**

    All commands can use CSS selectors to extract specific parts of the page through `--css-selector` or `-s` as you will see in the examples below.

## Available Commands

You can display the available commands through `scrapling extract --help` to get the following list:
```bash
Usage: scrapling extract [OPTIONS] COMMAND [ARGS]...

  Fetch web pages using various fetchers and extract full/selected HTML content as HTML, Markdown, or extract text content.

Options:
  --help  Show this message and exit.

Commands:
  get             Perform a GET request and save the content to a file.
  post            Perform a POST request and save the content to a file.
  put             Perform a PUT request and save the content to a file.
  delete          Perform a DELETE request and save the content to a file.
  fetch           Use DynamicFetcher to fetch content with browser...
  stealthy-fetch  Use StealthyFetcher to fetch content with advanced...
```

We will go through each Command in detail below.

### HTTP Requests

1. **GET Request**

    The most common Command for downloading website content:
    
    ```bash
    scrapling extract get [URL] [OUTPUT_FILE] [OPTIONS]
    ```
    
    **Examples:**
    ```bash
    # Basic download
    scrapling extract get "https://news.site.com" news.md
    
    # Download with custom timeout
    scrapling extract get "https://example.com" content.txt --timeout 60
    
    # Extract only specific content using CSS selectors
    scrapling extract get "https://blog.example.com" articles.md --css-selector "article"
   
    # Send a request with cookies
    scrapling extract get "https://scrapling.requestcatcher.com" content.md --cookies "session=abc123; user=john"
   
    # Add user agent
    scrapling extract get "https://api.site.com" data.json -H "User-Agent: MyBot 1.0"
    
    # Add multiple headers
    scrapling extract get "https://site.com" page.html -H "Accept: text/html" -H "Accept-Language: en-US"
    ```
    Get the available options for the Command with `scrapling extract get --help` as follows:
    ```bash
    Usage: scrapling extract get [OPTIONS] URL OUTPUT_FILE
    
      Perform a GET request and save the content to a file.
    
      The output file path can be an HTML file, a Markdown file of the HTML content, or the text content itself. Use file extensions (`.html`/`.md`/`.txt`) respectively.
    
    Options:
      -H, --headers TEXT                             HTTP headers in format "Key: Value" (can be used multiple times)
      --cookies TEXT                                 Cookies string in format "name1=value1;name2=value2"
      --timeout INTEGER                              Request timeout in seconds (default: 30)
      --proxy TEXT                                   Proxy URL in format "http://username:password@host:port"
      -s, --css-selector TEXT                        CSS selector to extract specific content from the page. It returns all matches.
      -p, --params TEXT                              Query parameters in format "key=value" (can be used multiple times)
      --follow-redirects / --no-follow-redirects     Whether to follow redirects (default: True)
      --verify / --no-verify                         Whether to verify SSL certificates (default: True)
      --impersonate TEXT                             Browser to impersonate (e.g., chrome, firefox).
      --stealthy-headers / --no-stealthy-headers     Use stealthy browser headers (default: True)
      --help                                         Show this message and exit.
    
    ```
    Note that the options will work in the same way for all other request commands, so no need to repeat them.

2. **Post Request**
    
    ```bash
    scrapling extract post [URL] [OUTPUT_FILE] [OPTIONS]
    ```
    
    **Examples:**
    ```bash
    # Submit form data
    scrapling extract post "https://api.site.com/search" results.html --data "query=python&type=tutorial"
    
    # Send JSON data
    scrapling extract post "https://api.site.com" response.json --json '{"username": "test", "action": "search"}'
    ```
    Get the available options for the Command with `scrapling extract post --help` as follows:
    ```bash
    Usage: scrapling extract post [OPTIONS] URL OUTPUT_FILE
    
      Perform a POST request and save the content to a file.
    
      The output file path can be an HTML file, a Markdown file of the HTML content, or the text content itself. Use file extensions (`.html`/`.md`/`.txt`) respectively.
    
    Options:
      -d, --data TEXT                                Form data to include in the request body (as string, ex: "param1=value1&param2=value2")
      -j, --json TEXT                                JSON data to include in the request body (as string)
      -H, --headers TEXT                             HTTP headers in format "Key: Value" (can be used multiple times)
      --cookies TEXT                                 Cookies string in format "name1=value1;name2=value2"
      --timeout INTEGER                              Request timeout in seconds (default: 30)
      --proxy TEXT                                   Proxy URL in format "http://username:password@host:port"
      -s, --css-selector TEXT                        CSS selector to extract specific content from the page. It returns all matches.
      -p, --params TEXT                              Query parameters in format "key=value" (can be used multiple times)
      --follow-redirects / --no-follow-redirects     Whether to follow redirects (default: True)
      --verify / --no-verify                         Whether to verify SSL certificates (default: True)
      --impersonate TEXT                             Browser to impersonate (e.g., chrome, firefox).
      --stealthy-headers / --no-stealthy-headers     Use stealthy browser headers (default: True)
      --help                                         Show this message and exit.
    
    ```

3. **Put Request**
    
    ```bash
    scrapling extract put [URL] [OUTPUT_FILE] [OPTIONS]
    ```
    
    **Examples:**
    ```bash
    # Send data
    scrapling extract put "https://scrapling.requestcatcher.com/put" results.html --data "update=info" --impersonate "firefox"
    
    # Send JSON data
    scrapling extract put "https://scrapling.requestcatcher.com/put" response.json --json '{"username": "test", "action": "search"}'
    ```
    Get the available options for the Command with `scrapling extract put --help` as follows:
    ```bash
    Usage: scrapling extract put [OPTIONS] URL OUTPUT_FILE
    
      Perform a PUT request and save the content to a file.
    
      The output file path can be an HTML file, a Markdown file of the HTML content, or the text content itself. Use file extensions (`.html`/`.md`/`.txt`) respectively.
    
    Options:
      -d, --data TEXT                                Form data to include in the request body
      -j, --json TEXT                                JSON data to include in the request body (as string)
      -H, --headers TEXT                             HTTP headers in format "Key: Value" (can be used multiple times)
      --cookies TEXT                                 Cookies string in format "name1=value1;name2=value2"
      --timeout INTEGER                              Request timeout in seconds (default: 30)
      --proxy TEXT                                   Proxy URL in format "http://username:password@host:port"
      -s, --css-selector TEXT                        CSS selector to extract specific content from the page. It returns all matches.
      -p, --params TEXT                              Query parameters in format "key=value" (can be used multiple times)
      --follow-redirects / --no-follow-redirects     Whether to follow redirects (default: True)
      --verify / --no-verify                         Whether to verify SSL certificates (default: True)
      --impersonate TEXT                             Browser to impersonate (e.g., chrome, firefox).
      --stealthy-headers / --no-stealthy-headers     Use stealthy browser headers (default: True)
      --help                                         Show this message and exit.
    ```

4. **Delete Request**
    
    ```bash
    scrapling extract delete [URL] [OUTPUT_FILE] [OPTIONS]
    ```
    
    **Examples:**
    ```bash
    # Send data
    scrapling extract delete "https://scrapling.requestcatcher.com/delete" results.html
    
    # Send JSON data
    scrapling extract delete "https://scrapling.requestcatcher.com/" response.txt --impersonate "chrome"
    ```
    Get the available options for the Command with `scrapling extract delete --help` as follows:
    ```bash
    Usage: scrapling extract delete [OPTIONS] URL OUTPUT_FILE
    
      Perform a DELETE request and save the content to a file.
    
      The output file path can be an HTML file, a Markdown file of the HTML content, or the text content itself. Use file extensions (`.html`/`.md`/`.txt`) respectively.
    
    Options:
      -H, --headers TEXT                             HTTP headers in format "Key: Value" (can be used multiple times)
      --cookies TEXT                                 Cookies string in format "name1=value1;name2=value2"
      --timeout INTEGER                              Request timeout in seconds (default: 30)
      --proxy TEXT                                   Proxy URL in format "http://username:password@host:port"
      -s, --css-selector TEXT                        CSS selector to extract specific content from the page. It returns all matches.
      -p, --params TEXT                              Query parameters in format "key=value" (can be used multiple times)
      --follow-redirects / --no-follow-redirects     Whether to follow redirects (default: True)
      --verify / --no-verify                         Whether to verify SSL certificates (default: True)
      --impersonate TEXT                             Browser to impersonate (e.g., chrome, firefox).
      --stealthy-headers / --no-stealthy-headers     Use stealthy browser headers (default: True)
      --help                                         Show this message and exit.
    ```

### Browsers fetching

1. **fetch - Handle Dynamic Content**

    For websites that load content with dynamic content or have slight protection
    
    ```bash
    scrapling extract fetch [URL] [OUTPUT_FILE] [OPTIONS]
    ```
    
    **Examples:**
    ```bash
    # Wait for JavaScript to load content and finish network activity
    scrapling extract fetch "https://scrapling.requestcatcher.com/" content.md --network-idle
    
    # Wait for specific content to appear
    scrapling extract fetch "https://scrapling.requestcatcher.com/" data.txt --wait-selector ".content-loaded"
    
    # Run in visible browser mode (helpful for debugging)
    scrapling extract fetch "https://scrapling.requestcatcher.com/" page.html --no-headless --disable-resources
    ```
    Get the available options for the Command with `scrapling extract fetch --help` as follows:
    ```bash
    Usage: scrapling extract fetch [OPTIONS] URL OUTPUT_FILE
    
      Use DynamicFetcher to fetch content with browser automation.
    
      The output file path can be an HTML file, a Markdown file of the HTML content, or the text content itself. Use file extensions (`.html`/`.md`/`.txt`) respectively.
    
    Options:
      --headless / --no-headless                  Run browser in headless mode (default: True)
      --disable-resources / --enable-resources    Drop unnecessary resources for speed boost (default: False)
      --network-idle / --no-network-idle          Wait for network idle (default: False)
      --timeout INTEGER                           Timeout in milliseconds (default: 30000)
      --wait INTEGER                              Additional wait time in milliseconds after page load (default: 0)
      -s, --css-selector TEXT                     CSS selector to extract specific content from the page. It returns all matches.
      --wait-selector TEXT                        CSS selector to wait for before proceeding
      --locale TEXT                               Browser locale (default: en-US)
      --stealth / --no-stealth                    Enable stealth mode (default: False)
      --hide-canvas / --show-canvas               Add noise to canvas operations (default: False)
      --disable-webgl / --enable-webgl            Disable WebGL support (default: False)
      --proxy TEXT                                Proxy URL in format "http://username:password@host:port"
      -H, --extra-headers TEXT                    Extra headers in format "Key: Value" (can be used multiple times)
      --help                                      Show this message and exit.
    ```

2. **stealthy-fetch - Bypass Protection**

    For websites with anti-bot protection or Cloudflare protection
    
    ```bash
    scrapling extract stealthy-fetch [URL] [OUTPUT_FILE] [OPTIONS]
    ```
    
    **Examples:**
    ```bash
    # Bypass basic protection
    scrapling extract stealthy-fetch "https://scrapling.requestcatcher.com" content.md
    
    # Solve Cloudflare challenges
    scrapling extract stealthy-fetch "https://nopecha.com/demo/cloudflare" data.txt --solve-cloudflare --css-selector "#padded_content a"
    
    # Use proxy for anonymity
    scrapling extract stealthy-fetch "https://site.com" content.md --proxy "http://proxy-server:8080"
    ```
    Get the available options for the Command with `scrapling extract stealthy-fetch --help` as follows:
    ```bash
    Usage: scrapling extract stealthy-fetch [OPTIONS] URL OUTPUT_FILE
    
      Use StealthyFetcher to fetch content with advanced stealth features.
    
      The output file path can be an HTML file, a Markdown file of the HTML content, or the text content itself. Use file extensions (`.html`/`.md`/`.txt`) respectively.
    
    Options:
      --headless / --no-headless                  Run browser in headless mode (default: True)
      --block-images / --allow-images             Block image loading (default: False)
      --disable-resources / --enable-resources    Drop unnecessary resources for speed boost (default: False)
      --block-webrtc / --allow-webrtc             Block WebRTC entirely (default: False)
      --humanize / --no-humanize                  Humanize cursor movement (default: False)
      --solve-cloudflare / --no-solve-cloudflare  Solve Cloudflare challenges (default: False)
      --allow-webgl / --block-webgl               Allow WebGL (default: True)
      --network-idle / --no-network-idle          Wait for network idle (default: False)
      --disable-ads / --allow-ads                 Install uBlock Origin addon (default: False)
      --timeout INTEGER                           Timeout in milliseconds (default: 30000)
      --wait INTEGER                              Additional wait time in milliseconds after page load (default: 0)
      -s, --css-selector TEXT                     CSS selector to extract specific content from the page. It returns all matches.
      --wait-selector TEXT                        CSS selector to wait for before proceeding
      --geoip / --no-geoip                        Use IP/Proxy geolocation for timezone/locale (default: False)
      --proxy TEXT                                Proxy URL in format "http://username:password@host:port"
      -H, --extra-headers TEXT                    Extra headers in format "Key: Value" (can be used multiple times)
      --help                                      Show this message and exit.
    ```

## When to use each Command

If you are not a Web Scraping expert and can't decide what to choose, you can use the following formula to help you decide:

- Use **`get`** with simple websites, blogs, or news articles
- Use **`fetch`** with modern web apps, or sites with dynamic content
- Use **`stealthy-fetch`** with protected sites, Cloudflare, or anti-bot systems

## Legal and Ethical Considerations

⚠️ **Important Guidelines:**

- **Check robots.txt**: Visit `https://website.com/robots.txt` to see scraping rules
- **Respect rate limits**: Don't overwhelm servers with requests
- **Terms of Service**: Read and comply with website terms
- **Copyright**: Respect intellectual property rights
- **Privacy**: Be mindful of personal data protection laws
- **Commercial use**: Ensure you have permission for business purposes

---

*Happy scraping! Remember to always respect website policies and comply with all applicable laws and regulations.*

----------------------------------------


## File: cli/interactive-shell.md
<!-- Source: docs/cli/interactive-shell.md -->

# Scrapling Interactive Shell Guide

<script src="https://asciinema.org/a/736339.js" id="asciicast-736339" async data-autoplay="1" data-loop="1" data-cols="225" data-rows="40" data-start-at="00:06" data-speed="1.5"></script>

**Powerful Web Scraping REPL for Developers and Data Scientists**

The Scrapling Interactive Shell is an enhanced IPython-based environment designed specifically for Web Scraping tasks. It provides instant access to all Scrapling features, clever shortcuts, automatic page management, and advanced tools like curl command conversion.

> 💡 **Prerequisites:**
> 
> 1. You’ve completed or read the [Fetchers basics](../fetching/choosing.md) page to understand what the [Response object](../fetching/choosing.md#response-object) is and which fetcher to use.
> 2. You’ve completed or read the [Querying elements](../parsing/selection.md) page to understand how to find/extract elements from the [Selector](../parsing/main_classes.md#selector)/[Response](../fetching/choosing.md#response-object) object.
> 3. You’ve completed or read the [Main classes](../parsing/main_classes.md) page to know what properties/methods the [Response](../fetching/choosing.md#response-object) class is inheriting from the [Selector](../parsing/main_classes.md#selector) class.
> 4. You’ve completed or read at least one page from the fetchers section to use here for requests: [HTTP requests](../fetching/static.md), [Dynamic websites](../fetching/dynamic.md), or [Dynamic websites with hard protections](../fetching/stealthy.md).


## Why use the Interactive Shell?

The interactive shell transforms web scraping from a slow script-and-run cycle into a fast, exploratory experience. It's perfect for:

- **Rapid prototyping**: Test scraping strategies instantly
- **Data exploration**: Interactively navigate and extract from websites  
- **Learning Scrapling**: Experiment with features in real-time
- **Debugging scrapers**: Step through requests and inspect results
- **Converting workflows**: Transform curl commands from browser DevTools to a Fetcher request in a one-liner

## Getting Started

### Launch the Shell

```bash
# Start the interactive shell
scrapling shell

# Execute code and exit (useful for scripting)
scrapling shell -c "get('https://quotes.toscrape.com'); print(len(page.css('.quote')))"

# Set logging level
scrapling shell --loglevel info
```

Once launched, you'll see the Scrapling banner and can immediately start scraping as the video above shows:

```python
# No imports needed - everything is ready!
>>> get('https://news.ycombinator.com')

>>> # Explore the page structure
>>> page.css('a')[:5]  # Look at first 5 links

>>> # Refine your selectors
>>> stories = page.css('.titleline>a')
>>> len(stories)
30

>>> # Extract specific data
>>> for story in stories[:3]:
...     title = story.text
...     url = story['href']
...     print(f"{title}: {url}")

>>> # Try different approaches
>>> titles = page.css('.titleline>a::text')  # Direct text extraction
>>> urls = page.css('.titleline>a::attr(href)')  # Direct attribute extraction
```

## Built-in Shortcuts

The shell provides convenient shortcuts that eliminate boilerplate code:

- **`get(url, **kwargs)`** - HTTP GET request (instead of `Fetcher.get`)
- **`post(url, **kwargs)`** - HTTP POST request (instead of `Fetcher.post`)
- **`put(url, **kwargs)`** - HTTP PUT request (instead of `Fetcher.put`)
- **`delete(url, **kwargs)`** - HTTP DELETE request (instead of `Fetcher.delete`)
- **`fetch(url, **kwargs)`** - Browser-based fetch (instead of `DynamicFetcher.fetch`) 
- **`stealthy_fetch(url, **kwargs)`** - Stealthy browser fetch (instead of `StealthyFetcher.fetch`)

The most commonly used classes are automatically available without any import, including `Fetcher`, `AsyncFetcher`, `DynamicFetcher`, `StealthyFetcher`, and `Selector`.

### Smart Page Management

The shell automatically tracks your requests and pages:

- **Current Page Access**

    The `page` and `response` commands are automatically updated with the last fetched page:
    
    ```python
    >>> get('https://quotes.toscrape.com')
    >>> # 'page' and 'response' both refer to the last fetched page
    >>> page.url
    'https://quotes.toscrape.com'
    >>> response.status  # Same as page.status
    200
    ```

- **Page History**

    The `pages` command keeps track of the last five pages (it's a `Selectors` object):
    
    ```python
    >>> get('https://site1.com')
    >>> get('https://site2.com') 
    >>> get('https://site3.com')
    
    >>> # Access last 5 pages
    >>> len(pages)  # `Selectors` object with `page` history
    3
    >>> pages[0].url  # First page in history
    'https://site1.com'
    >>> pages[-1].url  # Most recent page
    'https://site3.com'
    
    >>> # Work with historical pages
    >>> for i, old_page in enumerate(pages):
    ...     print(f"Page {i}: {old_page.url} - {old_page.status}")
    ```

## Additional helpful commands

### Page Visualization

View scraped pages in your browser:

```python
>>> get('https://quotes.toscrape.com')
>>> view(page)  # Opens the page HTML in your default browser
```

### Curl Command Integration

The shell provides a few functions to help you convert curl commands from the browser DevTools to `Fetcher` requests, which are `uncurl` and `curl2fetcher`. First, you need to copy a request as a curl command like the following:

<img src="../../assets/scrapling_shell_curl.png" title="Copying a request as a curl command from Chrome" alt="Copying a request as a curl command from Chrome" style="width: 70%;"/>

- **Convert Curl command to Request Object**

    ```python
    >>> curl_cmd = '''curl 'https://scrapling.requestcatcher.com/post' \
    ...   -X POST \
    ...   -H 'Content-Type: application/json' \
    ...   -d '{"name": "test", "value": 123}' '''
    
    >>> request = uncurl(curl_cmd)
    >>> request.method
    'post'
    >>> request.url
    'https://scrapling.requestcatcher.com/post'
    >>> request.headers
    {'Content-Type': 'application/json'}
    ```

- **Execute Curl Command Directly**

    ```python
    >>> # Convert and execute in one step
    >>> curl2fetcher(curl_cmd)
    >>> page.status
    200
    >>> page.json()['json']
    {'name': 'test', 'value': 123}
    ```

### IPython Features

The shell inherits all IPython capabilities:

```python
>>> # Magic commands
>>> %time page = get('https://example.com')  # Time execution
>>> %history  # Show command history
>>> %save filename.py 1-10  # Save commands 1-10 to file

>>> # Tab completion works everywhere
>>> page.c<TAB>  # Shows: css, css_first, cookies, etc.
>>> Fetcher.<TAB>  # Shows all Fetcher methods

>>> # Object inspection
>>> get? # Show get documentation
```

## Examples

Here are a few examples generated via AI:

#### E-commerce Data Collection

```python
>>> # Start with product listing page
>>> catalog = get('https://shop.example.com/products')

>>> # Find product links
>>> product_links = catalog.css('.product-link::attr(href)')
>>> print(f"Found {len(product_links)} products")

>>> # Sample a few products first
>>> for link in product_links[:3]:
...     product = get(f"https://shop.example.com{link}")
...     name = product.css('.product-name::text').get('')
...     price = product.css('.price::text').get('')
...     print(f"{name}: {price}")

>>> # Scale up with sessions for efficiency
>>> from scrapling.fetchers import FetcherSession
>>> with FetcherSession() as session:
...     products = []
...     for link in product_links:
...         product = session.get(f"https://shop.example.com{link}")
...         products.append({
...             'name': product.css('.product-name::text').get(''),
...             'price': product.css('.price::text').get(''),
...             'url': link
...         })
```

#### API Integration and Testing

```python
>>> # Test API endpoints interactively
>>> response = get('https://jsonplaceholder.typicode.com/posts/1')
>>> response.json()
{'userId': 1, 'id': 1, 'title': 'sunt aut...', 'body': 'quia et...'}

>>> # Test POST requests
>>> new_post = post('https://jsonplaceholder.typicode.com/posts', 
...                 json={'title': 'Test Post', 'body': 'Test content', 'userId': 1})
>>> new_post.json()['id']
101

>>> # Test with different data
>>> updated = put(f'https://jsonplaceholder.typicode.com/posts/{new_post.json()["id"]}',
...               json={'title': 'Updated Title'})
```

## Getting Help

If you need help other than what is available in-terminal, you can:

- [Scrapling Documentation](https://scrapling.readthedocs.io/)
- [Discord Community](https://discord.gg/EMgGbDceNQ)
- [GitHub Issues](https://github.com/D4Vinci/Scrapling/issues)  

And that's it! Happy scraping! The shell makes web scraping as easy as a conversation.

----------------------------------------


## File: cli/overview.md
<!-- Source: docs/cli/overview.md -->

# Command Line Interface

Since v0.3, Scrapling includes a powerful command-line interface that provides three main capabilities:

1. **Interactive Shell**: An interactive Web Scraping shell based on IPython that provides many shortcuts and useful tools
2. **Extract Commands**: Scrape websites from the terminal without any programming
3. **Utility Commands**: Installation and management tools

```bash
# Launch interactive shell
scrapling shell

# Convert the content of a page to markdown and save it to a file
scrapling extract get "https://example.com" content.md

# Get help for any command
scrapling --help
scrapling extract --help
```

## Requirements
This section requires you to install the extra `shell` dependency group, like the following:
```bash
pip install "scrapling[shell]"
```
and the installation of the fetchers' dependencies with the following command
```bash
scrapling install
```
This downloads all browsers with their system dependencies and fingerprint manipulation dependencies.

----------------------------------------


## File: development/adaptive_storage_system.md
<!-- Source: docs/development/adaptive_storage_system.md -->

Scrapling uses SQLite by default, but this tutorial covers writing your storage system to store element properties there for `adaptive` feature.

You might want to use FireBase, for example, and share the database between multiple spiders on different machines. It's a great idea to use an online database like that because the spiders will share with each other.

So first, to make your storage class work, it must do the big 3:

1. Inherit from the abstract class `scrapling.core.storage.StorageSystemMixin` and accept a string argument, which will be the `url` argument to maintain the library logic.
2. Use the decorator `functools.lru_cache` on top of the class to follow the Singleton design pattern as other classes.
3. Implement methods `save` and `retrieve`, as you see from the type hints:
    - The method `save` returns nothing and will get two arguments from the library
        * The first one is of type `lxml.html.HtmlElement`, which is the element itself. It must be converted to a dictionary using the function `element_to_dict` in submodule `scrapling.core.utils._StorageTools` to keep the same format and save it to your database as you wish.
        * The second one is a string, the identifier used for retrieval. The combination result of this identifier and the `url` argument from initialization must be unique for each row, or the `adaptive` data will be messed up.
    - The method `retrieve` takes a string, which is the identifier; using it with the `url` passed on initialization, the element's dictionary is retrieved from the database and returned if it exists; otherwise, it returns `None`.

> If the instructions weren't clear enough for you, you can check my implementation using SQLite3 in [storage_adaptors](https://github.com/D4Vinci/Scrapling/blob/main/scrapling/core/storage.py) file

If your class meets these criteria, the rest is straightforward. If you plan to use the library in a threaded application, ensure your class supports it. The default used class is thread-safe.

Some helper functions are added to the abstract class if you want to use them. It's easier to see it for yourself in the [code](https://github.com/D4Vinci/Scrapling/blob/main/scrapling/core/storage.py); it's heavily commented :)


## Real-World Example: Redis Storage

Here's a more practical example generated by AI using Redis:

```python
import redis
import orjson
from functools import lru_cache
from scrapling.core.storage import StorageSystemMixin
from scrapling.core.utils import _StorageTools

@lru_cache(None)
class RedisStorage(StorageSystemMixin):
    def __init__(self, host='localhost', port=6379, db=0, url=None):
        super().__init__(url)
        self.redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=False
        )
        
    def save(self, element, identifier: str) -> None:
        # Convert element to dictionary
        element_dict = _StorageTools.element_to_dict(element)
        
        # Create key
        key = f"scrapling:{self._get_base_url()}:{identifier}"
        
        # Store as JSON
        self.redis.set(
            key,
            orjson.dumps(element_dict)
        )
        
    def retrieve(self, identifier: str) -> dict:
        # Get data
        key = f"scrapling:{self._get_base_url()}:{identifier}"
        data = self.redis.get(key)
        
        # Parse JSON if exists
        if data:
            return orjson.loads(data)
        return None
```

----------------------------------------


## File: development/scrapling_custom_types.md
<!-- Source: docs/development/scrapling_custom_types.md -->

> You can take advantage of the custom-made types for Scrapling and use them outside the library if you want. It's better than copying their code, after all :)

### All current types can be imported alone like below
```python
>>> from scrapling.core.custom_types import TextHandler, AttributesHandler

>>> somestring = TextHandler('{}')
>>> somestring.json()
'{}'
>>> somedict_1 = AttributesHandler({'a': 1})
>>> somedict_2 = AttributesHandler(a=1)
```

Note that `TextHandler` is a subclass of Python's `str`, so all normal operations/methods that work with Python strings will work.
If you want to check for the type in your code, it's better to depend on Python's built-in function `issubclass`.

The class `AttributesHandler` is a subclass of `collections.abc.Mapping`, so it's immutable (read-only), and all operations are inherited from it. The data passed can be accessed later through the `_data` property, but be careful; it's of type `types.MappingProxyType`, so it's immutable (read-only) as well (faster than `collections.abc.Mapping` by fractions of seconds).

So, to make it simple for you if you are new to Python, the same operations and methods from the Python standard `dict` type will all work with class `AttributesHandler` except the ones that try to modify the actual data.

If you want to modify the data inside `AttributesHandler,` you have to convert it to a dictionary first, like using the `dict` function, and then modify it outside.

----------------------------------------


## File: donate.md
<!-- Source: docs/donate.md -->

I've been working on Scrapling and other public projects in my spare time and have invested considerable resources and effort to provide these projects for free to the community. By becoming a sponsor, you would directly fund my coffee reserves, helping me continuously update existing projects and create new ones.

You can sponsor me directly through [GitHub sponsors program](https://github.com/sponsors/D4Vinci) or [Buy Me A Coffe](https://buymeacoffee.com/d4vinci).

Thank you, stay curious, and hack the planet! ❤️

## Advertisement
If you are looking to **advertise** your business through Scrapling and take advantage of our target audience, check out the [available tiers](https://github.com/sponsors/D4Vinci):

### [The Silver tier](https://github.com/sponsors/D4Vinci/sponsorships?tier_id=435496) ($50/month)
Perks:

- Your logo will be featured at [the top of Scrapling's project page](https://github.com/D4Vinci/Scrapling?tab=readme-ov-file#sponsors).
- The same logo will be featured at [the top of Scrapling's PyPI page](https://pypi.org/project/scrapling/).
- The same logo will be featured at [the top of Docker's image page](https://hub.docker.com/r/pyd4vinci/scrapling).

### [The Gold tier](https://github.com/sponsors/D4Vinci/sponsorships?tier_id=435495) ($100/month)
Perks:

- Your logo will be featured at [the top of Scrapling's project page](https://github.com/D4Vinci/Scrapling?tab=readme-ov-file#sponsors).
- The same logo will be featured at [the top of Scrapling's PyPI page](https://pypi.org/project/scrapling/).
- The same logo will be featured at [the top of Docker's image page](https://hub.docker.com/r/pyd4vinci/scrapling).
- Your logo will be featured as a top sponsor on [Scrapling's website](https://scrapling.readthedocs.io/en/latest/) main page.
- A Shoutout with each [Release note](https://github.com/D4Vinci/Scrapling/releases).



----------------------------------------


## File: fetching/choosing.md
<!-- Source: docs/fetching/choosing.md -->

## Introduction
Fetchers are classes that can do requests or fetch pages for you easily in a single-line fashion with many features and then return a [Response](#response-object) object. Starting with v0.3, all fetchers have separate classes to keep the session running, so for example, a fetcher that uses a browser will keep the browser open till you finish all your requests through it instead of opening multiple browsers. So it depends on your use case.

This feature was introduced because, before v0.2, Scrapling was only a parsing engine. The target here is to gradually become the one-stop shop for all Web Scraping needs.

> Fetchers are not wrappers built on top of other libraries. However, they utilize these libraries as an engine to request/fetch pages easily for you, while fully leveraging that engine and adding features for you. Some fetchers don't even use the official library for requests; instead, they use their own custom version. For example, `StealthyFetcher` utilizes `Camoufox` browser directly, without relying on its Python library for anything except launch options. This last part might change soon as well.

## Fetchers Overview

Scrapling provides three different fetcher classes with their session classes; each fetcher is designed for a specific use case.

The following table compares them and can be quickly used for guidance.


| Feature            | Fetcher                                           | DynamicFetcher                                                                 | StealthyFetcher                                                                      |
|--------------------|---------------------------------------------------|--------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| Relative speed     | 🐇🐇🐇🐇🐇                                        | 🐇🐇🐇                                                                         | 🐇🐇                                                                                 |
| Stealth            | ⭐⭐                                                | ⭐⭐⭐                                                                            | ⭐⭐⭐⭐⭐                                                                                |
| Anti-Bot options   | ⭐⭐                                                | ⭐⭐⭐                                                                            | ⭐⭐⭐⭐⭐                                                                                |
| JavaScript loading | ❌                                                 | ✅                                                                              | ✅                                                                                    |
| Memory Usage       | ⭐                                                 | ⭐⭐⭐                                                                            | ⭐⭐⭐                                                                                  |
| Best used for      | Basic scraping when HTTP requests alone can do it | - Dynamically loaded websites <br/>- Small automation<br/>- Slight protections | - Dynamically loaded websites <br/>- Small automation <br/>- Complicated protections |
| Browser(s)         | ❌                                                 | Chromium and Google Chrome                                                     | Modified Firefox                                                                     |
| Browser API used   | ❌                                                 | PlayWright                                                                     | PlayWright                                                                           |
| Setup Complexity   | Simple                                            | Simple                                                                         | Simple                                                                               |

In the following pages, we will talk about each one in detail.

## Parser configuration in all fetchers
All fetchers share the same import method, as you will see in the upcoming pages
```python
>>> from scrapling.fetchers import Fetcher, AsyncFetcher, StealthyFetcher, DynamicFetcher
```
Then you use it right away without initializing like this, and it will use the default parser settings:
```python
>>> page = StealthyFetcher.fetch('https://example.com') 
```
If you want to configure the parser ([Selector class](../parsing/main_classes.md#selector)) that will be used on the response before returning it for you, then do this first:
```python
>>> from scrapling.fetchers import Fetcher
>>> Fetcher.configure(adaptive=True, encoding="utf-8", keep_comments=False, keep_cdata=False)  # and the rest
```
or
```python
>>> from scrapling.fetchers import Fetcher
>>> Fetcher.adaptive=True
>>> Fetcher.encoding="utf-8"
>>> Fetcher.keep_comments=False
>>> Fetcher.keep_cdata=False  # and the rest
```
Then, continue your code as usual.

The available configuration arguments are: `adaptive`, `huge_tree`, `keep_comments`, `keep_cdata`, `storage`, and `storage_args`, which are the same ones you give to the [Selector](../parsing/main_classes.md#selector) class. You can display the current configuration anytime by running `<fetcher_class>.display_config()`.

> Note: The `adaptive` argument is disabled by default; you must enable it to use that feature.

### Set parser config per request
As you probably understand, the logic above for setting the parser config will apply globally to all requests/fetches made through that class, and it's intended for simplicity.

If your use case requires a different configuration for each request/fetch, you can pass a dictionary to the request method (`fetch`/`get`/`post`/...) to an argument named `selector_config`.

## Response Object
The `Response` object is the same as the [Selector](../parsing/main_classes.md#selector) class, but it has additional details about the response, like response headers, status, cookies, etc., as shown below:
```python
>>> from scrapling.fetchers import Fetcher
>>> page = Fetcher.get('https://example.com')

>>> page.status          # HTTP status code
>>> page.reason          # Status message
>>> page.cookies         # Response cookies as a dictionary
>>> page.headers         # Response headers
>>> page.request_headers # Request headers
>>> page.history         # Response history of redirections, if any
>>> page.body            # Raw response body without any processing
>>> page.encoding        # Response encoding
```
All fetchers return the `Response` object.

----------------------------------------


## File: fetching/dynamic.md
<!-- Source: docs/fetching/dynamic.md -->

# Introduction

Here, we will discuss the `DynamicFetcher` class (previously known as `PlayWrightFetcher`). This class provides flexible browser automation with multiple configuration options and some stealth capabilities.

As we will explain later, to automate the page, you need some knowledge of [Playwright's Page API](https://playwright.dev/python/docs/api/class-page).

> 💡 **Prerequisites:**
> 
> 1. You’ve completed or read the [Fetchers basics](../fetching/choosing.md) page to understand what the [Response object](../fetching/choosing.md#response-object) is and which fetcher to use.
> 2. You’ve completed or read the [Querying elements](../parsing/selection.md) page to understand how to find/extract elements from the [Selector](../parsing/main_classes.md#selector)/[Response](../fetching/choosing.md#response-object) object.
> 3. You’ve completed or read the [Main classes](../parsing/main_classes.md) page to know what properties/methods the [Response](../fetching/choosing.md#response-object) class is inheriting from the [Selector](../parsing/main_classes.md#selector) class.

## Basic Usage
You have one primary way to import this Fetcher, which is the same for all fetchers.

```python
>>> from scrapling.fetchers import DynamicFetcher
```
Check out how to configure the parsing options [here](choosing.md#parser-configuration-in-all-fetchers)

Now, we will review most of the arguments one by one, using examples. If you want to jump to a table of all arguments for quick reference, [click here](#full-list-of-arguments)

> Note: The async version of the `fetch` method is the `async_fetch` method, of course.


This fetcher currently provides four main run options that can be combined as desired.

Which are:

### 1. Vanilla Playwright
```python
DynamicFetcher.fetch('https://example.com')
```
Using it in that manner will open a Chromium browser and load the page. There are no tricks or extra features unless you enable some; it's just a plain PlayWright API.

### 2. Stealth Mode
```python
DynamicFetcher.fetch('https://example.com', stealth=True)
```
It's the same as the vanilla Playwright option, but it provides a simple stealth mode suitable for websites with a small to medium protection layer(s).

Some of the things this fetcher's stealth mode does include:

  * Patching the CDP runtime fingerprint by using PatchRight.
  * Mimics some of the real browsers' properties by injecting several JS files and using custom options.
  * Custom flags are used on launch to hide Playwright even more and make it faster.
  * Generates real browser headers of the same type and user OS, then appends them to the request's headers.

### 3. Real Chrome
```python
DynamicFetcher.fetch('https://example.com', real_chrome=True)
```
If you have a Google Chrome browser installed, use this option. It's the same as the first option, but it will use the Google Chrome browser you installed on your device instead of Chromium.

This will make your requests look more authentic, so it's less detectable, and you can even use the `stealth=True` mode with it for better results, like below:
```python
DynamicFetcher.fetch('https://example.com', real_chrome=True, stealth=True)
```
If you don't have Google Chrome installed and want to use this option, you can use the command below in the terminal to install it for the library instead of installing it manually:
```commandline
playwright install chrome
```

### 4. CDP Connection
```python
DynamicFetcher.fetch('https://example.com', cdp_url='ws://localhost:9222')
```
Instead of launching a browser locally (Chromium/Google Chrome), you can connect to a remote browser through the [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/).

## Full list of arguments
Scrapling provides many options with this fetcher and its session classes. To make it as simple as possible, we will list the options here and give examples of how to use most of them.

|      Argument       | Description                                                                                                                                                                                                                                                                                                                                                                                                                 | Optional |
|:-------------------:|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------:|
|         url         | Target url                                                                                                                                                                                                                                                                                                                                                                                                                  |    ❌     |
|      headless       | Pass `True` to run the browser in headless/hidden (**default**) or `False` for headful/visible mode.                                                                                                                                                                                                                                                                                                                        |    ✔️    |
|  disable_resources  | Drop requests for unnecessary resources for a speed boost. It depends, but it made requests ~25% faster in my tests for some websites.<br/>Requests dropped are of type `font`, `image`, `media`, `beacon`, `object`, `imageset`, `texttrack`, `websocket`, `csp_report`, and `stylesheet`. _This can help save your proxy usage, but be cautious with this option, as it may cause some websites to never finish loading._ |    ✔️    |
|       cookies       | Set cookies for the next request.                                                                                                                                                                                                                                                                                                                                                                                           |    ✔️    |
|      useragent      | Pass a useragent string to be used. **Otherwise, the fetcher will generate and use a real Useragent of the same browser.**                                                                                                                                                                                                                                                                                                  |    ✔️    |
|    network_idle     | Wait for the page until there are no network connections for at least 500 ms.                                                                                                                                                                                                                                                                                                                                               |    ✔️    |
|      load_dom       | Enabled by default, wait for all JavaScript on page(s) to fully load and execute (wait for the `domcontentloaded` state).                                                                                                                                                                                                                                                                                                   |    ✔️    |
|       timeout       | The timeout (milliseconds) used in all operations and waits through the page. The default is 30,000 ms (30 seconds).                                                                                                                                                                                                                                                                                                        |    ✔️    |
|        wait         | The time (milliseconds) the fetcher will wait after everything finishes before closing the page and returning the `Response` object.                                                                                                                                                                                                                                                                                        |    ✔️    |
|     page_action     | Added for automation. Pass a function that takes the `page` object and does the necessary automation.                                                                                                                                                                                                                                                                                                                       |    ✔️    |
|    wait_selector    | Wait for a specific css selector to be in a specific state.                                                                                                                                                                                                                                                                                                                                                                 |    ✔️    |
|     init_script     | An absolute path to a JavaScript file to be executed on page creation for all pages in this session.                                                                                                                                                                                                                                                                                                                        |    ✔️    |
| wait_selector_state | Scrapling will wait for the given state to be fulfilled for the selector given with `wait_selector`. _Default state is `attached`._                                                                                                                                                                                                                                                                                         |    ✔️    |
|    google_search    | Enabled by default, Scrapling will set the referer header as if this request came from a Google search of this website's domain name.                                                                                                                                                                                                                                                                                       |    ✔️    |
|    extra_headers    | A dictionary of extra headers to add to the request. _The referer set by the `google_search` argument takes priority over the referer set here if used together._                                                                                                                                                                                                                                                           |    ✔️    |
|        proxy        | The proxy to be used with requests. It can be a string or a dictionary with only the keys 'server', 'username', and 'password'.                                                                                                                                                                                                                                                                                             |    ✔️    |
|     hide_canvas     | Add random noise to canvas operations to prevent fingerprinting.                                                                                                                                                                                                                                                                                                                                                            |    ✔️    |
|    disable_webgl    | Disables WebGL and WebGL 2.0 support entirely.                                                                                                                                                                                                                                                                                                                                                                              |    ✔️    |
|       stealth       | Enables stealth mode; you should always check the documentation to see what the stealth mode does currently.                                                                                                                                                                                                                                                                                                                |    ✔️    |
|     real_chrome     | If you have a Chrome browser installed on your device, enable this, and the Fetcher will launch and use an instance of your browser.                                                                                                                                                                                                                                                                                        |    ✔️    |
|       locale        | Set the locale for the browser if wanted. The default value is `en-US`.                                                                                                                                                                                                                                                                                                                                                     |    ✔️    |
|     timezone_id     | Set the timezone for the browser if wanted.                                                                                                                                                                                                                                                                                                                                                                                 |    ✔️    |
|       cdp_url       | Instead of launching a new browser instance, connect to this CDP URL to control real browsers through CDP.                                                                                                                                                                                                                                                                                                                  |    ✔️    |
|    user_data_dir    | Path to a User Data Directory, which stores browser session data like cookies and local storage. The default is to create a temporary directory. **Only Works with sessions**                                                                                                                                                                                                                                               |    ✔️    |
|     extra_flags     | A list of additional browser flags to pass to the browser on launch.                                                                                                                                                                                                                                                                                                                                                        |    ✔️    |
|   additional_args   | Additional arguments to be passed to Playwright's context as additional settings, and they take higher priority than Scrapling's settings.                                                                                                                                                                                                                                                                                  |    ✔️    |
|   selector_config   | A dictionary of custom parsing arguments to be used when creating the final `Selector`/`Response` class.                                                                                                                                                                                                                                                                                                                    |    ✔️    |

In session classes, all these arguments can be set globally for the session. Still, you can configure each request individually by passing some of the arguments here that can be configured on the browser tab level like: `google_search`, `timeout`, `wait`, `page_action`, `extra_headers`, `disable_resources`, `wait_selector`, `wait_selector_state`, `network_idle`, `load_dom`, and `selector_config`.


## Examples
It's easier to understand with examples, so let's take a look.

### Resource Control

```python
# Disable unnecessary resources
page = DynamicFetcher.fetch(
    'https://example.com',
    disable_resources=True  # Blocks fonts, images, media, etc...
)
```

### Network Control

```python
# Wait for network idle (Consider fetch to be finished when there are no network connections for at least 500 ms)
page = DynamicFetcher.fetch('https://example.com', network_idle=True)

# Custom timeout (in milliseconds)
page = DynamicFetcher.fetch('https://example.com', timeout=30000)  # 30 seconds

# Proxy support
page = DynamicFetcher.fetch(
    'https://example.com',
    proxy='http://username:password@host:port'  # Or it can be a dictionary with the keys 'server', 'username', and 'password' only
)
```

### Downloading Files

```python
page = DynamicFetcher.fetch('https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/poster.png')

with open(file='poster.png', mode='wb') as f:
    f.write(page.body)
```

The `body` attribute of the `Response` object is a `bytes` object containing the response body in case of Non-HTML responses.

### Browser Automation
This is where your knowledge about [Playwright's Page API](https://playwright.dev/python/docs/api/class-page) comes into play. The function you pass here takes the page object from Playwright's API, performs the desired action, and then the fetcher continues.

This function is executed immediately after waiting for `network_idle` (if enabled) and before waiting for the `wait_selector` argument, allowing it to be used for purposes beyond automation. You can alter the page as you want.

In the example below, I used the pages' [mouse events](https://playwright.dev/python/docs/api/class-mouse) to scroll the page with the mouse wheel, then move the mouse.
```python
from playwright.sync_api import Page

def scroll_page(page: Page):
    page.mouse.wheel(10, 0)
    page.mouse.move(100, 400)
    page.mouse.up()

page = DynamicFetcher.fetch(
    'https://example.com',
    page_action=scroll_page
)
```
Of course, if you use the async fetch version, the function must also be async.
```python
from playwright.async_api import Page

async def scroll_page(page: Page):
   await page.mouse.wheel(10, 0)
   await page.mouse.move(100, 400)
   await page.mouse.up()

page = await DynamicFetcher.async_fetch(
    'https://example.com',
    page_action=scroll_page
)
```

### Wait Conditions

```python
# Wait for the selector
page = DynamicFetcher.fetch(
    'https://example.com',
    wait_selector='h1',
    wait_selector_state='visible'
)
```
This is the last wait the fetcher will do before returning the response (if enabled). You pass a CSS selector to the `wait_selector` argument, and the fetcher will wait for the state you passed in the `wait_selector_state` argument to be fulfilled. If you didn't pass a state, the default would be `attached`, which means it will wait for the element to be present in the DOM.

After that, if `load_dom` is enabled (the default), the fetcher will check again to see if all JavaScript files are loaded and executed (in the `domcontentloaded` state) or continue waiting. If you have enabled `network_idle`, the fetcher will wait for `network_idle` to be fulfilled again, as explained above.

The states the fetcher can wait for can be any of the following ([source](https://playwright.dev/python/docs/api/class-page#page-wait-for-selector)):

- `attached`: Wait for an element to be present in the DOM.
- `detached`: Wait for an element to not be present in the DOM.
- `visible`: wait for an element to have a non-empty bounding box and no `visibility:hidden`. Note that an element without any content or with `display:none` has an empty bounding box and is not considered visible.
- `hidden`: wait for an element to be either detached from the DOM, or have an empty bounding box, or `visibility:hidden`. This is opposite to the `'visible'` option.

### Some Stealth Features

```python
# Full stealth mode
page = DynamicFetcher.fetch(
    'https://example.com',
    stealth=True,
    hide_canvas=True,
    disable_webgl=True,
    google_search=True
)

# Custom user agent
page = DynamicFetcher.fetch(
    'https://example.com',
    useragent='Mozilla/5.0...'
)

# Set browser locale
page = DynamicFetcher.fetch(
    'https://example.com',
    locale='en-US'
)
```
Hence, the `hide_canvas` argument doesn't disable the canvas; instead, it hides it by adding random noise to canvas operations, preventing fingerprinting. Also, if you didn't set a user agent (preferred), the fetcher will generate a real User Agent of the same browser and use it.

The `google_search` argument is enabled by default, making the request appear to come from a Google search page. So, a request for `https://example.com` will set the referer to `https://www.google.com/search?q=example`. Also, if used together, it takes priority over the referer set by the `extra_headers` argument.

### General example
```python
from scrapling.fetchers import DynamicFetcher

def scrape_dynamic_content():
    # Use Playwright for JavaScript content
    page = DynamicFetcher.fetch(
        'https://example.com/dynamic',
        network_idle=True,
        wait_selector='.content'
    )
    
    # Extract dynamic content
    content = page.css('.content')
    
    return {
        'title': content.css_first('h1::text'),
        'items': [
            item.text for item in content.css('.item')
        ]
    }
```

## Session Management

To keep the browser open until you make multiple requests with the same configuration, use `DynamicSession`/`AsyncDynamicSession` classes. Those classes can accept all the arguments that the `fetch` function can take, which enables you to specify a config for the entire session.

```python
from scrapling.fetchers import DynamicSession

# Create a session with default configuration
with DynamicSession(
    headless=True,
    stealth=True,
    disable_resources=True,
    real_chrome=True
) as session:
    # Make multiple requests with the same browser instance
    page1 = session.fetch('https://example1.com')
    page2 = session.fetch('https://example2.com')
    page3 = session.fetch('https://dynamic-site.com')
    
    # All requests reuse the same tab on the same browser instance
```

### Async Session Usage

```python
import asyncio
from scrapling.fetchers import AsyncDynamicSession

async def scrape_multiple_sites():
    async with AsyncDynamicSession(
        stealth=True,
        network_idle=True,
        timeout=30000,
        max_pages=3
    ) as session:
        # Make async requests with shared browser configuration
        pages = await asyncio.gather(
            session.fetch('https://spa-app1.com'),
            session.fetch('https://spa-app2.com'),
            session.fetch('https://dynamic-content.com')
        )
        return pages
```

You may have noticed the `max_pages` argument. This is a new argument that enables the fetcher to create a **rotating pool of Browser tabs**. Instead of using a single tab for all your requests, you set a limit on the maximum number of pages that can be displayed at once. With each request, the library will close all tabs that have finished their task and check if the number of the current tabs is lower than the maximum allowed number of pages/tabs, then:

1. If you are within the allowed range, the fetcher will create a new tab for you, and then all is as normal.
2. Otherwise, it will keep checking every subsecond if creating a new tab is allowed or not for 60 seconds, then raise `TimeoutError`. This can happen when the website you are fetching becomes unresponsive.

This logic allows for multiple websites to be fetched at the same time in the same browser, which saves a lot of resources, but most importantly, is so fast :)

In versions 0.3 and 0.3.1, the pool was reusing finished tabs to save more resources/time. That logic proved flawed, as it's nearly impossible to protect pages/tabs from contamination by the previous configuration used in the request before this one.

### Session Benefits

- **Browser reuse**: Much faster subsequent requests by reusing the same browser instance.
- **Cookie persistence**: Automatic cookie and session state handling as any browser does automatically.
- **Consistent fingerprint**: Same browser fingerprint across all requests.
- **Memory efficiency**: Better resource usage compared to launching new browsers with each fetch.

## When to Use

Use DynamicFetcher when:

- Need browser automation
- Want multiple browser options
- Using a real Chrome browser
- Need custom browser config
- Want flexible stealth options 

If you want more stealth and control without much config, check out the [StealthyFetcher](stealthy.md).

----------------------------------------


## File: fetching/static.md
<!-- Source: docs/fetching/static.md -->

# Introduction

The `Fetcher` class provides rapid and lightweight HTTP requests using the high-performance `curl_cffi` library with a lot of stealth capabilities.

> 💡 **Prerequisites:**
> 
> 1. You’ve completed or read the [Fetchers basics](../fetching/choosing.md) page to understand what the [Response object](../fetching/choosing.md#response-object) is and which fetcher to use.
> 2. You’ve completed or read the [Querying elements](../parsing/selection.md) page to understand how to find/extract elements from the [Selector](../parsing/main_classes.md#selector)/[Response](../fetching/choosing.md#response-object) object.
> 3. You’ve completed or read the [Main classes](../parsing/main_classes.md) page to know what properties/methods the [Response](../fetching/choosing.md#response-object) class is inheriting from the [Selector](../parsing/main_classes.md#selector) class.

## Basic Usage
You have one primary way to import this Fetcher, which is the same for all fetchers.

```python
>>> from scrapling.fetchers import Fetcher
```
Check out how to configure the parsing options [here](choosing.md#parser-configuration-in-all-fetchers)

### Shared arguments
All methods for making requests here share some arguments, so let's discuss them first.

- **url**: The targeted URL
- **stealthy_headers**: If enabled (default), it creates and adds real browser headers. It also sets the referer header as if this request came from a Google search of the URL's domain.
- **follow_redirects**: As the name implies, tell the fetcher to follow redirections. **Enabled by default**
- **timeout**: The number of seconds to wait for each request to be finished. **Defaults to 30 seconds**.
- **retries**: The number of retries that the fetcher will do for failed requests. **Defaults to three retries**.
- **retry_delay**: Number of seconds to wait between retry attempts. **Defaults to 1 second**.
- **impersonate**: Impersonate specific browsers' TLS fingerprints. Accepts browser strings like `"chrome110"`, `"firefox102"`, `"safari15_5"` to use specific versions or `"chrome"`, `"firefox"`, `"safari"`, `"edge"` to automatically use the latest version available. This makes your requests appear as if they're coming from real browsers at the TLS level. **Defaults to the latest available Chrome version.**
- **http3**: Use HTTP/3 protocol for requests. **Defaults to False**. It might be problematic if used with `impersonate`.
- **cookies**: Cookies to use in the request. Can be a dictionary of `name→value` or a list of dictionaries.
- **proxy**: As the name implies, the proxy for this request is used to route all traffic (HTTP and HTTPS). The format accepted here is `http://username:password@localhost:8030`.
- **proxy_auth**: HTTP basic auth for proxy, tuple of (username, password).
- **proxies**: Dict of proxies to use. Format: `{"http": proxy_url, "https": proxy_url}`.
- **headers**: Headers to include in the request. Can override any header generated by the `stealthy_headers` argument
- **max_redirects**: Maximum number of redirects. **Defaults to 30**, use -1 for unlimited.
- **verify**: Whether to verify HTTPS certificates. **Defaults to True**.
- **cert**: Tuple of (cert, key) filenames for the client certificate.
- **selector_config**: A dictionary of custom parsing arguments to be used when creating the final `Selector`/`Response` class.

> Note: <br/>
> 1. The currently available browsers to impersonate are (`"edge"`, `"chrome"`, `"chrome_android"`, `"safari"`, `"safari_beta"`, `"safari_ios"`, `"safari_ios_beta"`, `"firefox"`, `"tor"`)<br/>
> 2. The available browsers to impersonate and their corresponding versions are automatically displayed in the argument autocompletion and updated automatically with each `curl_cffi` update.

Other than this, for further customization, you can pass any arguments that `curl_cffi` supports for any method if that method doesn't already support it.

### HTTP Methods
There are additional arguments for each method, depending on the method, such as `params` for GET requests and `data`/`json` for POST/PUT/DELETE requests.

Examples are the best way to explain this, as follows.

> Hence: `OPTIONS` and `HEAD` methods are not supported.
#### GET
```python
>>> from scrapling.fetchers import Fetcher
>>> # Basic GET
>>> page = Fetcher.get('https://example.com')
>>> page = Fetcher.get('https://scrapling.requestcatcher.com/get', stealthy_headers=True, follow_redirects=True)
>>> page = Fetcher.get('https://scrapling.requestcatcher.com/get', proxy='http://username:password@localhost:8030')
>>> # With parameters
>>> page = Fetcher.get('https://example.com/search', params={'q': 'query'})
>>>
>>> # With headers
>>> page = Fetcher.get('https://example.com', headers={'User-Agent': 'Custom/1.0'})
>>> # Basic HTTP authentication
>>> page = Fetcher.get("https://example.com", auth=("my_user", "password123"))
>>> # Browser impersonation
>>> page = Fetcher.get('https://example.com', impersonate='chrome')
>>> # HTTP/3 support
>>> page = Fetcher.get('https://example.com', http3=True)
```
And for asynchronous requests, it's a small adjustment 
```python
>>> from scrapling.fetchers import AsyncFetcher
>>> # Basic GET
>>> page = await AsyncFetcher.get('https://example.com')
>>> page = await AsyncFetcher.get('https://scrapling.requestcatcher.com/get', stealthy_headers=True, follow_redirects=True)
>>> page = await AsyncFetcher.get('https://scrapling.requestcatcher.com/get', proxy='http://username:password@localhost:8030')
>>> # With parameters
>>> page = await AsyncFetcher.get('https://example.com/search', params={'q': 'query'})
>>>
>>> # With headers
>>> page = await AsyncFetcher.get('https://example.com', headers={'User-Agent': 'Custom/1.0'})
>>> # Basic HTTP authentication
>>> page = await AsyncFetcher.get("https://example.com", auth=("my_user", "password123"))
>>> # Browser impersonation
>>> page = await AsyncFetcher.get('https://example.com', impersonate='chrome110')
>>> # HTTP/3 support
>>> page = await AsyncFetcher.get('https://example.com', http3=True)
```
Needless to say, the `page` object in all cases is [Response](choosing.md#response-object) object, which is a [Selector](../parsing/main_classes.md#selector) as we said, so you can use it directly
```python
>>> page.css('.something.something')

>>> page = Fetcher.get('https://api.github.com/events')
>>> page.json()
[{'id': '<redacted>',
  'type': 'PushEvent',
  'actor': {'id': '<redacted>',
   'login': '<redacted>',
   'display_login': '<redacted>',
   'gravatar_id': '',
   'url': 'https://api.github.com/users/<redacted>',
   'avatar_url': 'https://avatars.githubusercontent.com/u/<redacted>'},
  'repo': {'id': '<redacted>',
...
```
#### POST
```python
>>> from scrapling.fetchers import Fetcher
>>> # Basic POST
>>> page = Fetcher.post('https://scrapling.requestcatcher.com/post', data={'key': 'value'}, params={'q': 'query'})
>>> page = Fetcher.post('https://scrapling.requestcatcher.com/post', data={'key': 'value'}, stealthy_headers=True, follow_redirects=True)
>>> page = Fetcher.post('https://scrapling.requestcatcher.com/post', data={'key': 'value'}, proxy='http://username:password@localhost:8030', impersonate="chrome")
>>> # Another example of form-encoded data
>>> page = Fetcher.post('https://example.com/submit', data={'username': 'user', 'password': 'pass'}, http3=True)
>>> # JSON data
>>> page = Fetcher.post('https://example.com/api', json={'key': 'value'})
```
And for asynchronous requests, it's a small adjustment
```python
>>> from scrapling.fetchers import AsyncFetcher
>>> # Basic POST
>>> page = await AsyncFetcher.post('https://scrapling.requestcatcher.com/post', data={'key': 'value'})
>>> page = await AsyncFetcher.post('https://scrapling.requestcatcher.com/post', data={'key': 'value'}, stealthy_headers=True, follow_redirects=True)
>>> page = await AsyncFetcher.post('https://scrapling.requestcatcher.com/post', data={'key': 'value'}, proxy='http://username:password@localhost:8030', impersonate="chrome")
>>> # Another example of form-encoded data
>>> page = await AsyncFetcher.post('https://example.com/submit', data={'username': 'user', 'password': 'pass'}, http3=True)
>>> # JSON data
>>> page = await AsyncFetcher.post('https://example.com/api', json={'key': 'value'})
```
#### PUT
```python
>>> from scrapling.fetchers import Fetcher
>>> # Basic PUT
>>> page = Fetcher.put('https://example.com/update', data={'status': 'updated'})
>>> page = Fetcher.put('https://example.com/update', data={'status': 'updated'}, stealthy_headers=True, follow_redirects=True, impersonate="chrome")
>>> page = Fetcher.put('https://example.com/update', data={'status': 'updated'}, proxy='http://username:password@localhost:8030')
>>> # Another example of form-encoded data
>>> page = Fetcher.put("https://scrapling.requestcatcher.com/put", data={'key': ['value1', 'value2']})
```
And for asynchronous requests, it's a small adjustment
```python
>>> from scrapling.fetchers import AsyncFetcher
>>> # Basic PUT
>>> page = await AsyncFetcher.put('https://example.com/update', data={'status': 'updated'})
>>> page = await AsyncFetcher.put('https://example.com/update', data={'status': 'updated'}, stealthy_headers=True, follow_redirects=True, impersonate="chrome")
>>> page = await AsyncFetcher.put('https://example.com/update', data={'status': 'updated'}, proxy='http://username:password@localhost:8030')
>>> # Another example of form-encoded data
>>> page = await AsyncFetcher.put("https://scrapling.requestcatcher.com/put", data={'key': ['value1', 'value2']})
```

#### DELETE
```python
>>> from scrapling.fetchers import Fetcher
>>> page = Fetcher.delete('https://example.com/resource/123')
>>> page = Fetcher.delete('https://example.com/resource/123', stealthy_headers=True, follow_redirects=True, impersonate="chrome")
>>> page = Fetcher.delete('https://example.com/resource/123', proxy='http://username:password@localhost:8030')
```
And for asynchronous requests, it's a small adjustment
```python
>>> from scrapling.fetchers import AsyncFetcher
>>> page = await AsyncFetcher.delete('https://example.com/resource/123')
>>> page = await AsyncFetcher.delete('https://example.com/resource/123', stealthy_headers=True, follow_redirects=True, impersonate="chrome")
>>> page = await AsyncFetcher.delete('https://example.com/resource/123', proxy='http://username:password@localhost:8030')
```

## Session Management

For making multiple requests with the same configuration, use the `FetcherSession` class. It can be used in both synchronous and asynchronous code without issue; the class detects and changes the session type automatically without requiring a different import.

The `FetcherSession` class can accept nearly all the arguments that the methods can take, which enables you to specify a config for the entire session and later choose a different config for one of the requests effortlessly, as you will see in the following examples.

```python
from scrapling.fetchers import FetcherSession

# Create a session with default configuration
with FetcherSession(
    impersonate='chrome',
    http3=True,
    stealthy_headers=True,
    timeout=30,
    retries=3
) as session:
    # Make multiple requests with the same settings
    page1 = session.get('https://scrapling.requestcatcher.com/get')
    page2 = session.post('https://scrapling.requestcatcher.com/post', data={'key': 'value'})
    page3 = session.get('https://api.github.com/events')
    
    # All requests share the same session and connection pool
```

And here's an async example

```python
async with FetcherSession(impersonate='firefox', http3=True) as session:
    # All standard HTTP methods available
    response = async session.get('https://example.com')
    response = async session.post('https://scrapling.requestcatcher.com/post', json={'data': 'value'})
    response = async session.put('https://scrapling.requestcatcher.com/put', data={'update': 'info'})
    response = async session.delete('https://scrapling.requestcatcher.com/delete')
```
or better
```python
import asyncio
from scrapling.fetchers import FetcherSession

# Async session usage
async with FetcherSession(impersonate="safari") as session:
    urls = ['https://example.com/page1', 'https://example.com/page2']

    tasks = [
        session.get(url) for url in urls
    ]

    pages = await asyncio.gather(*tasks)
```

The `Fetcher` class uses `FetcherSession` to create a temporary session with each request you make.

### Session Benefits

- **A lot faster**: 10 times faster than creating a single session for each request
- **Cookie persistence**: Automatic cookie handling across requests
- **Resource efficiency**: Better memory and CPU usage for multiple requests
- **Centralized configuration**: Single place to manage request settings

## Examples
Some well-rounded examples to aid newcomers to Web Scraping

### Basic HTTP Request

```python
from scrapling.fetchers import Fetcher

# Make a request
page = Fetcher.get('https://example.com')

# Check the status
if page.status == 200:
    # Extract title
    title = page.css_first('title::text')
    print(f"Page title: {title}")
    
    # Extract all links
    links = page.css('a::attr(href)')
    print(f"Found {len(links)} links")
```

### Product Scraping

```python
from scrapling.fetchers import Fetcher

def scrape_products():
    page = Fetcher.get('https://example.com/products')
    
    # Find all product elements
    products = page.css('.product')
    
    results = []
    for product in products:
        results.append({
            'title': product.css_first('.title::text'),
            'price': product.css_first('.price::text').re_first(r'\d+\.\d{2}'),
            'description': product.css_first('.description::text'),
            'in_stock': product.has_class('in-stock')
        })
    
    return results
```

### Downloading Files

```python
from scrapling.fetchers import Fetcher

page = Fetcher.get('https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/poster.png')
with open(file='poster.png', mode='wb') as f:
   f.write(page.body)
```

### Pagination Handling

```python
from scrapling.fetchers import Fetcher

def scrape_all_pages():
    base_url = 'https://example.com/products?page={}'
    page_num = 1
    all_products = []
    
    while True:
        # Get current page
        page = Fetcher.get(base_url.format(page_num))
        
        # Find products
        products = page.css('.product')
        if not products:
            break
            
        # Process products
        for product in products:
            all_products.append({
                'name': product.css_first('.name::text'),
                'price': product.css_first('.price::text')
            })
            
        # Next page
        page_num += 1
        
    return all_products
```

### Form Submission

```python
from scrapling.fetchers import Fetcher

# Submit login form
response = Fetcher.post(
    'https://example.com/login',
    data={
        'username': 'user@example.com',
        'password': 'password123'
    }
)

# Check login success
if response.status == 200:
    # Extract user info
    user_name = response.css_first('.user-name::text')
    print(f"Logged in as: {user_name}")
```

### Table Extraction

```python
from scrapling.fetchers import Fetcher

def extract_table():
    page = Fetcher.get('https://example.com/data')
    
    # Find table
    table = page.css_first('table')
    
    # Extract headers
    headers = [
        th.text for th in table.css('thead th')
    ]
    
    # Extract rows
    rows = []
    for row in table.css('tbody tr'):
        cells = [td.text for td in row.css('td')]
        rows.append(dict(zip(headers, cells)))
        
    return rows
```

### Navigation Menu

```python
from scrapling.fetchers import Fetcher

def extract_menu():
    page = Fetcher.get('https://example.com')
    
    # Find navigation
    nav = page.css_first('nav')
    
    menu = {}
    for item in nav.css('li'):
        link = item.css_first('a')
        if link:
            menu[link.text] = {
                'url': link['href'],
                'has_submenu': bool(item.css('.submenu'))
            }
            
    return menu
```

## When to Use

Use `Fetcher` when:

- Need rapid HTTP requests.
- Want minimal overhead.
- Don't need JavaScript execution (the website can be scraped through requests).
- Need some stealth features (ex, the targeted website is using protection but doesn't use JavaScript challenges).

Use `FetcherSession` when:

- Making multiple requests to the same or different sites.
- Need to maintain cookies/authentication between requests.
- Want connection pooling for better performance.
- Require consistent configuration across requests.
- Working with APIs that require a session state.

Use other fetchers when:

- Need browser automation.
- Need advanced anti-bot/stealth capabilities.
- Need JavaScript support or interacting with dynamic content

----------------------------------------


## File: fetching/stealthy.md
<!-- Source: docs/fetching/stealthy.md -->

# Introduction

Here, we will discuss the `StealthyFetcher` class. This class is similar to [DynamicFetcher](dynamic.md#introduction) in many ways, including browser automation and the use of [Playwright's API](https://playwright.dev/python/docs/intro). The main difference is that this class provides advanced anti-bot protection bypass capabilities and a custom version of a modified Firefox browser called [Camoufox](https://github.com/daijro/camoufox), from which most stealth comes.

As with [DynamicFetcher](dynamic.md#introduction), you will need some knowledge about [Playwright's Page API](https://playwright.dev/python/docs/api/class-page) to automate the page, as we will explain later.

> 💡 **Prerequisites:**
> 
> 1. You’ve completed or read the [Fetchers basics](../fetching/choosing.md) page to understand what the [Response object](../fetching/choosing.md#response-object) is and which fetcher to use.
> 2. You’ve completed or read the [Querying elements](../parsing/selection.md) page to understand how to find/extract elements from the [Selector](../parsing/main_classes.md#selector)/[Response](../fetching/choosing.md#response-object) object.
> 3. You’ve completed or read the [Main classes](../parsing/main_classes.md) page to know what properties/methods the [Response](../fetching/choosing.md#response-object) class is inheriting from the [Selector](../parsing/main_classes.md#selector) class.

## Basic Usage
You have one primary way to import this Fetcher, which is the same for all fetchers.

```python
>>> from scrapling.fetchers import StealthyFetcher
```
Check out how to configure the parsing options [here](choosing.md#parser-configuration-in-all-fetchers)

> Note: The async version of the `fetch` method is the `async_fetch` method, of course.

## Full list of arguments
Scrapling provides many options with this fetcher and its session classes. Before jumping to the [examples](#examples), here's the full list of arguments


|      Argument       | Description                                                                                                                                                                                                                                                                                                                                                                                                                 | Optional |
|:-------------------:|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------:|
|         url         | Target url                                                                                                                                                                                                                                                                                                                                                                                                                  |    ❌     |
|      headless       | Pass `True` to run the browser in headless/hidden (**default**) or `False` for headful/visible mode.                                                                                                                                                                                                                                                                                                                        |    ✔️    |
|    block_images     | Prevent the loading of images through Firefox preferences. _This can help save your proxy usage, but be cautious with this option, as it may cause some websites to never finish loading._                                                                                                                                                                                                                                  |    ✔️    |
|  disable_resources  | Drop requests for unnecessary resources for a speed boost. It depends, but it made requests ~25% faster in my tests for some websites.<br/>Requests dropped are of type `font`, `image`, `media`, `beacon`, `object`, `imageset`, `texttrack`, `websocket`, `csp_report`, and `stylesheet`. _This can help save your proxy usage, but be cautious with this option, as it may cause some websites to never finish loading._ |    ✔️    |
|       cookies       | Set cookies for the next request.                                                                                                                                                                                                                                                                                                                                                                                           |    ✔️    |
|    google_search    | Enabled by default, Scrapling will set the referer header as if this request came from a Google search of this website's domain name.                                                                                                                                                                                                                                                                                       |    ✔️    |
|    extra_headers    | A dictionary of extra headers to add to the request. _The referer set by the `google_search` argument takes priority over the referer set here if used together._                                                                                                                                                                                                                                                           |    ✔️    |
|    block_webrtc     | Blocks WebRTC entirely.                                                                                                                                                                                                                                                                                                                                                                                                     |    ✔️    |
|     page_action     | Added for automation. Pass a function that takes the `page` object and does the necessary automation.                                                                                                                                                                                                                                                                                                                       |    ✔️    |
|       addons        | List of Firefox addons to use. **Must be paths to extracted addons.**                                                                                                                                                                                                                                                                                                                                                       |    ✔️    |
|      humanize       | Humanize the cursor movement. The cursor movement takes either True or the maximum duration in seconds. The cursor typically takes up to 1.5 seconds to move across the window.                                                                                                                                                                                                                                             |    ✔️    |
|     allow_webgl     | Enabled by default. Disabling WebGL is not recommended, as many WAFs now check if WebGL is enabled.                                                                                                                                                                                                                                                                                                                         |    ✔️    |
|        geoip        | Recommended to use with proxies; Automatically use IPs' longitude, latitude, timezone, country, locale, & spoof the WebRTC IP address. It will also calculate and spoof the browser's language based on the distribution of language speakers in the target region.                                                                                                                                                         |    ✔️    |
|    os_randomize     | If enabled, Scrapling will randomize the OS fingerprints used. The default is matching the fingerprints with the current OS.                                                                                                                                                                                                                                                                                                |    ✔️    |
|     disable_ads     | Disabled by default; this installs the `uBlock Origin` addon on the browser if enabled.                                                                                                                                                                                                                                                                                                                                     |    ✔️    |
|  solve_cloudflare   | When enabled, fetcher solves all types of Cloudflare's Turnstile/Interstitial challenges before returning the response to you.                                                                                                                                                                                                                                                                                              |    ✔️    |
|    network_idle     | Wait for the page until there are no network connections for at least 500 ms.                                                                                                                                                                                                                                                                                                                                               |    ✔️    |
|      load_dom       | Enabled by default, wait for all JavaScript on page(s) to fully load and execute (wait for the `domcontentloaded` state).                                                                                                                                                                                                                                                                                                   |    ✔️    |
|       timeout       | The timeout used in all operations and waits through the page. It's in milliseconds, and the default is 30000.                                                                                                                                                                                                                                                                                                              |    ✔️    |
|        wait         | The time (milliseconds) the fetcher will wait after everything finishes before closing the page and returning the `Response` object.                                                                                                                                                                                                                                                                                        |    ✔️    |
|    wait_selector    | Wait for a specific css selector to be in a specific state.                                                                                                                                                                                                                                                                                                                                                                 |    ✔️    |
|     init_script     | An absolute path to a JavaScript file to be executed on page creation for all pages in this session.                                                                                                                                                                                                                                                                                                                        |    ✔️    |
| wait_selector_state | Scrapling will wait for the given state to be fulfilled for the selector given with `wait_selector`. _Default state is `attached`._                                                                                                                                                                                                                                                                                         |    ✔️    |
|        proxy        | The proxy to be used with requests. It can be a string or a dictionary with only the keys 'server', 'username', and 'password'.                                                                                                                                                                                                                                                                                             |    ✔️    |
|    user_data_dir    | Path to a User Data Directory, which stores browser session data like cookies and local storage. The default is to create a temporary directory. **Only Works with sessions**                                                                                                                                                                                                                                               |    ✔️    |
|   additional_args   | Additional arguments to be passed to Camoufox as additional settings, and they take higher priority than Scrapling's settings.                                                                                                                                                                                                                                                                                              |    ✔️    |
|   selector_config   | A dictionary of custom parsing arguments to be used when creating the final `Selector`/`Response` class.                                                                                                                                                                                                                                                                                                                    |    ✔️    |

In session classes, all these arguments can be set globally for the session. Still, you can configure each request individually by passing some of the arguments here that can be configured on the browser tab level like: `google_search`, `timeout`, `wait`, `page_action`, `extra_headers`, `disable_resources`, `wait_selector`, `wait_selector_state`, `network_idle`, `load_dom`, `solve_cloudflare`, and `selector_config`.

## Examples
It's easier to understand with examples, so we will now review most of the arguments individually.

### Browser Modes

```python
# Headless/hidden mode (default)
page = StealthyFetcher.fetch('https://example.com', headless=True)

# Visible browser mode
page = StealthyFetcher.fetch('https://example.com', headless=False)
```

### Resource Control

```python
# Block images
page = StealthyFetcher.fetch('https://example.com', block_images=True)

# Disable unnecessary resources
page = StealthyFetcher.fetch('https://example.com', disable_resources=True)  # Blocks fonts, images, media, etc.
```

### Cloudflare Protection Bypass

```python
# Automatic Cloudflare solver
page = StealthyFetcher.fetch(
    'https://nopecha.com/demo/cloudflare',
    solve_cloudflare=True  # Automatically solve Cloudflare challenges
)

# Works with other stealth options
page = StealthyFetcher.fetch(
    'https://protected-site.com',
    solve_cloudflare=True,
    humanize=True,
    geoip=True,
    os_randomize=True
)
```

The `solve_cloudflare` parameter enables automatic detection and solving all types of Cloudflare's Turnstile/Interstitial challenges:

- JavaScript challenges (managed)
- Interactive challenges (clicking verification boxes)
- Invisible challenges (automatic background verification)

And even solves the custom pages.

**Important notes:**

- Sometimes, with websites that use custom implementations, you will need to use `wait_selector` to make sure Scrapling waits for the real website content to be loaded after solving the captcha. Some websites can be the real definition of an edge case while we are trying to make the solver as generic as possible.
- When `solve_cloudflare=True` is enabled, `humanize=True` is automatically activated for more realistic behavior
- The timeout should be at least 60 seconds when using the Cloudflare solver for sufficient challenge-solving time
- This feature works seamlessly with proxies and other stealth options

### Additional stealth options

```python
page = StealthyFetcher.fetch(
   'https://example.com',
   block_webrtc=True,  # Block WebRTC
   allow_webgl=False,  # Disable WebGL
   humanize=True,      # Make the mouse move as a human would move it
   geoip=True,         # Use IP's longitude, latitude, timezone, country, and locale, then spoof the WebRTC IP address...
   os_randomize=True,  # Randomize the OS fingerprints used. The default is matching the fingerprints with the current OS.
   disable_ads=True,   # Block ads with uBlock Origin addon (enabled by default)
   google_search=True
)

# Custom humanization duration
page = StealthyFetcher.fetch(
    'https://example.com',
    humanize=1.5  # Max 1.5 seconds for cursor movement
)
```

The `google_search` argument is enabled by default, making the request appear to come from a Google search page. So, a request for `https://example.com` will set the referer to `https://www.google.com/search?q=example`. Also, if used together, it takes priority over the referer set by the `extra_headers` argument.

### Network Control

```python
# Wait for network idle (Consider fetch to be finished when there are no network connections for at least 500 ms)
page = StealthyFetcher.fetch('https://example.com', network_idle=True)

# Custom timeout (in milliseconds)
page = StealthyFetcher.fetch('https://example.com', timeout=30000)  # 30 seconds

# Proxy support
page = StealthyFetcher.fetch(
    'https://example.com',
    proxy='http://username:password@host:port' # Or it can be a dictionary with the keys 'server', 'username', and 'password' only
)
```

### Downloading Files

```python
page = StealthyFetcher.fetch('https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/poster.png')

with open(file='poster.png', mode='wb') as f:
    f.write(page.body)
```

The `body` attribute of the `Response` object is a `bytes` object containing the response body in case of Non-HTML responses.

### Browser Automation
This is where your knowledge about [Playwright's Page API](https://playwright.dev/python/docs/api/class-page) comes into play. The function you pass here takes the page object from Playwright's API, performs the desired action, and then the fetcher continues.

This function is executed immediately after waiting for `network_idle` (if enabled) and before waiting for the `wait_selector` argument, allowing it to be used for purposes beyond automation. You can alter the page as you want.

In the example below, I used the pages' [mouse events](https://playwright.dev/python/docs/api/class-mouse) to scroll the page with the mouse wheel, then move the mouse.
```python
from playwright.sync_api import Page

def scroll_page(page: Page):
    page.mouse.wheel(10, 0)
    page.mouse.move(100, 400)
    page.mouse.up()

page = StealthyFetcher.fetch(
    'https://example.com',
    page_action=scroll_page
)
```
Of course, if you use the async fetch version, the function must also be async.
```python
from playwright.async_api import Page

async def scroll_page(page: Page):
   await page.mouse.wheel(10, 0)
   await page.mouse.move(100, 400)
   await page.mouse.up()

page = await StealthyFetcher.async_fetch(
    'https://example.com',
    page_action=scroll_page
)
```

### Wait Conditions
```python
# Wait for the selector
page = StealthyFetcher.fetch(
    'https://example.com',
    wait_selector='h1',
    wait_selector_state='visible'
)
```
This is the last wait the fetcher will do before returning the response (if enabled). You pass a CSS selector to the `wait_selector` argument, and the fetcher will wait for the state you passed in the `wait_selector_state` argument to be fulfilled. If you didn't pass a state, the default would be `attached`, which means it will wait for the element to be present in the DOM.

After that, if `load_dom` is enabled (the default), the fetcher will check again to see if all JavaScript files are loaded and executed (in the `domcontentloaded` state) or continue waiting. If you have enabled `network_idle`, the fetcher will wait for `network_idle` to be fulfilled again, as explained above.

The states the fetcher can wait for can be any of the following ([source](https://playwright.dev/python/docs/api/class-page#page-wait-for-selector)):

- `attached`: Wait for an element to be present in the DOM.
- `detached`: Wait for an element to not be present in the DOM.
- `visible`: wait for an element to have a non-empty bounding box and no `visibility:hidden`. Note that an element without any content or with `display:none` has an empty bounding box and is not considered visible.
- `hidden`: wait for an element to be either detached from the DOM, or have an empty bounding box, or `visibility:hidden`. This is opposite to the `'visible'` option.

### Firefox Addons

```python
# Custom Firefox addons
page = StealthyFetcher.fetch(
    'https://example.com',
    addons=['/path/to/addon1', '/path/to/addon2']
)
```
The paths here must point to extracted addons that will be installed automatically upon browser launch.

### Real-world example (Amazon)
This is for educational purposes only; this example was generated by AI, which shows how easy it is to work with Scrapling through AI
```python
def scrape_amazon_product(url):
    # Use StealthyFetcher to bypass protection
    page = StealthyFetcher.fetch(url)

    # Extract product details
    return {
        'title': page.css_first('#productTitle::text').clean(),
        'price': page.css_first('.a-price .a-offscreen::text'),
        'rating': page.css_first('[data-feature-name="averageCustomerReviews"] .a-popover-trigger .a-color-base::text'),
        'reviews_count': page.css('#acrCustomerReviewText::text').re_first(r'[\d,]+'),
        'features': [
            li.clean() for li in page.css('#feature-bullets li span::text')
        ],
        'availability': page.css_first('#availability').get_all_text(strip=True),
        'images': [
            img.attrib['src'] for img in page.css('#altImages img')
        ]
    }
```

## Session Management

To keep the browser open until you make multiple requests with the same configuration, use `StealthySession`/`AsyncStealthySession` classes. Those classes can accept all the arguments that the `fetch` function can take, which enables you to specify a config for the entire session.

```python
from scrapling.fetchers import StealthySession

# Create a session with default configuration
with StealthySession(
    headless=True,
    geoip=True,
    humanize=True,
    solve_cloudflare=True
) as session:
    # Make multiple requests with the same browser instance
    page1 = session.fetch('https://example1.com')
    page2 = session.fetch('https://example2.com') 
    page3 = session.fetch('https://nopecha.com/demo/cloudflare')
    
    # All requests reuse the same tab on the same browser instance
```

### Async Session Usage

```python
import asyncio
from scrapling.fetchers import AsyncStealthySession

async def scrape_multiple_sites():
    async with AsyncStealthySession(
        geoip=True,
        os_randomize=True,
        solve_cloudflare=True,
        timeout=60000,  # 60 seconds for Cloudflare challenges
        max_pages=3
    ) as session:
        # Make async requests with shared browser configuration
        pages = await asyncio.gather(
            session.fetch('https://site1.com'),
            session.fetch('https://site2.com'), 
            session.fetch('https://protected-site.com')
        )
        return pages
```

You may have noticed the `max_pages` argument. This is a new argument that enables the fetcher to create a **rotating pool of Browser tabs**. Instead of using a single tab for all your requests, you set a limit on the maximum number of pages. With each request, the library will close all tabs that have finished their task and check if the number of the current tabs is lower than the maximum allowed number of pages/tabs, then:

1. If you are within the allowed range, the fetcher will create a new tab for you, and then all is as normal.
2. Otherwise, it will keep checking every subsecond if creating a new tab is allowed or not for 60 seconds, then raise `TimeoutError`. This can happen when the website you are fetching becomes unresponsive.

This logic allows for multiple websites to be fetched at the same time in the same browser, which saves a lot of resources, but most importantly, is so fast :)

In versions 0.3 and 0.3.1, the pool was reusing finished tabs to save more resources/time. That logic proved flawed, as it's nearly impossible to protect pages/tabs from contamination by the previous configuration used in the request before this one.

### Session Benefits

- **Browser reuse**: Much faster subsequent requests by reusing the same browser instance.
- **Cookie persistence**: Automatic cookie and session state handling as any browser does automatically.
- **Consistent fingerprint**: Same browser fingerprint across all requests.
- **Memory efficiency**: Better resource usage compared to launching new browsers with each fetch.

## When to Use

Use StealthyFetcher when:

- Bypassing anti-bot protection
- Need a reliable browser fingerprint
- Full JavaScript support needed
- Want automatic stealth features
- Need browser automation
- Dealing with Cloudflare protection

----------------------------------------


## File: index.md
<!-- Source: docs/index.md -->

<style>
.md-typeset h1 {
  display: none;
}
</style>

<div align="center">
    <a href="https://scrapling.readthedocs.io/en/latest/" alt="poster">
        <img alt="poster" src="assets/poster.png" style="width: 50%; height: 100%;"></a>
</div>

<div align="center">
    <i><code>Easy, effortless Web Scraping as it should be!</code></i>
    <br/><br/>
</div>

**Stop fighting anti-bot systems. Stop rewriting selectors after every website update.**

Scrapling isn't just another Web Scraping library. It's the first **adaptive** scraping library that learns from website changes and evolves with them. While other libraries break when websites update their structure, Scrapling automatically relocates your elements and keeps your scrapers running.

Built for the modern Web, Scrapling features its own rapid parsing engine and fetchers to handle all Web Scraping challenges you face or will face. Built by Web Scrapers for Web Scrapers and regular users, there's something for everyone.

```python
>> from scrapling.fetchers import Fetcher, AsyncFetcher, StealthyFetcher, DynamicFetcher
>> StealthyFetcher.adaptive = True
# Fetch websites' source under the radar!
>> page = StealthyFetcher.fetch('https://example.com', headless=True, network_idle=True)
>> print(page.status)
200
>> products = page.css('.product', auto_save=True)  # Scrape data that survives website design changes!
>> # Later, if the website structure changes, pass `adaptive=True`
>> products = page.css('.product', adaptive=True)  # and Scrapling still finds them!
```

## Top Sponsors 

<!-- sponsors -->
<div style="text-align: center;">
    <a href="https://www.scrapeless.com/en?utm_source=official&utm_term=scrapling" target="_blank" title="Effortless Web Scraping Toolkit for Business and Developers"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/scrapeless.jpg"></a>
    <a href="https://www.thordata.com/?ls=github&lk=github" target="_blank" title="Unblockable proxies and scraping infrastructure, delivering real-time, reliable web data to power AI models and workflows."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/thordata.jpg"></a>
    <a href="https://evomi.com?utm_source=github&utm_medium=banner&utm_campaign=d4vinci-scrapling" target="_blank" title="Evomi is your Swiss Quality Proxy Provider, starting at $0.49/GB"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/evomi.png"></a>
    <a href="https://serpapi.com/?utm_source=scrapling" target="_blank" title="Scrape Google and other search engines with SerpApi"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/SerpApi.png"></a>
    <a href="https://visit.decodo.com/Dy6W0b" target="_blank" title="Try the Most Efficient Residential Proxies for Free"><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/decodo.png"></a>
    <a href="https://petrosky.io/d4vinci" target="_blank" title="PetroSky delivers cutting-edge VPS hosting."><img src="https://raw.githubusercontent.com/D4Vinci/Scrapling/main/images/petrosky.png"></a>
</div>
<!-- /sponsors -->

<i><sub>Do you want to show your ad here? Click [here](https://github.com/sponsors/D4Vinci/sponsorships?tier_id=435495) and enjoy the rest of the perks!</sub></i>

## Key Features

### Advanced Websites Fetching with Session Support
- **HTTP Requests**: Fast and stealthy HTTP requests with the `Fetcher` class. Can impersonate browsers' TLS fingerprint, headers, and use HTTP/3.
- **Dynamic Loading**: Fetch dynamic websites with full browser automation through the `DynamicFetcher` class supporting Playwright's Chromium, real Chrome, and custom stealth mode.
- **Anti-bot Bypass**: Advanced stealth capabilities with `StealthyFetcher` using a modified version of Firefox and fingerprint spoofing. Can bypass all types of Cloudflare's Turnstile/Interstitial with automation easily.
- **Session Management**: Persistent session support with `FetcherSession`, `StealthySession`, and `DynamicSession` classes for cookie and state management across requests.
- **Async Support**: Complete async support across all fetchers and dedicated async session classes.

### Adaptive Scraping & AI Integration
- 🔄 **Smart Element Tracking**: Relocate elements after website changes using intelligent similarity algorithms.
- 🎯 **Smart Flexible Selection**: CSS selectors, XPath selectors, filter-based search, text search, regex search, and more. 
- 🔍 **Find Similar Elements**: Automatically locate elements similar to found elements.
- 🤖 **MCP Server to be used with AI**: Built-in MCP server for AI-assisted Web Scraping and data extraction. The MCP server features custom, powerful capabilities that utilize Scrapling to extract targeted content before passing it to the AI (Claude/Cursor/etc), thereby speeding up operations and reducing costs by minimizing token usage.

### High-Performance & battle-tested Architecture
- 🚀 **Lightning Fast**: Optimized performance outperforming most Python scraping libraries.
- 🔋 **Memory Efficient**: Optimized data structures and lazy loading for a minimal memory footprint.
- ⚡ **Fast JSON Serialization**: 10x faster than the standard library.
- 🏗️ **Battle tested**: Not only does Scrapling have 92% test coverage and full type hints coverage, but it has been used daily by hundreds of Web Scrapers over the past year.

### Developer/Web Scraper Friendly Experience
- 🎯 **Interactive Web Scraping Shell**: Optional built-in IPython shell with Scrapling integration, shortcuts, and new tools to speed up Web Scraping scripts development, like converting curl requests to Scrapling requests and viewing requests results in your browser.
- 🚀 **Use it directly from the Terminal**: Optionally, you can use Scrapling to scrape a URL without writing a single code!
- 🛠️ **Rich Navigation API**: Advanced DOM traversal with parent, sibling, and child navigation methods.
- 🧬 **Enhanced Text Processing**: Built-in regex, cleaning methods, and optimized string operations.
- 📝 **Auto Selector Generation**: Generate robust CSS/XPath selectors for any element.
- 🔌 **Familiar API**: Similar to Scrapy/BeautifulSoup with the same pseudo-elements used in Scrapy/Parsel.
- 📘 **Complete Type Coverage**: Full type hints for excellent IDE support and code completion.
- 🔋 **Ready Docker image**: With each release, a Docker image containing all browsers is automatically built and pushed.


## Star History
Scrapling’s GitHub stars have grown steadily since its release (see chart below).

<div id="chartContainer">
  <a href="https://github.com/D4Vinci/Scrapling">
    <img id="chartImage" alt="Star History Chart" loading="lazy" src="https://api.star-history.com/svg?repos=D4Vinci/Scrapling&type=date&legend=top-left&theme=dark" height="400"/>
  </a>
</div>


## Installation
Scrapling requires Python 3.10 or higher:

```bash
pip install scrapling
```

Starting with v0.3.2, this installation only includes the parser engine and its dependencies, without any fetchers or commandline dependencies.

### Optional Dependencies

1. If you are going to use any of the extra features below, the fetchers, or their classes, then you need to install fetchers' dependencies, and then install their browser dependencies with
    ```bash
    pip install "scrapling[fetchers]"
    
    scrapling install
    ```

    This downloads all browsers with their system dependencies and fingerprint manipulation dependencies.

2. Extra features:


     - Install the MCP server feature:
       ```bash
       pip install "scrapling[ai]"
       ```
     - Install shell features (Web Scraping shell and the `extract` command): 
         ```bash
         pip install "scrapling[shell]"
         ```
     - Install everything: 
         ```bash
         pip install "scrapling[all]"
         ```
     Don't forget that you need to install the browser dependencies with `scrapling install` after any of these extras (if you didn't already)

### Docker
You can also install a Docker image with all extras and browsers with the following command from DockerHub:
```bash
docker pull pyd4vinci/scrapling
```
Or download it from the GitHub registry:
```bash
docker pull ghcr.io/d4vinci/scrapling:latest
```
This image is automatically built and pushed through GitHub actions on the repository's main branch.

## How the documentation is organized
Scrapling has a lot of documentation, so we try to follow a guideline called the [Diátaxis documentation framework](https://diataxis.fr/).

## Support

If you like Scrapling and want to support its development:

- ⭐ Star the [GitHub repository](https://github.com/D4Vinci/Scrapling)
- 🚀 Follow us on [Twitter](https://x.com/Scrapling_dev) and join the [discord server](https://discord.gg/EMgGbDceNQ)
- 💝 Consider [sponsoring the project or buying me a coffee](donate.md) :wink:
- 🐛 Report bugs and suggest features through [GitHub Issues](https://github.com/D4Vinci/Scrapling/issues)

## License

This project is licensed under the BSD-3 License. See the [LICENSE](https://github.com/D4Vinci/Scrapling/blob/main/LICENSE) file for details.

----------------------------------------


## File: overview.md
<!-- Source: docs/overview.md -->

We will start by quickly reviewing the parsing capabilities. Then, we will fetch websites with custom browsers, make requests, and parse the response.

Here's an HTML document generated by ChatGPT that we will be using as an example throughout this page:
```html
<html>
  <head>
    <title>Complex Web Page</title>
    <style>
      .hidden { display: none; }
    </style>
  </head>
  <body>
    <header>
      <nav>
        <ul>
          <li> <a href="#home">Home</a> </li>
          <li> <a href="#about">About</a> </li>
          <li> <a href="#contact">Contact</a> </li>
        </ul>
      </nav>
    </header>
    <main>
      <section id="products" schema='{"jsonable": "data"}'>
        <h2>Products</h2>
        <div class="product-list">
          <article class="product" data-id="1">
            <h3>Product 1</h3>
            <p class="description">This is product 1</p>
            <span class="price">$10.99</span>
            <div class="hidden stock">In stock: 5</div>
          </article>

          <article class="product" data-id="2">
            <h3>Product 2</h3>
            <p class="description">This is product 2</p>
            <span class="price">$20.99</span>
            <div class="hidden stock">In stock: 3</div>
          </article>

          <article class="product" data-id="3">
            <h3>Product 3</h3>
            <p class="description">This is product 3</p>
            <span class="price">$15.99</span>
            <div class="hidden stock">Out of stock</div>
          </article>
        </div>
      </section>
      
      <section id="reviews">
        <h2>Customer Reviews</h2>
        <div class="review-list">
          <div class="review" data-rating="5">
            <p class="review-text">Great product!</p>
            <span class="reviewer">John Doe</span>
          </div>
          <div class="review" data-rating="4">
            <p class="review-text">Good value for money.</p>
            <span class="reviewer">Jane Smith</span>
          </div>
        </div>
      </section>
    </main>
    <script id="page-data" type="application/json">
      {
        "lastUpdated": "2024-09-22T10:30:00Z",
        "totalProducts": 3
      }
    </script>
  </body>
</html>
```
Starting with loading raw HTML above like this
```python
from scrapling.parser import Selector
page = Selector(html_doc)
page  # <data='<html><head><title>Complex Web Page</tit...'>
```
Get all text content on the page recursively
```python
page.get_all_text(ignore_tags=('script', 'style'))
# 'Complex Web Page\nHome\nAbout\nContact\nProducts\nProduct 1\nThis is product 1\n$10.99\nIn stock: 5\nProduct 2\nThis is product 2\n$20.99\nIn stock: 3\nProduct 3\nThis is product 3\n$15.99\nOut of stock\nCustomer Reviews\nGreat product!\nJohn Doe\nGood value for money.\nJane Smith'
```

## Finding elements
If there's an element you want to find on the page, you will! Your creativity level is the only limitation!

Finding the first HTML `section` element
```python
section_element = page.find('section')
# <data='<section id="products" schema='{"jsonabl...' parent='<main><section id="products" schema='{"j...'>
```
Find all `section` elements
```python
section_elements = page.find_all('section')
# [<data='<section id="products" schema='{"jsonabl...' parent='<main><section id="products" schema='{"j...'>, <data='<section id="reviews"><h2>Customer Revie...' parent='<main><section id="products" schema='{"j...'>]
```
Find all `section` elements whose `id` attribute value is `products`
```python
section_elements = page.find_all('section', {'id':"products"})
# Same as
section_elements = page.find_all('section', id="products")
# [<data='<section id="products" schema='{"jsonabl...' parent='<main><section id="products" schema='{"j...'>]
```
Find all `section` elements whose `id` attribute value contains `product`
```python
section_elements = page.find_all('section', {'id*':"product"})
```
Find all `h3` elements whose text content matches this regex `Product \d`
```python
page.find_all('h3', re.compile(r'Product \d'))
# [<data='<h3>Product 1</h3>' parent='<article class="product" data-id="1"><h3...'>, <data='<h3>Product 2</h3>' parent='<article class="product" data-id="2"><h3...'>, <data='<h3>Product 3</h3>' parent='<article class="product" data-id="3"><h3...'>]
```
Find all `h3` and `h2` elements whose text content matches the regex `Product` only
```python
page.find_all(['h3', 'h2'], re.compile(r'Product'))
# [<data='<h3>Product 1</h3>' parent='<article class="product" data-id="1"><h3...'>, <data='<h3>Product 2</h3>' parent='<article class="product" data-id="2"><h3...'>, <data='<h3>Product 3</h3>' parent='<article class="product" data-id="3"><h3...'>, <data='<h2>Products</h2>' parent='<section id="products" schema='{"jsonabl...'>]
```
Find all elements whose text content matches exactly `Products` (Whitespaces are not taken into consideration)
```python
page.find_by_text('Products', first_match=False)
# [<data='<h2>Products</h2>' parent='<section id="products" schema='{"jsonabl...'>]
```
Or find all elements whose text content matches regex `Product \d`
```python
page.find_by_regex(r'Product \d', first_match=False)
# [<data='<h3>Product 1</h3>' parent='<article class="product" data-id="1"><h3...'>, <data='<h3>Product 2</h3>' parent='<article class="product" data-id="2"><h3...'>, <data='<h3>Product 3</h3>' parent='<article class="product" data-id="3"><h3...'>]
```
Find all elements that are similar to the element you want
```python
target_element = page.find_by_regex(r'Product \d', first_match=True)
# <data='<h3>Product 1</h3>' parent='<article class="product" data-id="1"><h3...'>
target_element.find_similar()
# [<data='<h3>Product 2</h3>' parent='<article class="product" data-id="2"><h3...'>, <data='<h3>Product 3</h3>' parent='<article class="product" data-id="3"><h3...'>]
```
Find the first element that matches a CSS selector
```python
page.css_first('.product-list [data-id="1"]')
# <data='<article class="product" data-id="1"><h3...' parent='<div class="product-list"> <article clas...'>
```
Find all elements that match a CSS selector
```python
page.css('.product-list article')
# [<data='<article class="product" data-id="1"><h3...' parent='<div class="product-list"> <article clas...'>, <data='<article class="product" data-id="2"><h3...' parent='<div class="product-list"> <article clas...'>, <data='<article class="product" data-id="3"><h3...' parent='<div class="product-list"> <article clas...'>]
```
Find the first element that matches an XPath selector
```python
page.xpath_first("//*[@id='products']/div/article")
# <data='<article class="product" data-id="1"><h3...' parent='<div class="product-list"> <article clas...'>
```
Find all elements that match an XPath selector
```python
page.xpath("//*[@id='products']/div/article")
# [<data='<article class="product" data-id="1"><h3...' parent='<div class="product-list"> <article clas...'>, <data='<article class="product" data-id="2"><h3...' parent='<div class="product-list"> <article clas...'>, <data='<article class="product" data-id="3"><h3...' parent='<div class="product-list"> <article clas...'>]
```

With this, we just scratched the surface of these functions; more advanced options with these selection methods are shown later.
## Accessing elements' data
It's as simple as
```python
>>> section_element.tag
'section'
>>> print(section_element.attrib)
{'id': 'products', 'schema': '{"jsonable": "data"}'}
>>> section_element.attrib['schema'].json()  # If an attribute value can be converted to json, then use `.json()` to convert it
{'jsonable': 'data'}
>>> section_element.text  # Direct text content
''
>>> section_element.get_all_text()  # All text content recursively
'Products\nProduct 1\nThis is product 1\n$10.99\nIn stock: 5\nProduct 2\nThis is product 2\n$20.99\nIn stock: 3\nProduct 3\nThis is product 3\n$15.99\nOut of stock'
>>> section_element.html_content  # The HTML content of the element
'<section id="products" schema=\'{"jsonable": "data"}\'><h2>Products</h2>\n        <div class="product-list">\n          <article class="product" data-id="1"><h3>Product 1</h3>\n            <p class="description">This is product 1</p>\n            <span class="price">$10.99</span>\n            <div class="hidden stock">In stock: 5</div>\n          </article><article class="product" data-id="2"><h3>Product 2</h3>\n            <p class="description">This is product 2</p>\n            <span class="price">$20.99</span>\n            <div class="hidden stock">In stock: 3</div>\n          </article><article class="product" data-id="3"><h3>Product 3</h3>\n            <p class="description">This is product 3</p>\n            <span class="price">$15.99</span>\n            <div class="hidden stock">Out of stock</div>\n          </article></div>\n      </section>'
>>> print(section_element.prettify())  # The prettified version
'''
<section id="products" schema='{"jsonable": "data"}'><h2>Products</h2>
    <div class="product-list">
      <article class="product" data-id="1"><h3>Product 1</h3>
        <p class="description">This is product 1</p>
        <span class="price">$10.99</span>
        <div class="hidden stock">In stock: 5</div>
      </article><article class="product" data-id="2"><h3>Product 2</h3>
        <p class="description">This is product 2</p>
        <span class="price">$20.99</span>
        <div class="hidden stock">In stock: 3</div>
      </article><article class="product" data-id="3"><h3>Product 3</h3>
        <p class="description">This is product 3</p>
        <span class="price">$15.99</span>
        <div class="hidden stock">Out of stock</div>
      </article>
    </div>
</section>
'''
>>> section_element.path  # All the ancestors in the DOM tree of this element
[<data='<main><section id="products" schema='{"j...' parent='<body> <header><nav><ul><li> <a href="#h...'>,
 <data='<body> <header><nav><ul><li> <a href="#h...' parent='<html><head><title>Complex Web Page</tit...'>,
 <data='<html><head><title>Complex Web Page</tit...'>]
>>> section_element.generate_css_selector
'#products'
>>> section_element.generate_full_css_selector
'body > main > #products > #products'
>>> section_element.generate_xpath_selector
"//*[@id='products']"
>>> section_element.generate_full_xpath_selector
"//body/main/*[@id='products']"
```

## Navigation
Using the elements we found above 

```python
>>> section_element.parent
<data='<main><section id="products" schema='{"j...' parent='<body> <header><nav><ul><li> <a href="#h...'>
>>> section_element.parent.tag
'main'
>>> section_element.parent.parent.tag
'body'
>>> section_element.children
[<data='<h2>Products</h2>' parent='<section id="products" schema='{"jsonabl...'>,
 <data='<div class="product-list"> <article clas...' parent='<section id="products" schema='{"jsonabl...'>]
>>> section_element.siblings
[<data='<section id="reviews"><h2>Customer Revie...' parent='<main><section id="products" schema='{"j...'>]
>>> section_element.next  # gets the next element, the same logic applies to `quote.previous`
<data='<section id="reviews"><h2>Customer Revie...' parent='<main><section id="products" schema='{"j...'>
>>> section_element.children.css('h2::text')
['Products']
>>> page.css_first('[data-id="1"]').has_class('product')
True
```
If your case needs more than the element's parent, you can iterate over the whole ancestors' tree of any element, like the one below
```python
for ancestor in quote.iterancestors():
    # do something with it...
```
You can search for a specific ancestor of an element that satisfies a function; all you need to do is pass a function that takes a `Selector` object as an argument and returns `True` if the condition is satisfied or `False` otherwise, like below:
```python
>>> section_element.find_ancestor(lambda ancestor: ancestor.css('nav'))
<data='<body> <header><nav><ul><li> <a href="#h...' parent='<html><head><title>Complex Web Page</tit...'>
```

## Fetching websites
Instead of passing the raw HTML to Scrapling, you can get a website's response directly through HTTP requests or by fetching it from browsers.

A fetcher is made for every use case.

### HTTP Requests
For simple HTTP requests, there's a `Fetcher` class that can be imported and used as below:
```python
from scrapling.fetchers import Fetcher
page = Fetcher.get('https://scrapling.requestcatcher.com/get', impersonate="chrome")
```
With that out of the way, here's how to do all HTTP methods:
```python
>>> from scrapling.fetchers import Fetcher
>>> page = Fetcher.get('https://scrapling.requestcatcher.com/get', stealthy_headers=True, follow_redirects=True)
>>> page = Fetcher.post('https://scrapling.requestcatcher.com/post', data={'key': 'value'}, proxy='http://username:password@localhost:8030')
>>> page = Fetcher.put('https://scrapling.requestcatcher.com/put', data={'key': 'value'})
>>> page = Fetcher.delete('https://scrapling.requestcatcher.com/delete')
```
For Async requests, you will replace the import like below:
```python
>>> from scrapling.fetchers import AsyncFetcher
>>> page = await AsyncFetcher.get('https://scrapling.requestcatcher.com/get', stealthy_headers=True, follow_redirects=True)
>>> page = await AsyncFetcher.post('https://scrapling.requestcatcher.com/post', data={'key': 'value'}, proxy='http://username:password@localhost:8030')
>>> page = await AsyncFetcher.put('https://scrapling.requestcatcher.com/put', data={'key': 'value'})
>>> page = await AsyncFetcher.delete('https://scrapling.requestcatcher.com/delete')
```

> Notes:
> 
> 1. You have the `stealthy_headers` argument, which, when enabled, makes requests to generate real browser headers and use them, including a referer header, as if this request came from a Google search of this domain. It's enabled by default.
> 2. The `impersonate` argument allows you to fake the TLS fingerprint for a specific version of a browser.
> 3. There's also the `http3` argument, which, when enabled, makes the fetcher use HTTP/3 for requests, which makes your requests more authentic

This is just the tip of the iceberg with this fetcher; check out the rest from [here](fetching/static.md)

### Dynamic loading
We have you covered if you deal with dynamic websites like most today!

The `DynamicFetcher` class (previously known as `PlayWrightFetcher`) provides many options to fetch/load websites' pages through browsers.
```python
>>> from scrapling.fetchers import DynamicFetcher
>>> page = DynamicFetcher.fetch('https://www.google.com/search?q=%22Scrapling%22', disable_resources=True)  # Vanilla Playwright option
>>> page.css_first("#search a::attr(href)")
'https://github.com/D4Vinci/Scrapling'
>>> # The async version of fetch
>>> page = await DynamicFetcher.async_fetch('https://www.google.com/search?q=%22Scrapling%22', disable_resources=True)
>>> page.css_first("#search a::attr(href)")
'https://github.com/D4Vinci/Scrapling'
```
It's built on top of [Playwright](https://playwright.dev/python/) and it's currently providing three main run options that can be mixed as you want:

- Vanilla Playwright without any modifications other than the ones you chose. It uses the Chromium browser.
- Stealthy Playwright with custom stealth mode explicitly written for it. It's not top-tier stealth mode, but it bypasses many online tests like [Sannysoft's](https://bot.sannysoft.com/). Check out the `StealthyFetcher` class below for more advanced stealth mode. It uses the Chromium browser.
- Real browsers like your Chrome browser by passing the `real_chrome` argument or the CDP URL of your browser to be controlled by the Fetcher, and most of the options can be enabled on it.


Again, this is just the tip of the iceberg with this fetcher. Check out the rest from [here](fetching/dynamic.md) for all details and the complete list of arguments.

### Dynamic anti-protection loading
We also have you covered if you deal with dynamic websites with annoying anti-protections!

The `StealthyFetcher` class uses a custom version of a modified Firefox browser called [Camoufox](https://github.com/daijro/camoufox), bypassing most bot detections by default. Scrapling offers a faster custom version, includes extra tools, and features easy configurations to further increase undetectability.
```python
>>> from scrapling.fetchers import StealthyFetcher
>>> page = StealthyFetcher.fetch('https://www.browserscan.net/bot-detection')  # Running headless by default
>>> page.status == 200
True
>>> page = StealthyFetcher.fetch('https://nopecha.com/demo/cloudflare', solve_cloudflare=True)  # Solve Cloudflare captcha automatically if presented
>>> page.status == 200
True
>>> page = StealthyFetcher.fetch('https://www.browserscan.net/bot-detection', humanize=True, os_randomize=True) # and the rest of arguments...
>>> # The async version of fetch
>>> page = await StealthyFetcher.async_fetch('https://www.browserscan.net/bot-detection')
>>> page.status == 200
True
```

Again, this is just the tip of the iceberg with this fetcher. Check out the rest from [here](fetching/dynamic.md) for all details and the complete list of arguments.

---

That's Scrapling at a glance. If you want to learn more about it, continue to the next section.

----------------------------------------


## File: parsing/adaptive.md
<!-- Source: docs/parsing/adaptive.md -->

## Introduction

> 💡 **Prerequisites:**
> 
> 1. You’ve completed or read the [Querying elements](../parsing/selection.md) page to understand how to find/extract elements from the [Selector](../parsing/main_classes.md#selector) object.
> 2. You’ve completed or read the [Main classes](../parsing/main_classes.md) page to understand the [Selector](../parsing/main_classes.md#selector) class.
> <br><br>

Adaptive scraping (previously known as automatch) is one of Scrapling's most powerful features. It allows your scraper to survive website changes by intelligently tracking and relocating elements.

Let's say you are scraping a page with a structure like this:
```html
<div class="container">
    <section class="products">
        <article class="product" id="p1">
            <h3>Product 1</h3>
            <p class="description">Description 1</p>
        </article>
        <article class="product" id="p2">
            <h3>Product 2</h3>
            <p class="description">Description 2</p>
        </article>
    </section>
</div>
```
And you want to scrape the first product, the one with the `p1` ID. You will probably write a selector like this
```python
page.css('#p1')
```
When website owners implement structural changes like
```html
<div class="new-container">
    <div class="product-wrapper">
        <section class="products">
            <article class="product new-class" data-id="p1">
                <div class="product-info">
                    <h3>Product 1</h3>
                    <p class="new-description">Description 1</p>
                </div>
            </article>
            <article class="product new-class" data-id="p2">
                <div class="product-info">
                    <h3>Product 2</h3>
                    <p class="new-description">Description 2</p>
                </div>
            </article>
        </section>
    </div>
</div>
```
The selector will no longer function, and your code needs maintenance. That's where Scrapling's `adaptive` feature comes into play.

With Scrapling, you can enable the `adaptive` feature the first time you select an element, and the next time you select that element and it doesn't exist, Scrapling will remember its properties and search on the website for the element with the highest percentage of similarity to that element and without AI :)

```python
from scrapling import Selector, Fetcher
# Before the change
page = Selector(page_source, adaptive=True, url='example.com')
# or
Fetcher.adaptive = True
page = Fetcher.get('https://example.com')
# then
element = page.css('#p1', auto_save=True)
if not element:  # One day website changes?
    element = page.css('#p1', adaptive=True)  # Scrapling still finds it!
# the rest of your code...
```
Below, I will show you one usage example for this feature. Then, we will dive deep into how to use it and provide details about this feature. Note that it works with all selection methods, not just CSS/XPATH selection.

## Real-World Scenario
Let's use a real website as an example and use one of the fetchers to fetch its source. To achieve this, we need to identify a website that is about to update its design/structure, copy its source, and then wait for the website to change. Of course, that's nearly impossible to know unless I know the website's owner, but that will make it a staged test, haha.

To solve this issue, I will use [The Web Archive](https://archive.org/)'s [Wayback Machine](https://web.archive.org/). Here is a copy of [StackOverFlow's website in 2010](https://web.archive.org/web/20100102003420/http://stackoverflow.com/); pretty old, eh?</br>Let's see if the adaptive feature can extract the same button in the old design from 2010 and the current design using the same selector :)

If I want to extract the Questions button from the old design, I can use a selector like this: `#hmenus > div:nth-child(1) > ul > li:nth-child(1) > a`. This selector is too specific because it was generated by Google Chrome.


Now, let's test the same selector in both versions
```python
>> from scrapling import Fetcher
>> selector = '#hmenus > div:nth-child(1) > ul > li:nth-child(1) > a'
>> old_url = "https://web.archive.org/web/20100102003420/http://stackoverflow.com/"
>> new_url = "https://stackoverflow.com/"
>> Fetcher.configure(adaptive = True, adaptive_domain='stackoverflow.com')
>> 
>> page = Fetcher.get(old_url, timeout=30)
>> element1 = page.css_first(selector, auto_save=True)
>> 
>> # Same selector but used in the updated website
>> page = Fetcher.get(new_url)
>> element2 = page.css_first(selector, adaptive=True)
>> 
>> if element1.text == element2.text:
...    print('Scrapling found the same element in the old and new designs!')
'Scrapling found the same element in the old and new designs!'
```
Note that I introduced a new argument called `adaptive_domain`. This is because, for Scrapling, these are two different domains (`archive.org` and `stackoverflow.com`), so Scrapling will isolate their `adaptive` data. To inform Scrapling that they are the same website, we must pass the custom domain we wish to use while saving `adaptive` data for both, ensuring Scrapling doesn't isolate them.

The code will be the same in a real-world scenario, except it will use the same URL for both requests, so you won't need to use the `adaptive_domain` argument. This is the closest example I can give to real-world cases, so I hope it didn't confuse you :)

Hence, in the two examples above, I used both the `Selector` class and the `Fetcher` class to show you that the logic for adaptive is the same.

## How the adaptive scraping feature works
Adaptive scraping works in two phases:

1. **Save Phase**: Store unique properties of elements
2. **Match Phase**: Find elements with similar properties later

Let's say you've got an element through selection or any method and want the library to find it the next time you scrape this website, even if it undergoes structural/design changes. 

With as few technical details as possible, the general logic goes as follows:

  1. You tell Scrapling to save that element's unique properties in one of the ways we will show below.
  2. Scrapling uses its configured database (SQLite by default) and saves each element's unique properties.
  3. Now, because everything about the element can be changed or removed from the website's owner(s), nothing from the element can be used as a unique identifier for the database. To solve this issue, I made the storage system rely on two things:
     1. The domain of the current website. If you are using the `Selector` class, you should pass it while initializing the class, or if you are using one of the fetchers, the domain will be taken from the URL automatically.
     2. An `identifier` to query that element's properties from the database. You don't always have to set the identifier yourself, as you will see later when we discuss this.

     Together, they will be used to retrieve the element's unique properties from the database later.

  4. Later, when the website's structure changes, you tell Scrapling to find the element by enabling `adaptive`. Scrapling retrieves the element's unique properties and matches all elements on the page against the unique properties we already have for this element. A score is calculated for their similarity with the desired element. In that comparison, everything is taken into consideration, as you will see later 
  5. The element(s) with the highest similarity score to the wanted element are returned.

### The unique properties
You might wonder what unique properties we are referring to when discussing the removal or alteration of all element properties.

For Scrapling, the unique elements we are relying on are:

- Element tag name, text, attributes (names and values), siblings (tag names only), and path (tag names only).
- Element's parent tag name, attributes (names and values), and text.

But you need to understand that the comparison between elements is not exact; it's more about finding how similar these values are. So everything is considered, even the values' order, like the order in which the element class names were written before and the order in which the same element class names are written now.

## How to use adaptive feature
The adaptive feature can be applied to any found element, and it's added as arguments to CSS/XPath Selection methods, as you saw above, but we will get back to that later.

First, you must enable the `adaptive` feature by passing `adaptive=True` to the [Selector](main_classes.md#selector) class when you initialize it or enable it in the fetcher you are using of the available fetchers, as we will show.

Examples:
```python
>>> from scrapling import Selector, Fetcher
>>> page = Selector(html_doc, adaptive=True)
# OR
>>> Fetcher.adaptive = True
>>> page = Fetcher.fetch('https://example.com')
```
If you are using the [Selector](main_classes.md#selector) class, you need to pass the url of the website you are using with the argument `url` so Scrapling can separate the properties saved for each element by domain.

If you didn't pass a URL, the word `default` will be used in place of the URL field while saving the element's unique properties. So, this will only be an issue if you used the same identifier later for a different website and didn't pass the URL parameter while initializing it. The save process will overwrite the previous data, and the `adaptive` feature only uses the latest saved properties.

Besides those arguments, we have `storage` and `storage_args`. Both are for the class to be used to connect to the database; by default, it's set to the SQLite class that the library is using. Those arguments shouldn't matter unless you want to write your own storage system, which we will cover on a [separate page in the development section](../development/adaptive_storage_system.md).

Now, after enabling the `adaptive` feature globally, you have two main ways to use it.

### The CSS/XPath Selection way
As you have seen in the example above, first, you have to use the `auto_save` argument while selecting an element that exists on the page, like below
```python
element = page.css('#p1' auto_save=True)
```
And when the element doesn't exist, you can use the same selector and the `adaptive` argument, and the library will find it for you
```python
element = page.css('#p1', adaptive=True)
```
Pretty simple, eh?

Well, a lot happened under the hood here. Remember the identifier part we mentioned before that you need to set so you can retrieve the element you want? Here, with the `css`/`css_first`/`xpath`/`xpath_first` methods, the identifier is set automatically as the selector you passed here to make things easier :)

Additionally, for all these methods, you can pass the `identifier` argument to set it yourself. This is useful in some instances, or you can use it to save properties with the `auto_save` argument.

### The manual way
You manually save and retrieve an element, then relocate it, which all happens within the `adaptive` feature, as shown below. This allows you to relocate any element using any method or selection!

First, let's say you got an element like this by text:
```python
>>> element = page.find_by_text('Tipping the Velvet', first_match=True)
```
You can save its unique properties with the `save` method, like below, but you must set the identifier yourself. For this example, I chose `my_special_element` as an identifier, but it's best to use a meaningful identifier in your code for the same reason you use meaningful variable names :)
```python
>>> page.save(element, 'my_special_element')
```
Now, later, when you want to retrieve it and relocate it inside the page with `adaptive`, it would be like this
```python
>>> element_dict = page.retrieve('my_special_element')
>>> page.relocate(element_dict, selector_type=True)
[<data='<a href="catalogue/tipping-the-velvet_99...' parent='<h3><a href="catalogue/tipping-the-velve...'>]
>>> page.relocate(element_dict, selector_type=True).css('::text')
['Tipping the Velvet']
```
Hence, the `retrieve` and `relocate` methods are used.

If you want to keep it as a `lxml.etree` object, leave the `selector_type` argument
```python
>>> page.relocate(element_dict)
[<Element a at 0x105a2a7b0>]
```

## Troubleshooting

### No Matches Found
```python
# 1. Check if data was saved
element_data = page.retrieve('identifier')
if not element_data:
    print("No data saved for this identifier")

# 2. Try with different identifier
products = page.css('.product', adaptive=True, identifier='old_selector')

# 3. Save again with new identifier
products = page.css('.new-product', auto_save=True, identifier='new_identifier')
```

### Wrong Elements Matched
```python
# Use more specific selectors
products = page.css('.product-list .product', auto_save=True)

# Or save with more context
product = page.find_by_text('Product Name').parent
page.save(product, 'specific_product')
```

## Known Issues
In the `adaptive` save process, the unique properties of the first element from the selection results are the only ones that get saved. So if the selector you are using selects different elements on the page in other locations, `adaptive` will return the first element to you only when you relocate it later. This doesn't include combined CSS selectors (Using commas to combine more than one selector, for example), as these selectors get separated, and each selector gets executed alone.

## Final thoughts
Explaining this feature in detail without complications turned out to be challenging. However, still, if there's something left unclear, you can head out to the [discussions section](https://github.com/D4Vinci/Scrapling/discussions), and I will reply to you ASAP, or the Discord server, or reach out to me privately and have a chat :)

----------------------------------------


## File: parsing/main_classes.md
<!-- Source: docs/parsing/main_classes.md -->

## Introduction

> 💡 **Prerequisites:**
> 
> - You’ve completed or read the [Querying elements](../parsing/selection.md) page to understand how to find/extract elements from the [Selector](../parsing/main_classes.md#selector) object.
> <br><br>

After exploring the various ways to select elements with Scrapling and its related features, let's take a step back and examine the [Selector](#selector) class in general, as well as other objects, to gain a better understanding of the parsing engine.

The [Selector](#selector) class is the core parsing engine in Scrapling, providing HTML parsing and element selection capabilities. You can always import it with any of the following imports
```python
from scrapling import Selector
from scrapling.parser import Selector
```
Then use it directly as you already learned in the [overview](../overview.md) page
```python
page = Selector(
    '<html>...</html>',
    url='https://example.com'
)

# Then select elements as you like
elements = page.css('.product')
```
In Scrapling, the main object you deal with after passing an HTML source or fetching a website is, of course, a [Selector](#selector) object. Any operation you do, like selection, navigation, etc., will return either a [Selector](#selector) object or a [Selectors](#selectors) object, given that the result is element/elements from the page, not text or similar.

In other words, the main page is a [Selector](#selector) object, and the elements within are [Selector](#selector) objects, and so on. Any text, such as the text content inside elements or the text inside element attributes, is a [TextHandler](#texthandler) object, and the attributes of each element are stored as [AttributesHandler](#attributeshandler). We will return to both objects later, so let's focus on the [Selector](#selector) object.

## Selector
### Arguments explained
The most important one is `content`, it's used to pass the HTML code you want to parse, and it accepts the HTML content as `str` or `bytes`.

Otherwise, you have the arguments `url`, `adaptive`, `storage`, and `storage_args`. All these arguments are settings used with the `adaptive` feature, and they don't make a difference if you are not going to use that feature, so just ignore them for now, and we will explain them in the [adaptive](adaptive.md) feature page.

Then you have the arguments for parsing adjustments or adjusting/manipulating the HTML content while the library is parsing it:

- **encoding**: This is the encoding that will be used while parsing the HTML. The default is `UTF-8`.
- **keep_comments**: This tells the library whether to keep HTML comments while parsing the page. It's disabled by default because it can cause issues with your scraping in various ways.
- **keep_cdata**: Same logic as the HTML comments. [cdata](https://stackoverflow.com/questions/7092236/what-is-cdata-in-html) is removed by default for cleaner HTML.

I have intended to ignore the arguments `huge_tree` and `root` to avoid making this page more complicated than needed.
You may notice that I'm doing that a lot because it involves advanced features that you don't need to know to use the library. The development section will cover these missing parts if you are very invested.

After that, for the main page and elements within, most properties are lazily loaded. This means they don't get initialized until you use them like the text content of a page/element, and this is one of the reasons for Scrapling speed :)

### Properties
You have already seen much of this on the [overview](../overview.md) page, but don't worry if you didn't. We will review it more thoroughly using more advanced methods/usages. For clarity, the properties for traversal are separated below in the [traversal](#traversal) section.

Let's say we are parsing this HTML page for simplicity:
```html
<html>
  <head>
    <title>Some page</title>
  </head>
  <body>
    <div class="product-list">
      <article class="product" data-id="1">
        <h3>Product 1</h3>
        <p class="description">This is product 1</p>
        <span class="price">$10.99</span>
        <div class="hidden stock">In stock: 5</div>
      </article>
    
      <article class="product" data-id="2">
        <h3>Product 2</h3>
        <p class="description">This is product 2</p>
        <span class="price">$20.99</span>
        <div class="hidden stock">In stock: 3</div>
      </article>
    
      <article class="product" data-id="3">
        <h3>Product 3</h3>
        <p class="description">This is product 3</p>
        <span class="price">$15.99</span>
        <div class="hidden stock">Out of stock</div>
      </article>
    </div>

    <script id="page-data" type="application/json">
      {
        "lastUpdated": "2024-09-22T10:30:00Z",
        "totalProducts": 3
      }
    </script>
  </body>
</html>
```
Load the page directly as shown before:
```python
from scrapling import Selector
page = Selector(html_doc)
```
Get all text content on the page recursively
```python
>>> page.get_all_text()
'Some page\n\n    \n\n      \nProduct 1\nThis is product 1\n$10.99\nIn stock: 5\nProduct 2\nThis is product 2\n$20.99\nIn stock: 3\nProduct 3\nThis is product 3\n$15.99\nOut of stock'
```
Get the first article, as explained before; we will use it as an example
```python
article = page.find('article')
```
With the same logic, get all text content on the element recursively
```python
>>> article.get_all_text()
'Product 1\nThis is product 1\n$10.99\nIn stock: 5'
```
But if you try to get the direct text content, it will be empty because it doesn't have direct text in the HTML code above
```python
>>> article.text
''
```
The `get_all_text` method has the following optional arguments:

1. **separator**: All strings collected will be concatenated using this separator. The default is '\n'
2. **strip**: If enabled, strings will be stripped before concatenation. Disabled by default.
3. **ignore_tags**: A tuple of all tag names you want to ignore in the final results and ignore any elements nested within them. The default is `('script', 'style',)`.
4. **valid_values**: If enabled, the method will only collect elements with real values, so all elements with empty text content or only whitespaces will be ignored. It's enabled by default

By the way, the text returned here is not a standard string but a [TextHandler](#texthandler); we will get to this in detail later, so if the text content can be serialized to JSON, use `.json()` on it
```python
>>> script = page.find('script')
>>> script.json()
{'lastUpdated': '2024-09-22T10:30:00Z', 'totalProducts': 3}
```
Let's continue to get the element tag
```python
>>> article.tag
'article'
```
If you use it on the page directly, you will find that you are operating on the root `html` element
```python
>>> page.tag
'html'
```
Now, I think I hammered the (`page`/`element`) idea, so I won't return to it again.

Getting the attributes of the element
```python
>>> print(article.attrib)
{'class': 'product', 'data-id': '1'}
```
Access a specific attribute with any of the following
```python
>>> article.attrib['class']
>>> article.attrib.get('class')
>>> article['class']  # new in v0.3
```
Check if the attributes contain a specific attribute with any of the methods below
```python
>>> 'class' in article.attrib
>>> 'class' in article  # new in v0.3
```
Get the HTML content of the element
```python
>>> article.html_content
'<article class="product" data-id="1"><h3>Product 1</h3>\n        <p class="description">This is product 1</p>\n        <span class="price">$10.99</span>\n        <div class="hidden stock">In stock: 5</div>\n      </article>'
```
Get the prettified version of the element's HTML content
```python
print(article.prettify())
```
```html
<article class="product" data-id="1"><h3>Product 1</h3>
    <p class="description">This is product 1</p>
    <span class="price">$10.99</span>
    <div class="hidden stock">In stock: 5</div>
</article>
```
Use the `.body` property to get the raw content of the page
```python
>>> page.body
'<html>\n  <head>\n    <title>Some page</title>\n  </head>\n  <body>\n    <div class="product-list">\n      <article class="product" data-id="1">\n        <h3>Product 1</h3>\n        <p class="description">This is product 1</p>\n        <span class="price">$10.99</span>\n        <div class="hidden stock">In stock: 5</div>\n      </article>\n\n      <article class="product" data-id="2">\n        <h3>Product 2</h3>\n        <p class="description">This is product 2</p>\n        <span class="price">$20.99</span>\n        <div class="hidden stock">In stock: 3</div>\n      </article>\n\n      <article class="product" data-id="3">\n        <h3>Product 3</h3>\n        <p class="description">This is product 3</p>\n        <span class="price">$15.99</span>\n        <div class="hidden stock">Out of stock</div>\n      </article>\n    </div>\n\n    <script id="page-data" type="application/json">\n      {\n        "lastUpdated": "2024-09-22T10:30:00Z",\n        "totalProducts": 3\n      }\n    </script>\n  </body>\n</html>'
```
To get all the ancestors in the DOM tree of this element
```python
>>> article.path
[<data='<div class="product-list"> <article clas...' parent='<body> <div class="product-list"> <artic...'>,
 <data='<body> <div class="product-list"> <artic...' parent='<html><head><title>Some page</title></he...'>,
 <data='<html><head><title>Some page</title></he...'>]
```
Generate a CSS shortened selector if possible, or generate the full selector
```python
>>> article.generate_css_selector
'body > div > article'
>>> article.generate_full_css_selector
'body > div > article'
```
Same case with XPath
```python
>>> article.generate_xpath_selector
"//body/div/article"
>>> article.generate_full_xpath_selector
"//body/div/article"
```

### Traversal
Using the elements we found above, we will go over the properties/methods for moving on the page in detail.

If you are unfamiliar with the DOM tree or the tree data structure in general, the following traversal part can be confusing. I recommend you look up these concepts online for a better understanding.

If you are too lazy to search about it, here's a quick explanation to give you a good idea.<br/>
In simple words, the `html` element is the root of the website's tree, as every page starts with an `html` element.<br/>
This element will be positioned directly above elements such as `head` and `body`. These are considered "children" of the `html` element, and the `html` element is considered their "parent". The element `body` is a "sibling" of the element `head` and vice versa.

Accessing the parent of an element
```python
>>> article.parent
<data='<div class="product-list"> <article clas...' parent='<body> <div class="product-list"> <artic...'>
>>> article.parent.tag
'div'
```
You can chain it as you want, which applies to all similar properties/methods we will review.
```python
>>> article.parent.parent.tag
'body'
```
Get the children of an element
```python
>>> article.children
[<data='<h3>Product 1</h3>' parent='<article class="product" data-id="1"><h3...'>,
 <data='<p class="description">This is product 1...' parent='<article class="product" data-id="1"><h3...'>,
 <data='<span class="price">$10.99</span>' parent='<article class="product" data-id="1"><h3...'>,
 <data='<div class="hidden stock">In stock: 5</d...' parent='<article class="product" data-id="1"><h3...'>]
```
Get all elements underneath an element. It acts as a nested version of the `children` property
```python
>>> article.below_elements
[<data='<h3>Product 1</h3>' parent='<article class="product" data-id="1"><h3...'>,
 <data='<p class="description">This is product 1...' parent='<article class="product" data-id="1"><h3...'>,
 <data='<span class="price">$10.99</span>' parent='<article class="product" data-id="1"><h3...'>,
 <data='<div class="hidden stock">In stock: 5</d...' parent='<article class="product" data-id="1"><h3...'>]
```
This element returns the same result as the `children` property because its children don't have children.

Another example of using the element with the `product-list` class will clear the difference between the `children` property and the `below_elements` property
```python
>>> products_list = page.css_first('.product-list')
>>> products_list.children
[<data='<article class="product" data-id="1"><h3...' parent='<div class="product-list"> <article clas...'>,
 <data='<article class="product" data-id="2"><h3...' parent='<div class="product-list"> <article clas...'>,
 <data='<article class="product" data-id="3"><h3...' parent='<div class="product-list"> <article clas...'>]

>>> products_list.below_elements
[<data='<article class="product" data-id="1"><h3...' parent='<div class="product-list"> <article clas...'>,
 <data='<h3>Product 1</h3>' parent='<article class="product" data-id="1"><h3...'>,
 <data='<p class="description">This is product 1...' parent='<article class="product" data-id="1"><h3...'>,
 <data='<span class="price">$10.99</span>' parent='<article class="product" data-id="1"><h3...'>,
 <data='<div class="hidden stock">In stock: 5</d...' parent='<article class="product" data-id="1"><h3...'>,
 <data='<article class="product" data-id="2"><h3...' parent='<div class="product-list"> <article clas...'>,
...]
```
Get the siblings of an element
```python
>>> article.siblings
[<data='<article class="product" data-id="2"><h3...' parent='<div class="product-list"> <article clas...'>,
 <data='<article class="product" data-id="3"><h3...' parent='<div class="product-list"> <article clas...'>]
```
Get the next element of the current element
```python
>>> article.next
<data='<article class="product" data-id="2"><h3...' parent='<div class="product-list"> <article clas...'>
```
The same logic applies to the `previous` property
```python
>>> article.previous  # It's the first child, so it doesn't have a previous element
>>> second_article = page.css_first('.product[data-id="2"]')
>>> second_article.previous
<data='<article class="product" data-id="1"><h3...' parent='<div class="product-list"> <article clas...'>
```
You can check easily and pretty fast if an element has a specific class name or not
```python
>>> article.has_class('product')
True
```
If your case needs more than the element's parent, you can iterate over the whole ancestors' tree of any element, like the example below
```python
for ancestor in article.iterancestors():
    # do something with it...
```
You can search for a specific ancestor of an element that satisfies a search function; all you need to do is to pass a function that takes a [Selector](#selector) object as an argument and return `True` if the condition satisfies or `False` otherwise, like below:
```python
>>> article.find_ancestor(lambda ancestor: ancestor.has_class('product-list'))
<data='<div class="product-list"> <article clas...' parent='<body> <div class="product-list"> <artic...'>

>>> article.find_ancestor(lambda ancestor: ancestor.css('.product-list'))  # Same result, different approach
<data='<div class="product-list"> <article clas...' parent='<body> <div class="product-list"> <artic...'>
```
## Selectors
The class `Selectors` is the "List" version of the [Selector](#selector) class. It inherits from the Python standard `List` type, so it shares all `List` properties and methods while adding more methods to make the operations you want to execute on the [Selector](#selector) instances within more straightforward.

In the [Selector](#selector) class, all methods/properties that should return a group of elements return them as a [Selectors](#selectors) class instance. The only exceptions are when you use the CSS/XPath methods as follows:

- If you selected a text node with the selector, then the return type will be [TextHandler](#texthandler)/[TextHandlers](#texthandlers). <br/>Examples:
    ```python
    >>> page.css('a::text')              # -> TextHandlers
    >>> page.xpath('//a/text()')         # -> TextHandlers
    >>> page.css_first('a::text')        # -> TextHandler
    >>> page.xpath_first('//a/text()')   # -> TextHandler
    >>> page.css('a::attr(href)')        # -> TextHandlers
    >>> page.xpath('//a/@href')          # -> TextHandlers
    >>> page.css_first('a::attr(href)')  # -> TextHandler
    >>> page.xpath_first('//a/@href')    # -> TextHandler
    ```
- If you used a combined selector that returns mixed types, the result will be a Python standard `List`. <br/>Examples:
  ```python
  >>> page.css('.price_color')                               # -> Selectors
  >>> page.css('.product_pod a::attr(href)')                # -> TextHandlers
  >>> page.css('.price_color, .product_pod a::attr(href)')  # -> List
  ```

Let's see what [Selectors](#selectors) class adds to the table with that out of the way.
### Properties
Apart from the normal operations on Python lists, such as iteration and slicing, etc.

You can do the following:

Execute CSS and XPath selectors directly on the [Selector](#selector) instances it has, while the arguments and the return types are the same as [Selector](#selector)'s `css` and `xpath` methods. This, of course, makes chaining methods very straightforward.
```python
>>> page.css('.product_pod a')
[<data='<a href="catalogue/a-light-in-the-attic_...' parent='<div class="image_container"> <a href="c...'>,
 <data='<a href="catalogue/a-light-in-the-attic_...' parent='<h3><a href="catalogue/a-light-in-the-at...'>,
 <data='<a href="catalogue/tipping-the-velvet_99...' parent='<div class="image_container"> <a href="c...'>,
 <data='<a href="catalogue/tipping-the-velvet_99...' parent='<h3><a href="catalogue/tipping-the-velve...'>,
 <data='<a href="catalogue/soumission_998/index....' parent='<div class="image_container"> <a href="c...'>,
 <data='<a href="catalogue/soumission_998/index....' parent='<h3><a href="catalogue/soumission_998/in...'>,
...]

>>> page.css('.product_pod').css('a')  # Returns the same result
[<data='<a href="catalogue/a-light-in-the-attic_...' parent='<div class="image_container"> <a href="c...'>,
 <data='<a href="catalogue/a-light-in-the-attic_...' parent='<h3><a href="catalogue/a-light-in-the-at...'>,
 <data='<a href="catalogue/tipping-the-velvet_99...' parent='<div class="image_container"> <a href="c...'>,
 <data='<a href="catalogue/tipping-the-velvet_99...' parent='<h3><a href="catalogue/tipping-the-velve...'>,
 <data='<a href="catalogue/soumission_998/index....' parent='<div class="image_container"> <a href="c...'>,
 <data='<a href="catalogue/soumission_998/index....' parent='<h3><a href="catalogue/soumission_998/in...'>,
...]
```
Run the `re` and `re_first` methods directly. They take the same arguments passed to the [Selector](#selector) class. I will still leave these methods to be explained in the [TextHandler](#texthandler) section below.

However, in this class, the `re_first` behaves differently as it runs `re` on each [Selector](#selector) within and returns the first one with a result. The `re` method will return a [TextHandlers](#texthandlers) object as normal, which combines all the [TextHandler](#texthandler) instances into one [TextHandlers](#texthandlers) instance.
```python
>>> page.css('.price_color').re(r'[\d\.]+')
['51.77',
 '53.74',
 '50.10',
 '47.82',
 '54.23',
...]

>>> page.css('.product_pod h3 a::attr(href)').re(r'catalogue/(.*)/index.html')
['a-light-in-the-attic_1000',
 'tipping-the-velvet_999',
 'soumission_998',
 'sharp-objects_997',
...]
```
With the `search` method, you can search quickly in the available [Selector](#selector) instances. The function you pass must accept a [Selector](#selector) instance as the first argument and return True/False. The method will return the first [Selector](#selector) instance that satisfies the function; otherwise, it will return `None`.
```python
# Find all the products with price '53.23'
>>> search_function = lambda p: float(p.css('.price_color').re_first(r'[\d\.]+')) == 54.23
>>> page.css('.product_pod').search(search_function)
<data='<article class="product_pod"><div class=...' parent='<li class="col-xs-6 col-sm-4 col-md-3 co...'>
```
You can use the `filter` method, too, which takes a function like the `search` method but returns an `Selectors` instance of all the [Selector](#selector) instances that satisfy the function
```python
# Find all products with prices over $50
>>> filtering_function = lambda p: float(p.css('.price_color').re_first(r'[\d\.]+')) > 50
>>> page.css('.product_pod').filter(filtering_function)
[<data='<article class="product_pod"><div class=...' parent='<li class="col-xs-6 col-sm-4 col-md-3 co...'>,
 <data='<article class="product_pod"><div class=...' parent='<li class="col-xs-6 col-sm-4 col-md-3 co...'>,
 <data='<article class="product_pod"><div class=...' parent='<li class="col-xs-6 col-sm-4 col-md-3 co...'>,
...]
```
If you are too lazy like me and want to know the number of [Selector](#selector) instances in a [Selectors](#selectors) instance. You can do this:
```python
page.css('.product_pod').length
```
instead of this
```python
len(page.css('.product_pod'))
```
Yup, like JavaScript :)

## TextHandler
This class is mandatory to understand, as all methods/properties that should return a string for you will return `TextHandler`, and the ones that should return a list of strings will return [TextHandlers](#texthandlers) instead.

TextHandler is a subclass of the standard Python string, so you can do anything with it that you can do with a Python string. So, what is the difference that requires a different naming?

Of course, TextHandler provides extra methods and properties that standard Python strings can't do. We will review them now, but remember that all methods and properties in all classes that return string(s) return TextHandler, which opens the door for creativity and makes the code shorter and cleaner, as you will see. Also, you can import it directly and use it on any string, which we will explain [later](../development/scrapling_custom_types.md).
### Usage
First, before discussing the added methods, you need to know that all operations on it, like slicing, accessing by index, etc., and methods like `split`, `replace`, `strip`, etc., all return a `TextHandler` again, so you can chain them as you want. If you find a method or property that returns a standard string instead of `TextHandler`, please open an issue, and we will override it as well.

First, we start with the `re` and `re_first` methods. These are the same methods that exist in the other classes ([Selector](#selector), [Selectors](#selectors), and [TextHandlers](#texthandlers)), so they will accept the same arguments as well.

- The `re` method takes a string/compiled regex pattern as the first argument. It searches the data for all strings matching the regex and returns them as a [TextHandlers](#texthandlers) instance. The `re_first` method takes the same arguments and behaves similarly, but as you probably figured out from the naming, it returns the first result only as a `TextHandler` instance.
    
    Also, it takes other helpful arguments, which are:
    
    - **replace_entities**: This is enabled by default. It replaces character entity references with their corresponding characters.
    - **clean_match**: It's disabled by default. This causes the method to ignore all whitespace and consecutive spaces while matching.
    - **case_sensitive**: It's enabled by default. As the name implies, disabling it will cause the regex to ignore the case of letters while compiling.
  
    You have seen these examples before; the return result is [TextHandlers](#texthandlers) because we used the `re` method.
    ```python
    >>> page.css('.price_color').re(r'[\d\.]+')
    ['51.77',
     '53.74',
     '50.10',
     '47.82',
     '54.23',
    ...]
    
    >>> page.css('.product_pod h3 a::attr(href)').re(r'catalogue/(.*)/index.html')
    ['a-light-in-the-attic_1000',
     'tipping-the-velvet_999',
     'soumission_998',
     'sharp-objects_997',
    ...]
    ```
    To explain the other arguments better, we will use a custom string for each example below
    ```python
    >>> from scrapling import TextHandler
    >>> test_string = TextHandler('hi  there')  # Hence the two spaces
    >>> test_string.re('hi there')
    >>> test_string.re('hi there', clean_match=True)  # Using `clean_match` will clean the string before matching the regex
    ['hi there']
    
    >>> test_string2 = TextHandler('Oh, Hi Mark')
    >>> test_string2.re_first('oh, hi Mark')
    >>> test_string2.re_first('oh, hi Mark', case_sensitive=False)  # Hence disabling `case_sensitive`
    'Oh, Hi Mark'
    
    # Mixing arguments
    >>> test_string.re('hi there', clean_match=True, case_sensitive=False)
    ['hi There']
    ```
    Another use of the idea of replacing strings with `TextHandler` everywhere is that a property like `html_content` returns `TextHandler`, so you can do regex on the HTML content if you want:
    ```python
    >>> page.html_content.re('div class=".*">(.*)</div')
    ['In stock: 5', 'In stock: 3', 'Out of stock']
    ```

- You also have the `.json()` method, which tries to convert the content to a JSON object quickly if possible; otherwise, it throws an error
  ```python
  >>> page.css_first('#page-data::text')
    '\n      {\n        "lastUpdated": "2024-09-22T10:30:00Z",\n        "totalProducts": 3\n      }\n    '
  >>> page.css_first('#page-data::text').json()
    {'lastUpdated': '2024-09-22T10:30:00Z', 'totalProducts': 3}
  ```
  Hence, if you didn't specify a text node while selecting an element (like the text content or an attribute text content), the text content will be selected automatically, like this
  ```python
  >>> page.css_first('#page-data').json()
  {'lastUpdated': '2024-09-22T10:30:00Z', 'totalProducts': 3}
  ```
  The [Selector](#selector) class adds one thing here, too; let's say this is the page we are working with:
  ```html
  <html>
      <body>
          <div>
            <script id="page-data" type="application/json">
              {
                "lastUpdated": "2024-09-22T10:30:00Z",
                "totalProducts": 3
              }
            </script>
          </div>
      </body>
  </html>
  ```
  The [Selector](#selector) class has the `get_all_text` method, which you should be aware of by now. This method returns a `TextHandler`, of course.<br/><br/>
  So, as you know here, if you did something like this
  ```python
  >>> page.css_first('div::text').json()
  ```
  You will get an error because the `div` tag doesn't have direct text content that can be serialized to JSON; it actually doesn't have direct text content at all.<br/><br/>
  In this case, the `get_all_text` method comes to the rescue, so you can do something like that
  ```python
  >>> page.css_first('div').get_all_text(ignore_tags=[]).json()
    {'lastUpdated': '2024-09-22T10:30:00Z', 'totalProducts': 3}
  ```
  I used the `ignore_tags` argument here because the default value of it is `('script', 'style',)`, as you are aware.<br/><br/>
  Another related behavior to be aware of occurs when using any of the fetchers, which we will explain later. If you have a JSON response like this example:
  ```python
  >>> page = Selector("""{"some_key": "some_value"}""")
  ```
  Because the [Selector](#selector) class is optimized to deal with HTML pages, it will deal with it as a broken HTML response and fix it, so if you used the `html_content` property, you get this
  ```python
  >>> page.html_content
  '<html><body><p>{"some_key": "some_value"}</p></body></html>'
  ```
  Here, you can use the `json` method directly, and it will work
  ```python
  >>> page.json()
  {'some_key': 'some_value'}
  ```
  You might wonder how this happened, given that the `html` tag doesn't contain direct text.<br/>
  Well, for cases like JSON responses, I made the [Selector](#selector) class maintain a raw copy of the content passed to it. This way, when you use the `.json()` method, it checks for that raw copy and then converts it to JSON. If the raw copy is not available like the case with the elements, it checks for the current element text content, or otherwise it used the `get_all_text` method directly.<br/><br/>This might sound hacky a bit but remember, Scrapling is currently optimized to work with HTML pages only so that's the best way till now to handle JSON responses currently without sacrificing speed. This will be changed in the upcoming versions.

- Another handy method is `.clean()`, which will remove all white spaces and consecutive spaces for you and return a new `TextHandler` instance
```python
>>> TextHandler('\n wonderful  idea, \reh?').clean()
'wonderful idea, eh?'
```
Also, you can pass `remove_entities` argument to make `clean` replace HTML entities with their corresponding characters.

- Another method that might be helpful in some cases is the `.sort()` method to sort the string for you, as you do with lists
```python
>>> TextHandler('acb').sort()
'abc'
```
Or do it in reverse:
```python
>>> TextHandler('acb').sort(reverse=True)
'cba'
```

Other methods and properties will be added over time, but remember that this class is returned in place of strings nearly everywhere in the library.

## TextHandlers
You probably guessed it: This class is similar to [Selectors](#selectors) and [Selector](#selector), but here it inherits the same logic and method as standard lists, with only `re` and `re_first` as new methods.

The only difference is that the `re_first` method logic here does `re` on each [TextHandler](#texthandler) within and returns the first result it has or `None`. Nothing new needs to be explained here, but new methods will be added over time.

## AttributesHandler
This is a read-only version of Python's standard dictionary, or `dict`, that is used solely to store the attributes of each element or each [Selector](#selector) instance.
```python
>>> print(page.find('script').attrib)
{'id': 'page-data', 'type': 'application/json'}
>>> type(page.find('script').attrib).__name__
'AttributesHandler'
```
Because it's read-only, it will use fewer resources than the standard dictionary. Still, it has the same dictionary method and properties, except those that allow you to modify/override the data.

It currently adds two extra simple methods:

- The `search_values` method

    In standard dictionaries, you can do `dict.get("key_name")` to check if a key exists. However, if you want to search by values instead of keys, it will require some additional code lines. This method does that for you. It allows you to search the current attributes by values and returns a dictionary of each matching item.
    
    A simple example would be
    ```python
    >>> for i in page.find('script').attrib.search_values('page-data'):
            print(i)
    {'id': 'page-data'}
    ```
    But this method provides the `partial` argument as well, which allows you to search by part of the value:
    ```python
    >>> for i in page.find('script').attrib.search_values('page', partial=True):
            print(i)
    {'id': 'page-data'}
    ```
    These examples won't happen in the real world; most likely, a more real-world example would be using it with the `find_all` method to find all elements that have a specific value in their arguments:
    ```python
    >>> page.find_all(lambda element: list(element.attrib.search_values('product')))
    [<data='<article class="product" data-id="1"><h3...' parent='<div class="product-list"> <article clas...'>,
     <data='<article class="product" data-id="2"><h3...' parent='<div class="product-list"> <article clas...'>,
     <data='<article class="product" data-id="3"><h3...' parent='<div class="product-list"> <article clas...'>]
    ```
    All these elements have 'product' as a value for the attribute `class`.
    
    Hence, I used the `list` function here because `search_values` returns a generator, so it would be `True` for all elements.

- The `json_string` property

    This property converts current attributes to a JSON string if the attributes are JSON serializable; otherwise, it throws an error
  
    ```python
    >>>page.find('script').attrib.json_string
    b'{"id":"page-data","type":"application/json"}'
    ```

----------------------------------------


## File: parsing/selection.md
<!-- Source: docs/parsing/selection.md -->

## Introduction
Scrapling currently supports parsing HTML pages exclusively, so it doesn't support XML feeds. This decision was made because the adaptive feature won't work with XML, but that might change soon, so stay tuned :)

In Scrapling, there are five main ways to find elements:

1. CSS3 Selectors
2. XPath Selectors
3. Finding elements based on filters/conditions.
4. Finding elements whose content contains a specific text
5. Finding elements whose content matches a specific regex

Of course, there are other indirect ways to find elements with Scrapling, but here we will discuss the main ways in detail. We will also bring up one of the most remarkable features of Scrapling: the ability to find elements that are similar to the element you have; you can jump to that section directly from [here](#finding-similar-elements).

If you are new to Web Scraping, have little to no experience writing selectors, and want to start quickly, I recommend you jump directly to learning the `find`/`find_all` methods from [here](#filters-based-searching).

## CSS/XPath selectors

### What are CSS selectors?
[CSS](https://en.wikipedia.org/wiki/CSS) is a language for applying styles to HTML documents. It defines selectors to associate those styles with specific HTML elements.

Scrapling implements CSS3 selectors as described in the [W3C specification](http://www.w3.org/TR/2011/REC-css3-selectors-20110929/). CSS selectors support comes from `cssselect`, so it's better to read about which [selectors are supported from cssselect](https://cssselect.readthedocs.io/en/latest/#supported-selectors) and pseudo-functions/elements.

Also, Scrapling implements some non-standard pseudo-elements like:

* To select text nodes, use ``::text``
* To select attribute values, use ``::attr(name)`` where name is the name of the attribute that you want the value of

In short, if you come from Scrapy/Parsel, you will find the same logic for selectors here to make it easier. No need to implement a stranger logic to the one that most of us are used to :)

To select elements with CSS selectors, you have the `css` and `css_first` methods. The latter is ~10% faster and more valuable when you are interested in the first element it finds, or if it's just one element, etc. It's beneficial when there's more than one, as it returns `Selectors`.

### What are XPath selectors?
[XPath](https://en.wikipedia.org/wiki/XPath) is a language for selecting nodes in XML documents, which can also be used with HTML. This [cheatsheet](https://devhints.io/xpath) is a good resource for learning about [XPath](https://en.wikipedia.org/wiki/XPath). Scrapling adds XPath selectors directly through [lxml](https://lxml.de/).

In short, it is the same situation as CSS Selectors; if you come from Scrapy/Parsel, you will find the same logic for selectors here. However, Scrapling doesn't implement the XPath extension function `has-class` as Scrapy/Parsel does. Instead, it provides the `has_class` method, which can be used on elements returned for the same purpose.

To select elements with XPath selectors, you have the `xpath` and `xpath_first` methods. Again, these methods follow the same logic as the CSS selectors methods above, and `xpath_first` is faster.

> Note that each method of `css`, `css_first`, `xpath`, and `xpath_first` has additional arguments, but we didn't explain them here as they are all about the adaptive feature. The adaptive feature will have its own page later to be described in detail.

### Selectors examples
Let's see some shared examples of using CSS and XPath Selectors.

Select all elements with the class `product`
```python
products = page.css('.product')
products = page.xpath('//*[@class="product"]')
```
Note: The XPath one won't be accurate if there's another class; **it's always better to rely on CSS for selecting by class**

Select the first element with the class `product`
```python
product = page.css_first('.product')
product = page.xpath_first('//*[@class="product"]')
```
Which would be the same as doing (but a bit slower)
```python
product = page.css('.product')[0]
product = page.xpath('//*[@class="product"]')[0]
```
Get the text of the first element with the `h1` tag name
```python
title = page.css_first('h1::text')
title = page.xpath_first('//h1//text()')
```
Which is again the same as doing
```python
title = page.css_first('h1').text
title = page.xpath_first('//h1').text
```
Get the `href` attribute of the first element with the `a` tag name 
```python
link = page.css_first('a::attr(href)')
link = page.xpath_first('//a/@href')
```
Select the text of the first element with the `h1` tag name, which contains 'Phone', and under an element with class 'product'
```python
title = page.css_first('.product h1:contains("Phone")::text')
title = page.page.xpath_first('//*[@class="product"]//h1[contains(text(),"Phone")]/text()')
```
You can nest and chain selectors as you want, given that it returns results
```python
page.css_first('.product').css_first('h1:contains("Phone")::text')
page.xpath_first('//*[@class="product"]').xpath_first('//h1[contains(text(),"Phone")]/text()')
page.xpath_first('//*[@class="product"]').css_first('h1:contains("Phone")::text')
```
Another example

All links that have 'image' in their 'href' attribute
```python
links = page.css('a[href*="image"]')
links = page.xpath('//a[contains(@href, "image")]')
for index, link in enumerate(links):
    link_value = link.attrib['href']  # Cleaner than link.css('::attr(href)')
    link_text = link.text
    print(f'Link number {index} points to this url {link_value} with text content as "{link_text}"')
```

## Text-content selection
Scrapling provides the ability to select elements based on their direct text content, and you have two ways to do this:

1. Elements whose direct text content contains the given text with many options through the `find_by_text` method.
2. Elements whose direct text content matches the given regex pattern with many options through the `find_by_regex` method.

What you can do with `find_by_text` can be done with `find_by_regex` if you are good enough with regular expressions (regex), but we are providing more options to make them easier for all users to access.

With `find_by_text`, you will pass the text as the first argument; with the `find_by_regex` method, the regex pattern is the first argument. Both methods share the following arguments:

* **first_match**: If `True` (the default), the method used will return the first result it finds.
* **case_sensitive**: If `True`, the case of the letters will be considered.
* **clean_match**: If `True`, all whitespaces and consecutive spaces will be replaced with a single space before matching.

By default, Scrapling searches for the exact matching of the text/pattern you pass to `find_by_text`, so the text content of the wanted element has to be ONLY the text you input, but that's why it also has one extra argument, which is:

* **partial**: If enabled, `find_by_text` will return elements that contain the input text. So it's not an exact match anymore

Note: The method `find_by_regex` can accept both regular strings and a compiled regex pattern as its first argument, as you will see in the upcoming examples.

### Finding Similar Elements
One of the most remarkable new features that Scrapling puts on the table is the feature that allows the user to tell Scrapling to find elements similar to the element at hand. This feature's inspiration came from the AutoScraper library, but in Scrapling, it can be used on elements found by any method. Most of its usage would likely occur after finding elements through text content, similar to how AutoScraper works, making it convenient to explain here.

So, how does it work?

Imagine a scenario where you found a product by its title, for example, and you want to extract other products listed in the same table/container. With the element you have, you can call the method `.find_similar()` on it, and Scrapling will:

1. Find all page elements with the same DOM tree depth as this element. 
2. All found elements will be checked, and those without the same tag name, parent tag name, and grandparent tag name will be dropped.
3. Now we are sure (like 99% sure) that these elements are the ones we want, but as a last check, Scrapling will use fuzzy matching to drop the elements whose attributes don't look like the attributes of our element. There's a percentage to control this step, and I recommend you not play with it unless the default settings don't get the elements you want.

That's a lot of talking, I know, but I had to go deep. I will give examples of using this method in the next section, but first, these are the arguments that can be passed to this method:

* **similarity_threshold**: This is the percentage we discussed in step 3 for comparing elements' attributes. The default value is 0.2. In Simpler words, the values of the attributes of both elements should be at least 20% similar. If you want to turn off this check (Step 3, basically), you can set this attribute to 0, but I recommend you read what the other arguments do first.
* **ignore_attributes**: The attribute names passed will be ignored while matching the attributes in the last step. The default value is `('href', 'src',)` because URLs can change a lot between elements, making them unreliable.
* **match_text**: If `True`, the element's text content will be considered when matching (Step 3). Using this argument in typical cases is not recommended, but it depends.

Now, let's check out the examples below.

### Examples
Let's see some shared examples of finding elements with raw text and regex.

I will use the `Fetcher` class with these examples, but it will be explained in detail later.
```python
from scrapling.fetchers import Fetcher
page = Fetcher.get('https://books.toscrape.com/index.html')
```
Find the first element whose text fully matches this text
```python
>>> page.find_by_text('Tipping the Velvet')
<data='<a href="catalogue/tipping-the-velvet_99...' parent='<h3><a href="catalogue/tipping-the-velve...'>
```
Combining it with `page.urljoin` to return the full URL from the relative `href`
```python
>>> page.find_by_text('Tipping the Velvet').attrib['href']
'catalogue/tipping-the-velvet_999/index.html'
>>> page.urljoin(page.find_by_text('Tipping the Velvet').attrib['href'])
'https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html'
```
Get all matches if there are more (notice it returns a list)
```python
>>> page.find_by_text('Tipping the Velvet', first_match=False)
[<data='<a href="catalogue/tipping-the-velvet_99...' parent='<h3><a href="catalogue/tipping-the-velve...'>]
```
Get all elements that contain the word `the` (Partial matching)
```python
>>> results = page.find_by_text('the', partial=True, first_match=False)
>>> [i.text for i in results]
['A Light in the ...',
 'Tipping the Velvet',
 'The Requiem Red',
 'The Dirty Little Secrets ...',
 'The Coming Woman: A ...',
 'The Boys in the ...',
 'The Black Maria',
 'Mesaerion: The Best Science ...',
 "It's Only the Himalayas"]
```
The search is case-insensitive, so those results have `The`, not only the lowercase one `the`; let's limit the search to the elements with `the` only.
```python
>>> results = page.find_by_text('the', partial=True, first_match=False, case_sensitive=True)
>>> [i.text for i in results]
['A Light in the ...',
 'Tipping the Velvet',
 'The Boys in the ...',
 "It's Only the Himalayas"]
```
Get the first element whose text content matches my price regex
```python
>>> page.find_by_regex(r'£[\d\.]+')
<data='<p class="price_color">£51.77</p>' parent='<div class="product_price"> <p class="pr...'>
>>> page.find_by_regex(r'£[\d\.]+').text
'£51.77'
```
It's the same if you pass the compiled regex as well; Scrapling will detect the input type and act upon that:
```python
>>> import re
>>> regex = re.compile(r'£[\d\.]+')
>>> page.find_by_regex(regex)
<data='<p class="price_color">£51.77</p>' parent='<div class="product_price"> <p class="pr...'>
>>> page.find_by_regex(regex).text
'£51.77'
```
Get all elements that match the regex
```python
>>> page.find_by_regex(r'£[\d\.]+', first_match=False)
[<data='<p class="price_color">£51.77</p>' parent='<div class="product_price"> <p class="pr...'>,
 <data='<p class="price_color">£53.74</p>' parent='<div class="product_price"> <p class="pr...'>,
 <data='<p class="price_color">£50.10</p>' parent='<div class="product_price"> <p class="pr...'>,
 <data='<p class="price_color">£47.82</p>' parent='<div class="product_price"> <p class="pr...'>,
 ...]
```
And so on...

Find all elements similar to the current element in location and attributes. For our case, ignore the 'title' attribute while matching
```python
>>> element = page.find_by_text('Tipping the Velvet')
>>> element.find_similar(ignore_attributes=['title'])
[<data='<a href="catalogue/a-light-in-the-attic_...' parent='<h3><a href="catalogue/a-light-in-the-at...'>,
 <data='<a href="catalogue/soumission_998/index....' parent='<h3><a href="catalogue/soumission_998/in...'>,
 <data='<a href="catalogue/sharp-objects_997/ind...' parent='<h3><a href="catalogue/sharp-objects_997...'>,
...]
```
Notice that the number of elements is 19, not 20, because the current element is not included in the results.
```python
>>> len(element.find_similar(ignore_attributes=['title']))
19
```
Get the `href` attribute from all similar elements
```python
>>> [
    element.attrib['href']
    for element in element.find_similar(ignore_attributes=['title'])
]
['catalogue/a-light-in-the-attic_1000/index.html',
 'catalogue/soumission_998/index.html',
 'catalogue/sharp-objects_997/index.html',
 ...]
```
To increase the complexity a little bit, let's say we want to get all the books' data using that element as a starting point for some reason
```python
>>> for product in element.parent.parent.find_similar():
        print({
            "name": product.css_first('h3 a::text'),
            "price": product.css_first('.price_color').re_first(r'[\d\.]+'),
            "stock": product.css('.availability::text')[-1].clean()
        })
{'name': 'A Light in the ...', 'price': '51.77', 'stock': 'In stock'}
{'name': 'Soumission', 'price': '50.10', 'stock': 'In stock'}
{'name': 'Sharp Objects', 'price': '47.82', 'stock': 'In stock'}
...
```
### Advanced examples 
See more advanced or real-world examples using the `find_similar` method.

E-commerce Product Extraction
```python
def extract_product_grid(page):
    # Find the first product card
    first_product = page.find_by_text('Add to Cart').find_ancestor(
        lambda e: e.has_class('product-card')
    )

    # Find similar product cards
    products = first_product.find_similar()

    return [
        {
            'name': p.css_first('h3::text'),
            'price': p.css_first('.price::text').re_first(r'\d+\.\d{2}'),
            'stock': 'In stock' in p.text,
            'rating': p.css_first('.rating').attrib.get('data-rating')
        }
        for p in products
    ]
```
Table Row Extraction
```python
def extract_table_data(page):
    # Find the first data row
    first_row = page.css_first('table tbody tr')

    # Find similar rows
    rows = first_row.find_similar()

    return [
        {
            'column1': row.css_first('td:nth-child(1)::text'),
            'column2': row.css_first('td:nth-child(2)::text'),
            'column3': row.css_first('td:nth-child(3)::text')
        }
        for row in rows
    ]
```
Form Field Extraction
```python
def extract_form_fields(page):
    # Find first form field container
    first_field = page.css_first('input').find_ancestor(
        lambda e: e.has_class('form-field')
    )

    # Find similar field containers
    fields = first_field.find_similar()

    return [
        {
            'label': f.css_first('label::text'),
            'type': f.css_first('input').attrib.get('type'),
            'required': 'required' in f.css_first('input').attrib
        }
        for f in fields
    ]
```
Extracting reviews from a website
```python
def extract_reviews(page):
    # Find first review
    first_review = page.find_by_text('Great product!')
    review_container = first_review.find_ancestor(
        lambda e: e.has_class('review')
    )
    
    # Find similar reviews
    all_reviews = review_container.find_similar()
    
    return [
        {
            'text': r.css_first('.review-text::text'),
            'rating': r.attrib.get('data-rating'),
            'author': r.css_first('.reviewer::text')
        }
        for r in all_reviews
    ]
```
## Filters-based searching
This search method is arguably the best way to find elements in Scrapling, as it is powerful and easier to learn for newcomers to Web Scraping than writing selectors. 

Inspired by BeautifulSoup's `find_all` function, you can find elements using the `find_all` and `find` methods. Both methods can take multiple types of filters and return all elements in the pages that all these filters apply to.

To be more specific:

* Any string passed is considered a tag name.
* Any iterable passed, like List/Tuple/Set, is considered an iterable of tag names.
* Any dictionary is considered a mapping of HTML element(s), attribute names, and attribute values.
* Any regex patterns passed are used to filter elements by content, like the `find_by_regex` method
* Any functions passed are used to filter elements
* Any keyword argument passed is considered as an HTML element attribute with its value.

It collects all passed arguments and keywords, and each filter passes its results to the following filter in a waterfall-like filtering system.

It filters all elements in the current page/element in the following order:

1. All elements with the passed tag name(s) get collected.
2. All elements that match all passed attribute(s) are collected; if a previous filter is used, then previously collected elements are filtered.
3. All elements that match all passed regex patterns are collected, or if previous filter(s) are used, then previously collected elements are filtered.
4. All elements that fulfill all passed function(s) are collected; if a previous filter(s) is used, then previously collected elements are filtered.

Notes:

1. As you probably understood, the filtering process always starts from the first filter it finds in the filtering order above. So, if no tag name(s) are passed but attributes are passed, the process starts from that step (number 2), and so on.
2. The order in which you pass the arguments doesn't matter. The only order taken into consideration is the order explained above.

Check examples to clear any confusion :)

### Examples
```python
>>> from scrapling.fetchers import Fetcher
>>> page = Fetcher.get('https://quotes.toscrape.com/')
```
Find all elements with the tag name `div`.
```python
>>> page.find_all('div')
[<data='<div class="container"> <div class="row...' parent='<body> <div class="container"> <div clas...'>,
 <data='<div class="row header-box"> <div class=...' parent='<div class="container"> <div class="row...'>,
...]
```
Find all div elements with a class that equals `quote`.
```python
>>> page.find_all('div', class_='quote')
[<data='<div class="quote" itemscope itemtype="h...' parent='<div class="col-md-8"> <div class="quote...'>,
 <data='<div class="quote" itemscope itemtype="h...' parent='<div class="col-md-8"> <div class="quote...'>,
...]
```
Same as above.
```python
>>> page.find_all('div', {'class': 'quote'})
[<data='<div class="quote" itemscope itemtype="h...' parent='<div class="col-md-8"> <div class="quote...'>,
 <data='<div class="quote" itemscope itemtype="h...' parent='<div class="col-md-8"> <div class="quote...'>,
...]
```
Find all elements with a class that equals `quote`.
```python
>>> page.find_all({'class': 'quote'})
[<data='<div class="quote" itemscope itemtype="h...' parent='<div class="col-md-8"> <div class="quote...'>,
 <data='<div class="quote" itemscope itemtype="h...' parent='<div class="col-md-8"> <div class="quote...'>,
...]
```
Find all div elements with a class that equals `quote` and contains the element `.text`, which contains the word 'world' in its content.
```python
>>> page.find_all('div', {'class': 'quote'}, lambda e: "world" in e.css_first('.text::text'))
[<data='<div class="quote" itemscope itemtype="h...' parent='<div class="col-md-8"> <div class="quote...'>]
```
Find all elements that don't have children.
```python
>>> page.find_all(lambda element: len(element.children) > 0)
[<data='<html lang="en"><head><meta charset="UTF...'>,
 <data='<head><meta charset="UTF-8"><title>Quote...' parent='<html lang="en"><head><meta charset="UTF...'>,
 <data='<body> <div class="container"> <div clas...' parent='<html lang="en"><head><meta charset="UTF...'>,
...]
```
Find all elements that contain the word 'world' in their content.
```python
>>> page.find_all(lambda element: "world" in element.text)
[<data='<span class="text" itemprop="text">“The...' parent='<div class="quote" itemscope itemtype="h...'>,
 <data='<a class="tag" href="/tag/world/page/1/"...' parent='<div class="tags"> Tags: <meta class="ke...'>]
```
Find all span elements that match the given regex
```python
>>> page.find_all('span', re.compile(r'world'))
[<data='<span class="text" itemprop="text">“The...' parent='<div class="quote" itemscope itemtype="h...'>]
```
Find all div and span elements with class 'quote' (No span elements like that, so only div returned)
```python
>>> page.find_all(['div', 'span'], {'class': 'quote'})
[<data='<div class="quote" itemscope itemtype="h...' parent='<div class="col-md-8"> <div class="quote...'>,
 <data='<div class="quote" itemscope itemtype="h...' parent='<div class="col-md-8"> <div class="quote...'>,
...]
```
Mix things up
```python
>>> page.find_all({'itemtype':"http://schema.org/CreativeWork"}, 'div').css('.author::text')
['Albert Einstein',
 'J.K. Rowling',
...]
```
A bonus pro tip: Find all elements whose `href` attribute's value ends with the word 'Einstein'.
```python
>>> page.find_all({'href$': 'Einstein'})
[<data='<a href="/author/Albert-Einstein">(about...' parent='<span>by <small class="author" itemprop=...'>,
 <data='<a href="/author/Albert-Einstein">(about...' parent='<span>by <small class="author" itemprop=...'>,
 <data='<a href="/author/Albert-Einstein">(about...' parent='<span>by <small class="author" itemprop=...'>]
```
Another pro tip: Find all elements whose `href` attribute's value has '/author/' in it
```python
>>> page.find_all({'href*': '/author/'})
[<data='<a href="/author/Albert-Einstein">(about...' parent='<span>by <small class="author" itemprop=...'>,
 <data='<a href="/author/J-K-Rowling">(about)</a...' parent='<span>by <small class="author" itemprop=...'>,
 <data='<a href="/author/Albert-Einstein">(about...' parent='<span>by <small class="author" itemprop=...'>,
...]
```
And so on...

## Generating selectors
You can always generate CSS/XPath selectors for any element that can be reused here or anywhere else, and the most remarkable thing is that it doesn't matter what method you used to find that element!

Generate a short CSS selector for the `url_element` element (if possible, create a short one; otherwise, it's a full selector)
```python
>>> url_element = page.find({'href*': '/author/'})
>>> url_element.generate_css_selector
'body > div > div:nth-of-type(2) > div > div > span:nth-of-type(2) > a'
```
Generate a full CSS selector for the `url_element` element from the start of the page
```python
>>> url_element.generate_full_css_selector
'body > div > div:nth-of-type(2) > div > div > span:nth-of-type(2) > a'
```
Generate a short XPath selector for the `url_element` element (if possible, create a short one; otherwise, it's a full selector)
```python
>>> url_element.generate_xpath_selector
'//body/div/div[2]/div/div/span[2]/a'
```
Generate a full XPath selector for the `url_element` element from the start of the page
```python
>>> url_element.generate_full_xpath_selector
'//body/div/div[2]/div/div/span[2]/a'
```
> Note: <br>
> When you tell Scrapling to create a short selector, it tries to find a unique element to use in generation as a stop point, like an element with an `id` attribute, but in our case, there wasn't any, so that's why the short and the full selector will be the same.

## Using selectors with regular expressions
Similar to `parsel`/`scrapy`, `re` and `re_first` methods are available for extracting data using regular expressions. However, unlike the former libraries, these methods are in nearly all classes like `Selector`/`Selectors`/`TextHandler` and `TextHandlers`, which means you can use them directly on the element even if you didn't select a text node. 

We will have a deep look at it while explaining the [TextHandler](main_classes.md#texthandler) class, but in general, it works like the examples below:
```python
>>> page.css_first('.price_color').re_first(r'[\d\.]+')
'51.77'

>>> page.css('.price_color').re_first(r'[\d\.]+')
'51.77'

>>> page.css('.price_color').re(r'[\d\.]+')
['51.77',
 '53.74',
 '50.10',
 '47.82',
 '54.23',
...]

>>> page.css('.product_pod h3 a::attr(href)').re(r'catalogue/(.*)/index.html')
['a-light-in-the-attic_1000',
 'tipping-the-velvet_999',
 'soumission_998',
 'sharp-objects_997',
...]

>>> filtering_function = lambda e: e.parent.tag == 'h3' and e.parent.parent.has_class('product_pod')  # As above selector
>>> page.find('a', filtering_function).attrib['href'].re(r'catalogue/(.*)/index.html')
['a-light-in-the-attic_1000']

>>> page.find_by_text('Tipping the Velvet').attrib['href'].re(r'catalogue/(.*)/index.html')
['tipping-the-velvet_999']
```
And so on. You get the idea. We will explain this in more detail on the next page while explaining the [TextHandler](main_classes.md#texthandler) class.

----------------------------------------


## File: tutorials/external.md
<!-- Source: docs/tutorials/external.md -->


If you have issues with the browser installation, such as resource management, we recommend you try the Cloud Browser from [Scrapeless](https://www.scrapeless.com/en/product/scraping-browser?utm_source=official&utm_term=scrapling) for free!

The usage is straightforward: create an account and [get your API key](https://docs.scrapeless.com/en/scraping-browser/quickstart/getting-started/?utm_source=official&utm_term=scrapling), then pass it to the `DynamicSession` like this:

```python
from urllib.parse import urlencode

from scrapling.fetchers import DynamicSession

# Configure your browser session
config = {
    "token": "YOUR_API_KEY",
    "sessionName": "scrapling-session",
    "sessionTTL": "300",  # 5 minutes
    "proxyCountry": "ANY",
    "sessionRecording": "false",
}

# Build WebSocket URL
ws_endpoint = f"wss://browser.scrapeless.com/api/v2/browser?{urlencode(config)}"
print('Connecting to Scrapeless...')

with DynamicSession(cdp_url=ws_endpoint, disable_resources=True) as s:
    print("Connected!")
    page = s.fetch("https://httpbin.org/headers", network_idle=True)
    print(f"Page loaded, content length: {len(page.body)}")
    print(page.json())
```
The `DynamicSession` class instance will work as usual, so no further explanation is needed.

However, the Scrapeless Cloud Browser can be configured with proxy options, like the proxy country in the config above, [custom fingerprint](https://docs.scrapeless.com/en/scraping-browser/features/advanced-privacy-anti-detection/custom-fingerprint/?utm_source=official&utm_term=scrapling) configuration, [captcha solving](https://docs.scrapeless.com/en/scraping-browser/features/advanced-privacy-anti-detection/supported-captchas/?utm_source=official&utm_term=scrapling), and more.

Check out the [Scrapeless's browser documentation](https://docs.scrapeless.com/en/scraping-browser/quickstart/introduction/?utm_source=official&utm_term=scrapling) for more details.

----------------------------------------


## File: tutorials/migrating_from_beautifulsoup.md
<!-- Source: docs/tutorials/migrating_from_beautifulsoup.md -->

# Migrating from BeautifulSoup to Scrapling

If you're already familiar with BeautifulSoup, you're in for a treat. Scrapling is incredibly faster, provides the same parsing capabilities, adds more parsing capabilities not found in BS, and introduces powerful new features for fetching and handling modern web pages. This guide will help you quickly adapt your existing BeautifulSoup code to leverage Scrapling's capabilities.

Below is a table that covers the most common operations you'll perform when scraping web pages. Each row illustrates how to accomplish a specific task using BeautifulSoup and the corresponding method in Scrapling.

You will notice that some shortcuts in BeautifulSoup are missing in Scrapling, but that's one of the reasons why BeautifulSoup is slower than Scrapling. The point is: If the same feature can be used in a short oneliner, there is no need to sacrifice performance to shorten that short line :)


| Task                                                            | BeautifulSoup Code                                                                                            | Scrapling Code                                                                    |
|-----------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| Parser import                                                   | `from bs4 import BeautifulSoup`                                                                               | `from scrapling.parser import Selector`                                           |
| Parsing HTML from string                                        | `soup = BeautifulSoup(html, 'html.parser')`                                                                   | `page = Selector(html)`                                                           |
| Finding a single element                                        | `element = soup.find('div', class_='example')`                                                                | `element = page.find('div', class_='example')`                                    |
| Finding multiple elements                                       | `elements = soup.find_all('div', class_='example')`                                                           | `elements = page.find_all('div', class_='example')`                               |
| Finding a single element (Example 2)                            | `element = soup.find('div', attrs={"class": "example"})`                                                      | `element = page.find('div', {"class": "example"})`                                |
| Finding a single element (Example 3)                            | `element = soup.find(re.compile("^b"))`                                                                       | `element = page.find(re.compile("^b"))`<br/>`element = page.find_by_regex(r"^b")` |
| Finding a single element (Example 4)                            | `element = soup.find(lambda e: len(list(e.children)) > 0)`                                                    | `element = page.find(lambda e: len(e.children) > 0)`                              |
| Finding a single element (Example 5)                            | `element = soup.find(["a", "b"])`                                                                             | `element = page.find(["a", "b"])`                                                 |
| Find element by its text content                                | `element = soup.find(text="some text")`                                                                       | `element = page.find_by_text("some text", partial=False)`                         |
| Using CSS selectors to find the first matching element          | `elements = soup.select_one('div.example')`                                                                   | `elements = page.css_first('div.example')`                                        |
| Using CSS selectors to find all matching element                | `elements = soup.select('div.example')`                                                                       | `elements = page.css('div.example')`                                              |
| Get a prettified version of the page/element source             | `prettified = soup.prettify()`                                                                                | `prettified = page.prettify()`                                                    |
| Get a Non-pretty version of the page/element source             | `source = str(soup)`                                                                                          | `source = page.body`                                                              |
| Get tag name of an element                                      | `name = element.name`                                                                                         | `name = element.tag`                                                              |
| Extracting text content of an element                           | `string = element.string`                                                                                     | `string = element.text`                                                           |
| Extracting all the text in a document or beneath a tag          | `text = soup.get_text(strip=True)`                                                                            | `text = page.get_all_text(strip=True)`                                            |
| Access the dictionary of attributes                             | `attrs = element.attrs`                                                                                       | `attrs = element.attrib`                                                          |
| Extracting attributes                                           | `attr = element['href']`                                                                                      | `attr = element['href']`                                                          |
| Navigating to parent                                            | `parent = element.parent`                                                                                     | `parent = element.parent`                                                         |
| Get all parents of an element                                   | `parents = list(element.parents)`                                                                             | `parents = list(element.iterancestors())`                                         |
| Searching for an element in the parents of an element           | `target_parent = element.find_parent("a")`                                                                    | `target_parent = element.find_ancestor(lambda p: p.tag == 'a')`                   |
| Get all siblings of an element                                  | N/A                                                                                                           | `siblings = element.siblings`                                                     |
| Get next sibling of an element                                  | `next_element = element.next_sibling`                                                                         | `next_element = element.next`                                                     |
| Searching for an element in the siblings of an element          | `target_sibling = element.find_next_sibling("a")`<br/>`target_sibling = element.find_previous_sibling("a")`   | `target_sibling = element.siblings.search(lambda s: s.tag == 'a')`                |
| Searching for elements in the siblings of an element            | `target_sibling = element.find_next_siblings("a")`<br/>`target_sibling = element.find_previous_siblings("a")` | `target_sibling = element.siblings.filter(lambda s: s.tag == 'a')`                |
| Searching for an element in the next elements of an element     | `target_parent = element.find_next("a")`                                                                      | `target_parent = element.below_elements.search(lambda p: p.tag == 'a')`           |
| Searching for elements in the next elements of an element       | `target_parent = element.find_all_next("a")`                                                                  | `target_parent = element.below_elements.filter(lambda p: p.tag == 'a')`           |
| Searching for an element in the previous elements of an element | `target_parent = element.find_previous("a")`                                                                  | `target_parent = element.path.search(lambda p: p.tag == 'a')`                     |
| Searching for elements in the previous elements of an element   | `target_parent = element.find_all_previous("a")`                                                              | `target_parent = element.path.filter(lambda p: p.tag == 'a')`                     |
| Get previous sibling of an element                              | `prev_element = element.previous_sibling`                                                                     | `prev_element = element.previous`                                                 |
| Navigating to children                                          | `children = list(element.children)`                                                                           | `children = element.children`                                                     |
| Get all descendants of an element                               | `children = list(element.descendants)`                                                                        | `children = element.below_elements`                                               |
| Filtering a group of elements that satisfies a condition        | `group = soup.find('p', 'story').css.filter('a')`                                                             | `group = page.find_all('p', 'story').filter(lambda p: p.tag == 'a')`              |


**One key point to remember**: BeautifulSoup offers features for modifying and manipulating the page after it has been parsed. Scrapling focuses more on scraping the page faster for you, and then you can do what you want with the extracted information. So, two different tools can be used in Web Scraping, but one of them specializes in Web Scraping :)

### Putting It All Together

Here's a simple example of scraping a web page to extract all the links using BeautifulSoup and Scrapling.

**With BeautifulSoup:**

```python
import requests
from bs4 import BeautifulSoup

url = 'http://example.com'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

links = soup.find_all('a')
for link in links:
    print(link['href'])
```

**With Scrapling:**

```python
from scrapling import Fetcher

url = 'http://example.com'
page = Fetcher.get(url)

links = page.css('a::attr(href)')
for link in links:
    print(link)
```

As you can see, Scrapling simplifies the process by handling the fetching and parsing in a single step, making your code cleaner and more efficient.

**Additional Notes:**

- **Different parsers**: BeautifulSoup allows you to set the parser engine to use, and one of them is `lxml`. Scrapling doesn't do that and uses the `lxml` library by default for performance reasons.
- **Element Types**: In BeautifulSoup, elements are `Tag` objects, while in Scrapling, they are `Selector` objects. However, they provide similar methods and properties for navigation and data extraction.
- **Error Handling**: Both libraries return `None` when an element is not found (e.g., `soup.find()` or `page.css_first()`). To avoid errors, check for `None` before accessing properties.
- **Text Extraction**: Scrapling provides additional methods for handling text through `TextHandler`, such as `clean()`, which can help remove extra whitespace, consecutive spaces, or unwanted characters. Please check out the documentation for the complete list.

The documentation provides more details on Scrapling's features and the complete list of arguments that can be passed to all methods.

This guide should make your transition from BeautifulSoup to Scrapling smooth and straightforward. Happy scraping!

----------------------------------------


## File: tutorials/replacing_ai.md
<!-- Source: docs/tutorials/replacing_ai.md -->

# Scrapling: A Free Alternative to AI for Robust Web Scraping

Web scraping has long been a vital tool for data extraction, indexing, and preparing datasets, among other purposes. But experienced users often encounter persistent issues that can hinder effectiveness. Recently, there's been a noticeable shift toward AI-based web scraping, driven by its potential to address these challenges.

In this article, we will discuss these common issues, why companies are shifting toward that approach, the problems with that approach, and how scrapling solves them for you without the cost of using AI.

## Common issues and challenging goals

If you have been doing Web Scraping for a long time, you probably noticed that there are repeating problems with Web Scraping, like:

1. **Rapidly changing website structures** — Sites frequently update their DOM structures, breaking static XPath/CSS selectors.
2. **Unstable selectors** — Class names and IDs often change or use randomly generated values that break scrapers or make scraping these websites difficult.
3. **Increasingly complex anti-bot measures** — CAPTCHA systems, browser fingerprinting, and behavior analysis make traditional scraping difficult
and others

But that's only if you are doing targeted Web Scraping for known websites, in which case you can write specific code for every website.

If you start thinking about bigger goals like Broad Scraping or Generic Web Scraping, or what you like to call it, then the above issues intensify, and you will face new issues like:

1. **Extreme Website Diversity** — Generic scraping must handle countless variations in HTML structures, CSS usage, JavaScript frameworks, and backend technologies.
2. **Identifying Relevant Data** — How does the scraper know what data is important on a page it has never seen before?
3. **Pagination variations** — Infinite scroll, traditional pagination, "load more" buttons, all requiring different approaches
and more

How will you solve that manually? I'm referring to generic web scraping of various websites that don't share any common technologies.

## AI to the rescue, but at a high cost

Of course, the AI can easily solve most of these issues because it can understand the page source and identify the fields you want or create selectors for them. That's, of course, if you already solved the anti-bot measures through other tools :)

This approach is, of course, beautiful. I love AI and find it very fascinating, especially Generative AI. You will probably spend a lot of time on prompt engineering and tweaking the prompts, but if that's cool with you, you will soon hit the real issue with using AI here.

Most websites have vast amounts of content per page, which you will need to pass to the AI somehow so it can do its magic. This will burn through tokens like fire in a haystack, quickly accumulating high costs.

Unless money is irrelevant to you, you will try to find less expensive approaches, and that's why I made Scrapling :smile:

## Scrapling got you covered

Scrapling can handle almost all issues you will face during Web Scraping, and the following updates will cover the rest carefully.

### Solving issue T1: Rapidly changing website structures
That's why the [adaptive](https://scrapling.readthedocs.io/en/latest/parsing/adaptive/) feature was made. You knew I would talk about it, and here we are :)

While Web Scraping, if you have the `adaptive` feature enabled, you can save any element's unique properties to find it again later when the website's structure changes. The most frustrating thing about changes is that anything about an element can change, so there's nothing to rely on. 

That's how the adaptive feature works: it stores everything unique about an element. When the website structure changes, it returns the element with the highest similarity score of the previous element.

I have already explained that in more detail and with many examples. Read more from [here](https://scrapling.readthedocs.io/en/latest/parsing/adaptive/#how-the-adaptive-feature-works).

### Solving issue T2: Unstable selectors
If you have been doing Web scraping for a long enough time, you have likely experienced this once. I'm referring to a website that employs poor design patterns, built on raw HTML without any IDs/classes, or uses random class names with nothing else to rely on, etc...

In these cases, standard selection methods with CSS/XPath selectors won't be optimal, and that's why Scrapling provides three more methods for Selection:

1. [Selection by element content](https://scrapling.readthedocs.io/en/latest/parsing/selection/#text-content-selection): Through text content (`find_by_text`) or regex that matches text content (`find_by_regex`)
2. [Selecting elements similar to another element](https://scrapling.readthedocs.io/en/latest/parsing/selection/#finding-similar-elements): You find an element, and we will do the rest!
3. [Selecting elements by filters](https://scrapling.readthedocs.io/en/latest/parsing/selection/#filters-based-searching): You specify conditions/filters that this element must fulfill, we find it!

There is no need to explain any of these; click on the links, and it will be clear how Scrapling solves this.

### Solving issue T3: Increasingly complex anti-bot measures
It's known that making an undetectable spider takes more than residential/mobile proxies and human-like behavior. It also needs a hard-to-detect browser, which Scrapling provides two main options to solve:

1. [DynamicFetcher](https://scrapling.readthedocs.io/en/latest/fetching/dynamic/) — This fetcher provides many flexible options, like stealth mode suitable for small to medium protections and using your real browser.
2. [StealthyFetcher](https://scrapling.readthedocs.io/en/latest/fetching/stealthy/) — Because we live in a harsh world and you need to take [full measure instead of half-measures](https://www.youtube.com/watch?v=7BE4QcwX4dU), `StealthyFetcher` was born. This fetcher utilizes our version of a modified Firefox browser, called [Camoufox](https://camoufox.com/stealth/), which nearly passes all known tests and incorporates additional tricks. **With v0.3, this fetcher can bypass Cloudflare for you automatically as well!**

These two will be improved a lot with the upcoming updates, so stay tuned :)

### Solving issues B1 & B2: Extreme Website Diversity / Identifying Relevant Data

This one is tough to handle, but it's possible with Scrapling's flexibility. 

I talked with someone who uses AI to extract prices from different websites. He is only interested in prices and titles, so he uses AI to find the price for him.

I told him you don't need to use AI here and gave this code as an example
```python
price_element = page.find_by_regex(r'£[\d\.,]+', first_match=True)  # Get the first element that contains a text that matches price regex eg. £10.50
# If you want the container/element that contains the price element
price_element_container = price_element.parent or price_element.find_ancestor(lambda ancestor: ancestor.has_class('product'))  # or other methods...
target_element_selector = price_element_container.generate_css_selector or price_element_container.generate_full_css_selector # or xpath
```
Then he said What about cases like this:
```html
<span class='currency'> $ </span> <span class='a-price'> 45,000 </span>
```
So, I updated the code like this
```python
price_element_container = page.find_by_regex(r'[\d,]+', first_match=True).parent # Adjusted the regex for this example
full_price_data = price_element_container.get_all_text(strip=True)  # Returns '$45,000' in this case
```
This was enough for his use case. You can use the first regex, and if it doesn't find anything, use the following regex, and so on. Try to cover the most common patterns first, then the less common ones, and so on.
It will be a bit boring, but it's definitely less expensive than AI.

This example illustrates the point I aim to convey here. Not every challenge will need AI to be solved, but sometimes you need to be creative, and that might save you a lot of money.

### Solving issue B3: Pagination variations
This issue, Scrapling currently doesn't have a direct method to automatically extract pagination's URLs for you, but it will be added with the following updates :)

But you can handle most websites if you search for the most common patterns with `page.find_by_text('Next')['href']` or `page.find_by_text('load more')['href']` or selectors like `'a[href*="?page="]'` or `'a[href*="/page/"]'`—you get the idea.

## Cost Comparison and Savings
For a quick comparison.

| Aspect         | Scrapling                                                                  | AI-Based Tools (e.g., Browse AI, Oxylabs)                                  |
|----------------|----------------------------------------------------------------------------|----------------------------------------------------------------------------|
| Cost Structure | Likely free or low-cost, no per-use fees                                   | Starts at $19/month (Browse AI) to $49/month (Oxylabs), scales with usage  |
| Setup Effort   | Requires little technical expertise, manual setup                          | Often no-code, easier for non-technical users                              |
| Usage options  | Through code, terminal, or MCP server.                                     | Often through GUI or API, depending on the option the company is providing |
| Scalability    | Depends on user implementation                                             | Built-in support for large-scale, managed services                         |
| Adaptability   | High with features like `adaptive` and the non-selectors selection methods | High, automatic with AI, but costly for frequent changes                   |

This table is based on pricing from [Browse AI Pricing](https://www.browse.ai/pricing) and [Oxylabs Web Scraper API Pricing](https://oxylabs.io/products/scraper-api/web/pricing)

## Conclusion
While AI offers powerful capabilities, its cost can be prohibitive for many Web scraping tasks. Scrapling provides a robust, flexible, and cost-effective toolkit designed to tackle the real-world challenges of both targeted and broad scraping, often eliminating the need for expensive AI solutions. You can build resilient scrapers more efficiently by leveraging features like `adaptive`, diverse selection methods, and advanced fetchers.

Explore the documentation further and see how Scrapling can simplify your future Web Scraping projects!

----------------------------------------
