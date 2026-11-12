"""Build paper/paper.md from paper/template.md. Every number comes from docs/data/results.json or
docs/data/grace_cells.json, which the scripts in scripts/ write. Stops if a sentence in the template would be false.

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

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data"
R = json.loads((DATA / "results.json").read_text())
C = json.loads((DATA / "grace_cells.json").read_text())


def f1(x):
    return f"{x:.1f}".replace("-", "−")


def sgn(x):
    return ("+" if x > 0 else "") + f1(x)


def ci(t):
    lo, hi = t["ci95_block_bootstrap"]
    return f"{sgn(lo)} to {sgn(hi)}"


def need(cond, msg):
    if not cond:
        raise SystemExit("template statement no longer true: " + msg)


def main():
    P = R["areas"]["primary"]
    S = R["areas"]["sensitivity"]
    tws, res, rtc, soil = (P["series"][k]["trends"] for k in ("tws", "residual_gldas", "residual_terraclimate", "soil_gldas"))
    full, g1, g2, y21 = "2002-2026", "2002-2017 (GRACE)", "2018-2026 (GRACE-FO)", "2002-2021"
    for t in (tws[full], res[full]):
        need(t["ci95_block_bootstrap"][0] > 0, "the full-record trend is positive with an interval above zero")
    need(tws[g2]["trend_mm_yr"] > tws[g1]["trend_mm_yr"], "the trend is faster after 2018")
    ann = [a for a in P["series"]["tws"]["annual"] if a["months"] >= 9]
    early = [a["mean_mm"] for a in ann if a["year"] <= 2016]
    late = max((a for a in ann if a["year"] >= 2019), key=lambda a: a["mean_mm"])
    # cells overlapping the catchment
    lat = np.array(sorted({c["lat"] for c in C["cells"]}, reverse=True))
    lon = np.array(sorted({c["lon"] for c in C["cells"]}))
    w = grids.weights(lat, lon, grids.domains()["primary"])
    val = {(c["lat"], c["lon"]): c["trend"] for c in C["cells"]}
    over = [val[(a, o)] for i, a in enumerate(lat) for j, o in enumerate(lon) if w[i, j] > 0 and val.get((a, o)) is not None]
    sens = [("GLDAS soil water, Lake Chad sink catchment (main)", res[full]),
            ("TerraClimate soil water, to " + R["terraclimate_last"], rtc[y21]),
            ("GLDAS, same years as TerraClimate", res[y21]),
            ("GLDAS, leakage term removed", P["series"]["residual_gldas_leakage_removed"]["trends"][full]),
            ("GLDAS, level-3 unit", S["series"]["residual_gldas"]["trends"][full]),
            ("GLDAS, GRACE years only (2002–2017)", res[g1]),
            ("GLDAS, GRACE-FO years only (2018–2026)", res[g2])]
    table = "\n".join(f"| {lab} | {sgn(t['trend_mm_yr'])} | {ci(t)} |" for lab, t in sens)
    vals = {
        "date": date.today().strftime("%B %Y"),
        "n_epochs": str(R["grace"]["epochs"]), "grace_first": R["grace"]["first"], "grace_last": R["grace"]["last"],
        "missing": str(R["grace"]["missing_months"]), "baseline": R["baseline"].replace("-", "–"),
        "area_p": f"{P['area_km2']:,}", "area_s": f"{S['area_km2']:,}",
        "gldas_last": R["gldas_last"], "tc_last": R["terraclimate_last"],
        "tws_full": sgn(tws[full]["trend_mm_yr"]), "tws_full_ci": ci(tws[full]),
        "tws_g1": sgn(tws[g1]["trend_mm_yr"]), "tws_g1_ci": ci(tws[g1]),
        "tws_g2": sgn(tws[g2]["trend_mm_yr"]), "tws_g2_ci": ci(tws[g2]),
        "tws_ar1": f"{tws[full]['lag1_autocorr']:.2f}", "tws_amp": f"{tws[full]['annual_amplitude_mm']:.0f}",
        "grace_err": f"{tws[full]['grace_error_sd_mm_yr']:.2f}",
        "res_full": sgn(res[full]["trend_mm_yr"]), "res_full_ci": ci(res[full]),
        "res_km3": f"{res[full]['trend_mm_yr'] * P['km3_per_mm']:.1f}",
        "res_tc": sgn(rtc[y21]["trend_mm_yr"]), "res_tc_ci": ci(rtc[y21]), "res_gl_2021": sgn(res[y21]["trend_mm_yr"]),
        "soil_trend": sgn(soil[full]["trend_mm_yr"]),
        "early_lo": f1(min(early)), "early_hi": sgn(max(early)),
        "late_max": f"{late['mean_mm']:.0f}", "late_max_year": str(late["year"]),
        "cell_lo": sgn(min(over)), "cell_hi": sgn(max(over)),
        "cells_equiv": f"{P['area_km2'] / 12000:.0f}",
        "sens_table": table,
    }
    need(min(over) > 0, "every cell overlapping the catchment has a rising trend")
    G = R.get("g3p", {}).get("primary")
    if G:
        sw, gw = G["g3p_surface_water"], G["g3p_groundwater"]
        vals.update({"g3p_n": str(G["months_in_common"]), "g3p_first": G["first"], "g3p_last": G["last"]})
        swr = G["g3p_surface_water_range_mm"]
        need(max(abs(swr[0]), abs(swr[1])) < 10, "G3P surface water is near zero over the catchment")
        vals["g3p_text"] = (f"Over the {G['months_in_common']} months in common ({G['first']} to {G['last']}), our total storage and G3P's "
                            f"correlate at {G['corr_tws_vs_g3p_tws']:.3f}, with trends of {sgn(G['our_tws']['trend_mm_yr'])} and "
                            f"{sgn(G['g3p_tws']['trend_mm_yr'])} mm per year, as expected from the same gravity data. Our residual and G3P's "
                            f"groundwater correlate at {G['corr_residual_vs_g3p_gw_plus_sw']:.2f}; their trends over the same months are "
                            f"{sgn(G['our_residual_gldas']['trend_mm_yr'])} and {sgn(gw['trend_mm_yr'])} mm per year. G3P's surface-water layer "
                            f"stays between {f1(swr[0])} and {f1(swr[1])} mm over the catchment, so it does not represent Lake Chad and its wetlands, "
                            f"and G3P effectively counts the whole residual as groundwater. The comparison therefore cannot split lake water from groundwater.")
        vals["g3p_abstract"] = (f"G3P, a groundwater product built from the same gravity data, agrees on total storage but its surface-water layer "
                                f"is close to zero here, so it does not resolve the lake either.")
        vals["g3p_disc"] = ("G3P counts the whole change as groundwater, but only because its surface-water layer does not include the lake, "
                            "so it cannot settle the question.")
    else:
        for k in ("g3p_n", "g3p_first", "g3p_last"):
            vals[k] = "n/a"
        vals["g3p_text"] = "The G3P comparison has not been run."
        vals["g3p_abstract"] = vals["g3p_disc"] = ""
    t = (ROOT / "paper" / "template.md").read_text(encoding="utf-8")
    out = re.sub(r"\{\{(\w+)\}\}", lambda m: vals[m.group(1)], t)
    if "{{" in out:
        raise SystemExit("unfilled placeholder")
    (ROOT / "paper" / "paper.md").write_text(out, encoding="utf-8")
    print("wrote paper/paper.md")


if __name__ == "__main__":
    main()
