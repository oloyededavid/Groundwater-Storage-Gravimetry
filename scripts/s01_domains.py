"""Study areas from HydroBASINS (open data, data.hydrosheds.org).

Primary: the level-4 unit that contains Lake Chad (the lake's own sink catchment).
Sensitivity: the level-3 unit that contains it.
No published Chad Formation aquifer outline was available, so the study uses these catchments and says so.

Writes data/processed/domains.geojson.

    python scripts/s01_domains.py
"""
import json
import os
import urllib.request
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point, mapping

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "cache" / "hydrobasins"
OUT = ROOT / "data" / "processed" / "domains.geojson"
URL = "https://data.hydrosheds.org/file/HydroBASINS/standard/hybas_af_lev{lev}_v1c.zip"
LAKE = Point(14.0, 13.2)  # a point inside Lake Chad's southern pool, used only to pick the unit that holds the lake
EQUAL_AREA = "ESRI:102022"  # Africa Albers equal-area conic


def unit(level):
    path = CACHE / f"lev{level}.zip"
    if not path.exists():
        os.makedirs(CACHE, exist_ok=True)
        urllib.request.urlretrieve(URL.format(lev=level), path)
    g = gpd.read_file(f"zip://{path}")
    hit = g[g.contains(LAKE)]
    if len(hit) != 1:
        raise SystemExit(f"expected one level-{level} unit containing the lake, found {len(hit)}")
    return hit.iloc[0], g.crs


def main():
    feats = []
    for key, level, name in (("primary", "04", "Lake Chad sink catchment (HydroBASINS level 4)"),
                             ("sensitivity", "03", "Lake Chad basin unit (HydroBASINS level 3)")):
        row, crs = unit(level)
        area = gpd.GeoSeries([row.geometry], crs=crs).to_crs(EQUAL_AREA).area.iloc[0] / 1e6
        feats.append({"type": "Feature",
                      "properties": {"id": key, "name": name, "hybas_id": int(row.HYBAS_ID), "level": int(level),
                                     "area_km2": round(float(area)), "hydrobasins_sub_area_km2": float(row.SUB_AREA)},
                      "geometry": mapping(row.geometry.simplify(0.01, preserve_topology=True))})
        print(key, int(row.HYBAS_ID), round(float(area)), "km2")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": feats,
                               "source": "HydroBASINS v1c (Lehner and Grill, 2013), data.hydrosheds.org"}))


if __name__ == "__main__":
    main()
