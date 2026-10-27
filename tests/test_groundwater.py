from __future__ import annotations

import numpy as np
import pytest

from groundwater_storage_gravimetry import isolate_groundwater_storage


def test_mass_balance_ideal():
    time = np.array([2020.0, 2020.1, 2020.2])
    tws = np.array([10.0, 5.0, 0.0])
    tws_err = np.array([1.0, 1.0, 1.0])
    sms = np.array([2.0, 1.0, 0.0])
    sms_err = np.array([0.5, 0.5, 0.5])

    res = isolate_groundwater_storage(
        time=time,
        tws=tws,
        tws_err=tws_err,
        sms=sms,
        sms_err=sms_err,
    )

    # GWS = TWS - SMS = [8.0, 4.0, 0.0]
    np.testing.assert_allclose(res.gws_anomaly, [8.0, 4.0, 0.0])
    # Error propagation: sqrt(1.0^2 + 0.5^2) = sqrt(1.25) approx 1.118
    expected_err = np.full(3, np.sqrt(1.25))
    np.testing.assert_allclose(res.gws_uncertainty, expected_err)
    assert res.trend_mm_per_year < 0.0


def test_invalid_lengths_raises():
    with pytest.raises(ValueError, match="must have matching lengths"):
        isolate_groundwater_storage(
            time=[2020.0, 2020.1],
            tws=[10.0],
            tws_err=[1.0, 1.0],
            sms=[2.0, 2.0],
            sms_err=[0.5, 0.5],
        )
