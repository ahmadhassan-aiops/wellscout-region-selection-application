"""WellScout components: an engineering drawing set. The page is drafting paper with a fine grid; navigation is the
sheet index; every block is a framed drawing sheet (double rule) with a title block naming the sheet number; figures
sit in title-block cells; notes are numbered drawing notes."""

from __future__ import annotations

import html
from contextlib import contextmanager

import streamlit as st

from sheet import theme as t
from sheet.site import CODE_URL, DATA_CREDIT, LEARN_URL, NOTEBOOK_URL

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
:root {{ --paper:{t.PAPER}; --grid:{t.GRID}; --grid2:{t.GRID_MAJOR}; --panel:{t.PANEL}; --ink:{t.INK}; --muted:{t.MUTED}; --faint:{t.FAINT};
         --line:{t.LINE}; --accent:{t.ACCENT}; --accent-soft:{t.ACCENT_SOFT}; --gain:{t.GAIN}; --loss:{t.LOSS};
         --head:{t.HEAD}; --body:{t.BODY}; --mono:{t.MONO}; }}
html, body, [data-testid="stAppViewContainer"] {{ font-family: var(--body); color: var(--ink); }}
[data-testid="stAppViewContainer"], [data-testid="stMain"] {{ background-color: var(--paper);
    background-image: linear-gradient(var(--grid2) 1px, transparent 1px), linear-gradient(90deg, var(--grid2) 1px, transparent 1px),
                      linear-gradient(var(--grid) 1px, transparent 1px), linear-gradient(90deg, var(--grid) 1px, transparent 1px);
    background-size: 120px 120px, 120px 120px, 24px 24px, 24px 24px; }}
.block-container {{ padding-top: 4.1rem; max-width: 1240px; }}
/* Streamlit Cloud's toolbar strip is 60px tall and takes clicks: the sheet index starts below it */
header[data-testid="stHeader"] {{ background: var(--paper); }}
.msr {{ font-family: 'Material Symbols Rounded'; font-weight: normal; font-style: normal; line-height: 1; display: inline-block;
        -webkit-font-feature-settings: 'liga'; font-feature-settings: 'liga'; -webkit-font-smoothing: antialiased; }}

/* Drawing sheets: a white sheet in a double frame */
[data-testid="stVerticalBlock"][data-test-scroll-behavior] {{ border: 1.2px solid var(--ink) !important; border-radius: 0 !important;
    background: var(--panel); box-shadow: 3px 3px 0 rgba(19, 41, 75, .08); margin: 4px; }}
/* Primary sheets (keyed "main_*") get the drawing's double frame */
[class*="st-key-main_"] {{ border-width: 1.5px !important; box-shadow: 0 0 0 3px var(--paper), 0 0 0 4px var(--ink) !important; margin: 4px; }}

/* Sheet index (navigation) */
[data-testid="stHorizontalBlock"]:has(.brand) {{ background: var(--panel); border: 1.5px solid var(--ink); padding: 0; gap: 0;
    box-shadow: 0 0 0 3px var(--paper), 0 0 0 4px var(--ink); margin: 4px; }}
[data-testid="stHorizontalBlock"]:has(.brand) > [data-testid="stColumn"] {{ border-left: 1px solid var(--line); align-self: stretch;
    display: flex; flex-direction: column; justify-content: center; }}
[data-testid="stHorizontalBlock"]:has(.brand) > [data-testid="stColumn"]:first-child {{ border-left: none; }}
.brand {{ display: flex; align-items: center; gap: .65rem; padding: .55rem .8rem; }}
.brand .mk {{ width: 2.4rem; height: 2.4rem; border: 1.5px solid var(--ink); display: grid; place-items: center; color: var(--accent); }}
.brand .mk .msr {{ font-size: 1.6rem; }}
.brand .name {{ font-family: var(--head); font-weight: 700; font-size: 1.45rem; letter-spacing: .04em; text-transform: uppercase; margin: 0; line-height: 1; }}
.brand .tagline {{ font-family: var(--mono); font-size: .66rem; color: var(--muted); margin: .25rem 0 0; letter-spacing: .04em; }}
[data-testid="stHorizontalBlock"]:has(.brand) [data-testid="stPageLink"] a {{ border-radius: 0; padding: .7rem .5rem; justify-content: center;
    background: transparent; border: none; height: 100%; }}
