"""Prompt templates for Ollama LLM extraction tasks.

These prompts are designed for Bulgarian real estate data extraction.
"""

FIELD_MAPPING_PROMPT = """Ти си експерт по недвижими имоти.

Анализирай следния текст от обява и извлечи данни за базата данни.

ТЕКСТ:
{content}

НАЛИЧНИ ПОЛЕТА В БАЗАТА ДАННИ (използвай ТОЧНО тези английски стойности):
- price_eur: цена в евро (число)
- price_bgn: цена в лева (число)
- area_sqm: квадратура (число)
- floor: етаж (число)
- total_floors: общо етажи (число)
- construction: САМО "brick" (тухла), "panel" (панел) или "epk" (ЕПК)
- neighborhood: квартал (текст на български)
- address: адрес (текст на български)
- year_built: година на строителство (число)
- heating: САМО "district" (ТЕЦ), "gas" (газ), "electric" (ток) или "air_conditioner" (климатик)

Отговори САМО с валиден JSON:
{{
    "field_name": value,
    ...
    "confidence": 0.0-1.0
}}

Използвай null за липсваща информация.
"""

EXTRACTION_PROMPT = """Ти си експерт по недвижими имоти в България.

Анализирай следното описание и извлечи структурирана информация.

ОПИСАНИЕ:
{description}

ВАЖНО: Използвай ТОЧНО тези английски стойности:
- furnishing: САМО "furnished" (обзаведен), "partially" (частично), "unfurnished" (необзаведен)
- condition: САМО "new" (нов), "renovated" (ремонтиран), "needs_renovation" (за ремонт)
- parking_type: САМО "underground" (подземен), "outdoor" (двор), "garage" (гараж)
- orientation: САМО "north" (север), "south" (юг), "east" (изток), "west" (запад)
- view_type: САМО "city" (град), "mountain" (планина), "park" (парк)
- heating_type: САМО "district" (ТЕЦ), "gas" (газ), "electric" (ток), "air_conditioner" (климатик)

Отговори САМО с валиден JSON:
{{
    "rooms": число (едностаен=1, двустаен=2, тристаен=3, четиристаен=4, петстаен=5) или null,
    "bedrooms": число или null,
    "bathrooms": число или null,
    "furnishing": стойност от горните или null,
    "condition": стойност от горните или null,
    "has_parking": true/false/null,
    "parking_type": стойност от горните или null,
    "has_elevator": true (асансьор) / false (без асансьор) / null,
    "has_security": true (охрана) / false / null,
    "has_balcony": true (тераса/балкон) / false / null,
    "has_storage": true (мазе) / false / null,
    "orientation": стойност от горните или null,
    "has_view": true (гледка) / false / null,
    "view_type": стойност от горните или null,
    "heating_type": стойност от горните или null,
    "payment_options": "cash" | "installments" | "mortgage" | null,
    "confidence": 0.0-1.0
}}

Ако информацията липсва, използвай null.
"""
