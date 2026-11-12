---
title: "Water storage in the Lake Chad basin from GRACE and GRACE-FO, 2002–2026"
author: "David Oloyede"
date: "{{date}}"
---

# Abstract

We ask whether water storage in the Lake Chad basin has fallen or risen since 2002, when, by how much, and how much of the change remains after removing soil water. We average two GravIS gravity solutions (COST-G and GFZ; {{n_epochs}} monthly fields for COST-G, {{grace_first}} to {{grace_last}}, {{missing}} months missing including the 2017–2018 break between the GRACE and GRACE-FO missions) over the HydroBASINS level-3 unit that holds the whole lake system ({{area_main}} km²), and subtract soil water from GLDAS Noah and TerraClimate. Storage was close to flat for the first part of the record and then rose steeply. A two-segment fit puts the change in {{brk}} (best breaks {{brk_range}}): total storage changed by {{h_before}} mm per year before it ({{h_before_ci}}) and {{h_after}} mm per year after it ({{h_after_ci}}). After removing GLDAS soil water, storage rose by {{res_fo}} mm per year over the GRACE-FO years 2018–2026 ({{res_fo_ci}}), about {{res_fo_km3}} km³ per year over the basin unit. Across the two gravity solutions and with or without the product's leakage correction, that rate ranges from {{spread_fo_lo}} to {{spread_fo_hi}} mm per year. A straight line through the whole record gives {{res_full}} mm per year ({{res_full_ci}}), but this summary depends on the end date ({{res_end_2021}} mm per year to 2021, {{res_end_2023}} to 2023). The remainder holds groundwater and surface water together, which this study cannot separate, and there is no independent groundwater validation.

**Keywords:** GRACE; GRACE-FO; terrestrial water storage; groundwater; Lake Chad; Sahel

# 1. Introduction

Satellite gravimetry measures changes in all the water stored in a region: soil water, groundwater, lakes, rivers and wetlands together. Groundwater is usually estimated by subtracting the other stores, taken from land-surface models, so its quality depends on those models and on what is left out.

An earlier version of this study reported groundwater storage over the Quaternary Chad Formation falling by 5.84 mm per year from 2002 to 2025 and validated it against five boreholes. An audit found that its time series did not have the structure of the GRACE record (evenly spaced steps and no 2017–2018 gap), that the borehole series had no documented source, and that several numbers did not match the data. That series was not derived from the published GRACE record, and the version is withdrawn; it is kept in `archive/withdrawn-v1/` for the record. This note rebuilds the analysis from published gravity data.

We ask two questions. How has total water storage in the Lake Chad basin changed since 2002, and how certain is that? And how much of the change remains after removing soil water, which is the closest this study can get to groundwater?

# 2. Data and methods

## 2.1 Study area

No published outline of the Chad Formation aquifer was available, so the study area is a river-basin unit. The main area is the HydroBASINS level-3 unit that contains Lake Chad ({{area_main}} km²; Lehner & Grill, 2013). It holds the lake's terminal level-4 unit and every level-4 unit that drains to it. As a sensitivity test we use a smaller level-4 unit west of the lake ({{area_alt}} km²), which drains into the terminal unit and does not contain the whole lake.

## 2.2 Data

**Gravity.** Terrestrial water storage anomalies come from the GravIS Level-3 products on a 1-degree grid in equivalent water height, with a standard deviation for each month: the COST-G RL02 combination (Boergens et al., 2025), used for the main results, and the GFZ RL06 solution (Boergens et al., 2019), used as a second solution. The two are not independent: COST-G combines several analysis centres including GFZ, and both use the same GravIS processing. GRACE resolves features of a few hundred kilometres, so the 1-degree grid is smoother than it looks. Each monthly field is matched to the calendar month of its mid-date; where two fields fall in one month, the later one is moved to the following month, which has none. Missing months stay missing.

**Soil water.** GLDAS-2.1 Noah monthly (Rodell et al., 2004; Beaudoing & Rodell, 2020) gives soil moisture in four layers down to 2 m, snow and canopy water, from 2002 to {{gldas_last}}. TerraClimate (Abatzoglou et al., 2018) gives soil water at the end of each month from a simpler bucket model, available here to {{tc_last}}. Its seasonal cycle over the basin is about half that of GLDAS ({{amp_tc}} against {{amp_gldas}} mm), so it removes less water and is a weaker test. Neither model includes lakes, rivers or wetlands.

Each grid is averaged over the study area with weights equal to the fraction of each cell inside the area times the cosine of latitude.

## 2.3 Separation

