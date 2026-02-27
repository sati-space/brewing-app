from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IonRange:
    min_ppm: float
    max_ppm: float

    @property
    def target_ppm(self) -> float:
        return (self.min_ppm + self.max_ppm) / 2.0


@dataclass(frozen=True)
class BJCPStyleProfile:
    code: str
    name: str
    category: str
    impression: str
    examples: tuple[str, ...]
    calcium_ppm: IonRange
    magnesium_ppm: IonRange
    sodium_ppm: IonRange
    chloride_ppm: IonRange
    sulfate_ppm: IonRange
    bicarbonate_ppm: IonRange


_BJCP_STYLES: tuple[BJCPStyleProfile, ...] = (
    BJCPStyleProfile(
        code="8A",
        name="Munich Helles",
        category="German Lager",
        impression="Pale, smooth lager with restrained bitterness and soft malt balance.",
        examples=("Augustiner Lagerbier Hell", "Weihenstephaner Original"),
        calcium_ppm=IonRange(30, 60),
        magnesium_ppm=IonRange(5, 15),
        sodium_ppm=IonRange(0, 30),
        chloride_ppm=IonRange(40, 90),
        sulfate_ppm=IonRange(20, 80),
        bicarbonate_ppm=IonRange(0, 80),
    ),
    BJCPStyleProfile(
        code="15B",
        name="Irish Stout",
        category="Irish Beer",
        impression="Dry, roasty stout with moderate bitterness and dark grain character.",
        examples=("Guinness Draught", "Murphy's Irish Stout"),
        calcium_ppm=IonRange(70, 130),
        magnesium_ppm=IonRange(10, 25),
        sodium_ppm=IonRange(10, 60),
        chloride_ppm=IonRange(40, 90),
        sulfate_ppm=IonRange(50, 150),
        bicarbonate_ppm=IonRange(150, 260),
    ),
    BJCPStyleProfile(
        code="18B",
        name="American Pale Ale",
        category="Pale American Ale",
        impression="Hop-forward pale ale with clean fermentation and balanced malt support.",
        examples=("Sierra Nevada Pale Ale", "Dale's Pale Ale"),
        calcium_ppm=IonRange(60, 130),
        magnesium_ppm=IonRange(5, 20),
        sodium_ppm=IonRange(0, 40),
        chloride_ppm=IonRange(40, 90),
        sulfate_ppm=IonRange(120, 240),
        bicarbonate_ppm=IonRange(0, 120),
    ),
    BJCPStyleProfile(
        code="20A",
        name="American Porter",
        category="American Porter and Stout",
        impression="Assertive porter with roast, dark chocolate, and often hop character.",
        examples=("Anchor Porter", "Deschutes Black Butte Porter"),
        calcium_ppm=IonRange(70, 140),
        magnesium_ppm=IonRange(8, 24),
        sodium_ppm=IonRange(10, 60),
        chloride_ppm=IonRange(50, 130),
        sulfate_ppm=IonRange(50, 140),
        bicarbonate_ppm=IonRange(120, 240),
    ),
    BJCPStyleProfile(
        code="21A",
        name="American IPA",
        category="IPA",
        impression="Decisively hoppy, bitter, and dry with expressive American/New World hops.",
        examples=("Sierra Nevada Torpedo", "Stone IPA"),
        calcium_ppm=IonRange(80, 150),
        magnesium_ppm=IonRange(8, 22),
        sodium_ppm=IonRange(0, 40),
        chloride_ppm=IonRange(40, 100),
        sulfate_ppm=IonRange(180, 320),
        bicarbonate_ppm=IonRange(0, 90),
    ),
    BJCPStyleProfile(
        code="21B",
        name="Specialty IPA",
        category="IPA",
        impression="IPA family variants that retain hop-forward character with subtype-specific traits.",
        examples=("Black IPA examples", "Red IPA examples"),
        calcium_ppm=IonRange(80, 150),
        magnesium_ppm=IonRange(8, 22),
        sodium_ppm=IonRange(0, 45),
        chloride_ppm=IonRange(50, 120),
        sulfate_ppm=IonRange(140, 280),
        bicarbonate_ppm=IonRange(0, 140),
    ),
    BJCPStyleProfile(
        code="21C",
        name="Hazy IPA",
        category="IPA",
        impression="Juicy IPA with saturated hop aroma and softer perceived bitterness.",
        examples=("Julius", "Hazy Little Thing"),
        calcium_ppm=IonRange(70, 140),
        magnesium_ppm=IonRange(8, 20),
        sodium_ppm=IonRange(0, 50),
        chloride_ppm=IonRange(120, 220),
        sulfate_ppm=IonRange(60, 150),
        bicarbonate_ppm=IonRange(0, 120),
    ),
    BJCPStyleProfile(
        code="24A",
        name="Witbier",
        category="Belgian Ale",
        impression="Light, hazy wheat ale with citrus-spice expression and low bitterness.",
        examples=("Hoegaarden", "Allagash White"),
        calcium_ppm=IonRange(40, 90),
        magnesium_ppm=IonRange(5, 15),
        sodium_ppm=IonRange(0, 35),
        chloride_ppm=IonRange(60, 130),
        sulfate_ppm=IonRange(30, 90),
        bicarbonate_ppm=IonRange(0, 110),
    ),
)

_BY_CODE = {style.code.upper(): style for style in _BJCP_STYLES}
_BY_NAME = {style.name.lower(): style for style in _BJCP_STYLES}


def list_bjcp_styles(search: str | None = None) -> list[BJCPStyleProfile]:
    if not search:
        return sorted(_BJCP_STYLES, key=lambda style: style.code)

    query = search.strip().lower()
    return [
        style
        for style in sorted(_BJCP_STYLES, key=lambda row: row.code)
        if query in style.code.lower() or query in style.name.lower() or query in style.category.lower()
    ]


def resolve_bjcp_style(identifier: str) -> BJCPStyleProfile | None:
    token = identifier.strip()
    if not token:
        return None

    direct = _BY_CODE.get(token.upper())
    if direct:
        return direct

    return _BY_NAME.get(token.lower())
