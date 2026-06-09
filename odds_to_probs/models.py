"""
De-vigging models: Power Transform and Shin.

Both models take raw bookmaker odds (home, draw, away) and return
fair probabilities with the overround removed.
"""

import numpy as np
from .config import (
    GLOBAL_POWER_ALPHA,
    GLOBAL_SHIN_Z,
    BOOKMAKER_POWER_ALPHA,
    BOOKMAKER_SHIN_Z,
)


def _resolve_bookmaker(bookmaker: str | None) -> str | None:
    """Normalise bookmaker name for dict lookup."""
    if bookmaker is None:
        return None
    return bookmaker.strip().lower()


# ---------------------------------------------------------------------------
# Power Transform model
# ---------------------------------------------------------------------------

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

    Parameters
    ----------
    odds_home, odds_draw, odds_away : decimal odds (e.g. 2.50)
    bookmaker : optional bookmaker name; uses its calibrated alpha if known
    alpha : override alpha directly (takes precedence over bookmaker lookup)

    Returns
    -------
    (p_home, p_draw, p_away) summing to 1.0
    """
    pi = np.array([1.0 / odds_home, 1.0 / odds_draw, 1.0 / odds_away])

    if alpha is None:
        key = _resolve_bookmaker(bookmaker)
        alpha = BOOKMAKER_POWER_ALPHA.get(key, GLOBAL_POWER_ALPHA) if key else GLOBAL_POWER_ALPHA

    p = pi ** alpha
    p /= p.sum()
    return float(p[0]), float(p[1]), float(p[2])


# ---------------------------------------------------------------------------
# Shin model
# ---------------------------------------------------------------------------

def _shin_probs_single(pi: np.ndarray, S: float, z: float) -> np.ndarray:
    """Vectorised Shin formula for one match."""
    num = np.sqrt(z**2 + 4.0 * (1.0 - z) * (pi**2 / S)) - z
    den = 2.0 * (1.0 - z)
    if den < 1e-10:
        p = pi / S
    else:
        p = num / den
    p /= p.sum()
    return p


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

    Parameters
    ----------
    odds_home, odds_draw, odds_away : decimal odds (e.g. 2.50)
    bookmaker : optional bookmaker name; uses its calibrated z if known
    z : override z directly (takes precedence over bookmaker lookup)

    Returns
    -------
    (p_home, p_draw, p_away) summing to 1.0
    """
    pi = np.array([1.0 / odds_home, 1.0 / odds_draw, 1.0 / odds_away])
    S = pi.sum()

    if z is None:
        key = _resolve_bookmaker(bookmaker)
        z = BOOKMAKER_SHIN_Z.get(key, GLOBAL_SHIN_Z) if key else GLOBAL_SHIN_Z

    p = _shin_probs_single(pi, S, z)
    return float(p[0]), float(p[1]), float(p[2])


# ---------------------------------------------------------------------------
# Ensemble average
# ---------------------------------------------------------------------------

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

    This is the recommended default: both models beat the multiplicative
    baseline, and averaging reduces variance further.
    """
    pw = np.array(power_probs(odds_home, odds_draw, odds_away, bookmaker, alpha))
    sh = np.array(shin_probs(odds_home, odds_draw, odds_away, bookmaker, z))
    avg = (pw + sh) / 2.0
    return float(avg[0]), float(avg[1]), float(avg[2])
