"""Figures and page data.

  docs/assets/figures/fig1_area.png      study areas over the GRACE storage trend per 1-degree cell, 2002-2026
  docs/assets/figures/fig2_monthly.png   monthly storage, soil water and residual, with the GRACE error band
  docs/assets/figures/fig3_annual.png    annual means
  docs/data/storage_monthly.json         monthly series for the interactive chart
  docs/data/grace_cells.json             trend per 1-degree cell for the interactive map

    python scripts/s06_figures.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from shapely.geometry import shape

import study

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
FIG = ROOT / "docs" / "assets" / "figures"
DATA = ROOT / "docs" / "data"
GRACE = ROOT / "cache" / "grace" / "GRAVIS-3_COSTG_0200_TWS_GRID_GFZ_0001.nc"
INK, BLUE, ORANGE, GREEN, GREY = "#1f2328", "#1f56b0", "#d9500b", "#2e7d32", "#8a8f98"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150})


def cell_trends():
    ds = xr.open_dataset(GRACE)
    doms = json.loads((P / "domains.geojson").read_text())
    b = np.array([shape(f["geometry"]).bounds for f in doms["features"]])
    w, s, e, n = b[:, 0].min() - 3, b[:, 1].min() - 3, b[:, 2].max() + 3, b[:, 3].max() + 3
    sub = ds["tws"].sel(lat=slice(n, s), lon=slice(w, e)) * 10.0
    t = pd.DatetimeIndex(sub.time.values)
    td = (t.year + (t.dayofyear - 0.5) / 365.25).to_numpy()
    X = np.column_stack([np.ones_like(td), td - 2014, np.sin(2 * np.pi * td), np.cos(2 * np.pi * td),
                         np.sin(4 * np.pi * td), np.cos(4 * np.pi * td)])
    Y = sub.values.reshape(len(td), -1)
    coef = np.linalg.lstsq(X, np.nan_to_num(Y), rcond=None)[0][1]
    coef[np.isnan(Y).any(axis=0)] = np.nan  # ocean and missing cells stay blank
    coef = coef.reshape(sub.shape[1:])
    return sub.lat.values, sub.lon.values, coef, doms


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    lat, lon, tr, doms = cell_trends()
    # Figure 1
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    lim = float(np.nanmax(np.abs(tr)))
    m = ax.pcolormesh(lon, lat, np.ma.masked_invalid(tr), cmap="RdBu", vmin=-lim, vmax=lim, shading="nearest")
    order = sorted(doms["features"], key=lambda f: f["properties"]["id"] != study.MAIN)
    for f, ls, col in zip(order, ("-", "--"), (INK, GREY)):
        g = shape(f["geometry"])
        for poly in getattr(g, "geoms", [g]):
            x, y = poly.exterior.xy
            ax.plot(x, y, ls, color=col, lw=1.4)
    ax.plot(14.0, 13.2, "o", ms=4, color=INK)
    ax.annotate("Lake Chad (approximate)", (14.0, 13.2), xytext=(6, 4), textcoords="offset points", fontsize=9)
    ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)"); ax.set_aspect("equal")
    cb = fig.colorbar(m, ax=ax, shrink=0.8); cb.set_label("Storage trend, 2002–2026 (mm per year)")
    fig.tight_layout(); fig.savefig(FIG / "fig1_area.png"); plt.close(fig)
    cells = [{"lat": float(a), "lon": float(o), "trend": None if not np.isfinite(tr[i, j]) else round(float(tr[i, j]), 1)}
             for i, a in enumerate(lat) for j, o in enumerate(lon)]
    import grids
    wmain = grids.weights(lat, lon, shape(next(f["geometry"] for f in doms["features"] if f["properties"]["id"] == study.MAIN)))
    main_cells = [[float(a), float(o)] for i, a in enumerate(lat) for j, o in enumerate(lon) if wmain[i, j] > 0 and np.isfinite(tr[i, j])]
    (DATA / "grace_cells.json").write_text(json.dumps({"cell_deg": 1.0, "cells": cells, "domains": doms, "main": study.MAIN,
                                                       "lake": [14.0, 13.2], "main_cells": main_cells}))
    # Figure 2 and chart data
    s = pd.read_csv(P / "storage_monthly.csv")
    p = s[s.domain == study.MAIN].copy()
    p["t"] = pd.PeriodIndex(p.month, freq="M").to_timestamp() + pd.Timedelta(days=14)
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    full = pd.DataFrame({"t": pd.period_range(p.month.iloc[0], p.month.iloc[-1], freq="M").to_timestamp() + pd.Timedelta(days=14)})
    q = full.merge(p, on="t", how="left")
    ax.fill_between(q.t, q.tws_mm_anom - q.std_mm, q.tws_mm_anom + q.std_mm, color=BLUE, alpha=0.18, lw=0)
    ax.plot(q.t, q.tws_mm_anom, color=BLUE, lw=1.3, label="GRACE total storage")
    ax.plot(q.t, q.sm_gldas_anom, color=GREEN, lw=1.0, label="Soil water (GLDAS)")
    ax.plot(q.t, q.res_gldas, color=ORANGE, lw=1.3, label="Storage minus soil water (GLDAS)")
    ax.plot(q.t, q.res_tc, color=ORANGE, lw=0.9, ls="--", label="Storage minus soil water (TerraClimate)")
    ax.axvspan(pd.Timestamp("2017-07-01"), pd.Timestamp("2018-06-01"), color=GREY, alpha=0.15, lw=0)
    ax.axhline(0, color=GREY, lw=0.6)
    ax.set_ylabel("Anomaly from 2004–2009 (mm)")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    fig.tight_layout(); fig.savefig(FIG / "fig2_monthly.png"); plt.close(fig)
    keep = ["month", "tws_mm_anom", "std_mm", "sm_gldas_anom", "sm_tc_anom", "res_gldas", "res_tc"]
    (DATA / "storage_monthly.json").write_text(json.dumps({
        "note": "Lake Chad basin unit (HydroBASINS level 3). Anomalies in mm from the 2004-2009 mean. Missing months are absent.",
        "rows": [{k: (None if pd.isna(v) else (round(float(v), 1) if k != "month" else v)) for k, v in r.items()}
                 for r in p[keep].to_dict("records")]}))
    # Figure 3
    res = json.loads((DATA / "results.json").read_text())["main"]
    yrs = [a["year"] for a in res["tws"]["annual"]]
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    x = np.arange(len(yrs))
    for off, key, col, lab in ((-0.2, "tws", BLUE, "GRACE total storage"), (0.2, "residual_gldas", ORANGE, "Storage minus soil water (GLDAS)")):
        v = [a["mean_mm"] if a["months"] >= 9 else np.nan for a in res[key]["annual"]]
        ax.bar(x + off, v, width=0.4, color=col, label=lab)
    ax.set_xticks(x[::2]); ax.set_xticklabels(yrs[::2], rotation=0)
    ax.axhline(0, color=GREY, lw=0.6); ax.set_ylabel("Annual mean anomaly (mm)")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    fig.tight_layout(); fig.savefig(FIG / "fig3_annual.png"); plt.close(fig)
    print("figures written")


if __name__ == "__main__":
    main()
