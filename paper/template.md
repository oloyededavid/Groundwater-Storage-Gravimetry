---
title: "Water storage in the Lake Chad sink catchment from GRACE and GRACE-FO, 2002–2026"
author: "David Oloyede"
date: "{{date}}"
---

# Abstract

We ask whether water storage around Lake Chad has been falling or rising since 2002, by how much, and how much of the change can be called groundwater. We average the COST-G GravIS gravity record ({{n_epochs}} monthly fields, {{grace_first}} to {{grace_last}}, {{missing}} months missing including the 2017–2018 break between the GRACE and GRACE-FO missions) over the Lake Chad sink catchment ({{area_p}} km², HydroBASINS level 4), and subtract soil water from two land models, GLDAS Noah and TerraClimate. Total water storage rose by {{tws_full}} mm per year over the whole record (95% interval {{tws_full_ci}}), slowly before 2017 ({{tws_g1}} mm per year) and quickly after 2018 ({{tws_g2}} mm per year). Removing GLDAS soil water leaves {{res_full}} mm per year ({{res_full_ci}}), about {{res_km3}} km³ per year over the catchment. The remainder holds groundwater and surface water together: with no open lake-storage record in this study, the two cannot be separated, and there is no independent groundwater validation. {{g3p_abstract}} The rise is the opposite of the decline reported in an earlier version of this study, which was withdrawn.

**Keywords:** GRACE; GRACE-FO; terrestrial water storage; groundwater; Lake Chad; Sahel

# 1. Introduction

Satellite gravimetry measures changes in all the water stored in a region: soil water, groundwater, lakes, rivers and wetlands together. Groundwater is usually estimated by subtracting the other stores, taken from land-surface models, which means its quality depends on those models and on what is left out.

An earlier version of this study reported groundwater storage over the Quaternary Chad Formation falling by 5.84 mm per year from 2002 to 2025 and validated it against five boreholes. An audit found that the time series did not have the structure of the GRACE record (evenly spaced steps and no 2017–2018 gap), that the borehole series had no documented source, and that several numbers did not match the data. That version is withdrawn and kept in `archive/withdrawn-v1/` for the record. This note rebuilds the analysis from the published gravity record.

We ask two questions. Has total water storage in the Lake Chad sink catchment fallen or risen since 2002, and how certain is the trend? And how much of it remains after removing soil water, which is the closest this study can get to groundwater?

# 2. Data and methods

## 2.1 Study area

No published outline of the Chad Formation aquifer was available, so the study area is a river-basin unit. The main area is the HydroBASINS level-4 unit that contains Lake Chad ({{area_p}} km²), the lake's own sink catchment. The level-3 unit that contains it ({{area_s}} km²) is used as a sensitivity test (Lehner & Grill, 2013).

## 2.2 Data

**Gravity.** Terrestrial water storage anomalies come from the COST-G GravIS RL02 Level-3 product (Boergens et al., 2025), on a 1-degree grid in equivalent water height, with a standard deviation for each cell and month. GRACE resolves features of a few hundred kilometres, so the 1-degree grid is smoother than it looks. Each monthly field is matched to the calendar month of its mid-date; two months hold two fields each, and the later field is moved to the following month, which has none. Missing months stay missing.

**Soil water.** GLDAS-2.1 Noah monthly (Rodell et al., 2004; Beaudoing & Rodell, 2020) gives soil moisture in four layers down to 2 m, snow and canopy water, from 2002 to {{gldas_last}}. TerraClimate (Abatzoglou et al., 2018) gives a second, independent estimate of soil water from a simpler water-balance model, available here to {{tc_last}}. Neither model includes lakes, rivers or wetlands.

Each grid is averaged over the study area with weights equal to the fraction of each cell inside the area times the cosine of latitude.

## 2.3 Separation

All series are anomalies from their own mean over the GRACE months of {{baseline}}. The residual storage is the gravity anomaly minus the soil-water anomaly. It contains groundwater and surface water together.

## 2.4 Trend and uncertainty

The trend is a straight line fitted together with annual and semi-annual cycles to the months that exist. Monthly residuals are strongly autocorrelated (lag-1 correlation {{tws_ar1}} for total storage), so the plain regression error is too small. We report a 95% interval from a moving-block bootstrap of the residuals with 24-month blocks, and an AR(1)-adjusted interval in the data files. The stated GRACE error adds very little: repeating the fit with each month's standard deviation as random noise changes the trend by {{grace_err}} mm per year (one standard deviation). The choices tested are the soil model, the study area, removing the leakage term the product provides, and the period.

## 2.5 Consistency check

G3P (Güntner et al., 2024) is a groundwater product built from the same gravity data, with separate layers for groundwater, soil water and surface water. Because it uses the same GRACE record, agreement with it is a check of consistency, not a validation. Its surface-water layer gives an outside estimate of how much of the storage change sits in lakes and wetlands. We compare over the {{g3p_n}} months both cover ({{g3p_first}} to {{g3p_last}}).

# 3. Results

## 3.1 Total water storage

![**Figure 1.** Storage trend in each 1-degree GRACE cell, 2002–2026, with the Lake Chad sink catchment (solid) and the level-3 unit (dashed).](docs/assets/figures/fig1_area.png)

