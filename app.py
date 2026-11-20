"""
WellScout: which region should OilyGiant develop? 10,000 simulated surveys per region under three models, one
survey up close, a single-point check, the regions' data and the method. Models in model/ (built by train.py), code
in wellscout/.
"""

import streamlit as st

st.set_page_config(page_title="WellScout | Oil region selection | Ahmad Hassan", page_icon=":material/oil_barrel:",
                   layout="wide", initial_sidebar_state="collapsed")

from nav import PAGES  # noqa: E402
from sheet.ui import icon, inject_css  # noqa: E402

inject_css()
current = st.navigation(PAGES, position="hidden")
cols = st.columns([1.6, 1, 1, 1.1, 1.05, 1], vertical_alignment="center")
cols[0].html(f'<div class="brand"><span class="mk">{icon("oil_barrel")}</span><div><p class="name">WellScout</p>'
             '<p class="tagline">OIL REGION SELECTION</p></div></div>')
for col, p in zip(cols[1:], PAGES):
    col.page_link(p, label=p.title, icon=p.icon, width="stretch")
k = [p.title for p in PAGES].index(current.title) + 2
st.html(f'<style>[data-testid="stHorizontalBlock"]:has(.brand) > [data-testid="stColumn"]:nth-child({k}) {{ background: var(--ink); }} '
        f'[data-testid="stHorizontalBlock"]:has(.brand) > [data-testid="stColumn"]:nth-child({k}) a * '
        '{ color: #fff !important; }</style>')
current.run()
