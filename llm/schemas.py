"""Pydantic models for Ollama LLM extraction results.

These schemas define the structure of extracted real estate data.
"""

from pydantic import BaseModel
from typing import Optional, Literal


class MappedFields(BaseModel):
    """DB field mapping result from page content."""
    price_eur: Optional[int] = None
    price_bgn: Optional[int] = None
    area_sqm: Optional[float] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    construction: Optional[Literal["brick", "panel", "epk"]] = None
    neighborhood: Optional[str] = None
    address: Optional[str] = None
    year_built: Optional[int] = None
    heating: Optional[Literal["district", "gas", "electric", "air_conditioner"]] = None
    confidence: float = 0.0


class ExtractedDescription(BaseModel):
    """Extracted from free-text description."""
    rooms: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    furnishing: Optional[Literal["furnished", "partially", "unfurnished"]] = None
    condition: Optional[Literal["new", "renovated", "needs_renovation"]] = None
    has_parking: Optional[bool] = None
    parking_type: Optional[Literal["underground", "outdoor", "garage"]] = None
    has_elevator: Optional[bool] = None
    has_security: Optional[bool] = None
    has_balcony: Optional[bool] = None
    has_storage: Optional[bool] = None
    orientation: Optional[Literal["north", "south", "east", "west"]] = None
    has_view: Optional[bool] = None
    view_type: Optional[Literal["city", "mountain", "park"]] = None
    heating_type: Optional[Literal["district", "gas", "electric", "air_conditioner"]] = None
    payment_options: Optional[Literal["cash", "installments", "mortgage"]] = None
    confidence: float = 0.0
