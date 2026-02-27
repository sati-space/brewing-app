from __future__ import annotations

import math
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class HopProfile:
    name: str
    aliases: tuple[str, ...]
    alpha_acid_min_pct: float
    alpha_acid_max_pct: float
    flavor_descriptors: tuple[str, ...]
    flavor_vector: tuple[float, ...]
    use: str


@dataclass(frozen=True)
class HopSubstitutionCandidate:
    name: str
    alpha_acid_min_pct: float
    alpha_acid_max_pct: float
    flavor_similarity_score: float
    descriptor_overlap_score: float
    similarity_score: float
    recommended_bittering_ratio: float
    shared_descriptors: tuple[str, ...]


@dataclass(frozen=True)
class HopSubstitutionResult:
    target_hop: HopProfile
    substitutions: tuple[HopSubstitutionCandidate, ...]
    unresolved_hop_names: tuple[str, ...]
    recognized_candidate_count: int


_HOP_PROFILES: tuple[HopProfile, ...] = (
    HopProfile(
        name="Amarillo",
        aliases=("amarillo",),
        alpha_acid_min_pct=8.0,
        alpha_acid_max_pct=11.0,
        flavor_descriptors=("citrus", "floral", "orange", "tropical"),
        flavor_vector=(4.1, 3.4, 0.8, 1.0, 2.3, 0.8, 0.3, 0.2, 1.6, 0.3, 0.5),
        use="dual-purpose",
    ),
    HopProfile(
        name="Cascade",
        aliases=("cascade",),
        alpha_acid_min_pct=4.5,
        alpha_acid_max_pct=7.0,
        flavor_descriptors=("citrus", "floral", "grapefruit", "spicy"),
        flavor_vector=(4.0, 1.2, 1.0, 0.7, 2.4, 1.2, 1.0, 0.4, 0.5, 0.2, 0.2),
        use="dual-purpose",
    ),
    HopProfile(
        name="Centennial",
        aliases=("centennial",),
        alpha_acid_min_pct=9.5,
        alpha_acid_max_pct=11.5,
        flavor_descriptors=("citrus", "floral", "pine"),
        flavor_vector=(4.0, 1.5, 2.1, 1.2, 1.9, 0.9, 0.4, 0.2, 0.6, 0.1, 0.4),
        use="dual-purpose",
    ),
    HopProfile(
        name="Chinook",
        aliases=("chinook",),
        alpha_acid_min_pct=12.0,
        alpha_acid_max_pct=14.0,
        flavor_descriptors=("grapefruit", "pine", "resin", "spicy"),
        flavor_vector=(2.7, 0.9, 3.8, 3.6, 0.8, 1.0, 1.8, 0.5, 0.3, 0.1, 1.6),
        use="dual-purpose",
    ),
    HopProfile(
        name="Citra",
        aliases=("citra",),
        alpha_acid_min_pct=11.0,
        alpha_acid_max_pct=14.0,
        flavor_descriptors=("citrus", "tropical", "stone fruit"),
        flavor_vector=(4.8, 4.7, 0.5, 0.9, 0.9, 0.3, 0.1, 0.1, 3.3, 0.4, 1.0),
        use="aroma",
    ),
    HopProfile(
        name="Columbus",
        aliases=("columbus", "ctz", "tomahawk", "zeus"),
        alpha_acid_min_pct=14.0,
        alpha_acid_max_pct=18.0,
        flavor_descriptors=("citrus", "dank", "resin", "spicy"),
        flavor_vector=(2.5, 0.9, 2.0, 3.9, 0.5, 0.7, 1.1, 0.4, 0.2, 0.3, 3.9),
        use="bittering",
    ),
    HopProfile(
        name="Crystal",
        aliases=("crystal",),
        alpha_acid_min_pct=3.0,
        alpha_acid_max_pct=6.0,
        flavor_descriptors=("citrus", "floral", "spicy"),
        flavor_vector=(2.2, 0.8, 0.4, 0.4, 2.0, 1.4, 1.3, 0.7, 0.2, 0.1, 0.2),
        use="aroma",
    ),
    HopProfile(
        name="East Kent Goldings",
        aliases=("east kent goldings", "ekg"),
        alpha_acid_min_pct=4.0,
        alpha_acid_max_pct=6.0,
        flavor_descriptors=("earthy", "floral", "honey", "spicy"),
        flavor_vector=(0.4, 0.2, 0.3, 0.2, 2.6, 1.7, 1.7, 3.1, 0.2, 0.1, 0.2),
        use="aroma",
    ),
    HopProfile(
        name="Fuggle",
        aliases=("fuggle", "fuggles"),
        alpha_acid_min_pct=3.5,
        alpha_acid_max_pct=5.5,
        flavor_descriptors=("earthy", "herbal", "woody"),
        flavor_vector=(0.3, 0.2, 0.2, 0.2, 1.4, 2.6, 0.8, 3.7, 0.1, 0.1, 0.1),
        use="aroma",
    ),
    HopProfile(
        name="Hallertau Mittelfruh",
        aliases=("hallertau mittelfruh", "hallertau"),
        alpha_acid_min_pct=3.0,
        alpha_acid_max_pct=5.5,
        flavor_descriptors=("floral", "herbal", "spicy"),
        flavor_vector=(0.3, 0.1, 0.2, 0.1, 2.8, 2.1, 1.7, 1.9, 0.1, 0.1, 0.1),
        use="aroma",
    ),
    HopProfile(
        name="Magnum",
        aliases=("magnum",),
        alpha_acid_min_pct=12.0,
        alpha_acid_max_pct=15.0,
        flavor_descriptors=("clean", "herbal", "light citrus"),
        flavor_vector=(1.1, 0.2, 0.7, 0.8, 0.4, 1.6, 0.4, 0.5, 0.1, 0.1, 0.2),
        use="bittering",
    ),
    HopProfile(
        name="Mosaic",
        aliases=("mosaic",),
        alpha_acid_min_pct=10.5,
        alpha_acid_max_pct=13.5,
        flavor_descriptors=("berry", "citrus", "dank", "tropical"),
        flavor_vector=(4.1, 4.4, 1.3, 2.2, 0.9, 0.5, 0.2, 0.2, 2.2, 3.8, 2.8),
        use="aroma",
    ),
    HopProfile(
        name="Nugget",
        aliases=("nugget",),
        alpha_acid_min_pct=11.0,
        alpha_acid_max_pct=14.0,
        flavor_descriptors=("herbal", "resin", "spicy"),
        flavor_vector=(1.4, 0.4, 1.9, 2.9, 0.5, 2.1, 1.7, 0.6, 0.2, 0.1, 0.8),
        use="bittering",
    ),
    HopProfile(
        name="Saaz",
        aliases=("saaz",),
        alpha_acid_min_pct=2.5,
        alpha_acid_max_pct=4.5,
        flavor_descriptors=("floral", "herbal", "spicy"),
        flavor_vector=(0.2, 0.1, 0.1, 0.1, 2.2, 2.5, 2.0, 1.7, 0.1, 0.1, 0.1),
        use="aroma",
    ),
    HopProfile(
        name="Simcoe",
        aliases=("simcoe",),
        alpha_acid_min_pct=12.0,
        alpha_acid_max_pct=14.0,
        flavor_descriptors=("berry", "citrus", "dank", "pine", "resin"),
        flavor_vector=(3.1, 2.2, 3.8, 3.4, 0.7, 0.7, 0.4, 0.2, 1.0, 1.6, 2.6),
        use="dual-purpose",
    ),
    HopProfile(
        name="Warrior",
        aliases=("warrior",),
        alpha_acid_min_pct=14.0,
        alpha_acid_max_pct=17.0,
        flavor_descriptors=("citrus", "clean", "resin"),
        flavor_vector=(1.5, 0.4, 1.5, 2.3, 0.3, 0.8, 0.5, 0.3, 0.2, 0.1, 0.8),
        use="bittering",
    ),
)

