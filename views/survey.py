"""Survey simulator: one survey of 500 points, the model's best 200 developed, against perfect hindsight and a random
choice."""

from __future__ import annotations

import numpy as np
import streamlit as st

from sheet import charts, data, ui
from sheet import theme as t
from sheet.data import money
from wellscout.economics import Economics, profit
from wellscout.model import MODELS, REGIONS


def _new_survey() -> None:
    st.session_state["s_no"] = int(np.random.default_rng().integers(1, 10_000))


def render() -> None:
    econ = Economics()
    ui.page("A-2", "Survey simulator", "What does one survey of 500 points look like?",
            "Draw one survey in a region: 500 points the model never trained on. The model ranks them, the best 200 are "
            "developed, and each earns its <b>actual</b> reserves. Compare the result with perfect hindsight and with "
            "drilling 200 points at random.")
    with ui.panel("A-2.1", "Survey", "explore"):
        a, b, c = st.columns([1.35, 1.55, 1.1], gap="medium", vertical_alignment="bottom")
        region = a.segmented_control("Region", REGIONS, default=2, required=True, key="s_region", format_func=lambda r: f"Region {r}")
        model = b.segmented_control("Model", MODELS, default="Linear", required=True, key="s_model")
        if "s_no" not in st.session_state:
            st.session_state["s_no"] = 1
        c1, c2 = c.columns([1, 1], vertical_alignment="bottom")
        no = c1.number_input("Survey number", 1, 9999, step=1, key="s_no")
        c2.button("New survey", icon=":material/casino:", on_click=_new_survey, key="s_new", width="stretch")

    v = data.validation()
    v = v[v["region"] == region].reset_index(drop=True)
    rng = np.random.default_rng(int(no))
    idx = rng.integers(0, len(v), econ.points)
    sample = v.iloc[idx].reset_index(drop=True)
    actual, pred = sample["product"].to_numpy(), sample[model].to_numpy()
    order = np.argsort(-pred)
    sample["pred"] = pred
    sample["picked"] = False
    sample.loc[order[: econ.wells], "picked"] = True
    got = profit(actual, pred, econ)
    perfect = profit(actual, actual, econ)
    random_pick = float(actual[rng.permutation(econ.points)[: econ.wells]].sum() * econ.revenue_per_unit - econ.budget)
    developed = sample[sample["picked"]]
    below = int((developed["product"] < econ.break_even).sum())

    ui.cells([("Profit of this survey", money(got, signed=True), f"{model}, region {region}"),
              ("Perfect hindsight", money(perfect, signed=True), "the 200 truly richest points"),
              ("Random 200", money(random_pick, signed=True), "no model at all"),
              ("Developed wells below break-even", f"{below} of {econ.wells}", f"under {econ.break_even:.1f} thousand barrels"),
              ("Captured", f"{(got + econ.budget) / (perfect + econ.budget):.0%}", "of the hindsight revenue")], highlight=0)

    left, right = st.columns([1.6, 1], gap="medium")
    with left:
        with ui.panel("A-2.2", "The model's choice", "scatter_plot", main=True, sub=
                      "each point is one surveyed site: what the model predicted against what it holds; filled points are developed"):
            charts.show(charts.survey(sample, econ.break_even, region), f"survey_{region}_{model}_{no}")
    with right:
        with ui.panel("A-2.3", "Survey ledger", "receipt_long"):
            revenue = developed["product"].sum() * econ.revenue_per_unit
            st.html(f'''<div class="ledger">
<div><span>Reserves of the 200 wells</span><span>{developed["product"].sum():,.0f} k bbl</span></div>
<div><span>Revenue at ${econ.revenue_per_unit:,.0f} per thousand barrels</span><span>{money(revenue)}</span></div>
<div><span>Development budget</span><span>−{money(econ.budget)}</span></div>
<div class="tot"><span>Profit</span><span class="{"ok" if got >= 0 else "no"}">{money(got, signed=True)}</span></div>
</div>''')
            spread = {"Linear": "a straight-line model", "Linear + squares": "the squared-terms model", "LightGBM": "LightGBM"}[model]
            notes = [f"The cut-off: {spread} develops points predicted above {developed['pred'].min():.1f} thousand barrels.",
                     f"{below} developed wells hold less than break-even: they are carried by the richer ones."]
            if region == 1:
                notes.append("Region 1's reserves take 12 values that follow f2 almost exactly, so every model ranks its points "
                             "nearly perfectly: the result is close to hindsight.")
            elif region == 2 and model == "Linear":
                notes.append("In region 2 a straight line ignores f0 and f1, which matter through their squares; switch to "
                             "<b>Linear + squares</b> or <b>LightGBM</b> on the same survey and compare.")
            ui.notes(*notes)
            ui.caution(f'Survey {no} draws the same 500 points for every model, so the models can be compared on equal terms.',
                       "info")
    ui.footer()
