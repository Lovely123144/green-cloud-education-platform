"""Hourly grid carbon-intensity series (gCO2e/kWh) per AWS region.

IMPORTANT: the shapes below are *synthetic but plausible* (a midday solar dip and an
evening ramp on top of a regional base level). They are NOT measured data. For a real
deployment replace `actual_series()` by calls to an intensity API (Electricity Maps,
WattTime, UK Carbon Intensity ...). Base levels are rounded, order-of-magnitude values.
"""
import zlib
import numpy as np

# region: (utc_offset_h, base g/kWh, solar_dip, evening_ramp)
REGIONS = {
    "ap-northeast-1": (9, 480, 0.18, 0.08),    # Tokyo   - gas/coal/nuclear mix
    "us-east-1":      (-5, 380, 0.08, 0.06),   # N. Virginia
    "us-west-2":      (-8, 320, 0.12, 0.10),   # Oregon  - hydro + gas
    "eu-north-1":     (1, 25, 0.10, 0.10),     # Stockholm - hydro/nuclear/wind
}


def _bell(h, mu, sd):
    d = np.minimum(np.abs(h - mu), 24 - np.abs(h - mu))
    return np.exp(-0.5 * (d / sd) ** 2)


def profile_local(region: str, hour_local, amp: float = 1.0):
    _, base, solar, eve = REGIONS[region]
    h = np.asarray(hour_local, dtype=float) % 24
    return base * (1 - amp * solar * _bell(h, 13, 3.0) + amp * eve * _bell(h, 19.5, 2.0))


def actual_series(region: str, n_days: int, seed: int = 0, amp: float = 1.0,
                  noise_sd: float = 0.07, start_utc_hour: int = 0):
    """Hourly series in UTC, with AR(1) day-to-day multiplicative noise."""
    rng = np.random.default_rng(seed + zlib.crc32(region.encode()) % 1000)
    n = n_days * 24
    utc = (np.arange(n) + start_utc_hour) % 24
    local = (utc + REGIONS[region][0]) % 24
    prof = profile_local(region, local, amp)
    eps = np.zeros(n)
    for i in range(1, n):
        eps[i] = 0.9 * eps[i - 1] + rng.normal(0, noise_sd * np.sqrt(1 - 0.81))
    return prof * (1 + eps)


def forecast_from(actual: np.ndarray, err_sd: float, seed: int = 1):
    rng = np.random.default_rng(seed)
    return actual * (1 + rng.normal(0, err_sd, size=actual.shape))
