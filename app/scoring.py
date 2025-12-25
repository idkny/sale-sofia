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
from typing import Any, Callable, Dict, List, Optional, Tuple

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
class DealBreakerCheck:
    """Configuration for a deal breaker check."""
    name: str
    check_fn: Callable[[Dict[str, Any]], DealBreakerResult]


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


def _check_not_panel(listing: Dict[str, Any]) -> DealBreakerResult:
    """Check if building is not panel construction."""
    building_type = (listing.get("building_type") or "").lower()
    is_panel = "panel" in building_type or "панел" in building_type
    return DealBreakerResult(
        name="Not panel construction",
        passed=not is_panel,
        reason="Panel construction" if is_panel else "OK",
        value=building_type
    )


def _check_elevator(listing: Dict[str, Any]) -> DealBreakerResult:
    """Check if elevator exists for floor 3+."""
    floor, elevator = listing.get("floor_number"), listing.get("has_elevator")
    needs_elevator = floor and floor >= 3
    passed = bool(elevator) if needs_elevator else True
    reason = f"Floor {floor}, elevator: {elevator}" if needs_elevator else f"Floor {floor or 'N/A'} - elevator not required"
    return DealBreakerResult("Has elevator (floor 3+)", passed, reason, elevator)


def _check_floor_limit(listing: Dict[str, Any]) -> DealBreakerResult:
    """Check if floor is 4 or below."""
    floor = listing.get("floor_number")
    if not floor:
        return DealBreakerResult(f"Floor {MAX_FLOOR} or below", True, "Floor unknown", None)
    passed = floor <= MAX_FLOOR
    reason = f"Floor {floor}" + ("" if passed else " - too high")
    return DealBreakerResult(f"Floor {MAX_FLOOR} or below", passed, reason, floor)


def _check_bathrooms(listing: Dict[str, Any]) -> DealBreakerResult:
    """Check if listing has 2+ bathrooms."""
    bathrooms = listing.get("bathrooms_count") or 0
    bath_ok = bathrooms >= MIN_BATHROOMS
    return DealBreakerResult(
        name=f"{MIN_BATHROOMS}+ bathrooms",
        passed=bath_ok,
        reason=f"{bathrooms} bathroom(s)",
        value=bathrooms
    )


def _check_act_status(listing: Dict[str, Any]) -> DealBreakerResult:
    """Check if new build has Act 15+."""
    building_type = (listing.get("building_type") or "").lower()
    act_status = (listing.get("act_status") or "").lower()
    is_new_build = "new" in building_type or "ново" in building_type
    if not is_new_build:
        return DealBreakerResult("Act 15+ (new build)", True, "Not a new build - N/A", act_status)
    passed = "15" in act_status or "16" in act_status
    return DealBreakerResult("Act 15+ (new build)", passed, f"Act status: {act_status or 'unknown'}", act_status)


def _check_no_legal_issues(listing: Dict[str, Any]) -> DealBreakerResult:
    """Check if listing has no legal issues."""
    has_legal_issues = listing.get("has_legal_issues")
    return DealBreakerResult(
        name="No legal issues",
        passed=not has_legal_issues,
        reason="Has legal issues" if has_legal_issues else "OK",
        value=has_legal_issues
    )


def _check_outdoor_space(listing: Dict[str, Any]) -> DealBreakerResult:
    """Check if listing has balcony, garden, or terrace."""
    has_balcony = listing.get("has_balcony")
    has_garden = listing.get("has_garden")
    has_terrace = listing.get("has_terrace")
    outdoor_ok = any([has_balcony, has_garden, has_terrace])
    return DealBreakerResult(
        name="Has balcony/garden",
        passed=outdoor_ok,
        reason=f"Balcony: {has_balcony}, Garden: {has_garden}, Terrace: {has_terrace}",
        value=outdoor_ok
    )


def _check_orientation(listing: Dict[str, Any]) -> DealBreakerResult:
    """Check if listing has East/South orientation."""
    orientation = (listing.get("orientation") or "").lower()
    good_orientations = ["e", "s", "east", "south", "изток", "юг", "и", "ю", "се", "юи", "югоизток"]
    has_good_orientation = any(o in orientation for o in good_orientations) if orientation else True
    return DealBreakerResult(
        name="East/South orientation",
        passed=has_good_orientation,
        reason=f"Orientation: {orientation or 'unknown'}",
        value=orientation
    )


def _check_budget(listing: Dict[str, Any]) -> DealBreakerResult:
    """Check if total cost is within budget."""
    price = listing.get("price_eur") or 0
    renovation = listing.get("estimated_renovation_eur") or 0
    total = price + renovation
    budget_ok = total <= MAX_TOTAL_BUDGET
    return DealBreakerResult(
        name=f"Total cost <= {MAX_TOTAL_BUDGET:,} EUR",
        passed=budget_ok,
        reason=f"Price: {price:,.0f} + Reno: {renovation:,.0f} = {total:,.0f} EUR",
        value=total
    )


