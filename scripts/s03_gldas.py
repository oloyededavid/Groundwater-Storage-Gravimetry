"""GLDAS-2.1 Noah monthly (0.25 degree) land water storage over the study areas.

Storage = soil moisture in the four layers (0-200 cm) + snow water equivalent + canopy water, all in kg/m2 = mm.
GLDAS Noah has no surface-water or lake term.
Needs an Earthdata Login token for hydro1.gesdisc.eosdis.nasa.gov (sent by the environment's network proxy).
Each monthly file (about 25 MB) is downloaded, reduced to the area means, and deleted. Resumes where it stopped.

Writes data/processed/gldas_noah_monthly.csv.

    python scripts/s03_gldas.py [first_year] [last_year]
"""
import csv
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import xarray as xr

import grids

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "gldas_noah_monthly.csv"
TMP = ROOT / "cache" / "gldas"
BASE = "https://hydro1.gesdisc.eosdis.nasa.gov/data/GLDAS/GLDAS_NOAH025_M.2.1/{y}/GLDAS_NOAH025_M.A{y}{m:02d}.021.nc4"
LAYERS = ["SoilMoi0_10cm_inst", "SoilMoi10_40cm_inst", "SoilMoi40_100cm_inst", "SoilMoi100_200cm_inst"]
OTHER = ["SWE_inst", "CanopInt_inst"]
FIELDS = ["month", "domain", "soil_mm", "swe_mm", "canopy_mm", "storage_mm"]


def fetch(url, dest, tries=4):
    for k in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=180) as r, open(dest, "wb") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False
            err = e
        except Exception as e:  # network errors: wait and retry
            err = e
        time.sleep(5 * 2 ** k)
    raise SystemExit(f"failed {url}: {err!r}")


def main():
    y0 = int(sys.argv[1]) if len(sys.argv) > 1 else 2002
    y1 = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
    TMP.mkdir(parents=True, exist_ok=True)
    done = set()
    if OUT.exists():
        done = {r["month"] for r in csv.DictReader(open(OUT))}
    new = not OUT.exists()
    doms = grids.domains()
    w = None
    with open(OUT, "a", newline="") as fh:
        wr = csv.DictWriter(fh, FIELDS)
        if new:
            wr.writeheader()
        for y in range(y0, y1 + 1):
            for m in range(1, 13):
                key = f"{y}-{m:02d}"
                if key in done:
                    continue
                dest = TMP / f"{key}.nc4"
                if not fetch(BASE.format(y=y, m=m), dest):
                    print(key, "not published yet", flush=True)
                    continue
                with xr.open_dataset(dest, engine="netcdf4") as ds:
                    if w is None:
                        w = {k: grids.weights(ds.lat.values, ds.lon.values, g) for k, g in doms.items()}
                    soil = sum(ds[v].isel(time=0).values for v in LAYERS)
                    swe = ds["SWE_inst"].isel(time=0).values
                    can = ds["CanopInt_inst"].isel(time=0).values
                for k, wk in w.items():
                    s, sw, c = grids.wmean(soil, wk), grids.wmean(swe, wk), grids.wmean(can, wk)
                    wr.writerow({"month": key, "domain": k, "soil_mm": round(s, 3), "swe_mm": round(sw, 4),
                                 "canopy_mm": round(c, 4), "storage_mm": round(s + sw + c, 3)})
                fh.flush()
                dest.unlink()
                print(key, "ok", flush=True)


if __name__ == "__main__":
    main()
