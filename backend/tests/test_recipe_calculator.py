from app.services.recipe_calculator import attenuation_pct, estimate_abv


def test_estimate_abv() -> None:
    assert estimate_abv(1.060, 1.012) == 6.3


def test_attenuation_pct() -> None:
    assert attenuation_pct(1.060, 1.012) == 80.0
