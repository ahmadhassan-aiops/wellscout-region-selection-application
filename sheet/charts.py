"""Plotly charts drawn like technical figures: thin navy axes, region colours, system fonts."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sheet import theme as t

CONFIG = {"displayModeBar": False, "responsive": True}


def _base(fig: go.Figure, height: int = 340, legend: bool = False) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=8, r=14, t=12, b=8), paper_bgcolor="#fff", plot_bgcolor="#fff",
                      font=dict(family=t.CHART_FONT, size=12, color=t.MUTED), showlegend=legend,
                      legend=dict(orientation="h", y=1.1, x=0), hoverlabel=dict(bgcolor="#fff", font=dict(family=t.CHART_FONT, color=t.INK)))
    fig.update_xaxes(showgrid=True, gridcolor="#eef2f6", linecolor=t.INK, ticks="outside", tickcolor=t.INK, zeroline=False, mirror=True)
    fig.update_yaxes(showgrid=True, gridcolor="#eef2f6", linecolor=t.INK, ticks="outside", tickcolor=t.INK, zeroline=False, mirror=True)
    return fig


def show(fig: go.Figure, key: str) -> None:
    st.plotly_chart(fig, config=CONFIG, key=key, width="stretch")


def profit_curves(profits: dict[int, np.ndarray], chosen: int | None) -> go.Figure:
    """Distribution of simulated profits per region (million dollars), loss side shaded."""
    fig = go.Figure()
    lo = min(np.percentile(p, 0.2) for p in profits.values()) / 1e6
    hi = max(np.percentile(p, 99.8) for p in profits.values()) / 1e6
    edges = np.linspace(lo, hi, 70)
    fig.add_vrect(x0=lo, x1=0, fillcolor=t.LOSS, opacity=0.06, line_width=0)
    for r, p in profits.items():
        h, _ = np.histogram(p / 1e6, bins=edges)
        mid = (edges[:-1] + edges[1:]) / 2
        fig.add_trace(go.Scatter(x=mid, y=h / len(p) * 100, mode="lines", line=dict(color=t.REGION[r], width=3.2 if r == chosen else 1.8,
                                 shape="hvh"), name=f"Region {r}", hovertemplate="%{x:.1f} $M: %{y:.1f}% of surveys<extra>" + f"region {r}</extra>"))
    fig.add_vline(x=0, line=dict(color=t.LOSS, width=1.5))
    fig.add_annotation(x=0, y=1, yref="paper", text="loss | profit", showarrow=False, yanchor="top", font=dict(size=11, color=t.LOSS))
    fig.update_xaxes(title_text="profit of one survey and its 200 wells (million dollars)")
    fig.update_yaxes(title_text="share of surveys (%)", rangemode="tozero")
    return _base(fig, 340, legend=True)


def survey(df: pd.DataFrame, break_even: float, region: int) -> go.Figure:
    """One survey: predicted against actual reserves; the developed wells filled."""
    picked, rest = df[df["picked"]], df[~df["picked"]]
    fig = go.Figure()
    fig.add_hline(y=break_even, line=dict(color=t.ACCENT, width=1.4, dash="dash"))
    fig.add_annotation(x=1, xref="paper", y=break_even, text=f"break-even {break_even:.1f}", showarrow=False, xanchor="right",
                       yanchor="bottom", font=dict(size=11, color=t.ACCENT))
    fig.add_trace(go.Scatter(x=rest["pred"], y=rest["product"], mode="markers", name="Surveyed, not developed",
                             marker=dict(size=6, color="rgba(0,0,0,0)", line=dict(color=t.FAINT, width=1)),
                             hovertemplate="predicted %{x:.1f}, actual %{y:.1f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=picked["pred"], y=picked["product"], mode="markers", name="Developed (model's best)",
                             marker=dict(size=7, color=t.REGION[region], line=dict(color="#fff", width=0.6)),
                             hovertemplate="predicted %{x:.1f}, actual %{y:.1f}<extra>developed</extra>"))
    fig.update_xaxes(title_text="predicted reserves (thousand barrels)")
    fig.update_yaxes(title_text="actual reserves (thousand barrels)")
    return _base(fig, 400, legend=True)


def site(preds: dict[str, float], break_even: float, region: int) -> go.Figure:
    names = list(preds)
    fig = go.Figure(go.Bar(x=[preds[n] for n in names], y=names, orientation="h", marker_color=t.REGION[region],
                           text=[f"{preds[n]:.1f}" for n in names], textposition="outside", cliponaxis=False,
                           hovertemplate="%{y}: %{x:.1f} thousand barrels<extra></extra>"))
    fig.add_vline(x=break_even, line=dict(color=t.ACCENT, width=1.5, dash="dash"))
    fig.add_annotation(x=break_even, y=1, yref="paper", text=f"break-even {break_even:.1f}", showarrow=False, yanchor="top",
                       xanchor="left", xshift=4, font=dict(size=11, color=t.ACCENT), bgcolor="#fff")
    fig.update_xaxes(title_text="predicted reserves (thousand barrels)", range=[0, max(max(preds.values()), break_even) * 1.25])
    fig.update_yaxes(autorange="reversed", showgrid=False)
    return _base(fig, 230)


def histograms(geo: pd.DataFrame, break_even: float) -> go.Figure:
    fig = go.Figure()
    for r in (0, 1, 2):
        fig.add_trace(go.Histogram(x=geo.loc[geo["region"] == r, "product"], name=f"Region {r}", xbins=dict(start=0, end=190, size=4),
                                   histnorm="percent", marker_color=t.REGION[r], opacity=0.55,
                                   hovertemplate="%{x}: %{y:.1f}%<extra>" + f"region {r}</extra>"))
    fig.update_layout(barmode="overlay")
    fig.add_vline(x=break_even, line=dict(color=t.ACCENT, width=1.5, dash="dash"))
    fig.add_annotation(x=break_even, y=1, yref="paper", text=f"break-even {break_even:.1f}", showarrow=False, xanchor="left",
                       yanchor="top", xshift=4, font=dict(size=11, color=t.ACCENT))
    fig.update_xaxes(title_text="reserves per point (thousand barrels)")
    fig.update_yaxes(title_text="share of points (%)")
    return _base(fig, 330, legend=True)


def bowl(d: pd.DataFrame) -> go.Figure:
    """Mean reserves on a grid of f0 and f1 (region 2's curved pattern)."""
    b0 = pd.cut(d["f0"], np.linspace(-6, 6, 25))
    b1 = pd.cut(d["f1"], np.linspace(-6, 6, 25))
    g = d.groupby([b1, b0], observed=False)["product"].mean().unstack()
    x = [round(c.mid, 1) for c in g.columns]
    y = [round(c.mid, 1) for c in g.index]
    fig = go.Figure(go.Heatmap(z=g.values, x=x, y=y, colorscale=[[0, "#f4f0fc"], [0.5, "#a98be0"], [1, "#3b1d7a"]], xgap=1, ygap=1,
                               colorbar=dict(title=dict(text="mean reserves", side="right"), thickness=12, outlinewidth=0),
                               hovertemplate="f0 %{x}, f1 %{y}: %{z:.0f}<extra></extra>"))
    fig.update_xaxes(title_text="f0", showgrid=False)
    fig.update_yaxes(title_text="f1", showgrid=False, scaleanchor="x")
    return _base(fig, 360)


def steps(d: pd.DataFrame) -> go.Figure:
    """Region 1: reserves against f2 (12 levels)."""
    s = d.sample(5000, random_state=0)
    fig = go.Figure(go.Scatter(x=s["f2"], y=s["product"], mode="markers", marker=dict(size=4, color=t.REGION[1], opacity=0.45),
                               hovertemplate="f2 %{x:.2f}: %{y:.1f}<extra></extra>"))
    fig.update_xaxes(title_text="f2")
    fig.update_yaxes(title_text="reserves (thousand barrels)")
    return _base(fig, 360)
