"""Every page renders without an exception, including the main interactions."""

from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest

PAGES = ["views/decision.py", "views/survey.py", "views/site.py", "views/regions.py", "views/method.py"]


def run(module: str) -> AppTest:
    script = f"""
import importlib
from sheet.ui import inject_css
inject_css()
importlib.import_module("{module.replace('/', '.').removesuffix('.py')}").render()
"""
    return AppTest.from_string(script, default_timeout=120).run()


@pytest.mark.parametrize("page", PAGES)
def test_page_renders(page):
    at = run(page)
    assert not at.exception, at.exception


@pytest.mark.parametrize("model", ["Linear", "Linear + squares", "LightGBM"])
def test_decision_models(model):
    at = run("views/decision.py")
    at.segmented_control(key="d_model").set_value(model).run()
    assert not at.exception
    region = {"Linear": "1", "Linear + squares": "2", "LightGBM": "2"}[model]
    assert any(f"develop <b>region {region}</b>" in h.proto.body for h in at.get("html"))


def test_decision_invalid_and_strict_economics():
    at = run("views/decision.py")
    at.number_input(key="d_wells").set_value(600).run()
    assert at.error
    at.number_input(key="d_wells").set_value(200).run()
    at.number_input(key="d_risk").set_value(0.5).run()
    assert not at.exception


def test_survey_new_and_switch():
    at = run("views/survey.py")
    at.button(key="s_new").click().run()
    assert not at.exception
    at.segmented_control(key="s_region").set_value(1).run()
    at.segmented_control(key="s_model").set_value("LightGBM").run()
    assert not at.exception


def test_site_load_point():
    at = run("views/site.py")
    at.button(key="c_load").click().run()
    assert not at.exception
    assert any("point " in h.proto.body for h in at.get("html"))
