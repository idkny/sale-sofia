#!/usr/bin/env python3
"""Unit tests for app/scoring.py - deal breaker checks and scoring helpers."""

import pytest
from app.scoring import (
    check_deal_breakers,
    passes_all_deal_breakers,
    _check_not_panel,
    _check_elevator,
    _check_floor_limit,
    _check_bathrooms,
    _check_act_status,
    _check_no_legal_issues,
    _check_outdoor_space,
    _check_orientation,
    _check_budget,
    _check_metro_distance,
    DEAL_BREAKER_CHECKS,
    _score_location,
    _score_price_sqm,
    _score_condition,
    _score_layout,
    _score_building,
    _score_rental,
    _score_extras,
    calculate_score,
    ScoreBreakdown,
    WEIGHTS,
)


class TestCheckNotPanel:
    """Tests for _check_not_panel helper."""

    def test_brick_passes(self):
        result = _check_not_panel({"building_type": "brick"})
        assert result.passed is True

    def test_panel_fails(self):
        result = _check_not_panel({"building_type": "panel"})
        assert result.passed is False

    def test_panel_bulgarian_fails(self):
        result = _check_not_panel({"building_type": "панелен блок"})
        assert result.passed is False

    def test_unknown_passes(self):
        result = _check_not_panel({})
        assert result.passed is True


class TestCheckElevator:
    """Tests for _check_elevator helper."""

    def test_floor_2_no_elevator_passes(self):
        result = _check_elevator({"floor_number": 2, "has_elevator": False})
        assert result.passed is True

    def test_floor_3_no_elevator_fails(self):
        result = _check_elevator({"floor_number": 3, "has_elevator": False})
        assert result.passed is False

    def test_floor_3_with_elevator_passes(self):
        result = _check_elevator({"floor_number": 3, "has_elevator": True})
        assert result.passed is True

    def test_floor_5_with_elevator_passes(self):
        result = _check_elevator({"floor_number": 5, "has_elevator": True})
        assert result.passed is True


class TestCheckFloorLimit:
    """Tests for _check_floor_limit helper."""

    def test_floor_4_passes(self):
        result = _check_floor_limit({"floor_number": 4})
        assert result.passed is True

    def test_floor_5_fails(self):
        result = _check_floor_limit({"floor_number": 5})
        assert result.passed is False

    def test_floor_unknown_passes(self):
        result = _check_floor_limit({})
        assert result.passed is True


class TestCheckBathrooms:
    """Tests for _check_bathrooms helper."""

    def test_2_bathrooms_passes(self):
        result = _check_bathrooms({"bathrooms_count": 2})
        assert result.passed is True

    def test_1_bathroom_fails(self):
        result = _check_bathrooms({"bathrooms_count": 1})
        assert result.passed is False

    def test_0_bathrooms_fails(self):
        result = _check_bathrooms({})
        assert result.passed is False


class TestCheckActStatus:
    """Tests for _check_act_status helper."""

    def test_not_new_build_passes(self):
        result = _check_act_status({"building_type": "brick"})
        assert result.passed is True

    def test_new_build_with_act16_passes(self):
        result = _check_act_status({"building_type": "new construction", "act_status": "act16"})
        assert result.passed is True

    def test_new_build_with_act15_passes(self):
        result = _check_act_status({"building_type": "ново строителство", "act_status": "15"})
        assert result.passed is True

    def test_new_build_with_act14_fails(self):
        result = _check_act_status({"building_type": "new", "act_status": "act14"})
        assert result.passed is False


class TestCheckNoLegalIssues:
    """Tests for _check_no_legal_issues helper."""

    def test_no_legal_issues_passes(self):
        result = _check_no_legal_issues({"has_legal_issues": False})
        assert result.passed is True

    def test_has_legal_issues_fails(self):
        result = _check_no_legal_issues({"has_legal_issues": True})
        assert result.passed is False

    def test_unknown_passes(self):
        result = _check_no_legal_issues({})
        assert result.passed is True


