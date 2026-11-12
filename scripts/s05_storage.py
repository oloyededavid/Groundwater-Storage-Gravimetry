"""Separate storage and fit the trend, with uncertainty.

Residual storage = GRACE total water storage minus land-model soil water (GLDAS Noah, TerraClimate). It contains
groundwater AND surface water (Lake Chad, wetlands, rivers): no open lake-storage record was available to remove.

All series are anomalies from their own mean over the GRACE months of 2004-2009.
Trend model: storage = a + b*t + annual and semi-annual harmonics, fitted by least squares to the months that exist.
Uncertainty of b:
  - AR(1) adjusted standard error (residuals are autocorrelated, so the plain error is too small),
  - moving-block bootstrap of the residuals (24-month blocks, 2,000 resamples),
  - GRACE error: 1,000 runs adding each month's stated standard deviation as noise,
  - choices: soil model (GLDAS, TerraClimate), area (level 4, level 3), the product's leakage term, period.

Writes data/processed/storage_monthly.csv and docs/data/results.json.

    python scripts/s05_storage.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
OUT_CSV = P / "storage_monthly.csv"
OUT_JSON = ROOT / "docs" / "data" / "results.json"
BASE = (2004, 2009)
BLOCK = 24
RNG = np.random.default_rng(20261112)


def tdec(month):
    p = pd.PeriodIndex(month, freq="M")
    return (p.year + (p.month - 0.5) / 12).to_numpy()


def design(t):
    w = 2 * np.pi * t
    return np.column_stack([np.ones_like(t), t - 2014.0, np.sin(w), np.cos(w), np.sin(2 * w), np.cos(2 * w)])


def fit(t, y):
    X = design(t)
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    return b, y - X @ b


def trend(t, y, std=None):
    """Trend in mm/yr with three uncertainty estimates. t in decimal years, y in mm."""
    ok = np.isfinite(y)
    t, y = t[ok], y[ok]
    std = None if std is None else std[ok]
    X = design(t)
    b, res = fit(t, y)
    n, k = len(y), X.shape[1]
    s2 = res @ res / (n - k)
    se = float(np.sqrt(s2 * np.linalg.inv(X.T @ X)[1, 1]))
    phi = float(np.corrcoef(res[:-1], res[1:])[0, 1])
    infl = np.sqrt((1 + phi) / (1 - phi)) if phi > 0 else 1.0
    n_eff = n * (1 - phi) / (1 + phi) if phi > 0 else n
    se_ar = float(se * infl)
    tq = stats.t.ppf(0.975, max(n_eff - k, 2))
    # moving-block bootstrap of residuals
    nb = int(np.ceil(n / BLOCK))
    boots = []
    fitted = X @ b
    for _ in range(2000):
        starts = RNG.integers(0, n - BLOCK + 1, nb)
        r = np.concatenate([res[s:s + BLOCK] for s in starts])[:n]
        boots.append(np.linalg.lstsq(X, fitted + r, rcond=None)[0][1])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    out = {"trend_mm_yr": round(float(b[1]), 2), "se_plain": round(se, 2), "lag1_autocorr": round(phi, 3),
           "n_months": int(n), "n_eff": round(float(n_eff), 1),
           "ci95_ar1": [round(float(b[1] - tq * se_ar), 2), round(float(b[1] + tq * se_ar), 2)],
           "ci95_block_bootstrap": [round(float(lo), 2), round(float(hi), 2)],
           "annual_amplitude_mm": round(float(np.hypot(b[2], b[3])), 1),
           "first": None, "last": None}
    if std is not None:
        mc = [np.linalg.lstsq(X, y + RNG.normal(0, std), rcond=None)[0][1] for _ in range(1000)]
        out["grace_error_sd_mm_yr"] = round(float(np.std(mc)), 3)
    return out


def anomaly(df, col, months_ref):
    ref = df.loc[df["month"].isin(months_ref), col].mean()
    return df[col] - ref


def main():
    g = pd.read_csv(P / "grace_tws_monthly.csv")
    gl = pd.read_csv(P / "gldas_noah_monthly.csv")
    tc = pd.read_csv(P / "terraclimate_soil_monthly.csv")
    dom_json = json.loads((P / "domains.geojson").read_text())
    area = {f["properties"]["id"]: f["properties"]["area_km2"] for f in dom_json["features"]}
    rows, res = [], {"areas": {}, "notes": {}}
    for dom in ("primary", "sensitivity"):
        d = g[g.domain == dom][["month", "epoch", "tws_mm", "std_mm", "leakage_mm"]].copy()
        d = d.merge(gl[gl.domain == dom][["month", "storage_mm"]].rename(columns={"storage_mm": "sm_gldas"}), on="month", how="left")
        d = d.merge(tc[tc.domain == dom][["month", "soil_mm"]].rename(columns={"soil_mm": "sm_tc"}), on="month", how="left")
        yrs = pd.PeriodIndex(d.month, freq="M").year
        ref = d.month[(yrs >= BASE[0]) & (yrs <= BASE[1])]
        for c in ("tws_mm", "sm_gldas", "sm_tc"):
            d[c + "_anom"] = anomaly(d, c, ref)
        d["tws_noleak_anom"] = anomaly(d.assign(x=d.tws_mm - d.leakage_mm), "x", ref)
        d["res_gldas"] = d.tws_mm_anom - d.sm_gldas_anom
        d["res_tc"] = d.tws_mm_anom - d.sm_tc_anom
        d["res_gldas_noleak"] = d.tws_noleak_anom - d.sm_gldas_anom
        d["domain"] = dom
        rows.append(d)
        t = tdec(d.month)
        r = {"area_km2": area[dom], "km3_per_mm": round(area[dom] * 1e-6, 4), "series": {}}
        for name, col in (("tws", "tws_mm_anom"), ("soil_gldas", "sm_gldas_anom"), ("soil_terraclimate", "sm_tc_anom"),
                          ("residual_gldas", "res_gldas"), ("residual_terraclimate", "res_tc"),
                          ("residual_gldas_leakage_removed", "res_gldas_noleak")):
            y = d[col].to_numpy(float)
            per = {}
            for label, (a, z) in {"2002-2026": (2002, 2026), "2002-2017 (GRACE)": (2002, 2017),
                                  "2018-2026 (GRACE-FO)": (2018, 2026), "2002-2021": (2002, 2021)}.items():
                m = (t >= a) & (t < z + 1)
                if np.isfinite(y[m]).sum() < 36:
                    continue
                tr = trend(t[m], y[m], d.std_mm.to_numpy(float)[m] if col.startswith(("tws", "res")) else None)
                mm = d.month[m][np.isfinite(y[m])]
                tr["first"], tr["last"] = mm.iloc[0], mm.iloc[-1]
                per[label] = tr
            ann = d.assign(y=y, year=yrs).groupby("year").agg(mean=("y", "mean"), n=("y", "count")).reset_index()
            r["series"][name] = {"trends": per,
                                 "annual": [{"year": int(a.year), "mean_mm": None if pd.isna(a[2]) else round(float(a[2]), 1),
                                             "months": int(a.n)} for a in ann.itertuples()]}
        res["areas"][dom] = r
    allm = pd.concat(rows)
    keep = ["month", "epoch", "domain", "tws_mm_anom", "std_mm", "sm_gldas_anom", "sm_tc_anom", "res_gldas", "res_tc"]
    allm[keep].round(3).to_csv(OUT_CSV, index=False)
    p = allm[allm.domain == "primary"]
    res["grace"] = {"epochs": int(p.tws_mm.notna().sum()), "first": p.month.iloc[0], "last": p.month.iloc[-1],
                    "missing_months": int(len(pd.period_range(p.month.iloc[0], p.month.iloc[-1], freq="M")) - p.month.nunique()),
                    "std_mm_median": round(float(p.std_mm.median()), 1)}
    res["gldas_last"] = gl.month.max()
    res["terraclimate_last"] = tc.month.max()
    res["baseline"] = f"{BASE[0]}-{BASE[1]}"
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(res, indent=1))
    pr = res["areas"]["primary"]["series"]
    for k in ("tws", "residual_gldas", "residual_terraclimate"):
        print(k, {lab: (v["trend_mm_yr"], v["ci95_block_bootstrap"]) for lab, v in pr[k]["trends"].items()})


if __name__ == "__main__":
    main()
