"""Site check: enter one surveyed point's measurements; each model predicts its reserves against break-even and the
cut-off for the best 200 of a typical survey."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
from pydantic import ValidationError

from sheet import charts, data, ui
from wellscout.economics import Economics
from wellscout.model import MODELS, REGIONS
from wellscout.schema import Site


def _load_point() -> None:
    v = data.validation()
    region = st.session_state.get("c_region", 2)
    row = v[v["region"] == region].sample(1, random_state=int(np.random.default_rng().integers(0, 1_000_000))).iloc[0]
    for f in ("f0", "f1", "f2"):
        st.session_state[f"c_{f}"] = round(float(row[f]), 3)
    st.session_state["c_actual"] = (region, round(float(row["f0"]), 3), round(float(row["f1"]), 3), round(float(row["f2"]), 3),
                                    float(row["product"]), row["id"])


def render() -> None:
    econ = Economics()
    ui.page("A-3", "Site check", "How much oil does one surveyed point hold?",
            "Enter the three measurements of a surveyed point (or load one the models never trained on). Each model predicts "
            "its reserves; the point is worth developing if it would rank among the best 200 of a typical 500-point survey.")
    with ui.panel("A-3.1", "Measurements", "straighten"):
        a, b, c, d, e = st.columns([1.2, 1, 1, 1, 1.2], gap="small", vertical_alignment="bottom")
        region = a.segmented_control("Region", REGIONS, default=2, required=True, key="c_region", format_func=lambda r: f"R{r}")
        for f, default in (("f0", 2.5), ("f1", -2.0), ("f2", 4.0)):
            st.session_state.setdefault(f"c_{f}", default)
        f0 = b.number_input("f0", -35.0, 35.0, step=0.1, format="%.3f", key="c_f0")
        f1 = c.number_input("f1", -35.0, 35.0, step=0.1, format="%.3f", key="c_f1")
        f2 = d.number_input("f2", -30.0, 30.0, step=0.1, format="%.3f", key="c_f2")
        e.button("Load a held-out point", icon=":material/shuffle:", on_click=_load_point, key="c_load", width="stretch")
    try:
        point = Site(region=region, f0=f0, f1=f1, f2=f2)
    except ValidationError as exc:
        st.error(exc.errors()[0]["msg"], icon=":material/error:")
        ui.footer()
        return

    s = data.scout()
    X = pd.DataFrame([point.row()])
    preds = {m: float(s.predict(m, region, X)[0]) for m in MODELS}
    v = data.validation()
    v = v[v["region"] == region]
    cut = {m: float(np.quantile(v[m], 1 - econ.wells / econ.points)) for m in MODELS}

    known = st.session_state.get("c_actual")
    actual = known[4] if known and known[:4] == (region, round(f0, 3), round(f1, 3), round(f2, 3)) else None
    ui.cells([(f"{m}", f"{preds[m]:.1f}", "develop" if preds[m] >= cut[m] else "skip") for m in MODELS]
             + [("Actual reserves", f"{actual:.1f}" if actual is not None else "unknown",
                 f"point {known[5]}" if actual is not None else "load a held-out point to compare")],
             highlight=3 if actual is not None else None)

    left, right = st.columns([1.3, 1], gap="medium")
    with left:
        with ui.panel("A-3.2", "Predicted reserves by model", "bar_chart", "thousand barrels; dashed line: what one well must hold to pay for itself"):
            charts.show(charts.site(preds, econ.break_even, region), f"site_{region}_{f0}_{f1}_{f2}")
    with right:
        with ui.panel("A-3.3", "Would it be developed?", "rule"):
            rows = "".join(f'<tr><td>{m}</td><td class="n">{preds[m]:.1f}</td><td class="n">{cut[m]:.1f}</td>'
                           f'<td class="n">{ui.passfail(preds[m] >= cut[m]).replace("passes", "develop").replace("fails", "skip")}</td></tr>'
                           for m in MODELS)
            st.html('<table class="tbl"><thead><tr><th>Model</th><th class="n">Predicted</th><th class="n">Cut-off</th><th class="n">Call</th>'
                    f'</tr></thead><tbody>{rows}</tbody></table>')
            ui.notes(f"The cut-off is the 60th percentile of the model's predictions for region {region}'s points: in a typical survey, "
                     f"the best {econ.wells} of {econ.points} (40%) lie above it.",
                     "A developed point can still hold less than break-even; the 200 wells pay off together.")
    ui.footer()