class TestCheckOutdoorSpace:
    """Tests for _check_outdoor_space helper."""

    def test_has_balcony_passes(self):
        result = _check_outdoor_space({"has_balcony": True})
        assert result.passed is True

    def test_has_garden_passes(self):
        result = _check_outdoor_space({"has_garden": True})
        assert result.passed is True

    def test_has_terrace_passes(self):
        result = _check_outdoor_space({"has_terrace": True})
        assert result.passed is True

    def test_no_outdoor_space_fails(self):
        result = _check_outdoor_space({})
        assert result.passed is False


class TestCheckOrientation:
    """Tests for _check_orientation helper."""

    def test_south_passes(self):
        result = _check_orientation({"orientation": "south"})
        assert result.passed is True

    def test_east_passes(self):
        result = _check_orientation({"orientation": "east"})
        assert result.passed is True

    def test_bulgarian_south_passes(self):
        result = _check_orientation({"orientation": "юг"})
        assert result.passed is True

    def test_north_fails(self):
        result = _check_orientation({"orientation": "north"})
        assert result.passed is False

    def test_unknown_passes(self):
        # Unknown orientation passes (to be verified later)
        result = _check_orientation({})
        assert result.passed is True


class TestCheckBudget:
    """Tests for _check_budget helper."""

    def test_under_budget_passes(self):
        result = _check_budget({"price_eur": 200000, "estimated_renovation_eur": 50000})
        assert result.passed is True

    def test_at_budget_passes(self):
        result = _check_budget({"price_eur": 270000, "estimated_renovation_eur": 0})
        assert result.passed is True

    def test_over_budget_fails(self):
        result = _check_budget({"price_eur": 250000, "estimated_renovation_eur": 30000})
        assert result.passed is False


class TestCheckMetroDistance:
    """Tests for _check_metro_distance helper."""

    def test_within_distance_passes(self):
        result = _check_metro_distance({"metro_distance_m": 400})
        assert result.passed is True

    def test_at_limit_passes(self):
        result = _check_metro_distance({"metro_distance_m": 600})
        assert result.passed is True

    def test_over_distance_fails(self):
        result = _check_metro_distance({"metro_distance_m": 800})
        assert result.passed is False

    def test_unknown_passes(self):
        result = _check_metro_distance({})
        assert result.passed is True


class TestCheckDealBreakersIntegration:
    """Integration tests for check_deal_breakers main function."""

    def test_returns_10_results(self):
        """Should return exactly 10 deal breaker results."""
        results = check_deal_breakers({})
        assert len(results) == 10

    def test_config_matches_checks(self):
        """Config list should have 10 entries."""
        assert len(DEAL_BREAKER_CHECKS) == 10

    def test_perfect_listing_passes_all(self):
        """A perfect listing should pass all deal breakers."""
        listing = {
            "building_type": "brick",
            "floor_number": 3,
            "has_elevator": True,
            "bathrooms_count": 2,
            "has_balcony": True,
            "orientation": "south",
            "price_eur": 200000,
            "metro_distance_m": 300,
        }
        passes, failed = passes_all_deal_breakers(listing)
        assert passes is True
        assert failed == []

    def test_panel_fails_one(self):
        """Panel building should fail one check."""
        listing = {
            "building_type": "panel",
            "floor_number": 2,
            "bathrooms_count": 2,
            "has_balcony": True,
            "orientation": "south",
            "price_eur": 150000,
            "metro_distance_m": 300,
        }
        passes, failed = passes_all_deal_breakers(listing)
        assert passes is False
        assert "Not panel construction" in failed


