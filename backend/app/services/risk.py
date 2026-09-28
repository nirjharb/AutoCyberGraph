"""
TARA risk calculation — application implementation, configurable.

This is a documented engineering risk method implemented by AutoCyberGraph.
It is NOT an official ISO/SAE 21434 certification methodology and must not be
presented as one. See docs/tara.md.

Method:
    score = (impact_level + 1) * (feasibility_level + 1)      # 1 .. 25
    CRITICAL  score >= 20
    HIGH      score >= 12
    MEDIUM    score >= 6
    LOW       otherwise

Impact and feasibility are 0..4 scales with configurable labels
(`IMPACT_LEVELS`, `FEASIBILITY_LEVELS`); organizations may tune them.
"""
from __future__ import annotations

from ..models import RiskLevel

IMPACT_LEVELS: dict[str, int] = {
    "NEGLIGIBLE": 0,
    "MINOR": 1,
    "MODERATE": 2,
    "MAJOR": 3,
    "SEVERE": 4,
}

FEASIBILITY_LEVELS: dict[str, int] = {
    "VERY_LOW": 0,
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "VERY_HIGH": 4,
}

THRESHOLDS: list[tuple[int, RiskLevel]] = [
    (20, RiskLevel.CRITICAL),
    (12, RiskLevel.HIGH),
    (6, RiskLevel.MEDIUM),
    (0, RiskLevel.LOW),
]


def normalize_impact(impact: str) -> int:
    return IMPACT_LEVELS.get(impact.strip().upper(), 2)


def normalize_feasibility(feasibility: str) -> int:
    return FEASIBILITY_LEVELS.get(feasibility.strip().upper(), 2)


def risk_from_score(score: int) -> RiskLevel:
    for minimum, level in THRESHOLDS:
        if score >= minimum:
            return level
    return RiskLevel.LOW


def calculate_risk(impact: str, attack_feasibility: str) -> tuple[str, int, int, RiskLevel]:
    """Return (risk_level, impact_level, feasibility_level, enum)."""
    impact_level = normalize_impact(impact)
    feasibility_level = normalize_feasibility(attack_feasibility)
    score = (impact_level + 1) * (feasibility_level + 1)
    risk = risk_from_score(score)
    return risk.value, impact_level, feasibility_level, risk


def risk_from_levels(impact_level: int, feasibility_level: int) -> RiskLevel:
    return risk_from_score((impact_level + 1) * (feasibility_level + 1))