def _check_metro_distance(listing: Dict[str, Any]) -> DealBreakerResult:
    """Check if listing is within 600m of metro."""
    metro_distance = listing.get("metro_distance_m")
    if metro_distance is None:
        return DealBreakerResult(f"Within {MAX_METRO_DISTANCE}m of metro", True, "Metro distance unknown", None)
    passed = metro_distance <= MAX_METRO_DISTANCE
    return DealBreakerResult(f"Within {MAX_METRO_DISTANCE}m of metro", passed, f"{metro_distance}m from metro", metro_distance)


# Config-driven deal breaker checks
DEAL_BREAKER_CHECKS = [
    DealBreakerCheck("Not panel construction", _check_not_panel),
    DealBreakerCheck("Has elevator (floor 3+)", _check_elevator),
    DealBreakerCheck("Floor 4 or below", _check_floor_limit),
    DealBreakerCheck("2+ bathrooms", _check_bathrooms),
    DealBreakerCheck("Act 15+ (new build)", _check_act_status),
    DealBreakerCheck("No legal issues", _check_no_legal_issues),
    DealBreakerCheck("Has balcony/garden", _check_outdoor_space),
    DealBreakerCheck("East/South orientation", _check_orientation),
    DealBreakerCheck("Total cost within budget", _check_budget),
    DealBreakerCheck("Within metro distance", _check_metro_distance),
]


def check_deal_breakers(listing: Dict[str, Any]) -> List[DealBreakerResult]:
    """Check all deal breakers for a listing."""
    return [check.check_fn(listing) for check in DEAL_BREAKER_CHECKS]


def passes_all_deal_breakers(listing: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check if listing passes all deal breakers.

    Returns:
        Tuple of (passes_all, list of failed check names)
    """
    results = check_deal_breakers(listing)
    failed = [r.name for r in results if not r.passed]
    return len(failed) == 0, failed


def _score_location(listing: Dict[str, Any]) -> float:
    """Score location based on metro distance and district tier (0-5)."""
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

    return min(5.0, location_score)


def _score_price_sqm(listing: Dict[str, Any]) -> float:
    """Score price per sqm against benchmarks (0-5)."""
    price_sqm = listing.get("price_per_sqm_eur") or 0
    if price_sqm <= PRICE_BENCHMARKS["excellent"]:
        return 5.0
    elif price_sqm <= PRICE_BENCHMARKS["good"]:
        return 4.0
    elif price_sqm <= PRICE_BENCHMARKS["fair"]:
        return 3.0
    elif price_sqm <= PRICE_BENCHMARKS["expensive"]:
        return 2.0
    else:
        return 1.0


def _score_condition(listing: Dict[str, Any]) -> float:
    """Score condition and budget headroom (0-5)."""
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

    return condition_score


def _score_layout(listing: Dict[str, Any]) -> float:
    """Score layout based on rooms, bathrooms, orientation (0-5)."""
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

    return min(5.0, layout_score)


def _score_building(listing: Dict[str, Any]) -> float:
    """Score building type and construction year (0-5)."""
    building_type = (listing.get("building_type") or "").lower()
    year = listing.get("construction_year")

    if "panel" in building_type or "панел" in building_type:
        return 1.0  # Panel = bad
    elif "new" in building_type or "ново" in building_type:
        return 4.5
    elif "brick" in building_type or "тухла" in building_type:
        if year and year >= 2000:
            return 4.0
        elif year and year >= 1980:
            return 3.5
        else:
            return 3.0
    else:
        return 2.5


def _score_rental(listing: Dict[str, Any]) -> float:
    """Score rental potential based on amenities and location (0-5)."""
    rental_score = 2.5  # Base
    metro_distance = listing.get("metro_distance_m")

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

    return min(5.0, rental_score)


def _score_extras(listing: Dict[str, Any]) -> float:
    """Score extras like storage, parking, AC (0-5)."""
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

    return min(5.0, extras_score) if extras_score > 0 else 2.0


def calculate_score(listing: Dict[str, Any]) -> ScoreBreakdown:
    """Calculate weighted score for a listing. Each criterion scored 0-5, then weighted."""
    scores = {
        "location": _score_location(listing),
        "price_sqm": _score_price_sqm(listing),
        "condition": _score_condition(listing),
        "layout": _score_layout(listing),
        "building": _score_building(listing),
        "rental": _score_rental(listing),
        "extras": _score_extras(listing),
    }

    total_weighted = sum(
        scores[criterion] * (weight / 100) * 5
        for criterion, weight in WEIGHTS.items()
    ) / 5

    return ScoreBreakdown(**scores, total_weighted=round(total_weighted, 2))


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
