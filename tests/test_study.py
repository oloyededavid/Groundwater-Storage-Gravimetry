"""Tests for the Lake Chad study: the helper functions, and the outputs follow the real GRACE record."""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import grids  # noqa: E402
import s02_grace  # noqa: E402
import s05_storage as st  # noqa: E402
import study  # noqa: E402

PROC = ROOT / "data" / "processed"
DOCS = ROOT / "docs"


# helper functions -----------------------------------------------------------------------------------------------

def test_weights_give_the_fraction_of_each_cell_inside_the_shape():
    lat = np.array([1.5, 0.5])          # descending, 1-degree cells
    lon = np.array([0.5, 1.5, 2.5])
    w = grids.weights(lat, lon, box(0.0, 0.0, 1.5, 2.0), sub=10)
    frac = w / np.cos(np.deg2rad(lat))[:, None]
    assert np.allclose(frac, [[1, 0.5, 0], [1, 0.5, 0]], atol=1e-9)
    w_up = grids.weights(lat[::-1], lon, box(0.0, 0.0, 1.5, 2.0), sub=10)
    assert np.allclose(w_up, w[::-1])   # latitude order does not matter


def test_two_fields_in_one_month_move_the_later_one_forward():
    t = pd.to_datetime(["2011-09-15", "2011-10-02", "2011-10-30", "2011-12-16"])
    assert s02_grace.months(t) == ["2011-09", "2011-10", "2011-11", "2011-12"]


def test_gls_rate_recovers_a_known_slope_with_autocorrelated_noise_and_gaps():
    rng = np.random.default_rng(3)
    months = pd.period_range("2002-04", "2020-12", freq="M")
    keep = rng.random(len(months)) > 0.1
    e = np.zeros(len(months))
    for i in range(1, len(e)):
        e[i] = 0.8 * e[i - 1] + rng.normal(0, 5)
    t = st.tdec(months.astype(str))
    y = 2.0 * (t - 2014) + 30 * np.sin(2 * np.pi * t) + e
    r = st.rate(np.asarray(months.astype(str))[keep], y[keep])
    assert r["ci95"][0] < 2.0 < r["ci95"][1]
    assert 0.5 < r["phi"] < 0.95


def test_hinge_finds_a_break_in_a_flat_then_rising_series():
    months = pd.period_range("2002-01", "2025-12", freq="M").astype(str)
    t = st.tdec(months)
    y = np.where(t < 2018, 0.0, 30 * (t - 2018)) + np.random.default_rng(0).normal(0, 3, len(t))
    h = st.hinge(np.asarray(months), y)
    assert 2017 <= int(h["break"][:4]) <= 2019
    assert h["rate_before"] < 3 and 25 < h["rate_after"] < 35


# outputs --------------------------------------------------------------------------------------------------------

def test_grace_months_are_calendar_months_with_the_mission_gap():
    g = pd.read_csv(PROC / "grace_tws_monthly.csv")
    p = g[(g.domain == study.MAIN) & (g.solution == "costg")]
    assert p.month.is_unique
    for m in ["2017-08", "2017-12", "2018-01", "2018-05"]:
        assert m not in set(p.month)
    assert set(g.solution) == {"costg", "gfz"}


def test_every_input_has_both_areas_and_one_value_per_month():
    for name in ("gldas_noah_monthly.csv", "terraclimate_soil_monthly.csv"):
        d = pd.read_csv(PROC / name)
        assert set(d.domain) == set(study.AREAS)
        assert not d.duplicated(["month", "domain"]).any()


def test_results_have_the_g3p_block_and_consistent_intervals():
    r = json.loads((DOCS / "data" / "results.json").read_text())
    assert "g3p" in r and study.MAIN in r["g3p"]
    for series in r["main"].values():
        for part in ("full",):
            if isinstance(series, dict) and part in series:
                lo, hi = series[part]["ci95"]
                assert lo <= series[part]["rate_mm_yr"] <= hi


def test_paper_and_page_have_no_unfilled_placeholders_and_figures_exist():
    for p in (ROOT / "paper" / "paper.md", DOCS / "index.html"):
        assert "{{" not in p.read_text(encoding="utf-8")
    html = (DOCS / "index.html").read_text(encoding="utf-8")
    for s in re.findall(r'src="(assets/[^"]+)"', html):
        assert (DOCS / s).exists(), s


def test_build_paper_stops_without_the_g3p_block():
    import build_paper
    r = json.loads((DOCS / "data" / "results.json").read_text())
    c = json.loads((DOCS / "data" / "grace_cells.json").read_text())
    r.pop("g3p")
    with pytest.raises(SystemExit):
        build_paper.build(r, c)


def test_the_withdrawn_series_is_archived_not_used():
    assert (ROOT / "archive" / "withdrawn-v1" / "lake_chad_gravimetry_timeseries_2002_2025.csv").exists()
    for p in (ROOT / "scripts").glob("*.py"):
        assert "lake_chad_gravimetry_timeseries" not in p.read_text()