class TestScoreLocation:
    """Tests for _score_location helper."""

    def test_metro_200m_or_less(self):
        """Metro distance <= 200m should add 2.5 points."""
        result = _score_location({"metro_distance_m": 200, "district": "unknown"})
        assert result == 3.5  # 2.5 (metro) + 1.0 (unknown district)

    def test_metro_201_to_400m(self):
        """Metro distance 201-400m should add 2.0 points."""
        result = _score_location({"metro_distance_m": 300, "district": "unknown"})
        assert result == 3.0  # 2.0 (metro) + 1.0 (unknown district)

    def test_metro_401_to_600m(self):
        """Metro distance 401-600m should add 1.5 points."""
        result = _score_location({"metro_distance_m": 500, "district": "unknown"})
        assert result == 2.5  # 1.5 (metro) + 1.0 (unknown district)

    def test_metro_over_600m(self):
        """Metro distance > 600m should add 0.5 points."""
        result = _score_location({"metro_distance_m": 700, "district": "unknown"})
        assert result == 1.5  # 0.5 (metro) + 1.0 (unknown district)

    def test_metro_unknown(self):
        """Unknown metro distance should add 1.5 points (average)."""
        result = _score_location({"district": "unknown"})
        assert result == 2.5  # 1.5 (metro unknown) + 1.0 (unknown district)

    def test_district_tier_1(self):
        """District tier 1 (lozenets) should add 2.5 points."""
        result = _score_location({"metro_distance_m": 200, "district": "lozenets"})
        assert result == 5.0  # 2.5 (metro) + 2.5 (tier 1), capped at 5.0

    def test_district_tier_1_bulgarian(self):
        """District tier 1 Bulgarian name should work."""
        result = _score_location({"metro_distance_m": 500, "district": "лозенец"})
        assert result == 4.0  # 1.5 (metro) + 2.5 (tier 1)

    def test_district_tier_2(self):
        """District tier 2 (iztok) should add 2.0 points."""
        result = _score_location({"metro_distance_m": 300, "district": "iztok"})
        assert result == 4.0  # 2.0 (metro) + 2.0 (tier 2)

    def test_district_tier_3(self):
        """District tier 3 (mladost) should add 1.5 points."""
        result = _score_location({"metro_distance_m": 200, "district": "mladost 2"})
        assert result == 4.0  # 2.5 (metro) + 1.5 (tier 3)

    def test_district_unknown(self):
        """Unknown district should add 1.0 points."""
        result = _score_location({"metro_distance_m": 200, "district": "somewhere"})
        assert result == 3.5  # 2.5 (metro) + 1.0 (unknown)

    def test_capped_at_5(self):
        """Total score should be capped at 5.0."""
        result = _score_location({"metro_distance_m": 100, "district": "center"})
        assert result == 5.0  # Capped even if sum > 5.0


class TestScorePriceSqm:
    """Tests for _score_price_sqm helper."""

    def test_excellent_price(self):
        """Price <= 1800 should return 5.0."""
        result = _score_price_sqm({"price_per_sqm_eur": 1800})
        assert result == 5.0

    def test_excellent_price_below(self):
        """Price < 1800 should return 5.0."""
        result = _score_price_sqm({"price_per_sqm_eur": 1500})
        assert result == 5.0

    def test_good_price(self):
        """Price 1801-2200 should return 4.0."""
        result = _score_price_sqm({"price_per_sqm_eur": 2000})
        assert result == 4.0

    def test_good_price_at_limit(self):
        """Price exactly 2200 should return 4.0."""
        result = _score_price_sqm({"price_per_sqm_eur": 2200})
        assert result == 4.0

    def test_fair_price(self):
        """Price 2201-2600 should return 3.0."""
        result = _score_price_sqm({"price_per_sqm_eur": 2400})
        assert result == 3.0

    def test_expensive_price(self):
        """Price 2601-3000 should return 2.0."""
        result = _score_price_sqm({"price_per_sqm_eur": 2800})
        assert result == 2.0

    def test_very_expensive(self):
        """Price > 3000 should return 1.0."""
        result = _score_price_sqm({"price_per_sqm_eur": 3500})
        assert result == 1.0

    def test_zero_price(self):
        """Price 0 or missing should return 5.0."""
        result = _score_price_sqm({})
        assert result == 5.0


