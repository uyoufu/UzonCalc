import math
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

from JTG_3363_2019_shallow_foundation import (  # noqa: E402
    DEFAULT_LOAD_CASES,
    RectangleFoundation,
    evaluate_load_case,
)


def test_rectangle_foundation_properties():
    foundation = RectangleFoundation(length=8.0, width=6.0)

    assert foundation.area == 48.0
    assert foundation.inertia_x == 144.0
    assert math.isclose(foundation.inertia_y, 256.0)
    assert foundation.edge_x == 4.0
    assert foundation.edge_y == 3.0


def test_evaluate_load_case_uses_conservative_corner_stress():
    foundation = RectangleFoundation(length=8.0, width=6.0)
    result = evaluate_load_case(foundation, DEFAULT_LOAD_CASES[0], bearing_capacity=300.0)

    assert result.sigma_avg == 100.0 / 48.0
    assert math.isclose(result.sigma_max, 2.708333333333333)
    assert math.isclose(result.sigma_min, 1.4583333333333333)
    assert math.isclose(result.bearing_safety_factor, 110.76923076923077)
    assert math.isclose(result.average_safety_factor, 144.0)
    assert math.isclose(result.eccentric_value, 0.3)
    assert math.isclose(result.eccentric_safety_factor, 3.3333333333333335)


def test_evaluate_load_case_combines_biaxial_moments():
    foundation = RectangleFoundation(length=8.0, width=6.0)
    result = evaluate_load_case(foundation, DEFAULT_LOAD_CASES[2], bearing_capacity=300.0)

    assert math.isclose(result.sigma_max, 3.177083333333333)
    assert math.isclose(result.sigma_min, 0.9895833333333333)
    assert math.isclose(result.bearing_safety_factor, 141.63934426229508)
    assert math.isclose(result.eccentric_value, 0.525)
    assert math.isclose(result.eccentric_safety_factor, 2.857142857142857)
