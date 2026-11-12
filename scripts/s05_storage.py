"""Separate storage from soil water and describe how it changed, with uncertainty.

Residual storage = GRACE total water storage minus land-model soil water. It holds groundwater AND surface water
(Lake Chad, wetlands, floodplains): no open lake-storage record could be used.

Every series is an anomaly from its own mean over the GRACE months of 2004-2009 (study.BASELINE).

Rates come from generalised least squares with AR(1) errors that respect calendar gaps (correlation phi**|months
apart|), fitted with annual and semi-annual cycles. phi is estimated from consecutive-month pairs of the OLS
residuals. Because the record has separate phases, the study reports:
  - a rate for each period (study.PERIODS),
  - a continuous two-segment fit with the break month chosen by AIC, and the range of break months within 2 AIC units,
  - the full-record rate for several end dates (study.END_DATES),
  - the spread of rates across choices: GRACE solution, soil model, study area, leakage term.
The GRACE error term (each month's stated standard deviation drawn independently) is a lower bound: it leaves out
errors correlated between months and between missions.

Writes data/processed/storage_monthly.csv and docs/data/results.json (keeps an existing "g3p" block).

    python scripts/s05_storage.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import study

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
OUT_CSV = P / "storage_monthly.csv"
OUT_JSON = ROOT / "docs" / "data" / "results.json"
MAIN_SOLUTION = "costg"


def tdec(month):
    p = pd.PeriodIndex(month, freq="M")
    return (p.year + (p.month - 0.5) / 12).to_numpy()


def mindex(month):
    p = pd.PeriodIndex(month, freq="M")
    return (p.year * 12 + p.month).to_numpy()


def cycles(t):
    w = 2 * np.pi * t
    return np.column_stack([np.sin(w), np.cos(w), np.sin(2 * w), np.cos(2 * w)])


def gls(X, y, mi, phi=None):
    """GLS with AR(1) errors on an irregular monthly index mi. Returns beta, covariance, phi, residual sum of squares."""
    b_ols, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ b_ols
    if phi is None:
        cons = np.diff(mi) == 1
        phi = float(np.corrcoef(r[:-1][cons], r[1:][cons])[0, 1]) if cons.sum() > 5 else 0.0
        phi = min(max(phi, 0.0), 0.99)
    lag = np.abs(mi[:, None] - mi[None, :])
    S = phi ** lag
    L = np.linalg.cholesky(S)
    Xw, yw = np.linalg.solve(L, X), np.linalg.solve(L, y)
    b, *_ = np.linalg.lstsq(Xw, yw, rcond=None)
    rw = yw - Xw @ b
    n, k = X.shape
    s2 = rw @ rw / (n - k)
    cov = s2 * np.linalg.inv(Xw.T @ Xw)
    return b, cov, phi, float(((y - X @ b_ols) ** 2).sum())


def rate(month, y, std=None):
    """Linear rate (mm/yr) with cycles, GLS AR(1) interval, and the GRACE-error lower bound."""
    ok = np.isfinite(y)
    month, y = np.asarray(month)[ok], y[ok]
    t, mi = tdec(month), mindex(month)
    X = np.column_stack([np.ones_like(t), t - 2014.0, cycles(t)])
    b, cov, phi, _ = gls(X, y, mi)
    se = float(np.sqrt(cov[1, 1]))
    q = stats.t.ppf(0.975, len(y) - X.shape[1])
    out = {"rate_mm_yr": round(float(b[1]), 2), "ci95": [round(float(b[1] - q * se), 2), round(float(b[1] + q * se), 2)],
           "se": round(se, 2), "phi": round(phi, 3), "n_months": int(len(y)), "first": str(month[0]), "last": str(month[-1]),
           "annual_amplitude_mm": round(float(np.hypot(b[2], b[3])), 1)}
    if std is not None:
        rng = np.random.default_rng(1)
        Xo = X
        mc = [np.linalg.lstsq(Xo, y + rng.normal(0, std[ok]), rcond=None)[0][1] - np.linalg.lstsq(Xo, y, rcond=None)[0][1]
              for _ in range(500)]
        out["grace_error_sd_lower_bound"] = round(float(np.std(mc)), 3)
    return out


def hinge(month, y):
    """Continuous two-segment fit; break month by AIC (OLS), slopes and intervals by GLS at the chosen break."""
    ok = np.isfinite(y)
    month, y = np.asarray(month)[ok], y[ok]
    t, mi = tdec(month), mindex(month)
    n = len(y)
    X1 = np.column_stack([np.ones_like(t), t - 2014.0, cycles(t)])
    sse1 = float(((y - X1 @ np.linalg.lstsq(X1, y, rcond=None)[0]) ** 2).sum())
    aic1 = n * np.log(sse1 / n) + 2 * (X1.shape[1] + 1)
    scan = []
    for brk in np.arange(2008.0, 2023.0 + 1e-9, 1 / 12):
        X = np.column_stack([X1, np.clip(t - brk, 0, None)])
        sse = float(((y - X @ np.linalg.lstsq(X, y, rcond=None)[0]) ** 2).sum())
        scan.append((brk, n * np.log(sse / n) + 2 * (X.shape[1] + 2)))
    best = min(scan, key=lambda s: s[1])
    near = [s[0] for s in scan if s[1] <= best[1] + 2]
    X = np.column_stack([X1, np.clip(t - best[0], 0, None)])
    b, cov, phi, _ = gls(X, y, mi)
    q = stats.t.ppf(0.975, n - X.shape[1])
    before, after = b[1], b[1] + b[6]
    se_b, se_a = np.sqrt(cov[1, 1]), np.sqrt(cov[1, 1] + cov[6, 6] + 2 * cov[1, 6])
    y0 = int(np.floor(best[0])); m0 = int(round((best[0] - y0) * 12)) + 1
    return {"break": f"{y0}-{min(m0, 12):02d}", "break_range": [round(min(near), 2), round(max(near), 2)],
            "delta_aic_vs_single_line": round(float(best[1] - aic1), 1),
            "rate_before": round(float(before), 2), "ci95_before": [round(float(before - q * se_b), 2), round(float(before + q * se_b), 2)],
            "rate_after": round(float(after), 2), "ci95_after": [round(float(after - q * se_a), 2), round(float(after + q * se_a), 2)]}


def mission_step(month, y, gap_mid=2017.9, fo_start="2018-06"):
    """Separate straight lines for GRACE and GRACE-FO with shared cycles. The step is the GRACE-FO line minus the
    GRACE line at the middle of the gap. A step cannot be told apart from a change in trend with only the gap to go on."""
    ok = np.isfinite(y)
    month, y = np.asarray(month)[ok], y[ok]
    t, mi = tdec(month), mindex(month)
    fo = (month >= fo_start).astype(float)
    X = np.column_stack([1 - fo, (t - gap_mid) * (1 - fo), fo, (t - gap_mid) * fo, cycles(t)])
    b, cov, phi, _ = gls(X, y, mi)
    c = np.array([-1, 0, 1, 0, 0, 0, 0, 0])
    step, se = float(c @ b), float(np.sqrt(c @ cov @ c))
    q = stats.t.ppf(0.975, len(y) - X.shape[1])
    return {"step_mm": round(step, 1), "ci95": [round(step - q * se, 1), round(step + q * se, 1)],
            "rate_grace": round(float(b[1]), 2), "rate_gracefo": round(float(b[3]), 2)}


def window(df, first, last):
    return df[(df.month >= first) & (df.month <= last)]


def describe(df, col, with_err=False):
    """All descriptions of one series in df (columns month, col, std_mm)."""
    y = df[col].to_numpy(float)
    std = df.std_mm.to_numpy(float) if with_err else None
    out = {"full": rate(df.month, y, std), "periods": {}, "end_dates": {}}
    for name, (a, z) in study.PERIODS.items():
        w = window(df, a, z)
        if w[col].notna().sum() >= 24:
            out["periods"][name] = rate(w.month, w[col].to_numpy(float))
    for end in study.END_DATES:
        w = window(df, "0000-00", end)
        out["end_dates"][end] = rate(w.month, w[col].to_numpy(float))
    out["hinge"] = hinge(df.month, y)
    out["mission_step"] = mission_step(df.month.to_numpy(), y)
    yrs = pd.PeriodIndex(df.month, freq="M").year
    ann = df.assign(year=yrs).groupby("year")[col].agg(["mean", "count"]).reset_index()
    out["annual"] = [{"year": int(r.year), "mean_mm": None if pd.isna(r["mean"]) else round(float(r["mean"]), 1), "months": int(r["count"])}
                     for _, r in ann.iterrows()]
    return out


def main():
    g = pd.read_csv(P / "grace_tws_monthly.csv")
    gl = pd.read_csv(P / "gldas_noah_monthly.csv")
    tc = pd.read_csv(P / "terraclimate_soil_monthly.csv")
    dom = {f["properties"]["id"]: f["properties"] for f in json.loads((P / "domains.geojson").read_text())["features"]}
    frames = {}
    for sol in sorted(g.solution.unique()):
        for area in study.AREAS:
            d = g[(g.solution == sol) & (g.domain == area)][["month", "tws_mm", "std_mm", "leakage_mm"]].copy()
            d = d.merge(gl[gl.domain == area][["month", "storage_mm"]].rename(columns={"storage_mm": "sm_gldas"}), on="month", how="left")
            d = d.merge(tc[tc.domain == area][["month", "soil_mm"]].rename(columns={"soil_mm": "sm_tc"}), on="month", how="left")
            yrs = pd.PeriodIndex(d.month, freq="M").year
            base = (yrs >= study.BASELINE[0]) & (yrs <= study.BASELINE[1])
            for c in ("tws_mm", "sm_gldas", "sm_tc"):
                d[c + "_anom"] = d[c] - d.loc[base, c].mean()
            noleak = d.tws_mm - d.leakage_mm
            d["tws_noleak_anom"] = noleak - noleak[base].mean()
            d["res_gldas"] = d.tws_mm_anom - d.sm_gldas_anom
            d["res_tc"] = d.tws_mm_anom - d.sm_tc_anom
            d["res_gldas_noleak"] = d.tws_noleak_anom - d.sm_gldas_anom
            frames[(sol, area)] = d
    main_df = frames[(MAIN_SOLUTION, study.MAIN)]
    res = {"baseline": f"{study.BASELINE[0]}-{study.BASELINE[1]}", "main_area": study.MAIN, "alt_area": study.ALT,
           "main_solution": MAIN_SOLUTION, "areas": {k: {"name": v["name"], "area_km2": v["area_km2"], "hybas_id": v["hybas_id"],
                                                          "km3_per_mm": round(v["area_km2"] * 1e-6, 4)} for k, v in dom.items()}}
    res["main"] = {"tws": describe(main_df, "tws_mm_anom", with_err=True), "residual_gldas": describe(main_df, "res_gldas"),
                   "soil_gldas": {"full": rate(main_df.month, main_df.sm_gldas_anom.to_numpy(float))},
                   "soil_amplitude_mm": {"gldas": rate(main_df.month, main_df.sm_gldas_anom.to_numpy(float))["annual_amplitude_mm"],
                                         "terraclimate": rate(main_df.month[main_df.sm_tc.notna()], main_df.sm_tc_anom.dropna().to_numpy(float))["annual_amplitude_mm"]}}
    tc_end = tc.month.max()
    spread = []
    for sol in sorted(g.solution.unique()):
        for area in study.AREAS:
            d = frames[(sol, area)]
            for soil, col in (("GLDAS", "res_gldas"), ("GLDAS, leakage removed", "res_gldas_noleak")):
                fo = window(d, *study.PERIODS["2018-2026 (GRACE-FO)"])
                spread.append({"solution": sol, "area": area, "soil": soil, "full": rate(d.month, d[col].to_numpy(float)),
                               "gracefo": rate(fo.month, fo[col].to_numpy(float))})
            w = window(d, "0000-00", tc_end)
            spread.append({"solution": sol, "area": area, "soil": f"TerraClimate (to {tc_end})", "full": rate(w.month, w.res_tc.to_numpy(float)),
                           "same_years_gldas": rate(w.month, w.res_gldas.to_numpy(float))})
    res["spread"] = spread
    fulls = [s["full"]["rate_mm_yr"] for s in spread if not s["soil"].startswith("TerraClimate")]
    fos = [s["gracefo"]["rate_mm_yr"] for s in spread if "gracefo" in s]
    res["spread_range"] = {"full": [min(fulls), max(fulls)], "gracefo": [min(fos), max(fos)]}
    gm = g[(g.solution == MAIN_SOLUTION) & (g.domain == study.MAIN)]
    res["grace"] = {"epochs": int(len(gm)), "first": gm.month.iloc[0], "last": gm.month.iloc[-1],
                    "missing_months": int(len(pd.period_range(gm.month.iloc[0], gm.month.iloc[-1], freq="M")) - gm.month.nunique()),
                    "solutions": sorted(g.solution.unique().tolist())}
    res["gldas_last"], res["terraclimate_last"] = gl.month.max(), tc_end
    if OUT_JSON.exists():
        old = json.loads(OUT_JSON.read_text())
        if "g3p" in old:
            res["g3p"] = old["g3p"]
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(res, indent=1))
    rows = []
    for (sol, area), d in frames.items():
        if sol == MAIN_SOLUTION:
            rows.append(d.assign(domain=area))
    keep = ["month", "domain", "tws_mm_anom", "std_mm", "sm_gldas_anom", "sm_tc_anom", "res_gldas", "res_tc", "res_gldas_noleak"]
    pd.concat(rows)[keep].round(3).to_csv(OUT_CSV, index=False)
    m = res["main"]
    print("tws full", m["tws"]["full"]["rate_mm_yr"], m["tws"]["full"]["ci95"], "| periods",
          {k: (v["rate_mm_yr"], v["ci95"]) for k, v in m["tws"]["periods"].items()})
    print("hinge", m["tws"]["hinge"])
    print("residual full", m["residual_gldas"]["full"]["rate_mm_yr"], m["residual_gldas"]["full"]["ci95"],
          "| end dates", {k: v["rate_mm_yr"] for k, v in m["residual_gldas"]["end_dates"].items()})
    print("spread", res["spread_range"])


if __name__ == "__main__":
    main()
