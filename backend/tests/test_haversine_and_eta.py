"""Test suite for Haversine distance math and dynamic ETA calculations."""

import pytest
from app.services.order_service import calculate_haversine_distance_km, CATEGORY_PREP_MINUTES


def test_haversine_same_point_is_zero():
    """Distance between identical coordinates is 0.0 km."""
    lat, lng = 12.9716, 77.5946
    assert calculate_haversine_distance_km(lat, lng, lat, lng) == 0.0


def test_haversine_indiranagar_to_koramangala():
    """Indiranagar (12.9784, 77.6408) to Koramangala (12.9352, 77.6245) is approx 5-6 km."""
    dist = calculate_haversine_distance_km(12.9784, 77.6408, 12.9352, 77.6245)
    assert 4.5 <= dist <= 6.5


def test_haversine_whitefield_to_electronic_city():
    """Whitefield (12.9698, 77.7500) to Electronic City (12.8452, 77.6602) is approx 15-20 km."""
    dist = calculate_haversine_distance_km(12.9698, 77.7500, 12.8452, 77.6602)
    assert 14.0 <= dist <= 22.0


def test_haversine_symmetry():
    """Distance from A to B is strictly equal to distance from B to A."""
    p1 = (12.9279, 77.6271)
    p2 = (13.0358, 77.5970)
    assert calculate_haversine_distance_km(p1[0], p1[1], p2[0], p2[1]) == calculate_haversine_distance_km(p2[0], p2[1], p1[0], p1[1])


def test_category_prep_time_sanity():
    """Cooked foods take longer to prepare than pre-made bakery items."""
    assert CATEGORY_PREP_MINUTES["Biryani"] > CATEGORY_PREP_MINUTES["Cakes"]
    assert CATEGORY_PREP_MINUTES["Main Course"] > CATEGORY_PREP_MINUTES["Beverages"]
    assert CATEGORY_PREP_MINUTES["Party Supplies"] <= 5


def test_haversine_antipodal_extreme():
    """Halfway around earth (equator 0,0 to 0,180) is approx ~20,000 km."""
    dist = calculate_haversine_distance_km(0.0, 0.0, 0.0, 180.0)
    assert 19900 <= dist <= 20100
