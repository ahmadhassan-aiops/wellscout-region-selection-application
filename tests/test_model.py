"""The saved models match their evaluation, the economics are right, and the bootstrap is reproducible."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from wellscout.economics import Economics, bootstrap, choose, profit, summarise
from wellscout.model import MODELS, REGIONS, Scout
from wellscout.schema import Site

ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def scout() -> Scout:
    return Scout()


@pytest.fixture(scope="module")
def valid() -> pd.DataFrame:
    return pd.read_parquet(ROOT / "data" / "validation.parquet")


def test_break_even():
    e = Economics()
    assert e.cost_per_well == 500_000
    assert e.break_even == pytest.approx(111.111, abs=1e-3)
    with pytest.raises(ValueError):
        Economics(wells=600, points=500)


def test_profit_uses_actual_reserves_of_predicted_best():
    e = Economics(budget=2 * 4500 * 100, wells=2, points=4)
    actual = np.array([100.0, 300.0, 50.0, 200.0])
    predicted = np.array([10.0, 1.0, 9.0, 0.0])  # model picks points 0 and 2
    assert profit(actual, predicted, e) == pytest.approx((150 - 200) * 4500)


def test_saved_models_reproduce_validation(scout, valid):
    for m in MODELS:
        for r in REGIONS:
            v = valid[valid["region"] == r]
            p = scout.predict(m, r, v)
            assert np.allclose(p, v[m])
            rmse = float(np.sqrt(np.mean((v["product"] - p) ** 2)))
            assert rmse == pytest.approx(scout.meta["validation_rmse"][f"{m}|{r}"], abs=1e-9)


def test_bootstrap_matches_saved_decision(scout, valid):
    e = Economics()
    for m in MODELS:
        s = {}
        for r in REGIONS:
            v = valid[valid["region"] == r]
            s[r] = summarise(bootstrap(v["product"].to_numpy(), v[m].to_numpy(), e), e.risk_limit)
            assert s[r]["risk"] == pytest.approx(scout.meta["decision"][f"{m}|{r}"]["risk"])
            assert s[r]["mean"] == pytest.approx(scout.meta["decision"][f"{m}|{r}"]["mean"])
        assert choose(s) == scout.meta["choice"][m]
    assert scout.meta["choice"] == {"Linear": 1, "Linear + squares": 2, "LightGBM": 2}


def test_choose_none_when_all_fail():
    assert choose({0: {"passes": False, "mean": 1.0}, 1: {"passes": False, "mean": 2.0}}) is None


def test_site_schema():
    assert Site(region=2, f0=1, f1=2, f2=3).row() == {"f0": 1, "f1": 2, "f2": 3}
    with pytest.raises(ValueError):
        Site(region=3, f0=0, f1=0, f2=0)
    with pytest.raises(ValueError):
        Site(region=0, f0=99, f1=0, f2=0)