class TestScoreCondition:
    """Tests for _score_condition helper."""

    def test_ready_condition(self):
        """'ready' condition should give 4.5 base score."""
        result = _score_condition({"condition": "ready", "price_eur": 200000})
        assert result == 5.0  # 4.5 + 1.0 (70k budget remaining)

    def test_ready_bulgarian(self):
        """Bulgarian 'завършен' should give 4.5 base score."""
        result = _score_condition({"condition": "завършен", "price_eur": 200000})
        assert result == 5.0  # 4.5 + 1.0 (70k budget remaining)

    def test_renovation_condition(self):
        """'renovation' condition should give 3.0 base score."""
        result = _score_condition({"condition": "needs renovation", "price_eur": 200000})
        assert result == 4.0  # 3.0 + 1.0 (70k budget remaining)

    def test_bare_condition(self):
        """'bare' condition should give 2.0 base score."""
        result = _score_condition({"condition": "bare walls", "price_eur": 200000})
        assert result == 3.0  # 2.0 + 1.0 (70k budget remaining)

    def test_unknown_condition(self):
        """Unknown condition should give 2.5 base score."""
        result = _score_condition({"price_eur": 200000})
        assert result == 3.5  # 2.5 + 1.0 (70k budget remaining)

    def test_budget_remaining_50k_or_more(self):
        """Budget remaining >= 50000 should add 1.0."""
        result = _score_condition({"condition": "renovation", "price_eur": 200000, "estimated_renovation_eur": 10000})
        assert result == 4.0  # 3.0 (renovation) + 1.0 (60k remaining)

    def test_budget_remaining_20k_to_50k(self):
        """Budget remaining 20k-50k should add 0.5."""
        result = _score_condition({"condition": "bare", "price_eur": 230000, "estimated_renovation_eur": 20000})
        assert result == 2.5  # 2.0 (bare) + 0.5 (20k remaining)

    def test_budget_negative(self):
        """Negative budget remaining should subtract 2.0."""
        result = _score_condition({"condition": "ready", "price_eur": 260000, "estimated_renovation_eur": 20000})
        assert result == 2.5  # 4.5 (ready) - 2.0 (over budget)

    def test_ready_with_huge_headroom(self):
        """Ready + huge headroom should cap at 5.0."""
        result = _score_condition({"condition": "ready", "price_eur": 150000, "estimated_renovation_eur": 0})
        assert result == 5.0  # 4.5 + 1.0 = 5.5, capped at 5.0


class TestScoreLayout:
    """Tests for _score_layout helper."""

    def test_4_or_more_rooms(self):
        """4+ rooms should add 2.0 points."""
        result = _score_layout({"rooms_count": 4, "bathrooms_count": 0})
        assert result == 2.5  # 2.0 (rooms) + 0.5 (orientation default)

    def test_3_rooms(self):
        """3 rooms should add 1.5 points."""
        result = _score_layout({"rooms_count": 3, "bathrooms_count": 0})
        assert result == 2.0  # 1.5 (rooms) + 0.5 (orientation default)

    def test_less_than_3_rooms(self):
        """< 3 rooms should add 0.5 points."""
        result = _score_layout({"rooms_count": 2, "bathrooms_count": 0})
        assert result == 1.0  # 0.5 (rooms) + 0.5 (orientation default)

    def test_2_or_more_bathrooms(self):
        """2+ bathrooms should add 2.0 points."""
        result = _score_layout({"rooms_count": 3, "bathrooms_count": 2})
        assert result == 4.0  # 1.5 (rooms) + 2.0 (bathrooms) + 0.5 (orientation)

    def test_1_bathroom(self):
        """1 bathroom should add 1.0 point."""
        result = _score_layout({"rooms_count": 3, "bathrooms_count": 1})
        assert result == 3.0  # 1.5 (rooms) + 1.0 (bathroom) + 0.5 (orientation)

    def test_south_orientation(self):
        """South orientation should add 1.0 point."""
        result = _score_layout({"rooms_count": 3, "bathrooms_count": 1, "orientation": "south"})
        assert result == 3.5  # 1.5 + 1.0 + 1.0

    def test_south_bulgarian(self):
        """Bulgarian 'юг' orientation should add 1.0 point."""
        result = _score_layout({"rooms_count": 3, "bathrooms_count": 1, "orientation": "юг"})
        assert result == 3.5

    def test_east_orientation(self):
        """East orientation should add 0.75 points."""
        result = _score_layout({"rooms_count": 3, "bathrooms_count": 1, "orientation": "east"})
        assert result == 3.25  # 1.5 + 1.0 + 0.75

    def test_other_orientation(self):
        """Other orientation should add 0.5 points."""
        result = _score_layout({"rooms_count": 3, "bathrooms_count": 1, "orientation": "north"})
        assert result == 3.0  # 1.5 + 1.0 + 0.5

    def test_perfect_layout(self):
        """Perfect layout should cap at 5.0."""
        result = _score_layout({"rooms_count": 4, "bathrooms_count": 2, "orientation": "south"})
        assert result == 5.0  # 2.0 + 2.0 + 1.0 = 5.0


