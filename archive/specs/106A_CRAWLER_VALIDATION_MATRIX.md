# 106A: Crawler Validation Matrix

**Status**: Complete
**Created**: 2025-12-27
**Phase**: Crawler Validation Phase 1

---

## Summary

Both scrapers (imot.bg and bazar.bg) have been validated with 46 passing tests. All core extraction, pagination, and schema validation functionality works correctly.

---

## Validation Matrix

| Capability | imot.bg | bazar.bg | Tests |
|------------|---------|----------|-------|
| **URL Extraction** | ✅ | ✅ | 2 |
| **Listing Data Extraction** | ✅ | ✅ | 2 |
| **Schema Normalization** | ✅ | ✅ | 2 |
| **Price Extraction** | ✅ | ✅ | 7 |
| **SQM Extraction** | ✅ | ✅ | 6 |
| **Floor Extraction** | ✅ | ✅ | 6 |
| **Rooms Extraction** | ✅ | ✅ | 8 |
| **Pagination Detection** | ✅ | ✅ | 7 |
| **Pagination URL Build** | ✅ | ✅ | 6 |
| **TOTAL** | **23/23** | **23/23** | **46** |

---

## Detailed Test Coverage

### URL Extraction from Search Results

| Test | imot.bg | bazar.bg |
|------|---------|----------|
| Extract listing URLs | ✅ | ✅ |
| URLs are absolute | ✅ | ✅ |
| URLs contain `/obiava-` pattern | ✅ | ✅ |

### Listing Data Extraction

| Test | imot.bg | bazar.bg |
|------|---------|----------|
| Returns ListingData object | ✅ | ✅ |
| Extracts external_id from URL | ✅ | ✅ |
| Sets correct source_site | ✅ | ✅ |
| Extracts title | ✅ | ✅ |

### Price Extraction

| Pattern | imot.bg | bazar.bg |
|---------|---------|----------|
| EUR with spaces (150 000 EUR) | ✅ | N/A |
| EUR without spaces (150000 EUR) | ✅ | ✅ |
| EUR symbol (150000€) | ✅ | ✅ |
| Multiple prices (takes first) | ✅ | N/A |
| BGN JS variable (convert to EUR) | N/A | ✅ |
| EUR JS variable (no conversion) | N/A | ✅ |
| Text fallback | N/A | ✅ |

### SQM Extraction

| Pattern | imot.bg | bazar.bg |
|---------|---------|----------|
| Bulgarian format (115 кв.м) | ✅ | ✅ |
| Decimal format (115.5 кв.м) | ✅ | ✅ |
| m² symbol (115 m²) | ✅ | ✅ |

### Floor Extraction

| Pattern | imot.bg | bazar.bg |
|---------|---------|----------|
| Full format (Етаж 3 от 6) | ✅ | ✅ |
| Slash format (3/6) | ✅ | ✅ |
| Number only (Етаж 3) | ✅ | ✅ |

### Rooms Extraction

| Pattern | imot.bg | bazar.bg |
|---------|---------|----------|
| From URL (tristaen) | ✅ | ✅ |
| From URL (dvustaen) | ✅ | ✅ |
| From Bulgarian text | ✅ | ✅ |
| Numeric pattern (3-стаен) | ✅ | ✅ |

### Pagination Detection

| Scenario | imot.bg | bazar.bg |
|----------|---------|----------|
| Has next page | ✅ | ✅ |
| Max page reached | N/A | ✅ |
| No results message | ✅ | ✅ |
| No listings found | ✅ | ✅ |

### Pagination URL Building

| Scenario | imot.bg | bazar.bg |
|----------|---------|----------|
| Build page 2 URL | ✅ | ✅ |
| Build page 3 URL | ✅ | ✅ |
| Preserve query params | ✅ | ✅ |

---

## Test File Locations

| File | Tests |
|------|-------|
| `tests/scrapers/test_imot_bg.py` | 23 tests |
| `tests/scrapers/test_bazar_bg.py` | 23 tests |
| `tests/scrapers/conftest.py` | Shared fixtures |

---

## Bugs Fixed During Validation (Session 30)

| Bug | Scraper | Fix |
|-----|---------|-----|
| Floor extraction `Етаж: 3/6` format | imot.bg | Added slash pattern to selectors.py |
| Floor extraction `Етаж 3` format | imot.bg | Added number-only pattern |
| Floor extraction Cyrillic Е | bazar.bg | Fixed regex to match both E and Е |
| Price JS single/double quotes | bazar.bg | Pattern handles both quote types |
| Price JS decimals | bazar.bg | Added `\.?` for decimal support |
| SQM pattern spacing | bazar.bg | Added `\s*` flexible spacing |
| Test fixtures CSS classes | bazar.bg | Fixed conftest.py with proper classes |

---

## What's NOT Tested (Future Work)

| Capability | Notes |
|------------|-------|
| Real network requests | Tests use fixtures (cached HTML) |
| Database save | Schema validation only, no DB writes |
| Proxy integration | Not part of scraper tests |
| Rate limiting | Tested separately in resilience/ |
| Cross-site dedup | Phase 3.5 (not started) |

---

## Recommendations

1. **Periodically refresh fixtures** - Sites change HTML; update cached fixtures quarterly
2. **Add real-site smoke tests** - Optional CI job with real requests (rate limited)
3. **Monitor extraction rates** - Dashboard metric for fields extracted per listing

---

## Conclusion

Phase 1 validation complete. Both scrapers are production-ready for:
- Extracting listing URLs from search pages
- Extracting all fields from listing pages
- Handling pagination correctly
- Normalizing data to canonical schema

**Next**: Phase 3 (Change Detection tables) or Phase 4 (Async Orchestrator)
