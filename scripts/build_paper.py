"""Build paper/paper.md from paper/template.md. Every number comes from docs/data/results.json or
docs/data/grace_cells.json, which the scripts in scripts/ write. Stops if a statement in the template would be false
or if a step has not been run.

    python scripts/build_paper.py && pandoc paper/paper.md -o paper/paper.docx --resource-path=. && python scripts/build_page.py
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grids  # noqa: E402
import study  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data"
FO = "2018-2026 (GRACE-FO)"


def num(x, plus=True):
    s = f"{x:.1f}"
    if s in ("-0.0", "0.0"):
        s = "0.0"
    elif plus and x > 0:
        s = "+" + s
    return s.replace("-", "−")


def ci(c):
    return f"{num(c[0])} to {num(c[1])}"


def month_name(ym):
    y, m = ym.split("-")
    return ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
            "November", "December"][int(m) - 1] + " " + y


def frac_to_month(x):
    y = int(np.floor(x + 1e-9))
    m = int(round((x - y) * 12)) + 1
    return month_name(f"{y}-{min(m, 12):02d}")


def need(cond, msg):
    if not cond:
        raise SystemExit("template statement no longer true: " + msg)


def build(R, C):
    M = R["main"]
    tws, res = M["tws"], M["residual_gldas"]
    for key in ("g3p",):
        if key not in R:
            raise SystemExit(f"results.json has no {key} block: run scripts/s07_g3p.py after s05_storage.py")
    h = tws["hinge"]
    need(h["delta_aic_vs_single_line"] < -10, "the two-segment fit is much better than a straight line")
    need(h["ci95_before"][0] < 5 and h["rate_after"] > 3 * max(h["rate_before"], 1), "flat then steep")
    need(tws["periods"][FO]["ci95"][0] > 0 and res["periods"][FO]["ci95"][0] > 0, "the GRACE-FO rise is above zero")
    st = tws["mission_step"]
    need(st["ci95"][0] < 0 < st["ci95"][1], "the step between the missions is not distinguishable from zero")
    need(st["step_mm"] < 0, "the step points the wrong way to explain the rise")
    soil = M["soil_gldas"]["full"]
    need(soil["ci95"][0] < 0 < soil["ci95"][1], "GLDAS soil water has no clear trend")
    need(M["soil_amplitude_mm"]["terraclimate"] < 0.7 * M["soil_amplitude_mm"]["gldas"], "TerraClimate's cycle is much smaller")
    main_rows = [s for s in R["spread"] if s["area"] == study.MAIN and "gracefo" in s]
    fo_rates = [s["gracefo"]["rate_mm_yr"] for s in main_rows]
    alt_rows = [s for s in R["spread"] if s["area"] == study.ALT and "gracefo" in s]
    need(min(a["gracefo"]["rate_mm_yr"] for a in alt_rows) > min(fo_rates), "the western unit gives higher rates")
    noleak = [s["gracefo"]["rate_mm_yr"] for s in main_rows if "leakage" in s["soil"]]
    leak = [s["gracefo"]["rate_mm_yr"] for s in main_rows if "leakage" not in s["soil"]]
    need(min(noleak) > max(leak), "the leakage correction raises the GRACE-FO rate")
    tc = next(s for s in R["spread"] if s["area"] == study.MAIN and s["solution"] == R["main_solution"] and s["soil"].startswith("TerraClimate"))
    # annual means
    ann = [a for a in tws["annual"] if a["months"] >= 9]
    out_years = [str(a["year"]) for a in tws["annual"] if a["months"] < 9]
    early = [a["mean_mm"] for a in tws["annual"] if a["months"] == 12 and a["year"] <= 2016]
    late = max((a for a in ann if a["year"] >= 2019), key=lambda a: a["mean_mm"])
    # cells overlapping the main area
    lat = np.array(sorted({c["lat"] for c in C["cells"]}, reverse=True))
    lon = np.array(sorted({c["lon"] for c in C["cells"]}))
    w = grids.weights(lat, lon, grids.domains()[study.MAIN])
    val = {(c["lat"], c["lon"]): c["trend"] for c in C["cells"]}
    over = [((a, o), val[(a, o)]) for i, a in enumerate(lat) for j, o in enumerate(lon) if w[i, j] > 0 and val.get((a, o)) is not None]
    (mx_lat, mx_lon), mx = max(over, key=lambda x: x[1])
    lake = val[(13.5, 14.5)] if (13.5, 14.5) in val else val[min(val, key=lambda k: abs(k[0] - 13.2) + abs(k[1] - 14.0))]
    need(mx_lon < 14.0, "the largest trend is west of the lake")
    need(lake < mx, "the lake cell rises less than the largest")
    # table
    lab = {"costg": "COST-G RL02", "gfz": "GFZ RL06"}
    area_lab = {study.MAIN: "Basin unit (level 3)", study.ALT: "Western unit (level 4)"}
    rows = []
    for s in R["spread"]:
        fo = f"{num(s['gracefo']['rate_mm_yr'])} ({ci(s['gracefo']['ci95'])})" if "gracefo" in s else "not covered"
        rows.append(f"| {lab[s['solution']]} | {area_lab[s['area']]} | {s['soil']} | {num(s['full']['rate_mm_yr'])} ({ci(s['full']['ci95'])}) | {fo} |")
    G = R["g3p"][study.MAIN]
    swr = G["g3p_surface_water_range_mm"]
    need(max(abs(swr[0]), abs(swr[1])) < 10, "G3P surface water is near zero over the basin")
    g3p_text = (f"Over the {G['months_in_common']} months in common ({G['first']} to {G['last']}), our total storage and G3P's correlate at "
                f"{G['corr_tws_vs_g3p_tws']:.3f}, with rates of {num(G['our_tws']['rate_mm_yr'])} and {num(G['g3p_tws']['rate_mm_yr'])} mm per year. "
                f"Our residual and G3P's groundwater layer correlate at {G['corr_residual_vs_g3p_groundwater']:.2f}, with rates of "
                f"{num(G['our_residual_gldas']['rate_mm_yr'])} and {num(G['g3p_groundwater']['rate_mm_yr'])} mm per year; G3P's groundwater has a larger "
                f"seasonal cycle ({G['g3p_groundwater']['annual_amplitude_mm']:.0f} against {G['our_residual_gldas']['annual_amplitude_mm']:.0f} mm). "
                f"G3P's surface-water layer stays between {num(swr[0], False)} and {num(swr[1], False)} mm over the basin, so G3P counts nearly the whole "
                f"residual as groundwater; the comparison cannot split lake water from groundwater. It also ends before the steepest part of the rise.")
    km3 = R["areas"][study.MAIN]["km3_per_mm"]
    v = {
        "date": date.today().strftime("%B %Y"),
        "n_epochs": str(R["grace"]["epochs"]), "grace_first": R["grace"]["first"], "grace_last": R["grace"]["last"],
        "missing": str(R["grace"]["missing_months"]), "baseline": R["baseline"].replace("-", "–"),
        "area_main": f"{R['areas'][study.MAIN]['area_km2']:,}", "area_alt": f"{R['areas'][study.ALT]['area_km2']:,}",
        "gldas_last": R["gldas_last"], "tc_last": R["terraclimate_last"],
        "amp_tc": f"{M['soil_amplitude_mm']['terraclimate']:.0f}", "amp_gldas": f"{M['soil_amplitude_mm']['gldas']:.0f}",
        "grace_err": f"{tws['full']['grace_error_sd_lower_bound']:.2f}",
        "brk": month_name(h["break"]), "brk_range": f"{frac_to_month(h['break_range'][0])} to {frac_to_month(h['break_range'][1])}",
        "daic": f"{-h['delta_aic_vs_single_line']:.0f}",
        "h_before": num(h["rate_before"]), "h_before_ci": ci(h["ci95_before"]), "h_after": num(h["rate_after"]), "h_after_ci": ci(h["ci95_after"]),
        "p1": num(tws["periods"]["2002-2010"]["rate_mm_yr"]), "p1_ci": ci(tws["periods"]["2002-2010"]["ci95"]),
        "p2": num(tws["periods"]["2011-2017"]["rate_mm_yr"]), "p2_ci": ci(tws["periods"]["2011-2017"]["ci95"]),
        "p3": num(tws["periods"][FO]["rate_mm_yr"]), "p3_ci": ci(tws["periods"][FO]["ci95"]),
        "step": num(st["step_mm"]), "step_ci": ci(st["ci95"]),
        "early_lo": num(min(early)), "early_hi": num(max(early)), "late_max": f"{late['mean_mm']:.0f}", "late_max_year": str(late["year"]),
        "cell_lo": num(min(x[1] for x in over)), "cell_hi": num(mx), "cell_max_lat": f"{mx_lat:.1f}", "cell_max_lon": f"{mx_lon:.1f}",
        "cell_lake": num(lake),
        "soil_trend": num(soil["rate_mm_yr"]), "soil_ci": ci(soil["ci95"]),
        "res_p1": num(res["periods"]["2002-2010"]["rate_mm_yr"]), "res_p2": num(res["periods"]["2011-2017"]["rate_mm_yr"]),
        "res_fo": num(res["periods"][FO]["rate_mm_yr"]), "res_fo_ci": ci(res["periods"][FO]["ci95"]),
        "res_fo_km3": f"{res['periods'][FO]['rate_mm_yr'] * km3:.0f}", "res_brk": month_name(res["hinge"]["break"]),
        "res_full": num(res["full"]["rate_mm_yr"]), "res_full_ci": ci(res["full"]["ci95"]),
        "res_end_2021": num(res["end_dates"]["2021-12"]["rate_mm_yr"]), "res_end_2023": num(res["end_dates"]["2023-12"]["rate_mm_yr"]),
        "res_tc": num(tc["full"]["rate_mm_yr"]), "res_tc_gl": num(tc["same_years_gldas"]["rate_mm_yr"]),
        "spread_fo_lo": num(min(fo_rates)), "spread_fo_hi": num(max(fo_rates)),
        "years_out": ", ".join(out_years), "sens_table": "\n".join(rows),
        "g3p_n": str(G["months_in_common"]), "g3p_first": G["first"], "g3p_last": G["last"], "g3p_text": g3p_text,
    }
    t = (ROOT / "paper" / "template.md").read_text(encoding="utf-8")
    out = re.sub(r"\{\{(\w+)\}\}", lambda m: v[m.group(1)], t)
    if "{{" in out:
        raise SystemExit("unfilled placeholder")
    return out


def main():
    R = json.loads((DATA / "results.json").read_text())
    C = json.loads((DATA / "grace_cells.json").read_text())
    (ROOT / "paper" / "paper.md").write_text(build(R, C), encoding="utf-8")
    print("wrote paper/paper.md")


if __name__ == "__main__":
    main()
