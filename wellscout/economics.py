"""OilyGiant's economics: break-even reserves, the profit of developing the model's best wells, and the bootstrap of
many simulated surveys."""

from __future__ import annotations

import numpy as np
from pydantic import BaseModel, Field, model_validator


class Economics(BaseModel):
    budget: float = Field(100_000_000, gt=0, description="dollars for all wells")
    wells: int = Field(200, ge=1, le=1000)
    points: int = Field(500, ge=2, le=5000)
    revenue_per_unit: float = Field(4_500, gt=0, description="dollars per thousand barrels")
    risk_limit: float = Field(0.025, gt=0, lt=1)

    @model_validator(mode="after")
    def wells_within_points(self):
        if self.wells > self.points:
            raise ValueError("The survey must cover at least as many points as wells to develop.")
        return self

    @property
    def cost_per_well(self) -> float:
        return self.budget / self.wells

    @property
    def break_even(self) -> float:
        """Thousand barrels a well must hold to pay for itself."""
        return self.cost_per_well / self.revenue_per_unit


def profit(actual: np.ndarray, predicted: np.ndarray, econ: Economics) -> float:
    """Dollars from developing the `wells` points with the highest predictions (they earn their actual reserves)."""
    best = np.argsort(-predicted)[: econ.wells]
    return float(actual[best].sum() * econ.revenue_per_unit - econ.budget)


def bootstrap(actual: np.ndarray, predicted: np.ndarray, econ: Economics, draws: int = 10_000, seed: int = 12345,
              chunk: int = 2_000) -> np.ndarray:
    """Profit (dollars) of `draws` simulated surveys: `points` random points with replacement, the best `wells` by
    prediction developed. Vectorised in chunks; the same seed gives the same surveys for every model."""
    rng = np.random.default_rng(seed)
    out = np.empty(draws)
    for start in range(0, draws, chunk):
        n = min(chunk, draws - start)
        idx = rng.integers(0, len(actual), (n, econ.points))
        p, a = predicted[idx], actual[idx]
        top = np.argpartition(-p, econ.wells - 1, axis=1)[:, : econ.wells]
        out[start:start + n] = np.take_along_axis(a, top, axis=1).sum(axis=1) * econ.revenue_per_unit - econ.budget
    return out


def summarise(profits: np.ndarray, risk_limit: float) -> dict:
    """Mean, 95% interval and risk of loss (profits in dollars)."""
    risk = float(np.mean(profits < 0))
    return {"mean": float(profits.mean()), "low": float(np.percentile(profits, 2.5)), "high": float(np.percentile(profits, 97.5)),
            "risk": risk, "passes": risk < risk_limit}


def choose(summaries: dict[int, dict]) -> int | None:
    """The brief's rule: among regions under the risk limit, the highest mean profit."""
    ok = {r: s for r, s in summaries.items() if s["passes"]}
    return max(ok, key=lambda r: ok[r]["mean"]) if ok else None
