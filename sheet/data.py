"""Cached loaders and the cached bootstrap."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from wellscout.economics import Economics, bootstrap
from wellscout.model import Scout

ROOT = Path(__file__).resolve().parent.parent


@st.cache_resource(show_spinner="Loading the models...")
def scout() -> Scout:
    return Scout()


@st.cache_data
def geo() -> pd.DataFrame:
    """All 300,000 exploration points (three regions)."""
    return pd.read_parquet(ROOT / "data" / "geo_data.parquet")


@st.cache_data
def validation() -> pd.DataFrame:
    """The 25% validation points of each region with every model's prediction."""
    return pd.read_parquet(ROOT / "data" / "validation.parquet")


@st.cache_data(show_spinner="Simulating 10,000 surveys...")
def profits(model: str, region: int, econ_json: str, draws: int = 10_000) -> np.ndarray:
    econ = Economics.model_validate_json(econ_json)
    v = validation()
    v = v[v["region"] == region]
    return bootstrap(v["product"].to_numpy(), v[model].to_numpy(), econ, draws=draws)


def money(x: float, signed: bool = False) -> str:
    """Dollars in millions: $4.8M; signed: +$4.8M / −$1.3M."""
    m = x / 1e6
    if signed:
        return f"{'+' if m >= 0 else '−'}${abs(m):,.1f}M"
    return f"{'−' if m < 0 else ''}${abs(m):,.1f}M"
