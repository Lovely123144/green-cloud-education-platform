"""Carbon-aware scheduler: choose WHEN (and optionally WHERE) to run a delay-tolerant job."""
import math
import numpy as np


def best_start(forecast, now_idx: int, duration_h: float, deadline_h: float) -> int:
    """Start hour index (within [now, now+deadline-duration]) minimising the mean
    forecast intensity over the run. Ties -> earliest start."""
    dur = max(1, math.ceil(duration_h))
    last = int(now_idx + max(0, math.floor(deadline_h - dur)))
    best, best_i = float("inf"), now_idx
    for s in range(int(now_idx), last + 1):
        m = float(np.mean(forecast[s:s + dur]))
        if m < best - 1e-12:
            best, best_i = m, s
    return best_i


def best_region_start(forecasts: dict, now_idx, duration_h, deadline_h,
                      allowed=None, move_penalty_g_per_kwh=0.0, home=None):
    """Spatio-temporal choice. Returns (region, start_idx). A penalty (g/kWh equivalent)
    is added to non-home regions to account for data-transfer emissions."""
    dur = max(1, math.ceil(duration_h))
    best = (float("inf"), home, now_idx)
    for r, f in forecasts.items():
        if allowed is not None and r not in allowed:
            continue
        s = best_start(f, now_idx, duration_h, deadline_h)
        m = float(np.mean(f[s:s + dur])) + (move_penalty_g_per_kwh if r != home else 0.0)
        if m < best[0] - 1e-12:
            best = (m, r, s)
    return best[1], best[2]