[data-testid="stHorizontalBlock"]:has(.brand) [data-testid="stPageLink"] a p {{ font-family: var(--head); font-weight: 600; font-size: .95rem;
    letter-spacing: .05em; text-transform: uppercase; color: var(--ink); white-space: nowrap; }}
[data-testid="stHorizontalBlock"]:has(.brand) [data-testid="stPageLink"] a span {{ color: var(--accent); }}
[data-testid="stHorizontalBlock"]:has(.brand) [data-testid="stPageLink"] a:hover {{ background: #eef3f8; }}
[data-testid="stHorizontalBlock"]:has(.brand) [data-testid="stPageLink"] a:focus-visible {{ outline: 2px solid var(--ink) !important; outline-offset: -4px; }}

/* Page head */
.dwg {{ display: flex; gap: 0; margin: 1.4rem 0 .6rem; width: fit-content; border: 1.5px solid var(--ink); background: var(--panel); }}
.dwg span {{ font-family: var(--mono); font-size: .74rem; padding: .2rem .55rem; letter-spacing: .04em; }}
.dwg span:first-child {{ background: var(--ink); color: #fff; font-weight: 600; }}
.title {{ font-family: var(--head); font-size: 2.5rem; font-weight: 700; margin: 0; line-height: 1.08; color: var(--ink); }}
.lead {{ color: var(--muted); font-size: 1.05rem; line-height: 1.6; max-width: 780px; margin: .55rem 0 1.2rem; }}
.lead b {{ color: var(--ink); }}

/* Title block at the top of each sheet */
.tb {{ display: grid; grid-template-columns: auto 1fr auto; margin: -1rem -1rem .9rem; border-bottom: 1.5px solid var(--ink); }}
.tb .no {{ background: var(--ink); color: #fff; font-family: var(--mono); font-weight: 600; font-size: .85rem; padding: .55rem .75rem;
           display: flex; align-items: center; letter-spacing: .04em; }}
.tb .t {{ font-family: var(--head); font-weight: 700; font-size: 1.12rem; letter-spacing: .05em; text-transform: uppercase; margin: 0;
          padding: .5rem .8rem .45rem; align-self: center; line-height: 1.2; }}
.tb .ic {{ border-left: 1px solid var(--line); display: grid; place-items: center; padding: 0 .75rem; color: var(--accent); }}
.tb .ic .msr {{ font-size: 1.35rem; }}
.sub {{ font-family: var(--body); font-size: .88rem; color: var(--muted); margin: -.25rem 0 .85rem; line-height: 1.5; }}

/* Figures in title-block cells */
.cells {{ display: grid; grid-template-columns: repeat(var(--n), minmax(0, 1fr)); border: 1.5px solid var(--ink); background: var(--panel);
          margin: 4px 4px 1.1rem; box-shadow: 0 0 0 3px var(--paper), 0 0 0 4px var(--ink); }}
@media (max-width: 820px) {{ .cells {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
.cell {{ padding: .5rem .8rem .6rem; border-left: 1px solid var(--line); }}
.cell:first-child {{ border-left: none; }}
.cell.hl {{ background: var(--accent-soft); }}
.cell-l {{ font-family: var(--mono); font-size: .72rem; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); margin: 0; }}
.cell-v {{ font-family: var(--head); font-size: 1.75rem; font-weight: 700; margin: .1rem 0; line-height: 1.1; }}
.cell-n {{ font-size: .78rem; color: var(--faint); margin: 0; line-height: 1.4; }}

/* The decision block */
.decide {{ margin: 4px; display: grid; grid-template-columns: minmax(14rem, 1.1fr) repeat(3, minmax(0, 1fr)); border: 2px solid var(--ink); }}
@media (max-width: 860px) {{ .decide {{ grid-template-columns: 1fr 1fr; }} }}
.decide > div {{ padding: .7rem .9rem; border-left: 1px solid var(--line); }}
.decide > div:first-child {{ border-left: none; background: var(--c); color: #fff; }}
.decide .l {{ font-family: var(--mono); font-size: .68rem; letter-spacing: .07em; text-transform: uppercase; margin: 0; opacity: .85; }}
.decide .v {{ font-family: var(--head); font-size: 2rem; font-weight: 700; margin: .1rem 0 0; line-height: 1.05; }}
.decide .n {{ font-size: .8rem; margin: .25rem 0 0; color: var(--muted); }}
.decide > div:first-child .n {{ color: #fff; opacity: .9; }}
.decide.none > div:first-child {{ background: #5b6676; }}

/* Region columns */
.reg {{ border: 1.5px solid var(--ink); background: var(--panel); }}
.reg-h {{ display: flex; justify-content: space-between; align-items: center; background: var(--c); color: #fff; padding: .45rem .75rem; }}
.reg-h b {{ font-family: var(--head); font-size: 1.05rem; letter-spacing: .06em; text-transform: uppercase; }}
.reg-h span {{ font-family: var(--mono); font-size: .72rem; opacity: .9; }}
.reg dl {{ display: grid; grid-template-columns: 1fr auto; margin: 0; padding: 0 !important; }}
.reg dt, .reg dd {{ margin: 0; padding: .42rem .75rem; border-bottom: 1px solid #e5ebf1; font-size: .88rem; }}
.reg dt {{ color: var(--muted); }}
.reg dd {{ font-family: var(--mono); font-weight: 600; text-align: right; }}
.reg .verdict {{ padding: .5rem .75rem; font-family: var(--head); font-weight: 700; letter-spacing: .05em; text-transform: uppercase; font-size: .9rem;
                 display: flex; gap: .35rem; align-items: center; }}
.reg .verdict.ok {{ color: var(--gain); }} .reg .verdict.no {{ color: var(--loss); }}
.reg .verdict.pick {{ background: var(--accent-soft); color: var(--accent); border-top: 2px solid var(--accent); }}
.reg .verdict .msr {{ font-size: 1.15rem; }}

/* The answer: one column per model */
.answer {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0; border: 1.5px solid var(--ink); }}
@media (max-width: 820px) {{ .answer {{ grid-template-columns: 1fr; }} }}
.answer > div {{ padding: .9rem 1.1rem 1rem; border-left: 1px solid var(--line); position: relative; }}
.answer > div:first-child {{ border-left: none; }}
.answer .m {{ font-family: var(--mono); font-size: .74rem; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); margin: 0; }}
.answer .k {{ font-size: .82rem; color: var(--faint); margin: .1rem 0 .6rem; }}
.answer .r {{ font-family: var(--head); font-size: 2.3rem; font-weight: 700; margin: 0; line-height: 1; color: var(--c); display: flex; align-items: center; gap: .5rem; }}
.answer .r .msr {{ font-size: 1.8rem; color: var(--ink); }}
.answer .f {{ display: flex; gap: 1.2rem; margin: .7rem 0 0; font-size: .86rem; color: var(--muted); }}
.answer .f b {{ font-family: var(--mono); color: var(--ink); font-size: 1rem; }}
.answer .tag {{ position: absolute; top: .8rem; right: .9rem; font-family: var(--mono); font-size: .66rem; letter-spacing: .06em; text-transform: uppercase;
                border: 1px solid var(--line); padding: .05rem .4rem; color: var(--muted); }}
.takeaway {{ display: flex; gap: .7rem; align-items: flex-start; margin: .9rem 0 0; padding: .7rem .9rem; background: var(--accent-soft);
             border-left: 4px solid var(--accent); font-size: .98rem; line-height: 1.55; }}
.takeaway .msr {{ color: var(--accent); font-size: 1.4rem; }}

/* Region cards with a mini profit distribution and a risk gauge */
.rgrid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .9rem; }}
@media (max-width: 820px) {{ .rgrid {{ grid-template-columns: 1fr; }} }}
.rc {{ border: 1.2px solid var(--ink); background: var(--panel); display: flex; flex-direction: column; }}
.rc.pick {{ outline: 3px solid var(--accent); outline-offset: 2px; }}
.rc-h {{ display: flex; justify-content: space-between; align-items: center; background: var(--c); color: #fff; padding: .45rem .75rem; }}
.rc-h b {{ font-family: var(--head); font-size: 1.05rem; letter-spacing: .06em; text-transform: uppercase; }}
.rc-h span {{ font-family: var(--mono); font-size: .72rem; }}
.rc-b {{ padding: .7rem .8rem .2rem; }}
.rc-v {{ font-family: var(--head); font-size: 1.9rem; font-weight: 700; margin: 0; line-height: 1; }}
.rc-v small {{ font-family: var(--body); font-size: .8rem; font-weight: 400; color: var(--muted); margin-left: .35rem; }}
.rc-i {{ font-size: .8rem; color: var(--muted); margin: .25rem 0 .5rem; font-family: var(--mono); }}
.spark {{ position: relative; display: flex; align-items: flex-end; gap: 1px; height: 64px; border-bottom: 1px solid var(--line); }}
.spark i {{ flex: 1; display: block; }}
.spark em {{ position: absolute; top: 0; bottom: -4px; width: 1.5px; background: var(--ink); }}
.spark-x {{ display: flex; justify-content: space-between; font-family: var(--mono); font-size: .66rem; color: var(--faint); margin: .15rem 0 0; }}
.gauge {{ margin: .55rem 0 .2rem; }}
.gauge-t {{ display: flex; justify-content: space-between; font-size: .78rem; color: var(--muted); margin: 0 0 .25rem; }}
.gauge-t b {{ font-family: var(--mono); color: var(--ink); }}
.gauge-b {{ position: relative; height: 10px; background: #edf1f5; border: 1px solid var(--line); }}
.gauge-b i {{ position: absolute; left: 0; top: 0; bottom: 0; }}
.gauge-b em {{ position: absolute; top: -5px; bottom: -5px; width: 2px; background: var(--ink); }}
.rc-f {{ margin-top: auto; padding: .5rem .8rem; border-top: 1px solid var(--line); font-family: var(--head); font-weight: 700; letter-spacing: .05em;
         text-transform: uppercase; font-size: .88rem; display: flex; gap: .35rem; align-items: center; }}
.rc-f .msr {{ font-size: 1.1rem; }}
.rc-f.pick {{ background: var(--accent-soft); color: var(--accent); }}
.rc-f.ok {{ color: var(--gain); }} .rc-f.no {{ color: var(--loss); }}

/* Tables in drawing style */
.tbl {{ width: 100%; border-collapse: collapse; font-size: .88rem; border: 1.5px solid var(--ink); }}
.tbl th {{ font-family: var(--mono); font-size: .68rem; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); font-weight: 600;
           text-align: left; padding: .45rem .6rem; border-bottom: 1.5px solid var(--ink); background: #f6f8fb; }}
.tbl td {{ padding: .42rem .6rem; border-bottom: 1px solid #e5ebf1; border-left: 1px solid #eef2f6; }}
.tbl th.n, .tbl td.n {{ text-align: right; }}
.tbl td.n {{ font-family: var(--mono); }}
.tbl tr.pick td {{ background: var(--accent-soft); font-weight: 600; }}
.sw {{ display: inline-block; width: .7rem; height: .7rem; background: var(--c); margin-right: .4rem; vertical-align: -1px; }}
.ok {{ color: var(--gain); }} .no {{ color: var(--loss); }}
.ok .msr, .no .msr {{ font-size: 1rem; vertical-align: -3px; }}
.tbl.tight td, .tbl.tight th {{ padding-left: .4rem; padding-right: .4rem; }}

/* Survey ledger */
.ledger {{ border: 1.5px solid var(--ink); }}
.ledger div {{ display: grid; grid-template-columns: 1fr auto; padding: .45rem .75rem; border-bottom: 1px solid #e5ebf1; font-size: .9rem; }}
.ledger div span:last-child {{ font-family: var(--mono); font-weight: 600; }}
.ledger div.tot {{ border-top: 2px solid var(--ink); border-bottom: none; font-weight: 700; background: #f6f8fb; }}

/* Drawing notes */
.notes {{ border-top: 1.5px solid var(--ink); margin: .9rem 0 0; padding: .55rem 0 0; }}
.notes .h {{ font-family: var(--mono); font-size: .7rem; letter-spacing: .1em; color: var(--muted); margin: 0 0 .3rem; }}
.notes ol {{ margin: 0; padding-left: 1.4rem; }}
.notes li {{ font-size: .9rem; line-height: 1.55; margin: 0 0 .3rem; }}
.notes li::marker {{ font-family: var(--mono); font-weight: 600; color: var(--accent); }}
.caution {{ display: flex; gap: .55rem; border: 1px dashed var(--ink); padding: .55rem .8rem; margin: .8rem 0 0; font-size: .87rem;
            line-height: 1.5; color: var(--muted); background: #fafbfd; }}
.caution .msr {{ color: var(--accent); font-size: 1.15rem; }}

/* Data & method */
.facts {{ display: grid; grid-template-columns: minmax(9rem, 30%) 1fr; margin: 0; padding: 0 !important; border-top: 1.5px solid var(--ink); }}
.facts dt, .facts dd {{ padding: .48rem .3rem; border-bottom: 1px solid #e5ebf1; margin: 0; font-size: .9rem; line-height: 1.5; }}
.facts dt {{ font-family: var(--mono); font-size: .72rem; letter-spacing: .05em; text-transform: uppercase; color: var(--muted); }}

/* Footer: the drawing's revision strip */
.foot {{ margin: 2rem 4px .5rem; border: 1.5px solid var(--ink); background: var(--panel); display: flex; flex-wrap: wrap; font-size: .82rem; }}
.foot > * {{ padding: .5rem .8rem; border-right: 1px solid var(--line); }}
.foot a {{ color: var(--ink); font-weight: 600; text-decoration: none; }}
.foot a:hover {{ color: var(--accent); }}
.foot .credit {{ flex-basis: 100%; border-top: 1px solid var(--line); border-right: none; color: var(--faint); font-size: .78rem; }}
</style>
"""

CONTROLS = """<style>
/* Controls: one shape, one border weight and one focus ring for every button, segment and input */
:root { --k-a: #13294b; --k-a-text: #13294b; --k-fill: #13294b; --k-fill-2: #0a1830; --k-soft: #e9eff6; --k-ink: #13294b;
        --k-line: #8fa1b6; --k-panel: #ffffff; --k-r: 0px; }
[data-testid="stMain"] :is([data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-primary"],
  [data-testid="stBaseButton-secondaryFormSubmit"], [data-testid="stBaseButton-primaryFormSubmit"],
  [data-testid="stBaseButton-segmented_control"], [data-testid="stBaseButton-segmented_controlActive"],
  [data-testid="stBaseButton-pills"], [data-testid="stBaseButton-pillsActive"]) {
    border-radius: var(--k-r) !important; border: 1.5px solid var(--k-line) !important; background: var(--k-panel) !important;
    color: var(--k-ink) !important; box-shadow: none !important; min-height: 2.45rem; padding: .35rem .95rem !important;
    transition: border-color .12s ease, background-color .12s ease, color .12s ease; }
[data-testid="stMain"] :is([data-testid^="stBaseButton-secondary"], [data-testid^="stBaseButton-primary"],
  [data-testid^="stBaseButton-segmented_control"], [data-testid^="stBaseButton-pills"]) p {
    font-family: 'IBM Plex Sans Condensed', 'Arial Narrow', sans-serif; font-size: .95rem; font-weight: 600; letter-spacing: .04em; text-transform: uppercase; color: inherit; }
[data-testid="stMain"] :is([data-testid^="stBaseButton-secondary"], [data-testid="stBaseButton-segmented_control"],
  [data-testid="stBaseButton-pills"]):hover { border-color: var(--k-a) !important; color: var(--k-a-text) !important; background: var(--k-soft) !important; }
[data-testid="stMain"] :is([data-testid^="stBaseButton-primary"], [data-testid="stBaseButton-segmented_controlActive"],
  [data-testid="stBaseButton-pillsActive"]) { background: var(--k-fill) !important; border-color: var(--k-fill) !important; color: #fff !important; }
[data-testid="stMain"] :is([data-testid^="stBaseButton-primary"], [data-testid="stBaseButton-segmented_controlActive"],
  [data-testid="stBaseButton-pillsActive"]):hover { background: var(--k-fill-2) !important; border-color: var(--k-fill-2) !important; color: #fff !important; }
[data-testid="stMain"] :is([data-testid^="stBaseButton-secondary"], [data-testid^="stBaseButton-primary"]):active { transform: translateY(1px); }
[data-testid="stMain"] [data-testid^="stBaseButton-"]:disabled { opacity: .45; }

/* Segmented controls: one joined strip, the chosen segment filled */
[data-testid="stMain"] [data-baseweb="button-group"] { gap: 0 !important; width: fit-content; max-width: 100%; border-radius: var(--k-r); }
[data-testid="stMain"] [data-baseweb="button-group"] > button { border-radius: 0 !important; margin: 0 0 0 -1.5px !important; position: relative;
    padding: .35rem .8rem !important; white-space: nowrap; }
[data-testid="stMain"] [data-baseweb="button-group"] > button:first-child { margin-left: 0 !important; }
[data-testid="stMain"] [data-baseweb="button-group"] > button:hover { z-index: 1; }
[data-testid="stMain"] [data-baseweb="button-group"] > [data-testid$="Active"] { z-index: 2; }

/* The focus ring: the same 2px ring, 2px off the edge, on every control (mouse click and keyboard alike) */
[data-testid="stMain"] [data-testid^="stBaseButton-"]:focus, [data-testid="stMain"] [data-testid^="stBaseButton-"]:focus-visible,
[data-testid="stMain"] [role="slider"]:focus-visible, [data-testid="stMain"] summary:focus-visible, [data-testid="stMain"] a:focus-visible {
    outline: 2px solid var(--k-a) !important; outline-offset: 2px; box-shadow: none !important; }
[data-testid="stMain"] [data-baseweb="button-group"] > button:focus, [data-testid="stMain"] [data-baseweb="button-group"] > button:focus-visible { outline: none !important; }
[data-testid="stMain"] [data-baseweb="button-group"]:focus-within { outline: 2px solid var(--k-a); outline-offset: 2px; }

/* Inputs */
[data-testid="stMain"] :is([data-testid="stNumberInputContainer"], [data-testid="stTextInput"] [data-baseweb="input"],
  [data-baseweb="select"] > div, [data-baseweb="textarea"]) {
    border-radius: var(--k-r) !important; border: 1.5px solid var(--k-line) !important; background: var(--k-panel) !important;
    min-height: 2.45rem; transition: border-color .12s ease; }
[data-testid="stMain"] :is([data-testid="stNumberInputContainer"], [data-baseweb="select"] > div):hover { border-color: var(--k-a) !important; }
[data-testid="stMain"] :is([data-testid="stNumberInputContainer"], [data-testid="stTextInput"] [data-baseweb="input"],
  [data-baseweb="select"] > div, [data-baseweb="textarea"]):focus-within {
    border-color: var(--k-a) !important; outline: 2px solid var(--k-a); outline-offset: 2px; box-shadow: none !important; }
[data-testid="stMain"] :is([data-baseweb="input"], [data-baseweb="base-input"], input, textarea) { background: transparent !important; }
[data-testid="stMain"] [data-testid="stNumberInputContainer"] [data-baseweb="input"] { border: none !important; }
[data-testid="stMain"] :is(input, textarea) { font-family: 'IBM Plex Mono', Consolas, monospace; color: var(--k-ink); }
[data-testid="stMain"] [data-testid="stNumberInputContainer"] > div:last-child { border-left: 1px solid var(--k-line); }
[data-testid="stMain"] :is([data-testid="stNumberInputStepDown"], [data-testid="stNumberInputStepUp"]) { color: var(--k-ink) !important; border-radius: 0 !important; width: 2.1rem; }
[data-testid="stMain"] :is([data-testid="stNumberInputStepDown"], [data-testid="stNumberInputStepUp"]):hover:not(:disabled) { background: var(--k-soft) !important; }
[data-testid="stMain"] [data-testid="stNumberInputStepUp"] { border-left: 1px solid var(--k-line) !important; }
[data-baseweb="popover"] [data-baseweb="menu"], [data-baseweb="popover"] ul[role="listbox"] { border-radius: 0 !important; border: 1.5px solid var(--k-line); }
[data-baseweb="popover"] li[role="option"]:hover, [data-baseweb="popover"] li[aria-selected="true"] { background: var(--k-soft) !important; }

/* Labels and sliders */
[data-testid="stMain"] [data-testid="stWidgetLabel"]:not([data-testid="stCheckbox"] *) p { font-family: 'IBM Plex Mono', Consolas, monospace; font-size: .7rem;
    font-weight: 600; letter-spacing: .07em; text-transform: uppercase; color: #4a5a70; }
[data-testid="stMain"] [data-baseweb="slider"] [role="slider"] { border-radius: 0 !important; box-shadow: 0 0 0 3px var(--k-panel), 0 0 0 4.5px var(--k-fill) !important; }
[data-testid="stMain"] [data-testid="stSliderThumbValue"] { font-family: 'IBM Plex Mono', Consolas, monospace; font-weight: 600; }
[data-testid="stMain"] [data-testid="stAlert"] > div { border-radius: 0 !important; }
</style>"""


def inject_css() -> None:
    st.html(CSS + CONTROLS)


def icon(name: str) -> str:
    return f'<span class="msr" aria-hidden="true">{name}</span>'


def page(sheet_no: str, sheet_name: str, title: str, lead: str) -> None:
    st.html(f'<div class="dwg"><span>DWG {html.escape(sheet_no)}</span><span>{html.escape(sheet_name)}</span></div>'
            f'<h1 class="title">{html.escape(title)}</h1><p class="lead">{lead}</p>')


@contextmanager
def panel(no: str, title: str, pictogram: str, sub: str = "", main: bool = False):
    """A drawing sheet; `main` sheets (the page's primary result) get the double frame."""
    with st.container(border=True, key=f"main_{no.replace('.', '_').replace('-', '_')}" if main else None):
        st.html(f'<div class="tb"><span class="no">{html.escape(no)}</span><p class="t">{html.escape(title)}</p>'
                f'<span class="ic">{icon(pictogram)}</span></div>' + (f'<p class="sub">{sub}</p>' if sub else ""))
        yield


def cells(items: list[tuple[str, str, str]], highlight: int | None = None) -> None:
    body = "".join(f'<div class="cell{" hl" if i == highlight else ""}"><p class="cell-l">{html.escape(l)}</p>'
                   f'<p class="cell-v">{v}</p><p class="cell-n">{n}</p></div>' for i, (l, v, n) in enumerate(items))
    st.html(f'<div class="cells" style="--n:{len(items)}">{body}</div>')


def notes(*items: str) -> None:
    st.html('<div class="notes"><p class="h">NOTES</p><ol>' + "".join(f"<li>{i}</li>" for i in items) + "</ol></div>")


def caution(text: str, pictogram: str = "warning") -> None:
    st.html(f'<div class="caution">{icon(pictogram)}<div>{text}</div></div>')


def swatch(region: int) -> str:
    return f'<span class="sw" style="--c:{t.REGION[region]}"></span>'


def passfail(ok: bool) -> str:
    return (f'<span class="ok">{icon("check_circle")} passes</span>' if ok else f'<span class="no">{icon("cancel")} fails</span>')


def footer() -> None:
    st.html(f'<div class="foot"><span>WellScout · <b>Ahmad Hassan</b>, AI Engineer</span>'
            f'<a href="{NOTEBOOK_URL}" target="_blank">Notebook</a><a href="{CODE_URL}" target="_blank">App code</a>'
            f'<a href="{LEARN_URL}" target="_blank">Learn with Ahmad</a><span class="credit">{html.escape(DATA_CREDIT)}</span></div>')
