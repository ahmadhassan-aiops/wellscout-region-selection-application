"""The nine saved models (three per region) and their evaluation."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

MODEL_DIR = Path(__file__).resolve().parent.parent / "model"
FEATURES = ["f0", "f1", "f2"]
MODELS = ["Linear", "Linear + squares", "LightGBM"]
REGIONS = [0, 1, 2]


class Scout:
    def __init__(self, model_dir: Path = MODEL_DIR):
        self.models = joblib.load(model_dir / "wellscout_models.joblib")
        self.meta = json.loads((model_dir / "metadata.json").read_text(encoding="utf-8"))

    def predict(self, model: str, region: int, X: pd.DataFrame) -> np.ndarray:
        return self.models[f"{model}|{region}"].predict(X[FEATURES])
