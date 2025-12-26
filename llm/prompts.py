"""Prompt templates for Ollama LLM extraction tasks.

These prompts are designed to extract ENGLISH values from BULGARIAN real estate text.
The "RESPOND IN ENGLISH ONLY" constraint is critical for accurate enum extraction.

See: docs/specs/108_OLLAMA_PROMPT_IMPROVEMENTS.md
"""

FIELD_MAPPING_PROMPT = """You are a Bulgarian real estate data extraction expert.

CRITICAL RULES:
1. Extract information from the BULGARIAN TEXT below
2. RESPOND IN ENGLISH ONLY - use ONLY English enum values
3. Never translate enum values to Bulgarian
4. Return valid JSON matching the schema
5. Use null for missing information

BULGARIAN TEXT:
{content}

REQUIRED JSON FIELDS (use EXACT enum values):
- price_eur: number (price in euros) or null
- price_bgn: number (price in leva) or null
- area_sqm: number (area in square meters) or null
- floor: number (floor number) or null
- total_floors: number (total building floors) or null
- construction: "brick" | "panel" | "epk" | null
  (use "brick" for тухла/тухлена, "panel" for панел, "epk" for ЕПК)
- heating: "district" | "gas" | "electric" | "air_conditioner" | null
  (use "district" for ТЕЦ/централно, "gas" for газ, "electric" for ток, "air_conditioner" for климатик)
- neighborhood: string (keep in Bulgarian - proper noun) or null
- address: string (keep in Bulgarian - proper noun) or null
- year_built: number or null
- confidence: number (0.0-1.0, your extraction confidence)

Return ONLY valid JSON with these exact field names and enum values.
RESPOND IN ENGLISH ONLY. Your JSON values must be in English, not Bulgarian.
"""

EXTRACTION_PROMPT_BASE = """You are a Bulgarian real estate data extraction expert.

CRITICAL RULES:
1. Extract information from the BULGARIAN DESCRIPTION below
2. RESPOND IN ENGLISH ONLY - use ONLY English enum values
3. Use the DETECTED WORDS section - these are pre-matched for you
4. For boolean fields: set true when keyword is detected, null when not mentioned
5. Return valid JSON matching the schema

NOW EXTRACT FROM THIS DESCRIPTION:

BULGARIAN DESCRIPTION:
{description}

{hints}

REQUIRED JSON FIELDS:
- rooms: number or null
- bedrooms: number or null
- bathrooms: number or null
- furnishing: "furnished" | "partially" | "unfurnished" | null
- condition: "new" | "renovated" | "needs_renovation" | null
- has_parking: boolean or null
- parking_type: "underground" | "outdoor" | "garage" | null
- has_elevator: boolean or null
- has_security: boolean or null
- has_balcony: boolean or null
- has_storage: boolean or null
- orientation: "north" | "south" | "east" | "west" | null
- has_view: boolean or null
- view_type: "city" | "mountain" | "park" | null
- heating_type: "district" | "gas" | "electric" | "air_conditioner" | null
- payment_options: "cash" | "installments" | "mortgage" | null
- confidence: number (0.0-1.0)

Return ONLY valid JSON.
"""


def build_extraction_prompt(description: str, hints: str = "") -> str:
    """Build extraction prompt with dynamic hints."""
    hints_section = hints if hints else "No specific Bulgarian keywords detected."
    return EXTRACTION_PROMPT_BASE.format(description=description, hints=hints_section)


# DEPRECATED: Use EXTRACTION_PROMPT_BASE with build_extraction_prompt() instead.
# This legacy prompt is kept for backwards compatibility only.
EXTRACTION_PROMPT = """You are a Bulgarian real estate data extraction expert.

CRITICAL RULES:
1. Extract information from the BULGARIAN DESCRIPTION below
2. RESPOND IN ENGLISH ONLY - use ONLY English enum values
3. Never translate enum values to Bulgarian
4. Return valid JSON matching the schema
5. Use null for missing information

BULGARIAN DESCRIPTION:
{description}

REQUIRED JSON FIELDS (use EXACT enum values):
- rooms: number or null
  (едностаен=1, двустаен=2, тристаен=3, четиристаен=4, петстаен=5)
- bedrooms: number or null
- bathrooms: number or null
- furnishing: "furnished" | "partially" | "unfurnished" | null
  (use "furnished" for обзаведен/напълно обзаведен, "partially" for частично, "unfurnished" for необзаведен)
- condition: "new" | "renovated" | "needs_renovation" | null
  (use "new" for нов, "renovated" for ремонтиран, "needs_renovation" for за ремонт)
- has_parking: boolean or null
- parking_type: "underground" | "outdoor" | "garage" | null
  (use "underground" for подземен, "outdoor" for двор, "garage" for гараж)
- has_elevator: boolean or null (true for асансьор)
- has_security: boolean or null (true for охрана)
- has_balcony: boolean or null (true for тераса/балкон)
- has_storage: boolean or null (true for мазе)
- orientation: "north" | "south" | "east" | "west" | null
  (use "north" for север, "south" for юг, "east" for изток, "west" for запад)
- has_view: boolean or null (true for гледка)
- view_type: "city" | "mountain" | "park" | null
  (use "city" for град, "mountain" for планина, "park" for парк)
- heating_type: "district" | "gas" | "electric" | "air_conditioner" | null
  (use "district" for ТЕЦ/централно, "gas" for газ, "electric" for ток, "air_conditioner" for климатик)
- payment_options: "cash" | "installments" | "mortgage" | null
- confidence: number (0.0-1.0)

Return ONLY valid JSON with these exact field names and enum values.
RESPOND IN ENGLISH ONLY. Your JSON values must be in English, not Bulgarian.
"""