_SEPARATOR_PATTERN = re.compile(r"[^a-z0-9]+")
_NOISE_TOKENS = {"hop", "hops", "pellet", "pellets", "t90", "wholecone", "whole", "leaf", "cryo"}

_HOPS_BY_ALIAS: dict[str, HopProfile] = {}
for _hop in _HOP_PROFILES:
    canonical = _SEPARATOR_PATTERN.sub(" ", _hop.name.lower()).strip()
    _HOPS_BY_ALIAS[canonical] = _hop
    for _alias in _hop.aliases:
        _HOPS_BY_ALIAS[_SEPARATOR_PATTERN.sub(" ", _alias.lower()).strip()] = _hop


def normalize_hop_name(name: str) -> str:
    raw_tokens = [token for token in _SEPARATOR_PATTERN.split(name.lower().strip()) if token]
    kept_tokens = [token for token in raw_tokens if token not in _NOISE_TOKENS]
    return " ".join(kept_tokens)


def resolve_hop_profile(name: str) -> HopProfile | None:
    normalized = normalize_hop_name(name)
    if not normalized:
        return None
    return _HOPS_BY_ALIAS.get(normalized)


def recommend_hop_substitutions(
    *,
    target_hop_name: str,
    available_hop_names: list[str],
    top_k: int = 5,
) -> HopSubstitutionResult:
    target_hop = resolve_hop_profile(target_hop_name)
    if target_hop is None:
        raise ValueError("Target hop is not recognized by the flavor catalog.")

    unresolved: list[str] = []
    candidates: list[HopSubstitutionCandidate] = []
    seen_normalized: set[str] = set()

    for candidate_name in available_hop_names:
        normalized_name = normalize_hop_name(candidate_name)
        if not normalized_name or normalized_name in seen_normalized:
            continue
        seen_normalized.add(normalized_name)

        candidate_hop = resolve_hop_profile(candidate_name)
        if candidate_hop is None:
            unresolved.append(candidate_name)
            continue
        if candidate_hop.name == target_hop.name:
            continue
        candidates.append(_score_candidate(target_hop=target_hop, candidate_hop=candidate_hop))

    candidates.sort(key=lambda row: (-row.similarity_score, row.name))

    return HopSubstitutionResult(
        target_hop=target_hop,
        substitutions=tuple(candidates[:top_k]),
        unresolved_hop_names=tuple(unresolved),
        recognized_candidate_count=len(candidates),
    )


