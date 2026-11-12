# Withdrawn first version (October 2026)

These files are the first version of this study, kept for the record. They are not used by the rebuilt study and should not be cited.

An audit on 11 November 2026 (`AUDIT-2026-11-11.md` in the repository root) found that:

- the borehole column in `lake_chad_gravimetry_timeseries_2002_2025.csv` has no documented source, and its difference from the satellite series behaves like added random noise;
- the time axis is evenly spaced at 0.0862 years, not in calendar months, and has no gap for the 2017 to 2018 break between GRACE and GRACE-FO;
- the seasonal peak in the CSV (May) contradicts the report, and the trend and volume in the report (-5.84 mm per year, 1.97 km³ per year) do not match the CSV (-5.67);
- the surface-water column is said to come from GLDAS, which has no surface-water term.

The rebuilt study uses the real GRACE/GRACE-FO record and is described in the repository README.
