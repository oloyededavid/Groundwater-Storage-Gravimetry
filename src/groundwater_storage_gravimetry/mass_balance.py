from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd
from scipy.stats import linregress


@dataclass
class MassBalanceResult:
    """Container for isolated groundwater storage anomalies and trend statistics."""

    time: np.ndarray
    gws_anomaly: np.ndarray
    gws_uncertainty: np.ndarray
    trend_mm_per_year: float
    trend_p_value: float
    summary_table: pd.DataFrame


def isolate_groundwater_storage(
    time: np.ndarray | Sequence[Any],
    tws: np.ndarray | Sequence[float],
    tws_err: np.ndarray | Sequence[float],
    sms: np.ndarray | Sequence[float],
    sms_err: np.ndarray | Sequence[float],
    swe: np.ndarray | Sequence[float] | None = None,
    swe_err: np.ndarray | Sequence[float] | None = None,
    sw: np.ndarray | Sequence[float] | None = None,
    sw_err: np.ndarray | Sequence[float] | None = None,
) -> MassBalanceResult:
    """Isolate groundwater storage anomalies from GRACE TWS and land surface models.

    Equation:
        GWS = TWS - SMS - SWE - SW
    Error Propagation (RSS):
        sigma_GWS = sqrt(sigma_TWS^2 + sigma_SMS^2 + sigma_SWE^2 + sigma_SW^2)
    """
    t = np.asarray(time)
    tws_arr = np.asarray(tws, dtype=np.float64)
    tws_e = np.asarray(tws_err, dtype=np.float64)
    sms_arr = np.asarray(sms, dtype=np.float64)
    sms_e = np.asarray(sms_err, dtype=np.float64)

    n = len(t)
    if not (len(tws_arr) == len(tws_e) == len(sms_arr) == len(sms_e) == n):
        raise ValueError("TWS and SMS arrays and their errors must have matching lengths.")

    # Optional SWE (Snow Water Equivalent)
    if swe is not None and swe_err is not None:
        swe_arr = np.asarray(swe, dtype=np.float64)
        swe_e = np.asarray(swe_err, dtype=np.float64)
        if len(swe_arr) != n or len(swe_e) != n:
            raise ValueError("SWE arrays must match time series length.")
    else:
        swe_arr = np.zeros(n, dtype=np.float64)
        swe_e = np.zeros(n, dtype=np.float64)

    # Optional SW (Surface Water)
    if sw is not None and sw_err is not None:
        sw_arr = np.asarray(sw, dtype=np.float64)
        sw_e = np.asarray(sw_err, dtype=np.float64)
        if len(sw_arr) != n or len(sw_e) != n:
            raise ValueError("SW arrays must match time series length.")
    else:
        sw_arr = np.zeros(n, dtype=np.float64)
        sw_e = np.zeros(n, dtype=np.float64)

    # Mass balance subtraction
    gws = tws_arr - sms_arr - swe_arr - sw_arr

    # Root-sum-square error propagation
    gws_err = np.sqrt(tws_e**2 + sms_e**2 + swe_e**2 + sw_e**2)

    # Linear trend estimation (assuming time can be converted to numeric years)
    if pd.api.types.is_datetime64_any_dtype(t):
        numeric_time = pd.to_datetime(t).astype("int64") / 1e9 / (365.25 * 24 * 3600)
    else:
        numeric_time = np.asarray(t, dtype=np.float64)

    res = linregress(numeric_time, gws)
    trend_annual = float(res.slope)
    p_val = float(res.pvalue)

    df = pd.DataFrame(
        {
            "time": t,
            "tws": tws_arr,
            "sms": sms_arr,
            "swe": swe_arr,
            "sw": sw_arr,
            "gws_anomaly": gws,
            "gws_uncertainty": gws_err,
        }
    )

    return MassBalanceResult(
        time=t,
        gws_anomaly=gws,
        gws_uncertainty=gws_err,
        trend_mm_per_year=trend_annual,
        trend_p_value=p_val,
        summary_table=df,
    )
