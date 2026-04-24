"""Growth curve parsing and parameterization for the ENIGMA dataset.

Fits modified Gompertz model to (time, OD) trajectories and derives secondary
metrics: diauxy, cryptic growth, death-phase slope, AUC, QC flags.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import find_peaks, savgol_filter


def gompertz(t, A, mu, lag, od0):
    """Modified Gompertz model (Zwietering et al. 1990).

    OD(t) = od0 + A * exp(-exp((mu * e / A) * (lag - t) + 1))

    A: asymptotic increase (max OD above baseline)
    mu: maximum specific growth rate (per hour)
    lag: duration of lag phase (hours)
    od0: baseline OD at t=0
    """
    with np.errstate(over="ignore", invalid="ignore"):
        exponent = (mu * np.e / A) * (lag - t) + 1.0
        exponent = np.clip(exponent, -50.0, 50.0)
        return od0 + A * np.exp(-np.exp(exponent))


def _initial_guess(t: np.ndarray, od: np.ndarray) -> list[float]:
    od_min = float(np.nanmin(od))
    od_max = float(np.nanmax(od))
    a0 = max(od_max - od_min, 0.01)
    # Smoothed derivative for µmax estimate
    if len(od) >= 9:
        try:
            window = min(len(od) // 4 * 2 + 1, 21)
            od_s = savgol_filter(od, window, 3)
            dod = np.gradient(od_s, t)
        except Exception:
            dod = np.gradient(od, t)
    else:
        dod = np.gradient(od, t)
    mu0 = max(float(np.nanmax(dod)), 1e-3)
    # Lag: first time derivative exceeds 20% of peak
    above = np.where(dod > 0.2 * mu0)[0]
    lag0 = float(t[above[0]]) if len(above) else 0.0
    return [a0, mu0, lag0, od_min]


def fit_curve(
    t: np.ndarray,
    od: np.ndarray,
    min_range: float = 0.05,
    max_iter: int = 2000,
) -> dict:
    """Fit a single growth curve.

    Returns parameter dict with fit + derived metrics + QC flags. Never raises
    on bad data — sets flags to False/NaN instead.
    """
    t = np.asarray(t, dtype=float)
    od = np.asarray(od, dtype=float)

    # Drop NaNs
    finite = np.isfinite(t) & np.isfinite(od)
    t = t[finite]
    od = od[finite]

    out = {
        "n_points": int(len(t)),
        "t_min": float(t.min()) if len(t) else np.nan,
        "t_max": float(t.max()) if len(t) else np.nan,
        "od_min": float(od.min()) if len(od) else np.nan,
        "od_max": float(od.max()) if len(od) else np.nan,
        "od_range": float(od.max() - od.min()) if len(od) else np.nan,
        "A_fit": np.nan,
        "mu_fit": np.nan,
        "lag_fit": np.nan,
        "od0_fit": np.nan,
        "r2": np.nan,
        "rmse": np.nan,
        "auc": np.nan,
        "death_slope": np.nan,
        "n_diauxy_peaks": 0,
        "cryptic_score": np.nan,
        "no_growth": True,
        "monotone_violation": False,
        "fit_ok": False,
        "fit_error": "",
    }

    if len(t) < 10:
        out["fit_error"] = "too_few_points"
        return out

    # Sort by time
    order = np.argsort(t)
    t = t[order]
    od = od[order]

    od_range = float(od.max() - od.min())
    out["od_range"] = od_range
    out["no_growth"] = od_range < min_range

    # AUC via trapezoidal rule
    out["auc"] = float(np.trapz(od, t))

    # Monotone violation: large drops relative to range
    drops = np.maximum(np.maximum.accumulate(od) - od, 0.0)
    out["monotone_violation"] = bool(drops.max() > 0.2 * od_range) if od_range > 0 else False

    # Death-phase slope: slope from max-OD time to final time
    argmax = int(np.argmax(od))
    if argmax < len(od) - 5:
        dt = t[-1] - t[argmax]
        if dt > 0:
            out["death_slope"] = float((od[-1] - od[argmax]) / dt)
        else:
            out["death_slope"] = 0.0
    else:
        out["death_slope"] = 0.0

    # Diauxy: peaks in smoothed derivative
    try:
        window = min(len(od) // 4 * 2 + 1, 31)
        window = max(window, 5)
        od_s = savgol_filter(od, window, 3)
        dod_s = np.gradient(od_s, t)
        # Peaks with minimum prominence = 10% of overall max derivative
        max_deriv = float(np.nanmax(dod_s))
        if max_deriv > 0:
            peaks, _ = find_peaks(dod_s, prominence=0.1 * max_deriv, distance=10)
            out["n_diauxy_peaks"] = int(len(peaks))
    except Exception:
        pass

    # Cryptic growth: fraction of total OD rise that happens after first 80% of it
    try:
        target = od[0] + 0.8 * od_range
        idx_80 = int(np.argmax(od >= target))
        if idx_80 > 0 and idx_80 < len(od) - 1:
            late_rise = od[-1] - od[idx_80]
            out["cryptic_score"] = float(late_rise / (od_range + 1e-9))
    except Exception:
        pass

    if out["no_growth"]:
        out["fit_error"] = "no_growth"
        return out

    # Fit Gompertz
    p0 = _initial_guess(t, od)
    try:
        bounds = (
            [1e-4, 1e-4, 0.0, 0.0],
            [10.0, 5.0, float(t[-1]), 2.0],
        )
        popt, _ = curve_fit(gompertz, t, od, p0=p0, maxfev=max_iter, bounds=bounds)
        pred = gompertz(t, *popt)
        resid = od - pred
        ss_res = float(np.sum(resid ** 2))
        ss_tot = float(np.sum((od - np.mean(od)) ** 2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
        rmse = float(np.sqrt(np.mean(resid ** 2)))
        out["A_fit"] = float(popt[0])
        out["mu_fit"] = float(popt[1])
        out["lag_fit"] = float(popt[2])
        out["od0_fit"] = float(popt[3])
        out["r2"] = r2
        out["rmse"] = rmse
        out["fit_ok"] = bool(r2 > 0.8 and rmse < 0.1 * max(od_range, 0.01))
    except Exception as exc:
        out["fit_error"] = f"fit_failed:{type(exc).__name__}"

    return out


def is_edge_well(well_name: str) -> bool:
    """Return True for outer-row / outer-column wells (A*, H*, *1, *12) on a 96-well plate."""
    if not well_name or len(well_name) < 2:
        return False
    row = well_name[0].upper()
    try:
        col = int(well_name[1:])
    except ValueError:
        return False
    return row in ("A", "H") or col in (1, 12)
