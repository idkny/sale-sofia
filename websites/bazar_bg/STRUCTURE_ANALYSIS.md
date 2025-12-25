# Bazar.bg Website Structure Analysis

**Analysis Date:** 2025-12-24
**Analyzed URLs:**
- Search page: https://bazar.bg/obiavi/apartamenti/sofia
- Sample listings:
  - https://bazar.bg/obiava-52890419/prodawa-3-staen-gr-sofiia-tsentar
  - https://bazar.bg/obiava-50767353/prodawa-2-staen-gr-sofiia-borowo
  - https://bazar.bg/obiava-52890478/prodawa-mezonet-gr-sofiia-gr-bankia

---

## 1. Search Page Structure

### Base Search URL
```
https://bazar.bg/obiavi/apartamenti/sofia
```

### Listing Cards

**Container Structure:**
```html
<div class="listItemContainer listItemContainerV2">
    <a class="listItemLink" href="https://bazar.bg/obiava-[ID]/[slug]" data-id="[ID]">
        <img class="cover lazy" data-src="[image-url]" alt="...">
        <div class="title">
            <span class="title">[Property Title]</span>
            <span class="location">[Location]</span>
            <span class="date">[Posting Date]</span>
            <span class="price">[Price BGN]</span>
            <span class="price">[Price EUR]</span>
        </div>
    </a>
    <div class="fav tmb">[Favorites Button]</div>
    <div class="icon_new">[TOP Badge]</div>
</div>
```

**CSS Selectors:**

| Element | Selector |
|---------|----------|
| Listing Container | `.listItemContainer.listItemContainerV2` |
| Listing Link | `a.listItemLink` |
| Listing URL | `a.listItemLink[href]` |
| Listing ID | `a.listItemLink[data-id]` |
| Title | `.title span.title` |
| Location | `.title .location` |
| Date | `.title .date` |
| Price (BGN) | `.title .price:first-of-type` |
| Price (EUR) | `.title .price:last-of-type` |
| Image | `img.cover.lazy` |
| Image URL | `img.cover.lazy[data-src]` |

**Additional Notes:**
- Promoted listings have additional class: `a.listItemLink.listTop`
- Images use lazy loading with `data-src` attribute
- Total listings shown: ~29,028 apartments in Sofia
- Currency priority setting: `var currencyPriority = '1'` (BGN first)

---

## 2. Pagination

### URL Pattern
```
https://bazar.bg/obiavi/apartamenti/sofia?page=[N]
```

**Examples:**
- Page 1: `https://bazar.bg/obiavi/apartamenti/sofia` (no parameter)
- Page 2: `https://bazar.bg/obiavi/apartamenti/sofia?page=2`
- Page 3: `https://bazar.bg/obiavi/apartamenti/sofia?page=3`

### Pagination Structure

**HTML Structure:**
```
[« Предишна] [1] [2] [3] ... [10] ... [25] [Следваща »]
```

**JavaScript Variable:**
```javascript
var maxPage = 25;
```

**Detection Methods:**

1. **Maximum Page:** Extract `maxPage` variable from page JavaScript
2. **Next Button:** Check for "Следваща »" (Next) link presence/disabled state
3. **Last Page:** When current page equals `maxPage` or next button is disabled

**Regex Pattern for Page Parameter:**
```regex
[?&]page=(\d+)
```

---

## 3. Listing URL Pattern

### URL Structure
```
https://bazar.bg/obiava-[ID]/[slug]
```

**Examples:**
- `https://bazar.bg/obiava-52890419/prodawa-3-staen-gr-sofiia-tsentar`
- `https://bazar.bg/obiava-50767353/prodawa-2-staen-gr-sofiia-borowo`
- `https://bazar.bg/obiava-52890478/prodawa-mezonet-gr-sofiia-gr-bankia`

### Extraction Patterns

**Listing ID:**
```regex
obiava-(\d+)
```

**Slug Components:**
```regex
prodawa-(.*?)-gr-sofiia-(.+)
```

Where:
- Group 1: Property type (e.g., "3-staen", "mezonet")
- Group 2: Neighborhood (e.g., "tsentar", "borowo", "gr-bankia")

**Link Identification:**
- All listing links contain: `/obiava-`
- Format: starts with `/obiava-` followed by numeric ID

---

## 4. Individual Listing Page Structure

### JavaScript Data Variables

**Key Data:**
```javascript
var adId = '52890419';
var adPrice = '389998';
var adPriceCurrency = '€';
var smHash = '[hash]';
```

**Price Display Format:**
```
762 769,79 лв / 389 998 €
```
- Thousands separator: space
- Decimal separator: comma
- Both BGN (лв) and EUR (€) displayed

### Specifications Table

**Structure:**
Appears as label-value pairs without explicit table structure:

```
Тип сделка: Продава Апартамент
Тип апартамент: 3-стаен
Квадратура: 100 кв. м.
Цена на кв.м.: 3900 €/кв. м.
Eтаж: 4
Вид строителство: Тухла
Година: 1930
Отопление: ТЕЦ
```