class TestScoreBuilding:
    """Tests for _score_building helper."""

    def test_panel_building(self):
        """Panel building should return 1.0."""
        result = _score_building({"building_type": "panel"})
        assert result == 1.0

    def test_panel_bulgarian(self):
        """Bulgarian 'панелен' should return 1.0."""
        result = _score_building({"building_type": "панелен блок"})
        assert result == 1.0

    def test_new_construction(self):
        """New construction should return 4.5."""
        result = _score_building({"building_type": "new construction"})
        assert result == 4.5

    def test_new_bulgarian(self):
        """Bulgarian 'ново' should return 4.5."""
        result = _score_building({"building_type": "ново строителство"})
        assert result == 4.5

    def test_brick_year_2000_or_later(self):
        """Brick >= 2000 should return 4.0."""
        result = _score_building({"building_type": "brick", "construction_year": 2005})
        assert result == 4.0

    def test_brick_year_1980_to_1999(self):
        """Brick 1980-1999 should return 3.5."""
        result = _score_building({"building_type": "brick", "construction_year": 1990})
        assert result == 3.5

    def test_brick_year_before_1980(self):
        """Brick < 1980 should return 3.0."""
        result = _score_building({"building_type": "brick", "construction_year": 1970})
        assert result == 3.0

    def test_brick_no_year(self):
        """Brick without year should return 3.0."""
        result = _score_building({"building_type": "brick"})
        assert result == 3.0

    def test_unknown_building(self):
        """Unknown building type should return 2.5."""
        result = _score_building({})
        assert result == 2.5


class TestScoreRental:
    """Tests for _score_rental helper."""

    def test_base_score(self):
        """Base rental score should be 2.5."""
        result = _score_rental({})
        assert result == 2.5

    def test_near_schools(self):
        """Near schools should add 0.5."""
        result = _score_rental({"near_schools": True})
        assert result == 3.0  # 2.5 + 0.5

    def test_metro_400m_or_less(self):
        """Metro <= 400m should add 1.0."""
        result = _score_rental({"metro_distance_m": 300})
        assert result == 3.5  # 2.5 + 1.0

    def test_metro_401_to_600m(self):
        """Metro 401-600m should add 0.5."""
        result = _score_rental({"metro_distance_m": 500})
        assert result == 3.0  # 2.5 + 0.5

    def test_metro_over_600m(self):
        """Metro > 600m should not add points."""
        result = _score_rental({"metro_distance_m": 700})
        assert result == 2.5

    def test_near_restaurants_or_supermarket(self):
        """Near restaurants/supermarket should add 0.5."""
        result = _score_rental({"near_restaurants": True})
        assert result == 3.0
        result = _score_rental({"near_supermarket": True})
        assert result == 3.0

    def test_is_furnished(self):
        """Furnished should add 0.5."""
        result = _score_rental({"is_furnished": True})
        assert result == 3.0

    def test_perfect_rental(self):
        """Perfect rental should cap at 5.0."""
        result = _score_rental({
            "near_schools": True,
            "metro_distance_m": 300,
            "near_restaurants": True,
            "near_supermarket": True,
            "is_furnished": True
        })
        assert result == 5.0  # 2.5 + 0.5 + 1.0 + 0.5 + 0.5 = 5.0, capped