All series are anomalies from their own mean over the GRACE months of {{baseline}}. The residual storage is the gravity anomaly minus the soil-water anomaly. It contains groundwater and surface water together.

## 2.4 Rates and uncertainty

Rates are fitted together with annual and semi-annual cycles by generalised least squares with first-order autoregressive errors that respect the missing months; monthly values are strongly autocorrelated, so ordinary least squares would understate the uncertainty. Because the record has distinct phases, we report: a rate for each period (2002–2010, 2011 to mid-2017, and the GRACE-FO years from mid-2018); a continuous two-segment fit whose break month is chosen by the Akaike information criterion, with the range of break months within 2 units of the best; the straight-line rate through the whole record for three end dates; and the spread of rates across choices (gravity solution, leakage correction, soil model, study area). The GRACE errors stated in the product change the full-record rate by only {{grace_err}} mm per year when drawn independently each month. That is a lower bound, because it ignores errors shared between months and between the missions; the spread across choices is the larger uncertainty.

The break falls close to the 2017–2018 gap between the missions, so we also fit separate straight lines to the GRACE and GRACE-FO years and estimate the step between them at the middle of the gap.

## 2.5 Consistency check

G3P v1.12 (Güntner et al., 2024) is a groundwater product built from an earlier release of the COST-G combination (RL01), with separate layers for groundwater, soil water and surface water. Because it uses largely the same gravity data, agreement with it is a check of consistency, not a validation. We compare over the {{g3p_n}} months both cover ({{g3p_first}} to {{g3p_last}}).

# 3. Results

## 3.1 Total water storage

![**Figure 1.** Straight-line storage trend in each 1-degree GRACE cell, 2002–2026 (COST-G), with the level-3 basin unit (solid) and the western level-4 unit (dashed). Blank cells are ocean. The marker shows the approximate position of the lake.](docs/assets/figures/fig1_area.png)

Over the basin unit, total storage changed little until 2018: {{p1}} mm per year in 2002–2010 ({{p1_ci}}) and {{p2}} mm per year from 2011 to mid-2017 ({{p2_ci}}). In the GRACE-FO years it rose by {{p3}} mm per year ({{p3_ci}}). The two-segment fit is much better than a single line (Akaike criterion lower by {{daic}}), with its break in {{brk}}. Annual mean storage stayed within {{early_lo}} to {{early_hi}} mm of the {{baseline}} mean in the complete years up to 2016, and reached {{late_max}} mm above it in {{late_max_year}} (Figure 2, Figure 3).

The step between the missions is estimated at {{step}} mm ({{step_ci}}). It is not distinguishable from zero and points the wrong way to explain the rise, which is measured within the GRACE-FO years alone. A small step cannot be ruled out; it would mostly affect the straight-line rate through the whole record.

The cells that overlap the basin unit have straight-line trends from {{cell_lo}} to {{cell_hi}} mm per year (Figure 1). The largest is in the cell centred at {{cell_max_lat}}° N, {{cell_max_lon}}° E, west of the lake, while the cell holding the lake marker has {{cell_lake}} mm per year.

![**Figure 2.** Monthly anomalies from the {{baseline}} mean for the basin unit: total storage with its stated error band, GLDAS soil water, and storage minus soil water from each model. The grey band is the 2017–2018 gap between the missions.](docs/assets/figures/fig2_monthly.png)

## 3.2 After removing soil water

GLDAS soil water shows no clear trend over the record ({{soil_trend}} mm per year, {{soil_ci}}), so the residual follows total storage. Its rate is {{res_p1}} mm per year in 2002–2010, {{res_p2}} mm per year from 2011 to mid-2017 and {{res_fo}} mm per year in the GRACE-FO years ({{res_fo_ci}}); its two-segment fit breaks in {{res_brk}}. With TerraClimate soil water over the years it covers (to {{tc_last}}), the residual changes by {{res_tc}} mm per year, against {{res_tc_gl}} mm per year with GLDAS over the same years; both are small because those years end before most of the rise.

The straight-line rate through the whole record is {{res_full}} mm per year ({{res_full_ci}}). It is a summary, not a constant rate: ending the record in 2021 gives {{res_end_2021}} mm per year and ending in 2023 gives {{res_end_2023}}.

![**Figure 3.** Annual mean anomalies for the basin unit, total storage and storage minus GLDAS soil water. Years with fewer than nine months of data ({{years_out}}) are left out.](docs/assets/figures/fig3_annual.png)

## 3.3 Sensitivity and consistency

| Gravity solution | Area | Soil water | Rate 2002–2026, mm per year (95% interval) | Rate in GRACE-FO years, mm per year (95% interval) |
| :--- | :--- | :--- | :--- | :--- |
{{sens_table}}

