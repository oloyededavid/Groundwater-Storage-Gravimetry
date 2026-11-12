"""TerraClimate soil moisture (Abatzoglou et al., 2018; monthly, 1/24 degree, mm, end of month) over the study areas,
read from the Microsoft Planetary Computer copy. It is a second land model for the soil term, independent of GLDAS.
The Planetary Computer copy ends in December 2021.

The zarr store is read chunk by chunk over HTTPS with the signed URL from the Planetary Computer STAC API
(general-purpose zarr readers fail behind this environment's proxy), and only the chunks covering the study areas.

Writes data/processed/terraclimate_soil_monthly.csv.

    python scripts/s04_terraclimate.py
"""
import csv
import json
import math
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import planetary_computer
import pystac_client
from numcodecs import Blosc

import grids

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "terraclimate_soil_monthly.csv"
START = "2002-01"


def get(base, q, key):
    with urllib.request.urlopen(f"{base}/{key}?{q}", timeout=180) as r:
        return r.read()


def array(base, q, meta, name):
    za = meta[f"{name}/.zarray"]
    return np.frombuffer(Blosc().decode(get(base, q, f"{name}/0")), dtype=za["dtype"])


def main():
    col = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1",
                                    modifier=planetary_computer.sign_inplace).get_collection("terraclimate")
    base, q = col.assets["zarr-https"].href.split("?", 1)
    meta = json.loads(get(base, q, ".zmetadata"))["metadata"]
    lat, lon = array(base, q, meta, "lat"), array(base, q, meta, "lon")
    tdays = array(base, q, meta, "time")
    times = pd.Timestamp("1958-01-01") + pd.to_timedelta(tdays, unit="D")
    za = meta["soil/.zarray"]
    ct, cy, cx = za["chunks"]
    doms = grids.domains()
    b = np.array([g.bounds for g in doms.values()])
    west, south, east, north = b[:, 0].min() - 0.5, b[:, 1].min() - 0.5, b[:, 2].max() + 0.5, b[:, 3].max() + 0.5
    rows_i = np.where((lat >= south) & (lat <= north))[0]
    cols_i = np.where((lon >= west) & (lon <= east))[0]
    r0, r1, c0, c1 = rows_i.min(), rows_i.max() + 1, cols_i.min(), cols_i.max() + 1
    sub_lat, sub_lon = lat[r0:r1], lon[c0:c1]
    w = {k: grids.weights(sub_lat, sub_lon, g, sub=2) for k, g in doms.items()}
    t_idx = np.where(times >= pd.Timestamp(START + "-01"))[0]
    out = []
    for tc in range(t_idx.min() // ct, math.ceil((t_idx.max() + 1) / ct)):
        block = np.full((ct, r1 - r0, c1 - c0), np.nan, dtype="f4")
        for yc in range(r0 // cy, math.ceil(r1 / cy)):
            for xc in range(c0 // cx, math.ceil(c1 / cx)):
                raw = Blosc().decode(get(base, q, f"soil/{tc}.{yc}.{xc}"))
                chunk = np.frombuffer(raw, dtype="<f4").reshape(ct, cy, cx)
                ys, xs = yc * cy, xc * cx
                ya, yb = max(r0, ys), min(r1, ys + cy)
                xa, xb = max(c0, xs), min(c1, xs + cx)
                block[:, ya - r0:yb - r0, xa - c0:xb - c0] = chunk[:, ya - ys:yb - ys, xa - xs:xb - xs]
        for k in range(ct):
            ti = tc * ct + k
            if ti >= len(times) or ti not in t_idx:
                continue
            f = block[k].astype(float)
            for d, wk in w.items():
                out.append({"month": times[ti].strftime("%Y-%m"), "domain": d, "soil_mm": round(grids.wmean(f, wk), 3)})
        print(times[min(tc * ct + ct - 1, len(times) - 1)].strftime("%Y-%m"), flush=True)
    with open(OUT, "w", newline="") as fh:
        wr = csv.DictWriter(fh, ["month", "domain", "soil_mm"])
        wr.writeheader()
        wr.writerows(out)
    print(len(out) // len(w), "months, last", out[-1]["month"])


if __name__ == "__main__":
    main()
