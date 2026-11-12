# Water Storage in the Lake Chad Basin from GRACE and GRACE-FO (2002–2026)

**Author:** David Oloyede

**Study page:** <https://oloyededavid.github.io/Groundwater-Storage-Gravimetry/>

This repository was rebuilt in November 2026. The first version (October 2026) reported a groundwater decline and a borehole validation that the data could not support. It is withdrawn and kept in [`archive/withdrawn-v1/`](archive/withdrawn-v1/) with a note. The audit that led to the rebuild is [`AUDIT-2026-11-11.md`](AUDIT-2026-11-11.md).

## Question

How has water storage in the Lake Chad basin changed since 2002, when did it change, how certain is that, and how much of it remains after removing soil water? The results are in the research note [`paper/paper.md`](paper/paper.md) and on the study page. The results there are read from [`docs/data/results.json`](docs/data/results.json) and `docs/data/grace_cells.json`, which the scripts below write; the build stops if a sentence in the template no longer matches them.

## What this study can and cannot say

- The gravity record measures all stored water. After removing soil water from two land models, the remainder holds **groundwater and surface water together** (Lake Chad, wetlands, floodplains). They are not separated here.
- There is **no independent groundwater validation**: no well records were available.
- The main study area is the HydroBASINS level-3 unit that contains Lake Chad, which holds the whole lake system, because no outline of the Chad Formation aquifer was available. A smaller level-4 unit west of the lake, which drains into the lake's terminal unit, is a sensitivity test.
- The record is flat until about 2018 and then rises steeply, so the study reports rates by period and a two-segment fit, not one straight line.
- Lake altimetry (Hydroweb) could not be reached from the environment used, so the lake's own storage is not removed.
- G3P, a groundwater product built from an earlier release of the same gravity combination, is a consistency check, not a validation.

## Data

| Term | Source | Access |
| :--- | :--- | :--- |
| Total water storage | COST-G GravIS RL02 Level-3, 1 degree, monthly, with per-month standard deviations (Boergens et al., 2025, [doi:10.5880/COST-G.GRAVIS_02_L3_TWS](https://doi.org/10.5880/COST-G.GRAVIS_02_L3_TWS)) | Open, GFZ ISDC |
| Second gravity solution | GFZ GravIS RL06 Level-3 (Boergens et al., 2019, [doi:10.5880/GFZ.GRAVIS_06_L3_TWS](https://doi.org/10.5880/GFZ.GRAVIS_06_L3_TWS)); not independent of COST-G | Open, GFZ ISDC |
| Soil water (main) | GLDAS-2.1 Noah monthly, soil 0–200 cm plus snow and canopy (Beaudoing & Rodell, 2020, [doi:10.5067/SXAVCZFAQLNO](https://doi.org/10.5067/SXAVCZFAQLNO)) | NASA Earthdata login |
| Soil water (second model) | TerraClimate soil moisture (Abatzoglou et al., 2018) | Open, Microsoft Planetary Computer (to 2021) |
| Consistency check | G3P v1.12 groundwater, soil and surface-water layers (Güntner et al., 2024, [doi:10.5880/G3P.2024.001](https://doi.org/10.5880/G3P.2024.001)) | Open, GFZ ISDC |
| Study areas | HydroBASINS v1c (Lehner & Grill, 2013) | Open, data.hydrosheds.org |

## Reproduce

```bash
pip install numpy pandas scipy xarray netCDF4 geopandas rasterio shapely matplotlib planetary-computer pystac-client numcodecs pytest
cd scripts
python s01_domains.py         # study areas
python s02_grace.py           # GRACE/GRACE-FO storage, two solutions (downloads about 1 GB once)
python s03_gldas.py           # GLDAS soil water (needs an Earthdata token; 295 files, each deleted after use)
python s04_terraclimate.py    # TerraClimate soil water
python s05_storage.py         # separation, rates by period, two-segment fit, spread of choices -> docs/data/results.json
python s07_g3p.py             # G3P check, must run after s05 (download G3P_v1.12.zip to cache/g3p/ first)
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
