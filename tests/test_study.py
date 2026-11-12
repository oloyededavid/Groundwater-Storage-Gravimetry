"""Checks on the rebuilt Lake Chad study: the data follow the real GRACE record and the page shows only computed numbers."""
import json
import re
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
DOCS = ROOT / "docs"


def test_grace_months_are_calendar_months_with_the_mission_gap():
    g = pd.read_csv(PROC / "grace_tws_monthly.csv")
    p = g[g.domain == "primary"]
    assert p.month.is_unique
    months = set(p.month)
    for m in ["2017-08", "2017-12", "2018-01", "2018-05"]:
        assert m not in months  # the GRACE to GRACE-FO break must stay a gap
    assert {"2002-04", "2018-06"} <= months


def test_soil_models_have_one_value_per_month_and_area():
    for name in ("gldas_noah_monthly.csv", "terraclimate_soil_monthly.csv"):
        d = pd.read_csv(PROC / name)
        assert not d.duplicated(["month", "domain"]).any()
        assert set(d.domain) == {"primary", "sensitivity"}


def test_results_intervals_contain_the_estimate():
    r = json.loads((DOCS / "data" / "results.json").read_text())
    for area in r["areas"].values():
        for s in area["series"].values():
            for t in s["trends"].values():
                lo, hi = t["ci95_block_bootstrap"]
                assert lo <= t["trend_mm_yr"] <= hi
                assert t["n_eff"] <= t["n_months"]


def test_paper_and_page_have_no_unfilled_placeholders():
    for p in (ROOT / "paper" / "paper.md", DOCS / "index.html"):
        text = p.read_text(encoding="utf-8")
        assert "{{" not in text and "}}" not in text


def test_page_figures_exist():
    html = (DOCS / "index.html").read_text(encoding="utf-8")
    srcs = re.findall(r'src="(assets/[^"]+)"', html)
    assert srcs
    for s in srcs:
        assert (DOCS / s).exists(), s


def test_the_withdrawn_series_is_archived_not_used():
    assert (ROOT / "archive" / "withdrawn-v1" / "lake_chad_gravimetry_timeseries_2002_2025.csv").exists()
    for p in (ROOT / "scripts").glob("*.py"):
        assert "lake_chad_gravimetry_timeseries" not in p.read_text()
