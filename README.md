# Odds to Probabilities API

Converts raw 1X2 bookmaker odds into **fair (de-vigged) probabilities** for football matches.  
Two independently calibrated models are available — **Power Transform** and **Shin** — plus an **ensemble average** that is the default.

---

## Background

Bookmakers embed a margin (overround) into their odds, so naively inverting them gives implied probabilities that sum to more than 1. *De-vigging* removes that margin to produce fair probabilities.

### Models

| Model | Parameter | What it does |
|---|---|---|
| **Power Transform** | α (alpha) | Raises each implied probability to the power α, then normalises. `α > 1` deflates the favourite. |
| **Shin** | z | Accounts for inside-trader fraction z in the market. `z = 0` reduces to the multiplicative baseline. |
| **Average** *(default)* | both | Simple mean of the two models; reduces variance. |

### Calibrated Parameters

Parameters were calibrated on ~19,000 European football matches (training ≤ 2023) and validated out-of-sample on 2024–2025 data.

**Global (used when bookmaker is unknown):**

| Model | Parameter | Test MSE |
|---|---|---|
| Power | α = 1.046646 | 0.189802 |
| Shin | z = 0.028471 | 0.189790 |
| Multiplicative baseline | — | 0.189995 |

**Per-bookmaker calibrated values:**

| Bookmaker | Power α | Shin z |
|---|---|---|
| Betsson | 1.05427 | 0.03225 |
| bet365 | 1.04371 | 0.02697 |
| 888sport | 1.05968 | 0.03561 |
| 1xBet | 1.00032 | 0.00043 |
| GGBET | 1.04590 | 0.02445 |
| 22Bet | 1.02493 | 0.01154 |
| BetInAsia | 1.05087 | 0.02637 |
| N1 Bet | 1.06147 | 0.03697 |
| Inkabet | 0.91956 | 0.00001 |
| DoradoBet | 0.95087 | 0.00001 |

---

## Installation

```bash
pip install -r requirements.txt
```

## Running the API

```bash
uvicorn api:app --reload
```

The server starts at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

---

## Usage

### POST /convert

**Request body:**

```json
{
  "odds_home": 2.50,
  "odds_draw": 3.20,
  "odds_away": 2.80,
  "bookmaker": "bet365",
  "model": "average"
}
```

**Fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `odds_home` | float > 1 | Yes | Decimal odds for home win |
| `odds_draw` | float > 1 | Yes | Decimal odds for draw |
| `odds_away` | float > 1 | Yes | Decimal odds for away win |
| `bookmaker` | string | No | Bookmaker name (uses calibrated params if recognised) |
| `model` | `"average"` / `"power"` / `"shin"` | No | Default: `"average"` |
| `alpha` | float > 0 | No | Override Power model α directly |
| `z` | 0 ≤ float < 1 | No | Override Shin z directly |

**Response:**

```json
{
  "p_home": 0.389112,
  "p_draw": 0.298745,
  "p_away": 0.312143,
  "model_used": "average",
  "bookmaker": "bet365",
  "bookmaker_recognised": true,
  "alpha_used": 1.04371,
  "z_used": 0.02697,
  "overround": 1.043155
}
```

### GET /convert (quick testing)

```bash
curl "http://localhost:8000/convert?odds_home=2.5&odds_draw=3.2&odds_away=2.8&bookmaker=bet365"
```

### GET /bookmakers

Returns the full list of supported bookmakers and their calibrated parameters.

```bash
curl http://localhost:8000/bookmakers
```

### GET /health

```bash
curl http://localhost:8000/health
```

---

## Using as a Python library

```python
from odds_to_probs import average_probs, power_probs, shin_probs

# Ensemble (default)
ph, pd, pa = average_probs(2.50, 3.20, 2.80, bookmaker="bet365")

# Power only with a specific bookmaker
ph, pd, pa = power_probs(2.50, 3.20, 2.80, bookmaker="bet365")

# Shin only with a manual z override
ph, pd, pa = shin_probs(2.50, 3.20, 2.80, z=0.03)

print(f"Home: {ph:.4f}  Draw: {pd:.4f}  Away: {pa:.4f}")
```

---

## Project structure

```
prediction-using-odds/
├── api.py                      # FastAPI application
├── requirements.txt
├── README.md
├── odds_to_probs/
│   ├── __init__.py
│   ├── models.py               # Power and Shin model math
│   └── config.py               # Calibrated parameters
├── power-model/
│   ├── run_calibration.py
│   ├── run_bookmaker_calibration.py
│   ├── power_calibration_report.md
│   └── bookmaker_power_report.md
└── shins-model/
    ├── run_calibration.py
    ├── run_bookmaker_calibration.py
    ├── shin_calibration_report.md
    └── bookmaker_shin_report.md
```
