"""Consistency check against G3P v1.12 (Guentner et al., 2024, doi:10.5880/G3P.2024.001; 0.5 degree, monthly,
2002-04 to 2023-09). G3P is built from an earlier release of the COST-G gravity combination (RL01; this study uses
RL02), so agreement is a consistency check, not validation. Its groundwater layer is GRACE minus its own soil, snow,
glacier and surface-water layers.

Reads cache/g3p/G3P_v1.12.zip (download it from https://isdc-data.gfz.de/grace/GravIS/G3P/v1.12/).
Writes data/processed/g3p_monthly.csv and adds a "g3p" block to docs/data/results.json.

    python scripts/s07_g3p.py
"""
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

import grids
import s05_storage as st
import study

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / "cache" / "g3p" / "G3P_v1.12.zip"
EXT = ROOT / "cache" / "g3p" / "x"
OUT = ROOT / "data" / "processed" / "g3p_monthly.csv"
RES = ROOT / "docs" / "data" / "results.json"
LAYERS = {"gwsa": "GWSA/gwsa", "sws": "SWS/sws", "rzsm": "RZSM/rzsm", "tws": "TWS/tws"}


def path_for(names, stem):
    hit = [n for n in names if f"/{stem}_g3p_" in "/" + n.split("G3P_v1.12/")[-1] and n.endswith(".nc")]
    if len(hit) != 1:
        raise SystemExit(f"cannot find {stem} in the archive")
    return hit[0]


def main():
    z = zipfile.ZipFile(ZIP)
    names = z.namelist()
    doms = grids.domains()
    frames = []
    for key, stem in LAYERS.items():
        name = path_for(names, stem)
        target = EXT / name
        if not target.exists():
            z.extract(name, EXT)
        ds = xr.open_dataset(target)
        var = key if key in ds.data_vars else None  # the TWS file also holds a leakage grid; use the named layer
        if var is None:
            raise SystemExit(f"no {key} variable in {name}")
        units = ds[var].attrs.get("units", "")
        scale = {"m": 1000.0, "cm": 10.0, "mm": 1.0}.get(units.strip().lower(), np.nan)
        if not np.isfinite(scale):
            raise SystemExit(f"unexpected units {units!r} for {key}")
        latn = "lat" if "lat" in ds.dims else "latitude"
        lonn = "lon" if "lon" in ds.dims else "longitude"
        lon = ds[lonn].values
        w = {k: grids.weights(ds[latn].values, lon, g) for k, g in doms.items()}
        t = pd.DatetimeIndex(ds.time.values)
        for i in range(len(t)):
            f = ds[var].isel(time=i).values * scale
            for k, wk in w.items():
                frames.append({"month": t[i].strftime("%Y-%m"), "domain": k, "layer": key, "mm": grids.wmean(f, wk)})
    df = pd.DataFrame(frames).pivot_table(index=["month", "domain"], columns="layer", values="mm").reset_index()
    df.round(3).to_csv(OUT, index=False)
    ours = pd.read_csv(ROOT / "data" / "processed" / "storage_monthly.csv")
    res = json.loads(RES.read_text())
    out = {}
    for dom in study.AREAS:
        a = ours[ours.domain == dom].merge(df[df.domain == dom], on="month", how="inner")
        yrs = pd.PeriodIndex(a.month, freq="M").year
        ref = (yrs >= study.BASELINE[0]) & (yrs <= study.BASELINE[1])
        for c in ("gwsa", "sws", "rzsm", "tws"):
            a[c] = a[c] - a.loc[ref, c].mean()
        block = {"months_in_common": int(len(a)), "first": a.month.iloc[0], "last": a.month.iloc[-1]}
        for name, col in (("our_tws", "tws_mm_anom"), ("g3p_tws", "tws"), ("our_residual_gldas", "res_gldas"),
                          ("g3p_groundwater", "gwsa"), ("g3p_surface_water", "sws")):
            block[name] = st.rate(a.month.to_numpy(), a[col].to_numpy(float))
        ok = a[["res_gldas", "gwsa"]].dropna()
        block["corr_residual_vs_g3p_groundwater"] = round(float(np.corrcoef(ok.res_gldas, ok.gwsa)[0, 1]), 3)
        ok = a[["tws_mm_anom", "tws"]].dropna()
        block["corr_tws_vs_g3p_tws"] = round(float(np.corrcoef(ok.tws_mm_anom, ok.tws)[0, 1]), 3)
        block["g3p_surface_water_range_mm"] = [round(float(a.sws.min()), 1), round(float(a.sws.max()), 1)]
        out[dom] = block
    res["g3p"] = out
    RES.write_text(json.dumps(res, indent=1))
    p = out[study.MAIN]
    print({k: (v["rate_mm_yr"], v["annual_amplitude_mm"]) if isinstance(v, dict) else v for k, v in p.items()})


if __name__ == "__main__":
    main()
