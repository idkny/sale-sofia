# app/scoring.py
"""
Scoring and deal breaker calculations for apartment listings.

Scoring Criteria (from apartment-criteria.md):
- Location (metro, neighborhood): 25%
- Price/sqm: 20%
- Condition vs renovation budget: 15%
- Layout (2 toilets, rooms, orientation): 15%
- Building quality (brick/new): 10%
- Rental potential: 10%
- Extras (storage, parking): 5%
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# Budget constraints
MAX_TOTAL_BUDGET = 270_000  # EUR
MAX_METRO_DISTANCE = 600  # meters
MAX_FLOOR = 4
MIN_ROOMS = 3
MIN_BATHROOMS = 2

# Scoring weights (sum = 100)
WEIGHTS = {
    "location": 25,
    "price_sqm": 20,
    "condition": 15,
    "layout": 15,
    "building": 10,
    "rental": 10,
    "extras": 5,
}

# Average price per sqm benchmarks by district tier
# Tier 1: Premium (Lozenets, Ivan Vazov, Center)
# Tier 2: Good (Iztok, Izgrev, Geo Milev, Studentski Grad)
# Tier 3: Average (Mladost 1-4, Manastirski Livadi, Ovcha Kupel)
DISTRICT_TIERS = {
    "lozenets": 1,
    "лозенец": 1,
    "ivan vazov": 1,
    "иван вазов": 1,
    "center": 1,
    "център": 1,
    "iztok": 2,
    "изток": 2,
    "izgrev": 2,
    "изгрев": 2,
    "geo milev": 2,
    "гео милев": 2,
    "studentski grad": 2,
    "студентски град": 2,
    "mladost": 3,
    "младост": 3,
    "manastirski livadi": 3,
    "манастирски ливади": 3,
    "ovcha kupel": 3,
    "овча купел": 3,
    "vitosha": 2,
    "витоша": 2,
    "krastova vada": 2,
    "кръстова вада": 2,
}

# Benchmark prices per sqm (EUR) - Sofia 2024
PRICE_BENCHMARKS = {
    "excellent": 1800,  # Below this is excellent value
    "good": 2200,       # Below this is good value
    "fair": 2600,       # Below this is fair value
    "expensive": 3000,  # Above this is expensive
}


@dataclass
class DealBreakerResult:
    """Result of a deal breaker check."""
    name: str
    passed: bool
    reason: str
    value: Any = None


@dataclass
class ScoreBreakdown:
    """Detailed score breakdown for a listing."""
    location: float
    price_sqm: float
    condition: float
    layout: float
    building: float
    rental: float
    extras: float
    total_weighted: float


def check_deal_breakers(listing: Dict[str, Any]) -> List[DealBreakerResult]:
    """
    Check all deal breakers for a listing.

    Args:
        listing: Dict with listing data (from sqlite3.Row or dict)

    Returns:
        List of DealBreakerResult objects
    """
    results = []

    # 1. Not panel construction
    building_type = (listing.get("building_type") or "").lower()
    is_panel = "panel" in building_type or "панел" in building_type
    results.append(DealBreakerResult(
        name="Not panel construction",
        passed=not is_panel,
        reason="Panel construction" if is_panel else "OK",
        value=building_type
    ))

    # 2. Has elevator (if floor 3+)
    floor = listing.get("floor_number")
    has_elevator = listing.get("has_elevator")
    if floor and floor >= 3:
        elevator_ok = bool(has_elevator)
        results.append(DealBreakerResult(
            name="Has elevator (floor 3+)",
            passed=elevator_ok,
            reason=f"Floor {floor}, elevator: {has_elevator}",
            value=has_elevator
        ))
    else:
        results.append(DealBreakerResult(
            name="Has elevator (floor 3+)",
            passed=True,
            reason=f"Floor {floor or 'N/A'} - elevator not required",
            value=has_elevator
        ))

    # 3. Floor 4 or below
    if floor:
        floor_ok = floor <= MAX_FLOOR
        results.append(DealBreakerResult(
            name=f"Floor {MAX_FLOOR} or below",
            passed=floor_ok,
            reason=f"Floor {floor}" + (" - too high" if not floor_ok else ""),
            value=floor
        ))
    else:
        results.append(DealBreakerResult(
            name=f"Floor {MAX_FLOOR} or below",
            passed=True,  # Unknown = pass (verify later)
            reason="Floor unknown",
            value=None
        ))

    # 4. 2+ toilets/bathrooms
    bathrooms = listing.get("bathrooms_count") or 0
    bath_ok = bathrooms >= MIN_BATHROOMS
    results.append(DealBreakerResult(
        name=f"{MIN_BATHROOMS}+ bathrooms",
        passed=bath_ok,
        reason=f"{bathrooms} bathroom(s)",
        value=bathrooms
    ))

    # 5. Act 15+ (if new build)
    act_status = (listing.get("act_status") or "").lower()
    building_type_lower = building_type.lower()
    is_new_build = "new" in building_type_lower or "ново" in building_type_lower

    if is_new_build:
        has_act_15_plus = "15" in act_status or "16" in act_status
        results.append(DealBreakerResult(
            name="Act 15+ (new build)",
            passed=has_act_15_plus,
            reason=f"Act status: {act_status or 'unknown'}",
            value=act_status
        ))
    else:
        results.append(DealBreakerResult(
            name="Act 15+ (new build)",
            passed=True,
            reason="Not a new build - N/A",
            value=act_status
        ))

    # 6. No legal issues
    has_legal_issues = listing.get("has_legal_issues")
    results.append(DealBreakerResult(
        name="No legal issues",
        passed=not has_legal_issues,
        reason="Has legal issues" if has_legal_issues else "OK",
        value=has_legal_issues
    ))

    # 7. Has balcony or garden
    has_balcony = listing.get("has_balcony")
    has_garden = listing.get("has_garden")
    has_terrace = listing.get("has_terrace")
    outdoor_ok = any([has_balcony, has_garden, has_terrace])
    results.append(DealBreakerResult(
        name="Has balcony/garden",
        passed=outdoor_ok,
        reason=f"Balcony: {has_balcony}, Garden: {has_garden}, Terrace: {has_terrace}",
        value=outdoor_ok
    ))

    # 8. East/South orientation
    orientation = (listing.get("orientation") or "").lower()
    # Check for E, S, East, South, Изток, Юг
    good_orientations = ["e", "s", "east", "south", "изток", "юг", "и", "ю", "се", "юи", "югоизток"]
    has_good_orientation = any(o in orientation for o in good_orientations) if orientation else True
    results.append(DealBreakerResult(
        name="East/South orientation",
        passed=has_good_orientation,
        reason=f"Orientation: {orientation or 'unknown'}",
        value=orientation
    ))

    # 9. Total cost <= 270,000 EUR
    price = listing.get("price_eur") or 0
    renovation = listing.get("estimated_renovation_eur") or 0
    total = price + renovation
    budget_ok = total <= MAX_TOTAL_BUDGET
    results.append(DealBreakerResult(
        name=f"Total cost <= {MAX_TOTAL_BUDGET:,} EUR",
        passed=budget_ok,
        reason=f"Price: {price:,.0f} + Reno: {renovation:,.0f} = {total:,.0f} EUR",
        value=total
    ))

    # 10. Within 600m of metro
    metro_distance = listing.get("metro_distance_m")
    if metro_distance is not None:
        metro_ok = metro_distance <= MAX_METRO_DISTANCE
        results.append(DealBreakerResult(
            name=f"Within {MAX_METRO_DISTANCE}m of metro",
            passed=metro_ok,
            reason=f"{metro_distance}m from metro",
            value=metro_distance
        ))
    else:
        results.append(DealBreakerResult(
            name=f"Within {MAX_METRO_DISTANCE}m of metro",
            passed=True,  # Unknown = pass (verify later)
            reason="Metro distance unknown",
            value=None
        ))

    return results


def passes_all_deal_breakers(listing: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check if listing passes all deal breakers.

    Returns:
        Tuple of (passes_all, list of failed check names)
    """
    results = check_deal_breakers(listing)
    failed = [r.name for r in results if not r.passed]
    return len(failed) == 0, failed


