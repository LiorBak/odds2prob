"""
Calibrated model parameters from out-of-sample backtesting (train ≤ 2023, test 2024-2025).

Global parameters were fitted on all bookmakers combined.
Per-bookmaker parameters were fitted on each bookmaker's data independently.
"""

# Global calibrated parameters (fallback when bookmaker is unknown)
GLOBAL_POWER_ALPHA = 1.046646   # Power model exponent a
GLOBAL_SHIN_Z = 0.028471        # Shin model insider-fraction z

# Per-bookmaker calibrated parameters
# Keys are lowercase, stripped bookmaker names for fuzzy matching
BOOKMAKER_POWER_ALPHA: dict[str, float] = {
    "betsson":   1.05427,
    "bet365":    1.04371,
    "888sport":  1.05968,
    "1xbet":     1.00032,
    "ggbet":     1.04590,
    "22bet":     1.02493,
    "betinasia": 1.05087,
    "n1 bet":    1.06147,
    "inkabet":   0.91956,
    "doradobet": 0.95087,
}

BOOKMAKER_SHIN_Z: dict[str, float] = {
    "betsson":   0.03225,
    "bet365":    0.02697,
    "888sport":  0.03561,
    "1xbet":     0.00043,
    "ggbet":     0.02445,
    "22bet":     0.01154,
    "betinasia": 0.02637,
    "n1 bet":    0.03697,
    "inkabet":   0.00001,
    "doradobet": 0.00001,
}

SUPPORTED_BOOKMAKERS = sorted(BOOKMAKER_POWER_ALPHA.keys())
