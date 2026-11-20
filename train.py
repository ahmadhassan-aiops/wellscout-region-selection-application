"""Reproduce the WellScout models from data/geo_data.parquet (about 30 seconds).

For each region: drop point ids measured twice, split 75% / 25% (seed 42), fit linear regression, linear regression
with squared terms and LightGBM on the 75%, score them by 5-fold cross-validation and on the 25%, and run the
bootstrap (10,000 simulated surveys of 500 points, best 200 developed) with the brief's economics. Writes model/ and
data/validation.parquet (the 25% with every model's prediction, for the app).
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures

from wellscout.economics import Economics, bootstrap, choose, summarise
from wellscout.model import FEATURES, MODELS, REGIONS

ROOT = Path(__file__).resolve().parent
SEED = 42
CANDIDATES = {
    "Linear": lambda: LinearRegression(),
    "Linear + squares": lambda: make_pipeline(PolynomialFeatures(2), LinearRegression()),
    "LightGBM": lambda: LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=31, random_state=SEED, verbose=-1),
}


def rmse(a, b) -> float:
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def main() -> None:
    geo = pd.read_parquet(ROOT / "data" / "geo_data.parquet")
    econ = Economics()
    fitted, cv, val_rmse, decision, valid = {}, {}, {}, {}, []
    for r in REGIONS:
        d = geo[geo["region"] == r]
        d = d[~d["id"].duplicated(keep=False)].reset_index(drop=True)
        X_tr, X_va, y_tr, y_va = train_test_split(d[FEATURES], d["product"], test_size=0.25, random_state=SEED)
        v = d.loc[X_va.index, ["id", "region", *FEATURES, "product"]].reset_index(drop=True)
        for m in MODELS:
            cv[f"{m}|{r}"] = float(-cross_val_score(CANDIDATES[m](), X_tr, y_tr, cv=KFold(5, shuffle=True, random_state=SEED),
                                                   scoring="neg_root_mean_squared_error").mean())
            model = CANDIDATES[m]().fit(X_tr, y_tr)
            fitted[f"{m}|{r}"] = model
            p = model.predict(X_va)
            v[m] = p
            val_rmse[f"{m}|{r}"] = rmse(y_va, p)
            decision[f"{m}|{r}"] = summarise(bootstrap(y_va.to_numpy(), p, econ), econ.risk_limit)
        valid.append(v)

    choice = {m: choose({r: decision[f"{m}|{r}"] for r in REGIONS}) for m in MODELS}
    out = ROOT / "model"
    out.mkdir(exist_ok=True)
    joblib.dump(fitted, out / "wellscout_models.joblib", compress=3)
    meta = {"economics": econ.model_dump() | {"break_even": econ.break_even}, "bootstrap": {"draws": 10_000, "seed": 12345},
            "cv_rmse": cv, "validation_rmse": val_rmse, "decision": decision, "choice": choice,
            "points": {str(r): int((geo["region"] == r).sum()) for r in REGIONS}}
    (out / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    pd.concat(valid, ignore_index=True).to_parquet(ROOT / "data" / "validation.parquet", index=False)
    for m in MODELS:
        print(m, "->", choice[m], {r: (round(decision[f'{m}|{r}']['mean'] / 1e6, 2), f"{decision[f'{m}|{r}']['risk']:.1%}")
                                   for r in REGIONS})


if __name__ == "__main__":
    main()
