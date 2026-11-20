"""Page registry (custom sheet index, native navigation hidden)."""

import streamlit as st

from views import decision, method, regions, site, survey

DECISION = st.Page(decision.render, title="A-1 Decision", icon=":material/gavel:", url_path="decision", default=True)
SURVEY = st.Page(survey.render, title="A-2 Survey", icon=":material/explore:", url_path="survey")
SITE = st.Page(site.render, title="A-3 Site check", icon=":material/straighten:", url_path="site")
REGIONS = st.Page(regions.render, title="B-1 Regions", icon=":material/map:", url_path="regions")
METHOD = st.Page(method.render, title="C-1 Method", icon=":material/description:", url_path="method")

PAGES = [DECISION, SURVEY, SITE, REGIONS, METHOD]
