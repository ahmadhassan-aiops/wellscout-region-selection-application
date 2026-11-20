"""Region decision. First the answer (which region each model picks under the brief's economics), then an explorer:
pick a model, adjust the economics, and read each region's profit distribution and risk against the limit."""

from __future__ import annotations

import numpy as np
import streamlit as st
from pydantic import ValidationError

from sheet import data, ui
from sheet import theme as t
from sheet.data import money
from wellscout.economics import Economics, choose, summarise
from wellscout.model import MODELS, REGIONS

TAG = {"Linear": "the brief", "Linear + squares": "still linear", "LightGBM": "beyond the brief"}
WHY = {"Linear": "straight-line regression on f0, f1, f2",
       "Linear + squares": "adds squared and cross terms",
       "LightGBM": "gradient-boosted trees"}


def _answer() -> None:
    """Which region each model picks with the brief's economics (from the saved evaluation)."""
    meta = data.scout().meta
    cols = []
    for m in MODELS:
        r = meta["choice"][m]
        s = meta["decision"][f"{m}|{r}"]
        cols.append(f'<div style="--c:{t.REGION[r]}"><span class="tag">{TAG[m]}</span><p class="m">{m}</p><p class="k">{WHY[m]}</p>'
                    f'<p class="r">{ui.icon("arrow_forward")}Region {r}</p>'
                    f'<p class="f"><span>mean profit <b>{money(s["mean"])}</b></span><span>risk of loss <b>{s["risk"]:.1%}</b></span></p></div>')
    st.html('<div class="answer">' + "".join(cols) + "</div>"
            f'<div class="takeaway">{ui.icon("lightbulb")}<div>The brief\'s straight-line model can only trust <b>region 1</b>, where '
            "reserves follow one measurement. Region 2's reserves follow a curve that straight lines miss: models that see it "
            "pick better wells there and choose <b>region 2</b>, with more profit and, with LightGBM, less risk.</div></div>")


def _economics() -> Economics | None:
    with st.expander("Change the economics (budget, wells, survey size, price, risk limit)", icon=":material/tune:"):
        a, b, c, d, e = st.columns(5, gap="small")
        budget = a.number_input("Budget ($ million)", 10.0, 1000.0, 100.0, step=10.0, format="%.0f", key="d_budget")
        wells = b.number_input("Wells developed", 10, 1000, 200, step=10, key="d_wells")
        points = c.number_input("Points surveyed", 20, 5000, 500, step=50, key="d_points")
        price = d.number_input("Revenue per barrel ($)", 1.0, 20.0, 4.5, step=0.5, format="%.1f", key="d_price")
        risk = e.number_input("Risk limit (%)", 0.5, 20.0, 2.5, step=0.5, format="%.1f", key="d_risk")
    try:
        return Economics(budget=budget * 1e6, wells=int(wells), points=int(points), revenue_per_unit=price * 1000, risk_limit=risk / 100)
    except ValidationError as exc:
        st.error(exc.errors()[0]["msg"].removeprefix("Value error, "), icon=":material/error:")
        return None


def _spark(p: np.ndarray, edges: np.ndarray, color: str) -> str:
    """Mini histogram of simulated profits: loss bars in red, profit bars in the region colour, a line at zero."""
    h, _ = np.histogram(p, bins=edges)
    h = h / max(h.max(), 1)
    bars = "".join(f'<i style="height:{max(v * 100, 1.5):.1f}%;background:{t.LOSS if (edges[i] + edges[i + 1]) / 2 < 0 else color};'
                   f'opacity:{0.6 if (edges[i] + edges[i + 1]) / 2 < 0 else 0.9}"></i>' for i, v in enumerate(h))
    zero = (0 - edges[0]) / (edges[-1] - edges[0]) * 100
    return (f'<div class="spark" role="img" aria-label="distribution of simulated profits">{bars}'
            f'<em style="left:{zero:.1f}%"></em></div><p class="spark-x"><span>{money(edges[0])}</span><span>profit per survey (line: $0)</span>'
            f'<span>{money(edges[-1])}</span></p>')


