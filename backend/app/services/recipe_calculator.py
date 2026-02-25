def estimate_abv(og: float, fg: float) -> float:
    """Estimate ABV from OG and FG using a standard approximation."""
    return round((og - fg) * 131.25, 2)


def attenuation_pct(og: float, fg: float) -> float:
    if og <= 1.0:
        return 0.0
    return round(((og - fg) / (og - 1.0)) * 100, 2)