class TestScoreExtras:
    """Tests for _score_extras helper."""

    def test_no_extras(self):
        """No extras should return 2.0."""
        result = _score_extras({})
        assert result == 2.0

    def test_has_storage(self):
        """Storage should add 1.5."""
        result = _score_extras({"has_storage": True})
        assert result == 1.5  # Just the extra, no base

    def test_has_parking(self):
        """Parking should add 1.5."""
        result = _score_extras({"has_parking": True})
        assert result == 1.5

    def test_has_garage(self):
        """Garage should add 2.0."""
        result = _score_extras({"has_garage": True})
        assert result == 2.0

    def test_has_ac_preinstalled(self):
        """AC preinstalled should add 0.5."""
        result = _score_extras({"has_ac_preinstalled": True})
        assert result == 0.5

    def test_has_builtin_wardrobes(self):
        """Built-in wardrobes should add 0.5."""
        result = _score_extras({"has_builtin_wardrobes": True})
        assert result == 0.5

    def test_multiple_extras(self):
        """Multiple extras should sum and cap at 5.0."""
        result = _score_extras({
            "has_storage": True,
            "has_parking": True,
            "has_garage": True
        })
        assert result == 5.0  # 1.5 + 1.5 + 2.0 = 5.0, capped

    def test_all_extras(self):
        """All extras should cap at 5.0."""
        result = _score_extras({
            "has_storage": True,
            "has_parking": True,
            "has_garage": True,
            "has_ac_preinstalled": True,
            "has_builtin_wardrobes": True
        })
        assert result == 5.0  # Capped at 5.0


class TestCalculateScore:
    """Integration tests for calculate_score."""

    def test_returns_score_breakdown(self):
        """Should return ScoreBreakdown with all fields."""
        result = calculate_score({})
        assert isinstance(result, ScoreBreakdown)
        assert hasattr(result, "location")
        assert hasattr(result, "price_sqm")
        assert hasattr(result, "condition")
        assert hasattr(result, "layout")
        assert hasattr(result, "building")
        assert hasattr(result, "rental")
        assert hasattr(result, "extras")
        assert hasattr(result, "total_weighted")

    def test_total_weighted_in_range(self):
        """Total weighted score should be 0-5."""
        result = calculate_score({})
        assert 0 <= result.total_weighted <= 5

    def test_perfect_listing_high_score(self):
        """Perfect listing should get high score."""
        perfect = {
            "metro_distance_m": 200,
            "district": "lozenets",
            "price_per_sqm_eur": 1500,
            "condition": "ready",
            "price_eur": 150000,
            "estimated_renovation_eur": 0,
            "rooms_count": 4,
            "bathrooms_count": 2,
            "orientation": "south",
            "building_type": "new construction",
            "near_schools": True,
            "near_restaurants": True,
            "is_furnished": True,
            "has_storage": True,
            "has_parking": True,
            "has_garage": True,
        }
        result = calculate_score(perfect)
        assert result.total_weighted >= 4.5  # Should be very high

    def test_poor_listing_low_score(self):
        """Poor listing should get low score."""
        poor = {
            "metro_distance_m": 800,
            "district": "unknown",
            "price_per_sqm_eur": 3500,
            "condition": "bare",
            "price_eur": 250000,
            "estimated_renovation_eur": 30000,
            "rooms_count": 2,
            "bathrooms_count": 1,
            "orientation": "north",
            "building_type": "panel",
        }
        result = calculate_score(poor)
        assert result.total_weighted <= 2.5  # Should be low

    def test_weights_sum_to_100(self):
        """Weights should sum to 100."""
        assert sum(WEIGHTS.values()) == 100

    def test_individual_scores_0_to_5(self):
        """Each individual score should be 0-5."""
        listing = {
            "metro_distance_m": 300,
            "district": "iztok",
            "price_per_sqm_eur": 2000,
            "condition": "renovation",
            "price_eur": 200000,
            "rooms_count": 3,
            "bathrooms_count": 2,
            "building_type": "brick",
            "construction_year": 2000,
        }
        result = calculate_score(listing)
        assert 0 <= result.location <= 5
        assert 0 <= result.price_sqm <= 5
        assert 0 <= result.condition <= 5
        assert 0 <= result.layout <= 5
        assert 0 <= result.building <= 5
        assert 0 <= result.rental <= 5
        assert 0 <= result.extras <= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
