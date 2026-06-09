"""
De-vigging models: Power Transform and Shin.

Both models take raw bookmaker odds (home, draw, away) and return
fair probabilities with the overround removed. Pure Python, no dependencies.
"""

import math
from .config import (
    GLOBAL_POWER_ALPHA,
    GLOBAL_SHIN_Z,
    BOOKMAKER_POWER_ALPHA,
    BOOKMAKER_SHIN_Z,
)


def _resolve_bookmaker(bookmaker: str | None) -> str | None:
    if bookmaker is None:
        return None
    return bookmaker.strip().lower()


def power_probs(
    odds_home: float,
    odds_draw: float,
    odds_away: float,
    bookmaker: str | None = None,
    alpha: float | None = None,
) -> tuple[float, float, float]:
    """
    Convert 1X2 odds to fair probabilities using the Power Transform model.

    p_i = pi_i^a / sum(pi_j^a)
    """
    if alpha is None:
        key = _resolve_bookmaker(bookmaker)
        alpha = BOOKMAKER_POWER_ALPHA.get(key, GLOBAL_POWER_ALPHA) if key else GLOBAL_POWER_ALPHA

    pi = [1.0 / odds_home, 1.0 / odds_draw, 1.0 / odds_away]
    p = [x ** alpha for x in pi]
    total = sum(p)
    return p[0] / total, p[1] / total, p[2] / total


def shin_probs(
    odds_home: float,
    odds_draw: float,
    odds_away: float,
    bookmaker: str | None = None,
    z: float | None = None,
) -> tuple[float, float, float]:
    """
    Convert 1X2 odds to fair probabilities using Shin's model.

    Shin (1992) models insider trading: z is the fraction of bets from
    insiders; z=0 reduces to the multiplicative (basic) model.
    """
    if z is None:
        key = _resolve_bookmaker(bookmaker)
        z = BOOKMAKER_SHIN_Z.get(key, GLOBAL_SHIN_Z) if key else GLOBAL_SHIN_Z

    pi = [1.0 / odds_home, 1.0 / odds_draw, 1.0 / odds_away]
    S = sum(pi)
    den = 2.0 * (1.0 - z)

    if den < 1e-10:
        p = [x / S for x in pi]
    else:
        p = [(math.sqrt(z**2 + 4.0 * (1.0 - z) * (x**2 / S)) - z) / den for x in pi]

    total = sum(p)
    return p[0] / total, p[1] / total, p[2] / total


def average_probs(
    odds_home: float,
    odds_draw: float,
    odds_away: float,
    bookmaker: str | None = None,
    alpha: float | None = None,
    z: float | None = None,
) -> tuple[float, float, float]:
    """
    Return the simple average of Power and Shin model probabilities.

    Recommended default: both models beat the multiplicative baseline,
    and averaging reduces variance further.
    """
    pw = power_probs(odds_home, odds_draw, odds_away, bookmaker, alpha)
    sh = shin_probs(odds_home, odds_draw, odds_away, bookmaker, z)
    return (
        (pw[0] + sh[0]) / 2.0,
        (pw[1] + sh[1]) / 2.0,
        (pw[2] + sh[2]) / 2.0,
    )
