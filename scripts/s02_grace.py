"""GRACE/GRACE-FO terrestrial water storage over the study areas, from the COST-G GravIS RL02 Level-3 grid
(Boergens, Dobslaw and Dill, 2025, doi:10.5880/COST-G.GRAVIS_02_L3_TWS, CC BY 4.0; 1 degree, cm, anomalies
relative to the 2002-04 to 2020-03 mean).

Each epoch is matched to the calendar month of its mid-date. Two epochs share a month (2011-10, 2015-04); the later
one is moved to the following month, which has no epoch of its own. Missing months stay missing.

Uncertainty: the product gives a standard deviation per cell. Neighbouring cells are strongly correlated, so the area
value uses the weighted mean of the cell standard deviations (full correlation, the larger and safer choice); the
uncorrelated value is kept for reference.

Writes data/processed/grace_tws_monthly.csv.

    python scripts/s02_grace.py
"""
import csv
import os
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

import grids

ROOT = Path(__file__).resolve().parents[1]
NAME = "GRAVIS-3_COSTG_0200_TWS_GRID_GFZ_0001.nc"
SRC = ROOT / "cache" / "grace" / NAME
URL = "https://isdc-data.gfz.de/grace/GravIS/COST-G/Level-3/TWS/" + NAME
OUT = ROOT / "data" / "processed" / "grace_tws_monthly.csv"


def months(times):
    p = pd.DatetimeIndex(times).to_period("M")
    out = list(p)
    for i in range(1, len(out)):
        if out[i] == out[i - 1]:
            nxt = out[i] + 1
            if nxt in out:
                raise SystemExit(f"duplicate month {out[i]} and the next month is taken")
            out[i] = nxt
    return [str(x) for x in out]


def main():
    if not SRC.exists():
        os.makedirs(SRC.parent, exist_ok=True)
        urllib.request.urlretrieve(URL, SRC)
    ds = xr.open_dataset(SRC)
    w = {k: grids.weights(ds.lat.values, ds.lon.values, g) for k, g in grids.domains().items()}
    t = pd.DatetimeIndex(ds.time.values)
    mon = months(t)
    rows = []
    for i in range(len(t)):
        tws = ds["tws"].isel(time=i).values * 10.0
        std = ds["std_tws"].isel(time=i).values * 10.0
        leak = ds["leakage"].isel(time=i).values * 10.0
        for k, wk in w.items():
            ok = wk > 0
            s_unc = float(np.sqrt(np.nansum((wk[ok] * std[ok]) ** 2)) / wk[ok].sum())
            rows.append({"epoch": t[i].strftime("%Y-%m-%d"), "month": mon[i], "domain": k,
                         "tws_mm": round(grids.wmean(tws, wk), 3), "std_mm": round(grids.wmean(std, wk), 3),
                         "std_uncorrelated_mm": round(s_unc, 3), "leakage_mm": round(grids.wmean(leak, wk), 3)})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as fh:
        wr = csv.DictWriter(fh, list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)
    print(len(t), "epochs;", len(set(mon)), "months; first", mon[0], "last", mon[-1])


if __name__ == "__main__":
    main()
