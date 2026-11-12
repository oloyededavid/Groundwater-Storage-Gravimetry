# Water Storage in the Lake Chad Sink Catchment from GRACE and GRACE-FO (2002–2026)

**Author:** David Oloyede

**Study page:** <https://oloyededavid.github.io/Groundwater-Storage-Gravimetry/>

This repository was rebuilt in November 2026. The first version (October 2026) reported a groundwater decline and a borehole validation that the data could not support. It is withdrawn and kept in [`archive/withdrawn-v1/`](archive/withdrawn-v1/) with a note. The audit that led to the rebuild is [`AUDIT-2026-11-11.md`](AUDIT-2026-11-11.md).

## Question

Has water storage around Lake Chad fallen or risen since 2002, how certain is the trend, and how much of it remains after removing soil water? The results are in the research note [`paper/paper.md`](paper/paper.md) and on the study page. Every number there is read from [`docs/data/results.json`](docs/data/results.json), which the scripts below write; none is typed by hand.

## What this study can and cannot say

- The gravity record measures all stored water. After removing soil water from two land models, the remainder holds **groundwater and surface water together** (Lake Chad, wetlands, floodplains). They are not separated here.
- There is **no independent groundwater validation**: no well records were available.
- The study area is the HydroBASINS level-4 unit that contains Lake Chad (the lake's sink catchment), because no outline of the Chad Formation aquifer was available. The level-3 unit is a sensitivity test.
- G3P, a groundwater product built from the same gravity data, is a consistency check, not a validation.

## Data

| Term | Source | Access |
| :--- | :--- | :--- |
| Total water storage | COST-G GravIS RL02 Level-3, 1 degree, monthly, with per-cell standard deviations (Boergens et al., 2025, [doi:10.5880/COST-G.GRAVIS_02_L3_TWS](https://doi.org/10.5880/COST-G.GRAVIS_02_L3_TWS)) | Open, GFZ ISDC |
| Soil water (main) | GLDAS-2.1 Noah monthly, soil 0–200 cm plus snow and canopy (Beaudoing & Rodell, 2020, [doi:10.5067/SXAVCZFAQLNO](https://doi.org/10.5067/SXAVCZFAQLNO)) | NASA Earthdata login |
| Soil water (second model) | TerraClimate soil moisture (Abatzoglou et al., 2018) | Open, Microsoft Planetary Computer (to 2021) |
| Consistency check | G3P v1.12 groundwater, soil and surface-water layers (Güntner et al., 2024, [doi:10.5880/G3P.2024.001](https://doi.org/10.5880/G3P.2024.001)) | Open, GFZ ISDC |
| Study areas | HydroBASINS v1c (Lehner & Grill, 2013) | Open, data.hydrosheds.org |

## Reproduce

```bash
pip install numpy pandas scipy xarray netCDF4 geopandas rasterio shapely matplotlib planetary-computer pystac-client numcodecs pytest
cd scripts
python s01_domains.py         # study areas
python s02_grace.py           # GRACE/GRACE-FO storage (downloads about 540 MB once)
python s03_gldas.py           # GLDAS soil water (needs an Earthdata token; about 290 files, each deleted after use)
python s04_terraclimate.py    # TerraClimate soil water
python s05_storage.py         # separation, trends and uncertainty -> docs/data/results.json
python s07_g3p.py             # G3P check (download G3P_v1.12.zip to cache/g3p/ first)
python s06_figures.py         # figures and page data
cd ..
python scripts/build_paper.py && pandoc paper/paper.md -o paper/paper.docx --resource-path=. && python scripts/build_page.py
pytest
```

Downloads go to `cache/`, which is not committed. The area means in `data/processed/` are committed, so the trend, figures, paper and page can be rebuilt without downloading anything.

## Repository layout

```
scripts/            data, analysis, figures, paper and page build
data/processed/     area means per month (GRACE, GLDAS, TerraClimate, G3P) and the study areas
docs/               study page (GitHub Pages): index.html, data/, assets/
paper/              research note: template.md (with placeholders) and the built paper.md and paper.docx
src/                small mass-balance helper package and its tests
archive/withdrawn-v1/  the withdrawn first version
tests/
```

## Licence

Code: MIT (`LICENSE`). Derived data and figures: CC BY 4.0. Source datasets keep their own terms.
