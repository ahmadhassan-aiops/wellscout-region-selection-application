"""Models & method: data, models, validation, the bootstrap and the limits."""

from __future__ import annotations

import streamlit as st

from sheet import data, ui
from sheet.data import money
from sheet.site import NOTEBOOK_URL
from wellscout.model import MODELS, REGIONS


def render() -> None:
    meta = data.scout().meta
    econ = meta["economics"]
    ui.page("C-1", "Models & method", "How WellScout is built",
            f'The data, the three models, how they were scored and how profit and risk are simulated. The full analysis is in the '
            f'<a href="{NOTEBOOK_URL}" target="_blank">project notebook</a>.')

    with ui.panel("C-1.1", "Model accuracy", "speed", "RMSE in thousand barrels: 5-fold cross-validation on the 75% training points, "
                  "then the 25% validation points the models never saw"):
        rows = ""
        for m in MODELS:
            rows += f"<tr><td>{m}</td>" + "".join(
                f'<td class="n">{meta["cv_rmse"][f"{m}|{r}"]:.2f}</td><td class="n">{meta["validation_rmse"][f"{m}|{r}"]:.2f}</td>'
                for r in REGIONS) + "</tr>"
        st.html('<table class="tbl"><thead><tr><th rowspan="2">Model</th>' + "".join(f'<th class="n" colspan="2">{ui.swatch(r)}Region {r}</th>'
                for r in REGIONS) + "</tr><tr>" + '<th class="n">CV</th><th class="n">Validation</th>' * 3
                + f"</tr></thead><tbody>{rows}</tbody></table>")
        ui.notes("Region 1 is nearly exact for every model. Region 2 gains the most from squared terms (40.0 to 38.7) and from LightGBM "
                 "(37.5): the bowl in f0 and f1. Region 0 gains a little from LightGBM.",
                 "Errors of 37 to 40 thousand barrels in regions 0 and 2 are large next to points averaging 92 to 95: the models "
                 "rank points far better than they measure them, and ranking is what the decision needs.")

    with ui.panel("C-1.2", "The decision under each model", "gavel", main=True, sub="brief's economics, 10,000 simulated surveys"):
        rows = ""
        for m in MODELS:
            for r in REGIONS:
                s = meta["decision"][f"{m}|{r}"]
                pick = meta["choice"][m] == r
                rows += (f'<tr class="{"pick" if pick else ""}"><td>{m if r == 0 else ""}</td><td>{ui.swatch(r)}Region {r}</td>'
                         f'<td class="n">{money(s["mean"])}</td><td class="n">{money(s["low"])} to {money(s["high"])}</td>'
                         f'<td class="n">{s["risk"]:.1%}</td><td class="n">{ui.passfail(s["passes"])}</td>'
                         f'<td class="n">{"chosen" if pick else ""}</td></tr>')
        st.html('<table class="tbl"><thead><tr><th>Model</th><th>Region</th><th class="n">Mean profit</th><th class="n">95% of surveys</th>'
                f'<th class="n">Risk of loss</th><th class="n">2.5% rule</th><th class="n"></th></tr></thead><tbody>{rows}</tbody></table>')

    a, b = st.columns(2, gap="medium")
    with a:
        with ui.panel("C-1.3", "Data and economics", "dataset"):
            st.html(f"""<dl class="facts">
<dt>Points</dt><dd>100,000 per region; 18 ids measured twice with different values are removed (36 rows)</dd>
<dt>Split</dt><dd>75% training, 25% validation per region (seed 42)</dd>
<dt>Budget</dt><dd>{money(econ["budget"])} for {econ["wells"]} wells: ${econ["budget"] / econ["wells"]:,.0f} per well</dd>
<dt>Revenue</dt><dd>${econ["revenue_per_unit"] / 1000:.1f} per barrel, ${econ["revenue_per_unit"]:,.0f} per thousand barrels</dd>
<dt>Break-even</dt><dd>{econ["break_even"]:.1f} thousand barrels per well</dd>
<dt>Rule</dt><dd>Risk of a loss under {econ["risk_limit"]:.1%}, then the highest mean profit</dd>
</dl>""")
        with ui.panel("C-1.4", "The models", "model_training"):
            st.html("""<dl class="facts">
<dt>Linear</dt><dd>Linear regression on f0, f1, f2: the model the brief asks for</dd>
<dt>Linear + squares</dt><dd>Linear regression on f0, f1, f2, their squares and pairwise products (9 terms): still a linear regression</dd>
<dt>LightGBM</dt><dd>Gradient-boosted trees, 300 trees, learning rate 0.05, 31 leaves: beyond the brief, as a check of what a flexible model finds</dd>
</dl>""")
    with b:
        with ui.panel("C-1.5", "Profit and risk", "functions"):
            st.html("""<ol style="margin:0;padding-left:1.3rem;font-size:.9rem;line-height:1.6">
<li>Draw 500 validation points at random, with replacement (one survey).</li>
<li>Rank them by the model's prediction; develop the best 200.</li>
<li>Profit = actual reserves of the 200 × $4,500 − $100 million.</li>
<li>Repeat 10,000 times with a fixed seed; the same surveys are used for every model.</li>
<li>Mean profit, the 2.5th to 97.5th percentile, and the share of surveys with a loss.</li>
</ol>""")
        with ui.panel("C-1.6", "Limits", "report"):
            ui.notes("The data is a training case: synthetic, with anonymous features. Region 1's 12 reserve values and region 2's "
                     "bowl are properties of this data, not geology to rely on.",
                     "Points are drawn from each region's validation set; a real survey would sample new ground, and the result "
                     "depends on the model ranking it as well as it ranks these points.",
                     "Prices, costs and the budget are fixed for the whole project life; there is no discounting or decline curve.")
    ui.footer()
