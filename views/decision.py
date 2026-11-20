"""Region decision: choose a model and the economics; 10,000 simulated surveys per region give mean profit, interval
and risk of loss; the brief's rule picks the region."""

from __future__ import annotations

import streamlit as st
from pydantic import ValidationError

from sheet import charts, data, ui
from sheet import theme as t
from sheet.data import money
from wellscout.economics import Economics, choose, summarise
from wellscout.model import MODELS, REGIONS


def _settings() -> tuple[str, Economics | None]:
    model = st.segmented_control("Model that ranks the surveyed points", MODELS, default="Linear", required=True, key="d_model")
    st.caption(t.MODEL_NOTE[model].capitalize() + ".")
    a, b, c, d, e = st.columns(5, gap="small")
    budget = a.number_input("Budget ($ million)", 10.0, 1000.0, 100.0, step=10.0, format="%.0f", key="d_budget")
    wells = b.number_input("Wells developed", 10, 1000, 200, step=10, key="d_wells")
    points = c.number_input("Points surveyed", 20, 5000, 500, step=50, key="d_points")
    price = d.number_input("Revenue per barrel ($)", 1.0, 20.0, 4.5, step=0.5, format="%.1f", key="d_price")
    risk = e.number_input("Risk limit (%)", 0.5, 20.0, 2.5, step=0.5, format="%.1f", key="d_risk")
    try:
        econ = Economics(budget=budget * 1e6, wells=int(wells), points=int(points), revenue_per_unit=price * 1000, risk_limit=risk / 100)
    except ValidationError as exc:
        st.error(exc.errors()[0]["msg"].removeprefix("Value error, "), icon=":material/error:")
        econ = None
    return model, econ


def _decision_block(chosen: int | None, s: dict | None, econ: Economics, model: str) -> None:
    if chosen is None:
        st.html(f'<div class="decide none"><div><p class="l">Decision</p><p class="v">No region</p><p class="n">every region risks a loss '
                f'in at least {econ.risk_limit:.1%} of surveys</p></div><div><p class="l">Model</p><p class="v" style="font-size:1.2rem">'
                f'{model}</p></div><div></div><div></div></div>')
        return
    st.html(f'''<div class="decide" style="--c:{t.REGION[chosen]}">
<div><p class="l">Decision</p><p class="v">Develop region {chosen}</p><p class="n">rule: risk of a loss under {econ.risk_limit:.1%}, then the highest mean profit</p></div>
<div><p class="l">Mean profit</p><p class="v">{money(s["mean"])}</p><p class="n">over 10,000 simulated surveys</p></div>
<div><p class="l">95% of surveys</p><p class="v" style="font-size:1.45rem">{money(s["low"])} to {money(s["high"])}</p><p class="n">profit range</p></div>
<div><p class="l">Risk of a loss</p><p class="v">{s["risk"]:.1%}</p><p class="n">limit {econ.risk_limit:.1%}</p></div>
</div>''')


def _region_card(r: int, s: dict, chosen: int | None, mean_reserves: float) -> str:
    if r == chosen:
        verdict = f'<div class="verdict pick">{ui.icon("verified")} Chosen</div>'
    elif s["passes"]:
        verdict = f'<div class="verdict ok">{ui.icon("check_circle")} Passes the risk limit</div>'
    else:
        verdict = f'<div class="verdict no">{ui.icon("cancel")} Fails the risk limit</div>'
    return (f'<div class="reg"><div class="reg-h" style="--c:{t.REGION[r]}"><b>Region {r}</b><span>mean point {mean_reserves:.1f}</span></div>'
            f'<dl><dt>Mean profit</dt><dd>{money(s["mean"])}</dd><dt>95% of surveys</dt><dd>{money(s["low"])} to {money(s["high"])}</dd>'
            f'<dt>Risk of a loss</dt><dd>{s["risk"]:.1%}</dd></dl>{verdict}</div>')


def render() -> None:
    ui.page("A-1", "Region decision", "Which region should OilyGiant develop?",
            "In the chosen region OilyGiant surveys <b>500 points</b>, a model predicts each point's reserves, and the <b>best "
            "200</b> become wells on a <b>$100 million</b> budget. WellScout repeats that survey 10,000 times on points the "
            "models never trained on, and applies the rule: keep regions whose <b>risk of a loss is under 2.5%</b>, then "
            "take the highest mean profit. Change the model or the economics to see the decision move.")

    with ui.panel("A-1.1", "Model and economics", "tune"):
        model, econ = _settings()
    if econ is None:
        ui.footer()
        return
    key = econ.model_dump_json()
    summaries = {r: summarise(data.profits(model, r, key), econ.risk_limit) for r in REGIONS}
    chosen = choose(summaries)
    _decision_block(chosen, summaries.get(chosen), econ, model)
    st.html('<div style="height:.9rem"></div>')

    geo = data.geo()
    with ui.panel("A-1.2", "The three regions under this model", "map",
                  f"break-even: {econ.break_even:.1f} thousand barrels per well (${econ.cost_per_well:,.0f} ÷ ${econ.revenue_per_unit:,.0f} "
                  "per thousand barrels)"):
        st.html('<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.8rem">'
                + "".join(_region_card(r, summaries[r], chosen, geo.loc[geo["region"] == r, "product"].mean()) for r in REGIONS)
                + "</div>")
        ui.notes(f"The average point holds less than the {econ.break_even:.1f} thousand barrels a well needs in every region: profit "
                 "comes only from picking the best wells, so a region is as good as the model's ranking in it.",
                 "Risk of a loss is the share of the 10,000 simulated surveys whose 200 wells earn less than the budget.")

    a, b = st.columns([1.35, 1], gap="medium")
    with a:
        with ui.panel("A-1.3", "Profit of 10,000 simulated surveys", "bar_chart", "each line is one region; the shaded side is a loss"):
            charts.show(charts.profit_curves({r: data.profits(model, r, key) for r in REGIONS}, chosen), f"curves_{model}_{key}")
    with b:
        with ui.panel("A-1.4", "Same economics, three models", "compare_arrows", "mean profit and risk of loss for each model and region"):
            rows = []
            for m in MODELS:
                ss = {r: summarise(data.profits(m, r, key), econ.risk_limit) for r in REGIONS}
                c = choose(ss)
                cells = "".join(f'<td class="n">{money(ss[r]["mean"])}<br><span class="{"ok" if ss[r]["passes"] else "no"}">'
                                f'{ss[r]["risk"]:.1%}{ui.icon("check" if ss[r]["passes"] else "close")}</span></td>' for r in REGIONS)
                rows.append(f'<tr class="{"pick" if m == model else ""}"><td>{m}</td>{cells}'
                            f'<td class="n">{"none" if c is None else ui.swatch(c) + str(c)}</td></tr>')
            st.html('<table class="tbl tight"><thead><tr><th>Model</th>' + "".join(f'<th class="n">{ui.swatch(r)}R{r}</th>' for r in REGIONS)
                    + '<th class="n">Chosen</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table>")
            if econ == Economics():
                ui.notes("With the brief's economics, the plain linear regression (the brief's model) can only choose region 1, "
                         "the one region where reserves follow a single feature almost exactly.",
                         "Region 2's reserves grow with the square of f0 and f1. Squared terms (still a linear regression) and "
                         "LightGBM see that curve, pick better wells there, and move the decision to region 2.")
            else:
                ui.notes("Every model sees the same surveys; only its ranking of the points differs, and with it which wells are "
                         "developed.")
    ui.footer()