Total water storage over the sink catchment rose by {{tws_full}} mm per year from {{grace_first}} to {{grace_last}} (95% interval {{tws_full_ci}}). The rise is uneven. Over the GRACE mission years it was {{tws_g1}} mm per year ({{tws_g1_ci}}), and over the GRACE-FO years {{tws_g2}} mm per year ({{tws_g2_ci}}). Annual mean storage stayed within {{early_lo}} to {{early_hi}} mm of the {{baseline}} mean up to 2016, then rose to {{late_max}} mm above it in {{late_max_year}} (Figure 2, Figure 3). The seasonal cycle has an amplitude of about {{tws_amp}} mm. Figure 1 shows the rise across the region at the resolution GRACE allows; the cells that overlap the catchment have trends from {{cell_lo}} to {{cell_hi}} mm per year.

![**Figure 2.** Monthly anomalies from the {{baseline}} mean for the Lake Chad sink catchment: total storage with its stated error band, GLDAS soil water, and storage minus soil water from each model. The grey band is the 2017–2018 gap between the missions.](docs/assets/figures/fig2_monthly.png)

## 3.2 After removing soil water

Soil water in GLDAS changes by {{soil_trend}} mm per year over the record, so most of the storage trend remains after removing it: {{res_full}} mm per year ({{res_full_ci}}), or about {{res_km3}} km³ per year over {{area_p}} km². With TerraClimate soil water, over the years it covers (to {{tc_last}}), the residual trend is {{res_tc}} mm per year ({{res_tc_ci}}), against {{res_gl_2021}} mm per year with GLDAS over the same years.

![**Figure 3.** Annual mean anomalies, total storage and storage minus GLDAS soil water. Years with fewer than nine months of data (2017 and 2018) are left out.](docs/assets/figures/fig3_annual.png)

## 3.3 Sensitivity and consistency

| Specification | Trend, mm per year | 95% interval |
| :--- | ---: | :--- |
{{sens_table}}

Table 1. Residual storage trend (gravity minus soil water) under different choices. Intervals from the moving-block bootstrap.

{{g3p_text}}

# 4. Discussion

Water storage around Lake Chad has risen since 2002, and mostly since 2018. This study does not test what caused the rise: rainfall, inflow and lake extent were not analysed. Most of the rise survives the removal of soil water in both models, so it sits deeper than 2 m or in surface water.

Whether it is groundwater cannot be settled here. The lake, its wetlands and the floodplains of its inflowing rivers lie inside the catchment, and the gravity record cannot tell water in them from groundwater. {{g3p_disc}}

The earlier version of this study reported a steady decline. The real gravity record shows the opposite sign, and the decline cannot be reproduced from any published GRACE series used here.

# 5. Limitations

There is no independent groundwater measurement: no well records were available, so the result is not validated. The residual contains groundwater and surface water together. The study area is a river-basin unit, not the aquifer outline. GRACE resolves a few hundred kilometres, the catchment covers only about {{cells_equiv}} 1-degree cells, and signal leaks in and out of it; the product's leakage term was tested but not used for the main result. The soil models differ in depth and physics, and neither was compared with soil-moisture observations. The trend is a straight line through a record whose rise is concentrated in the last eight years, so the full-period rate is a summary, not a constant rate. The intervals cover sampling and autocorrelation, not errors shared by the models.

# 6. Conclusion

Water storage in the Lake Chad sink catchment rose by {{tws_full}} mm per year from {{grace_first}} to {{grace_last}}, and by {{tws_g2}} mm per year in the GRACE-FO years. After removing soil water, {{res_full}} mm per year remains, in groundwater and surface water that this study cannot separate. The earlier claim of a groundwater decline is not supported by the gravity record.

# Data and code availability

Code is released under the MIT licence and derived data under CC BY 4.0, from <https://github.com/oloyededavid/Groundwater-Storage-Gravimetry>. Every number in this note is read from `docs/data/results.json`, which the scripts in `scripts/` write. Source data keep their own terms.

# References

Abatzoglou, J. T., Dobrowski, S. Z., Parks, S. A., & Hegewisch, K. C. (2018). TerraClimate, a high-resolution global dataset of monthly climate and climatic water balance from 1958–2015. *Scientific Data*, 5, 170191. https://doi.org/10.1038/sdata.2017.191

Beaudoing, H., & Rodell, M. (2020). *GLDAS Noah Land Surface Model L4 monthly 0.25 x 0.25 degree, Version 2.1*. NASA Goddard Earth Sciences Data and Information Services Center. https://doi.org/10.5067/SXAVCZFAQLNO

Boergens, E., Dobslaw, H., & Dill, R. (2025). *COST-G GravIS RL02 Terrestrial Water Storage Anomalies* (Version 0001). GFZ Data Services. https://doi.org/10.5880/COST-G.GRAVIS_02_L3_TWS

Güntner, A., Sharifi, E., Haas, J., et al. (2024). *Global Gravity-based Groundwater Product (G3P)* (Version 1.12). GFZ Data Services. https://doi.org/10.5880/G3P.2024.001

Lehner, B., & Grill, G. (2013). Global river hydrography and network routing: baseline data and new approaches to study the world's large river systems. *Hydrological Processes*, 27(15), 2171–2186. https://doi.org/10.1002/hyp.9740

Rodell, M., Houser, P. R., Jambor, U., et al. (2004). The Global Land Data Assimilation System. *Bulletin of the American Meteorological Society*, 85(3), 381–394. https://doi.org/10.1175/BAMS-85-3-381