def _card(r: int, s: dict, p: np.ndarray, edges: np.ndarray, chosen: int | None, econ: Economics) -> str:
    scale = max(0.10, s["risk"] * 1.2, econ.risk_limit * 1.6)
    fill = t.GAIN if s["passes"] else t.LOSS
    if r == chosen:
        foot = f'<div class="rc-f pick">{ui.icon("verified")} Develop this region</div>'
    elif s["passes"]:
        foot = f'<div class="rc-f ok">{ui.icon("check_circle")} Passes, lower profit</div>'
    else:
        foot = f'<div class="rc-f no">{ui.icon("cancel")} Too risky</div>'
    return (f'<div class="rc{" pick" if r == chosen else ""}"><div class="rc-h" style="--c:{t.REGION[r]}"><b>Region {r}</b>'
            f'<span>{"chosen" if r == chosen else ""}</span></div><div class="rc-b">'
            f'<p class="rc-v">{money(s["mean"])}<small>mean profit</small></p>'
            f'<p class="rc-i">95% of surveys: {money(s["low"])} to {money(s["high"])}</p>{_spark(p, edges, t.REGION[r])}'
            f'<div class="gauge"><p class="gauge-t"><span>Risk of a loss</span><b>{s["risk"]:.1%}</b></p>'
            f'<div class="gauge-b"><i style="width:{min(s["risk"] / scale, 1) * 100:.1f}%;background:{fill}"></i>'
            f'<em style="left:{econ.risk_limit / scale * 100:.1f}%"></em></div>'
            f'<p class="gauge-t" style="margin-top:.2rem"><span></span><span>limit {econ.risk_limit:.1%}</span></p></div></div>{foot}</div>')


def render() -> None:
    ui.page("A-1", "Region decision", "Which region should OilyGiant develop?",
            "Survey <b>500 points</b>, develop the model's <b>best 200</b> on a <b>$100 million</b> budget, and accept a region only "
            "if the <b>risk of a loss is under 2.5%</b>. Each answer below comes from 10,000 simulated surveys of points the "
            "models never trained on.")

    with ui.panel("A-1.1", "The answer depends on the model", "gavel", "the region each model picks with the brief's economics", main=True):
        _answer()

    with ui.panel("A-1.2", "Explore the decision", "tune", "pick a model; each card shows the profit of 10,000 surveys (red: a loss) "
                  "and the risk of a loss against the limit"):
        model = st.segmented_control("Model that ranks the surveyed points", MODELS, default="Linear", required=True, key="d_model")
        econ = _economics()
        if econ is None:
            ui.footer()
            return
        key = econ.model_dump_json()
        profits = {r: data.profits(model, r, key) for r in REGIONS}
        summaries = {r: summarise(profits[r], econ.risk_limit) for r in REGIONS}
        chosen = choose(summaries)
        lo = min(np.percentile(p, 0.5) for p in profits.values())
        hi = max(np.percentile(p, 99.5) for p in profits.values())
        edges = np.linspace(min(lo, -abs(hi) * 0.05), hi, 36)
        st.html('<div class="rgrid">' + "".join(_card(r, summaries[r], profits[r], edges, chosen, econ) for r in REGIONS) + "</div>")
        if chosen is None:
            verdict = f"No region keeps the risk of a loss under {econ.risk_limit:.1%} with {model}."
        else:
            s = summaries[chosen]
            richest = data.geo().groupby("region")["product"].mean().max()
            verdict = (f"With <b>{model}</b>, develop <b>region {chosen}</b>: mean profit {money(s['mean'])}, risk of a loss "
                       f"{s['risk']:.1%}. Break-even is {econ.break_even:.1f} thousand barrels per well"
                       + (", more than the average point holds in any region, so the profit comes from picking the best wells."
                          if econ.break_even > richest else "."))
        ui.notes(verdict)
    ui.footer()
