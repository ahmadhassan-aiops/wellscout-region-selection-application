"""Regions: what the exploration data looks like, and the two patterns that drive the decision."""

from __future__ import annotations

import streamlit as st

from sheet import charts, data, ui
from wellscout.economics import Economics
from wellscout.model import REGIONS


def render() -> None:
    econ = Economics()
    geo = data.geo()
    ui.page("B-1", "Regions", "What the exploration data shows",
            "100,000 exploration points per region, each with three measurements (<b>f0, f1, f2</b>; anonymous but "
            "meaningful) and its reserves in thousand barrels. Two patterns decide which region wins.")
    stats = []
    for r in REGIONS:
        d = geo[geo["region"] == r]["product"]
        stats.append((f"Region {r}: mean reserves", f"{d.mean():.1f}", f"{(d >= econ.break_even).mean():.0%} of points above break-even"))
    stats.append(("Break-even per well", f"{econ.break_even:.1f}", "thousand barrels ($500,000 at $4,500 each)"))
    ui.cells(stats, highlight=3)

    with ui.panel("B-1.1", "Reserves per point", "stacked_bar_chart", main=True, sub="share of each region's points by reserves; dashed: break-even"):
        charts.show(charts.histograms(geo, econ.break_even), "hist")
        ui.notes("Regions 0 and 2 spread widely around 92 to 95 thousand barrels; about a third of their points would pay for a well.",
                 "Region 1 is lumpy: its points hold one of 12 values, and its mean is the lowest (69). Yet it is the safest region "
                 "for a straight-line model, as the next sheet shows.")

    a, b = st.columns(2, gap="medium")
    with a:
        with ui.panel("B-1.2", "Region 1: twelve steps along f2", "stairs", "5,000 random points"):
            d1 = geo[geo["region"] == 1]
            charts.show(charts.steps(d1), "steps")
            ui.notes(f"Reserves rise in steps of about 27 thousand barrels with f2 (correlation {d1[['f2', 'product']].corr().iloc[0, 1]:.3f}). "
                     "Any model reads f2 and knows a point's reserves almost exactly, so the best 200 of a survey are always "
                     "the truly rich points: low risk, but a capped upside.")
    with b:
        with ui.panel("B-1.3", "Region 2: a bowl in f0 and f1", "blur_circular", "mean reserves on a grid of f0 and f1"):
            d2 = geo[geo["region"] == 2]
            charts.show(charts.bowl(d2), "bowl")
            ui.notes("Reserves grow the further a point lies from f0 = 0 and f1 = 0, in every direction. A straight line through "
                     "a bowl is flat, so plain linear regression ignores f0 and f1 here; squared terms or trees capture it and "
                     "pick richer wells.")

    with ui.panel("B-1.4", "How each measurement relates to reserves", "table_chart", "correlation with reserves (straight-line relationship only)"):
        rows = ""
        for r in REGIONS:
            d = geo[geo["region"] == r]
            corr = d[["f0", "f1", "f2", "product"]].corr()["product"]
            rows += (f'<tr><td>{ui.swatch(r)}Region {r}</td>' + "".join(f'<td class="n">{corr[f]:+.3f}</td>' for f in ("f0", "f1", "f2"))
                     + f'<td class="n">{d["product"].nunique():,}</td></tr>')
        st.html('<table class="tbl"><thead><tr><th>Region</th><th class="n">f0</th><th class="n">f1</th><th class="n">f2</th>'
                f'<th class="n">Distinct reserve values</th></tr></thead><tbody>{rows}</tbody></table>')
        ui.notes("In region 2, f0 and f1 show no straight-line correlation at all (about 0), yet they matter through the bowl: "
                 "correlation alone would have missed them.")
    ui.footer()