def _score_candidate(*, target_hop: HopProfile, candidate_hop: HopProfile) -> HopSubstitutionCandidate:
    flavor_similarity = _cosine_similarity(target_hop.flavor_vector, candidate_hop.flavor_vector)

    target_descriptors = set(target_hop.flavor_descriptors)
    candidate_descriptors = set(candidate_hop.flavor_descriptors)
    shared_descriptors = tuple(sorted(target_descriptors.intersection(candidate_descriptors)))
    descriptor_overlap = len(shared_descriptors) / len(target_descriptors) if target_descriptors else 0.0

    target_alpha_mid = _alpha_midpoint(target_hop)
    candidate_alpha_mid = _alpha_midpoint(candidate_hop)
    alpha_gap_ratio = abs(candidate_alpha_mid - target_alpha_mid) / max(target_alpha_mid, 0.1)
    alpha_similarity = max(0.0, 1.0 - min(alpha_gap_ratio, 1.0))

    use_bonus = 0.05 if target_hop.use == candidate_hop.use else 0.0
    similarity_score = min(1.0, (0.65 * flavor_similarity) + (0.2 * descriptor_overlap) + (0.15 * alpha_similarity) + use_bonus)
    recommended_bittering_ratio = target_alpha_mid / max(candidate_alpha_mid, 0.1)

    return HopSubstitutionCandidate(
        name=candidate_hop.name,
        alpha_acid_min_pct=round(candidate_hop.alpha_acid_min_pct, 2),
        alpha_acid_max_pct=round(candidate_hop.alpha_acid_max_pct, 2),
        flavor_similarity_score=round(flavor_similarity, 3),
        descriptor_overlap_score=round(descriptor_overlap, 3),
        similarity_score=round(similarity_score, 3),
        recommended_bittering_ratio=round(recommended_bittering_ratio, 3),
        shared_descriptors=shared_descriptors,
    )


def _alpha_midpoint(hop: HopProfile) -> float:
    return (hop.alpha_acid_min_pct + hop.alpha_acid_max_pct) / 2.0


def _cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