**Common Fields:**
- **Тип сделка** (Transaction type): Продава Апартамент
- **Тип апартамент** (Apartment type): 2-стаен, 3-стаен, Многостаен, Мезонет
- **Квадратура** (Area): [number] кв. м.
- **Цена на кв.м.** (Price per sqm): [number] €/кв. м.
- **Eтаж** (Floor): [number]
- **Вид строителство** (Construction type): Тухла, Панел
- **Година** (Year): [year]
- **Отопление** (Heating): ТЕЦ, ЦО, Газ, ТЕЦ/Електричество

**Extraction Method:**
Use regex patterns on page text:
```regex
Квадратура:\s*(\d+)\s*кв\.\s*м\.
Eтаж:\s*(\d+)
Тип апартамент:\s*(\d+-стаен|Многостаен|Мезонет)
Вид строителство:\s*(Тухла|Панел|Ново строителство)
Година:\s*(\d{4})
```

### Description

**Container:**
- No specific CSS class identified
- Appears as paragraph text after specifications
- Usually starts with property highlights or agency intro

**Example Start:**
```
"Възможност в преустройство..."
"ПАНОРАМЕН ПЕНТХАУС..."
"Unique Estates представя за продажба..."
```

**Extraction Method:**
Look for large text blocks after specifications table, typically the longest continuous text segment.

### Images

**Image URL Pattern:**
```
//cdn3.focus.bg/imot/photosimotbg/1/[folder]/[size]/[id].jpg
//imotstatic2.focus.bg/imot/photosimotbg/1/[folder]/[size]/[id].jpg
//imotstatic4.focus.bg/imot/photosimotbg/1/[folder]/[size]/[id].jpg
```

**Size Variants:**
- `/big/` - Full size images
- `/med/` - Medium/thumbnail size

**HTML Structure:**
```html
<img src="//cdn3.focus.bg/imot/photosimotbg/1/454/big/[ID].jpg"
     alt="Продава АПАРТАМЕНТ, гр. София, Център, снимка 1">
```

**Extraction:**
```regex
//(cdn\d+|imotstatic\d+)\.focus\.bg/imot/photosimotbg/\d+/\d+/(big|med)/.*?\.(jpg|jpeg|png)
```

### Contact Information

**Structure:**
- Agency name (if applicable)
- Agent name (often obfuscated: "Николай Божков")
- Phone number (obfuscated on page load)

**Location Display:**
```
гр. София, [Neighborhood]
```

Examples:
- `гр. София, Център`
- `гр. София, Борово`
- `гр. София, гр. Банкя`

### Metadata

**Posted Date:**
```
Публикувана/обновена днес в 12:00 ч.
Публикувана/обновена вчера в 14:30 ч.
```

**Views Counter:**
```
6 pregleds
```

---

## 5. Data Extraction Regex Patterns

### Price
```regex
EUR Pattern: ([\d\s]+)\s*€
BGN Pattern: ([\d\s]+)\s*лв
Combined: var adPrice = '(\d+)';\s*var adPriceCurrency = '([€лв])';
```

### Square Meters
```regex
(\d+)\s*кв\.\s*м\.
Квадратура:\s*(\d+)\s*кв\.\s*м\.
```

### Floor
```regex
Simple: Eтаж:\s*(\d+)
With total: (\d+)\s*(?:от|/)\s*(\d+)\s*етаж
Floor only: Eтаж:\s*(\d+)(?:\s|$)
```

### Rooms
**Bulgarian Terms:**
```regex
едностаен -> 1
двустаен|2-стаен -> 2
тристаен|3-стаен -> 3
четиристаен|4-стаен -> 4
многостаен -> 5
мезонет -> 3
```

**Pattern:**
```regex
Тип апартамент:\s*(\d+-стаен|[А-Яа-я]+стаен|Мезонет)
(\d+)-стаен
```

### Building Type
```regex
Панел|ЕПК|ПК -> panel
Тухла|Гредоред -> brick
Ново строителство|Ново -> new_construction
```

**Pattern:**
```regex
Вид строителство:\s*(Тухла|Панел|Ново строителство|ЕПК|Гредоред)
```

### Construction Year
```regex
Година:\s*(\d{4})
```

### Act Status (for new construction)
```regex
Акт 16|Act 16|АКТ 16 -> act16
Акт 15|Act 15|АКТ 15 -> act15
Акт 14|Act 14|АКТ 14 -> act14
```

### Heating Type
```regex
ТЕЦ -> central
ЦО|Централно -> central
Газ|газ -> gas
Електричество|ел\. -> electric
Климатик|AC -> ac
Камина -> fireplace
```

**Pattern:**
```regex
Отопление:\s*(ТЕЦ|ЦО|Газ|Електричество|Климатик)
```

### Bathrooms
```regex
(\d+)\s*(?:бани|бан|санитарен възел|тоалетн)
2 санитарни възела -> 2
```