def calculate_score(listing: Dict[str, Any]) -> ScoreBreakdown:
    """
    Calculate weighted score for a listing.

    Each criterion scored 0-5, then weighted.

    Returns:
        ScoreBreakdown with individual and total scores
    """
    scores = {}

    # 1. Location Score (25%) - metro distance + district quality
    location_score = 0.0
    metro_distance = listing.get("metro_distance_m")
    if metro_distance is not None:
        if metro_distance <= 200:
            location_score += 2.5
        elif metro_distance <= 400:
            location_score += 2.0
        elif metro_distance <= 600:
            location_score += 1.5
        else:
            location_score += 0.5
    else:
        location_score += 1.5  # Unknown = average

    # District tier bonus
    district = (listing.get("district") or "").lower()
    district_tier = None
    for key, tier in DISTRICT_TIERS.items():
        if key in district:
            district_tier = tier
            break

    if district_tier == 1:
        location_score += 2.5
    elif district_tier == 2:
        location_score += 2.0
    elif district_tier == 3:
        location_score += 1.5
    else:
        location_score += 1.0  # Unknown district

    scores["location"] = min(5.0, location_score)

    # 2. Price/sqm Score (20%)
    price_sqm = listing.get("price_per_sqm_eur") or 0
    if price_sqm <= PRICE_BENCHMARKS["excellent"]:
        scores["price_sqm"] = 5.0
    elif price_sqm <= PRICE_BENCHMARKS["good"]:
        scores["price_sqm"] = 4.0
    elif price_sqm <= PRICE_BENCHMARKS["fair"]:
        scores["price_sqm"] = 3.0
    elif price_sqm <= PRICE_BENCHMARKS["expensive"]:
        scores["price_sqm"] = 2.0
    else:
        scores["price_sqm"] = 1.0

    # 3. Condition vs Budget Score (15%)
    price = listing.get("price_eur") or 0
    renovation = listing.get("estimated_renovation_eur") or 0
    total = price + renovation
    budget_remaining = MAX_TOTAL_BUDGET - total
    condition = (listing.get("condition") or "").lower()

    condition_score = 2.5  # Default
    if "ready" in condition or "завършен" in condition:
        condition_score = 4.5
    elif "renovation" in condition or "ремонт" in condition:
        condition_score = 3.0
    elif "bare" in condition or "шпакловка" in condition:
        condition_score = 2.0

    # Adjust for budget headroom
    if budget_remaining >= 50000:
        condition_score = min(5.0, condition_score + 1.0)
    elif budget_remaining >= 20000:
        condition_score = min(5.0, condition_score + 0.5)
    elif budget_remaining < 0:
        condition_score = max(1.0, condition_score - 2.0)

    scores["condition"] = condition_score

    # 4. Layout Score (15%) - rooms, bathrooms, orientation
    layout_score = 0.0

    rooms = listing.get("rooms_count") or 0
    if rooms >= 4:
        layout_score += 2.0
    elif rooms >= 3:
        layout_score += 1.5
    else:
        layout_score += 0.5

    bathrooms = listing.get("bathrooms_count") or 0
    if bathrooms >= 2:
        layout_score += 2.0
    elif bathrooms >= 1:
        layout_score += 1.0

    orientation = (listing.get("orientation") or "").lower()
    good_orientations = ["south", "юг", "southeast", "югоизток"]
    if any(o in orientation for o in good_orientations):
        layout_score += 1.0
    elif "east" in orientation or "изток" in orientation:
        layout_score += 0.75
    else:
        layout_score += 0.5

    scores["layout"] = min(5.0, layout_score)

    # 5. Building Quality Score (10%)
    building_type = (listing.get("building_type") or "").lower()
    year = listing.get("construction_year")

    if "panel" in building_type or "панел" in building_type:
        scores["building"] = 1.0  # Panel = bad
    elif "new" in building_type or "ново" in building_type:
        scores["building"] = 4.5
    elif "brick" in building_type or "тухла" in building_type:
        if year and year >= 2000:
            scores["building"] = 4.0
        elif year and year >= 1980:
            scores["building"] = 3.5
        else:
            scores["building"] = 3.0
    else:
        scores["building"] = 2.5

    # 6. Rental Potential Score (10%)
    rental_score = 2.5  # Base

    if listing.get("near_schools"):
        rental_score += 0.5
    if metro_distance and metro_distance <= 400:
        rental_score += 1.0
    elif metro_distance and metro_distance <= 600:
        rental_score += 0.5
    if listing.get("near_restaurants") or listing.get("near_supermarket"):
        rental_score += 0.5
    if listing.get("is_furnished"):
        rental_score += 0.5

    scores["rental"] = min(5.0, rental_score)

    # 7. Extras Score (5%)
    extras_score = 0.0

    if listing.get("has_storage"):
        extras_score += 1.5
    if listing.get("has_parking"):
        extras_score += 1.5
    if listing.get("has_garage"):
        extras_score += 2.0
    if listing.get("has_ac_preinstalled"):
        extras_score += 0.5
    if listing.get("has_builtin_wardrobes"):
        extras_score += 0.5

    scores["extras"] = min(5.0, extras_score) if extras_score > 0 else 2.0

    # Calculate weighted total
    total_weighted = sum(
        scores[criterion] * (weight / 100) * 5
        for criterion, weight in WEIGHTS.items()
    ) / 5  # Normalize to 0-5 scale

    return ScoreBreakdown(
        location=scores["location"],
        price_sqm=scores["price_sqm"],
        condition=scores["condition"],
        layout=scores["layout"],
        building=scores["building"],
        rental=scores["rental"],
        extras=scores["extras"],
        total_weighted=round(total_weighted, 2)
    )


def calculate_total_investment(listing: Dict[str, Any]) -> float:
    """Calculate total investment (price + estimated renovation)."""
    price = listing.get("price_eur") or 0
    renovation = listing.get("estimated_renovation_eur") or 0
    return price + renovation


def get_score_summary(listing: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get complete scoring summary for a listing.

    Returns dict with:
    - scores: ScoreBreakdown
    - deal_breakers: List of DealBreakerResult
    - passes_all: bool
    - failed_breakers: list of names
    - total_investment: float
    """
    scores = calculate_score(listing)
    deal_breakers = check_deal_breakers(listing)
    passes, failed = passes_all_deal_breakers(listing)

    return {
        "scores": scores,
        "deal_breakers": deal_breakers,
        "passes_all": passes,
        "failed_breakers": failed,
        "total_investment": calculate_total_investment(listing),
    }


# Utility function for Streamlit
def listing_to_dict(row) -> Dict[str, Any]:
    """Convert sqlite3.Row to dict for scoring functions."""
    if hasattr(row, "keys"):
        return {key: row[key] for key in row.keys()}
    return dict(row)