Table 1. Residual storage rates (gravity minus soil water) under each choice. Intervals from generalised least squares with autoregressive errors. TerraClimate rows end in {{tc_last}}.

In the basin unit, the GRACE-FO rate ranges from {{spread_fo_lo}} to {{spread_fo_hi}} mm per year across the two solutions and the leakage choice, and the product's leakage correction raises it. The western level-4 unit, where the rise is strongest, gives higher rates throughout.

{{g3p_text}}

# 4. Discussion

Water storage in the Lake Chad basin changed little from 2002 to about 2018 and then rose steeply. Almost all of the rise remains after removing GLDAS soil water. This study does not test what caused it: rainfall, river inflow and lake extent were not analysed.

Whether the rise is groundwater cannot be settled here. The basin unit contains the lake, its wetlands and the floodplains of its inflowing rivers, and the gravity record cannot tell water in them from groundwater. G3P counts the change as groundwater, but its surface-water layer stays close to zero over the basin, so it does not settle the question either. Lake level from satellite altimetry would help; the Hydroweb service lists a Lake Chad series, but it could not be reached from the environment used for this study.

The earlier version of this study reported a steady decline for a differently drawn and undocumented area. Its series was not derived from the published GRACE record, and the gravity record used here shows no decline over the basin unit.

# 5. Limitations

There is no independent groundwater measurement: no well records were available, so the result is not validated. The residual contains groundwater and surface water together. The study area is a river-basin unit, not the aquifer outline, and the strongest rise lies in its western part. GRACE resolves a few hundred kilometres and signal leaks in and out of the unit; the leakage correction changes the GRACE-FO rate by more than its stated interval. Only two gravity solutions from the same processing chain were used. The soil models differ in depth and physics, and neither was compared with soil-moisture observations. The rise is concentrated in the last years of the record, so the full-record rate depends on the end date, and the break sits near the mission gap, so a small step between the missions cannot be ruled out. The intervals cover sampling and autocorrelation, not errors shared by the models or the gravity solutions.

# 6. Conclusion

Over the Lake Chad basin unit, water storage was close to flat until about 2018 and then rose by {{p3}} mm per year in total storage and {{res_fo}} mm per year after removing soil water ({{spread_fo_lo}} to {{spread_fo_hi}} across the gravity solution and leakage choices). The water is in groundwater, surface water or both, which this study cannot separate. The earlier claim of a groundwater decline is not supported by the gravity record.

# Data and code availability

Code is released under the MIT licence and derived data under CC BY 4.0, from <https://github.com/oloyededavid/Groundwater-Storage-Gravimetry>. The results in this note are read from `docs/data/results.json` and `docs/data/grace_cells.json`, which the scripts in `scripts/` write. Source data keep their own terms.

# References

Abatzoglou, J. T., Dobrowski, S. Z., Parks, S. A., & Hegewisch, K. C. (2018). TerraClimate, a high-resolution global dataset of monthly climate and climatic water balance from 1958–2015. *Scientific Data*, 5, 170191. <https://doi.org/10.1038/sdata.2017.191>

Beaudoing, H., & Rodell, M. (2020). *GLDAS Noah Land Surface Model L4 monthly 0.25 x 0.25 degree, Version 2.1*. NASA Goddard Earth Sciences Data and Information Services Center. <https://doi.org/10.5067/SXAVCZFAQLNO>

Boergens, E., Dobslaw, H., & Dill, R. (2019). *GFZ GravIS RL06 Continental Water Storage Anomalies* (Version 0006). GFZ Data Services. <https://doi.org/10.5880/GFZ.GRAVIS_06_L3_TWS>

Boergens, E., Dobslaw, H., & Dill, R. (2025). *COST-G GravIS RL02 Terrestrial Water Storage Anomalies* (Version 0001). GFZ Data Services. <https://doi.org/10.5880/COST-G.GRAVIS_02_L3_TWS>

Güntner, A., Sharifi, E., Haas, J., et al. (2024). *Global Gravity-based Groundwater Product (G3P)* (Version 1.12). GFZ Data Services. <https://doi.org/10.5880/G3P.2024.001>

Lehner, B., & Grill, G. (2013). Global river hydrography and network routing: baseline data and new approaches to study the world's large river systems. *Hydrological Processes*, 27(15), 2171–2186. <https://doi.org/10.1002/hyp.9740>

Rodell, M., Houser, P. R., Jambor, U., et al. (2004). The Global Land Data Assimilation System. *Bulletin of the American Meteorological Society*, 85(3), 381–394. <https://doi.org/10.1175/BAMS-85-3-381>