### Orientation
**Bulgarian Terms:**
```
изток -> E
запад -> W
север -> N
юг -> S
югоизток -> SE
югозапад -> SW
североизток -> NE
северозапад -> NW
```

**Pattern:**
```regex
изположение:\s*(изток|запад|север|юг|югоизток|югозапад|североизток|северозапад)
```

### Metro Stations (Sofia)
```
сердика, св. климент охридски, опълченска, западен парк, вардар,
константин величков, обеля, люлин, запад, бизнес парк, младост,
интер експо център, цариградско шосе, академик александър теодоров-балан,
г.м. димитров, мусагеница, жолио кюри, надежда, хан кубрат,
княгиня мария луиза, централна гара, лъвов мост, орлов мост,
стадион васил левски, джеймс баучер, витоша, хладилника, околовръстен път
```

**Distance Pattern:**
```regex
(\d+)\s*(?:м|метра)\s*(?:до|от)\s*метро
метро\s*(\d+)\s*(?:м|метра)
```

### Features/Amenities

**Elevator:**
```regex
асансьор|лифт|elevator
```

**Balcony:**
```regex
балкон|тераса|balcony
```

**Parking:**
```regex
паркинг|гараж|паркомясто|parking
```

**Storage:**
```regex
мазе|избено помещение|storage|склад
```

**Garden:**
```regex
градина|двор|yard|garden
```

**Furnished:**
```regex
обзаведен|мебелиран|furnished
```

**Air Conditioning:**
```regex
климатик|AC|въздушно
```

### Condition
```regex
на зелено -> bare_walls
зелено -> bare_walls
груб строеж -> bare_walls
завършен -> ready
луксозно -> ready
за ремонт -> renovation
```

---

## 6. Location Extraction

### District
All listings in this search are in Sofia (гр. София), so district defaults to "София".

### Neighborhood
**From URL Slug:**
```regex
gr-sofiia-(.+)$
```

Examples:
- `gr-sofiia-tsentar` -> Център (Center)
- `gr-sofiia-borowo` -> Борово
- `gr-sofiia-gr-bankia` -> гр. Банкя

**Transliteration Mapping:**
```
tsentar -> Център
borowo -> Борово
gr-bankia -> гр. Банкя
mladost -> Младост
lyulin -> Люлин
```

**From Page Text:**
```regex
гр\.\s*София,\s*([А-Яа-я\s\.]+)
```

---

## 7. Phone Number Pattern

**Bulgarian Phone Format:**
```regex
(\+?359|0)\s*\d{2,3}\s*\d{3}\s*\d{2,3}
```

Examples:
- `+359 888 123 456`
- `0888 123 456`
- `02 123 4567`

---

## 8. No Results Detection

**Indicators:**
- Total listings count = 0
- No `.listItemContainer` elements found
- Empty pagination
- Message like "Няма намерени обяви" or similar

---

## 9. Summary of Key Selectors

### Search Page
```python
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
```

### Listing Page
```python
# Most data extracted via JavaScript variables and regex on page text
AD_ID_JS = r"var adId = '(\d+)';"
AD_PRICE_JS = r"var adPrice = '(\d+)';"
AD_CURRENCY_JS = r"var adPriceCurrency = '([€лв])';"

# Image pattern
IMAGE_PATTERN = r"//(cdn\d+|imotstatic\d+)\.focus\.bg/imot/photosimotbg/.*?/big/.*?\.(jpg|jpeg|png)"
```

---

## 10. Additional Notes

1. **Lazy Loading:** Search page uses lazy loading for images (`data-src` instead of `src`)
2. **JavaScript Variables:** Listing page stores key data in JS variables rather than semantic HTML
3. **Dual Currency:** Prices shown in both BGN and EUR
4. **CDN Domains:** Images hosted on multiple subdomains (cdn3, imotstatic2, imotstatic4)
5. **Max Pagination:** Currently 25 pages for Sofia apartments
6. **Total Listings:** ~29,028 apartments in Sofia
7. **Transliteration:** URL slugs use Latin transliteration of Bulgarian Cyrillic

---

## 11. Recommended Scraping Approach

1. **Search Page Scraping:**
   - Extract listing URLs from `a.listItemLink[href]`
   - Extract listing IDs from `data-id` attribute
   - Use `?page=N` parameter for pagination
   - Stop when `N` equals `maxPage` from JavaScript

2. **Listing Page Scraping:**
   - Extract `adId`, `adPrice`, `adPriceCurrency` from JavaScript variables
   - Use regex patterns on page text for specifications
   - Find images with regex pattern on href/src attributes
   - Extract description as largest text block after specifications

3. **Data Validation:**
   - Verify price exists and is reasonable (> 0)
   - Check sqm is within valid range (20-300 typical)
   - Validate floor number is positive
   - Ensure construction type matches known values

4. **Error Handling:**
   - Handle missing optional fields gracefully
   - Log warnings for missing required fields (price, sqm, url)
   - Skip listings with invalid/missing IDs
