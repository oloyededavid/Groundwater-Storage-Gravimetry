"""Shared settings for the Lake Chad study."""
MAIN = "lev3"        # HydroBASINS level-3 unit that holds the whole Lake Chad system (main study area)
ALT = "lev4_west"    # level-4 unit west of the lake that drains into its terminal unit (sensitivity test)
AREAS = (MAIN, ALT)
BASELINE = (2004, 2009)
PERIODS = {  # name: (first month, last month); GRACE-FO data start in 2018-06
    "2002-2010": ("2002-01", "2010-12"),
    "2011-2017": ("2011-01", "2017-06"),
    "2018-2026 (GRACE-FO)": ("2018-06", "2026-12"),
}
END_DATES = ("2021-12", "2023-12", "2026-12")
