"""
Odds-to-Probabilities API
=========================
Converts raw 1X2 bookmaker odds into fair (de-vigged) probabilities
using the Power Transform model, Shin's model, or an ensemble average.

Run:
    uvicorn api:app --reload
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, model_validator
from typing import Literal

from odds_to_probs import power_probs, shin_probs, average_probs, SUPPORTED_BOOKMAKERS
from odds_to_probs.config import (
    GLOBAL_POWER_ALPHA,
    GLOBAL_SHIN_Z,
    BOOKMAKER_POWER_ALPHA,
    BOOKMAKER_SHIN_Z,
)

app = FastAPI(
    title="Odds to Probabilities API",
    description=(
        "De-vigs 1X2 football odds into fair probabilities. "
        "Supports the Power Transform model, Shin's model, and their ensemble average."
    ),
    version="1.0.0",
)

ModelChoice = Literal["average", "power", "shin"]
DEFAULT_MODEL: ModelChoice = "average"


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class OddsInput(BaseModel):
    odds_home: float = Field(..., gt=1.0, description="Decimal odds for home win (e.g. 2.50)")
    odds_draw: float = Field(..., gt=1.0, description="Decimal odds for draw (e.g. 3.20)")
    odds_away: float = Field(..., gt=1.0, description="Decimal odds for away win (e.g. 2.80)")
    bookmaker: str | None = Field(
        None,
        description=(
            "Optional bookmaker name. When provided and recognised, uses that "
            "bookmaker's calibrated parameters instead of the global defaults."
        ),
    )
    model: ModelChoice = Field(
        DEFAULT_MODEL,
        description=(
            "'average' (default) — ensemble of Power and Shin; "
            "'power' — Power Transform only; "
            "'shin' — Shin model only."
        ),
    )
    alpha: float | None = Field(
        None,
        gt=0,
        description="Override Power model exponent α (ignores bookmaker lookup for Power).",
    )
    z: float | None = Field(
        None,
        ge=0.0,
        lt=1.0,
        description="Override Shin insider-fraction z (ignores bookmaker lookup for Shin).",
    )

    @model_validator(mode="after")
    def check_bookmaker_known(self):
        if self.bookmaker is not None:
            key = self.bookmaker.strip().lower()
            if key not in BOOKMAKER_POWER_ALPHA:
                # Not an error — will silently fall back to global params.
                # We surface this as a warning in the response.
                pass
        return self


class ProbabilityResult(BaseModel):
    p_home: float = Field(..., description="Fair probability of home win")
    p_draw: float = Field(..., description="Fair probability of draw")
    p_away: float = Field(..., description="Fair probability of away win")
    model_used: ModelChoice
    bookmaker: str | None
    bookmaker_recognised: bool
    alpha_used: float | None = Field(None, description="α used by Power model (None if Shin only)")
    z_used: float | None = Field(None, description="z used by Shin model (None if Power only)")
    overround: float = Field(..., description="Raw bookmaker overround (sum of implied probs)")


class BookmakerInfo(BaseModel):
    name: str
    power_alpha: float
    shin_z: float


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_params(bookmaker: str | None, alpha_override: float | None, z_override: float | None):
    """Return (recognised, alpha, z) for a given bookmaker / override combo."""
    key = bookmaker.strip().lower() if bookmaker else None
    recognised = key in BOOKMAKER_POWER_ALPHA if key else False

    alpha = alpha_override or (BOOKMAKER_POWER_ALPHA.get(key) if recognised else GLOBAL_POWER_ALPHA)
    z = z_override or (BOOKMAKER_SHIN_Z.get(key) if recognised else GLOBAL_SHIN_Z)
    return recognised, alpha, z


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Meta"])
def health():
    return {"status": "ok"}


@app.get("/bookmakers", response_model=list[BookmakerInfo], tags=["Meta"])
def list_bookmakers():
    """Return all supported bookmakers with their calibrated parameters."""
    return [
        BookmakerInfo(name=name, power_alpha=BOOKMAKER_POWER_ALPHA[name], shin_z=BOOKMAKER_SHIN_Z[name])
        for name in SUPPORTED_BOOKMAKERS
    ]


@app.post("/convert", response_model=ProbabilityResult, tags=["Convert"])
def convert(body: OddsInput):
    """
    Convert 1X2 bookmaker odds to fair probabilities.

    - **model=average** (default): ensemble of Power and Shin.
    - **model=power**: Power Transform only.
    - **model=shin**: Shin model only.

    Optionally supply a `bookmaker` name to use its individually calibrated
    parameters. If the bookmaker is unrecognised, global parameters are used.
    """
    recognised, alpha, z = _resolve_params(body.bookmaker, body.alpha, body.z)

    try:
        if body.model == "power":
            ph, pd, pa = power_probs(body.odds_home, body.odds_draw, body.odds_away, alpha=alpha)
            z_used = None
        elif body.model == "shin":
            ph, pd, pa = shin_probs(body.odds_home, body.odds_draw, body.odds_away, z=z)
            alpha = None
        else:  # average
            ph, pd, pa = average_probs(body.odds_home, body.odds_draw, body.odds_away, alpha=alpha, z=z)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    overround = (1.0 / body.odds_home) + (1.0 / body.odds_draw) + (1.0 / body.odds_away)

    return ProbabilityResult(
        p_home=round(ph, 6),
        p_draw=round(pd, 6),
        p_away=round(pa, 6),
        model_used=body.model,
        bookmaker=body.bookmaker,
        bookmaker_recognised=recognised,
        alpha_used=round(alpha, 6) if alpha is not None else None,
        z_used=round(z, 6) if z is not None else None,
        overround=round(overround, 6),
    )


@app.get("/convert", response_model=ProbabilityResult, tags=["Convert"])
def convert_get(
    odds_home: float = Query(..., gt=1.0),
    odds_draw: float = Query(..., gt=1.0),
    odds_away: float = Query(..., gt=1.0),
    bookmaker: str | None = Query(None),
    model: ModelChoice = Query(DEFAULT_MODEL),
    alpha: float | None = Query(None, gt=0),
    z: float | None = Query(None, ge=0.0, lt=1.0),
):
    """GET version of /convert for quick browser/curl testing."""
    body = OddsInput(
        odds_home=odds_home,
        odds_draw=odds_draw,
        odds_away=odds_away,
        bookmaker=bookmaker,
        model=model,
        alpha=alpha,
        z=z,
    )
    return convert(body)
