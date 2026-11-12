"""Area-weighted means of a regular lat/lon grid over a polygon, using the fraction of each cell inside it."""
import json
from pathlib import Path

import numpy as np
from rasterio.features import rasterize
from rasterio.transform import from_origin
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]
DOMAINS = ROOT / "data" / "processed" / "domains.geojson"


def domains():
    g = json.loads(DOMAINS.read_text())
    return {f["properties"]["id"]: shape(f["geometry"]) for f in g["features"]}


def weights(lat, lon, geom, sub=10):
    """Weight per cell = fraction of the cell inside geom x cos(latitude). lat and lon are cell centres,
    evenly spaced; lat may run either way. Returns an array shaped (len(lat), len(lon))."""
    lat = np.asarray(lat, float)
    lon = np.asarray(lon, float)
    dlat, dlon = abs(lat[1] - lat[0]), abs(lon[1] - lon[0])
    north = lat.max() + dlat / 2
    west = lon.min() - dlon / 2
    n_r, n_c = len(lat), len(lon)
    t = from_origin(west, north, dlon / sub, dlat / sub)
    fine = rasterize([(geom, 1)], out_shape=(n_r * sub, n_c * sub), transform=t, fill=0, dtype="uint8", all_touched=False)
    frac = fine.reshape(n_r, sub, n_c, sub).mean(axis=(1, 3))  # rows run north to south
    if lat[0] < lat[-1]:
        frac = frac[::-1]
    return frac * np.cos(np.deg2rad(lat))[:, None]


def wmean(field, w):
    """Weighted mean ignoring NaN cells; returns NaN if less than half the weight has data."""
    ok = np.isfinite(field) & (w > 0)
    if w[ok].sum() < 0.5 * w.sum():
        return np.nan
    return float((field[ok] * w[ok]).sum() / w[ok].sum())
