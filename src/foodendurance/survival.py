"""Time-to-event tools written from scratch (no lifelines dependency).

Endurance T is right-censored at the simulation horizon tau (administrative censoring),
so RMST(tau) = E[min(T, tau)] exactly; the Kaplan-Meier curve reduces to the empirical
survival function but the estimator below handles general censoring for reuse.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize


def km(T: np.ndarray, tau: float = 365.0):
    """Kaplan-Meier estimate. T = np.inf means 'no event within the horizon'.
    Returns (times, survival) as step-function knots starting at (0, 1)."""
    T = np.asarray(T, dtype=float)
    event = np.isfinite(T) & (T <= tau)
    time = np.where(event, T, tau)
    order = np.argsort(time, kind="mergesort")
    time, event = time[order], event[order]
    uniq = np.unique(time[event])
    at_risk = len(time) - np.searchsorted(time, uniq, side="left")
    d = np.array([np.sum((time == u) & event) for u in uniq])
    s = np.cumprod(1 - d / at_risk)
    return np.concatenate([[0.0], uniq]), np.concatenate([[1.0], s])


def km_at(times, surv, t):
    idx = np.searchsorted(times, t, side="right") - 1
    return surv[np.clip(idx, 0, len(surv) - 1)]


def median_survival(T, tau=365.0):
    times, s = km(T, tau)
    below = np.where(s <= 0.5)[0]
    return float(times[below[0]]) if len(below) else np.inf


def rmst(T, tau=365.0):
    return float(np.mean(np.minimum(T, tau)))


def summarise(T, event=None, tau=365.0) -> dict:
    T = np.asarray(T, dtype=float)
    Tt = np.minimum(T, tau)
    out = {
        "n": len(T),
        "median": median_survival(T, tau),
        "rmst": rmst(T, tau),
        "p_gt_90": float(np.mean(T > 90)),
        "p_gt_180": float(np.mean(T > 180)),
        "p_gt_270": float(np.mean(T > 270)),
        "p_survive_year": float(np.mean(~np.isfinite(T) | (T >= tau))),
        "q10": float(np.quantile(Tt, 0.10)),
        "q25": float(np.quantile(Tt, 0.25)),
        "q75": float(np.quantile(Tt, 0.75)),
        "q90": float(np.quantile(Tt, 0.90)),
    }
    if event is not None:
        out["share_protein_events"] = float(np.mean(np.asarray(event) == 2))
    return out


# ------------------------------------------------------------------------------------------
# Weibull accelerated failure time model:  log T = mu + x'b + sigma * W,  W ~ Gumbel(min)
# ------------------------------------------------------------------------------------------
def weibull_aft(T: np.ndarray, X: np.ndarray, names: list[str], tau: float = 365.0) -> pd.DataFrame:
    """Fit by maximum likelihood with right-censoring at tau. Returns time ratios exp(b)
    with Wald 95% intervals. X should not contain an intercept."""
    T = np.asarray(T, dtype=float)
    event = np.isfinite(T) & (T < tau)
    t = np.log(np.clip(np.where(event, T, tau), 0.5, None))
    X = np.asarray(X, dtype=float)
    n, k = X.shape

    def nll(theta):
        mu, b, log_s = theta[0], theta[1:k + 1], theta[-1]
        s = np.exp(log_s)
        z = (t - mu - X @ b) / s
        ez = np.exp(np.clip(z, -50, 50))
        ll = np.where(event, -log_s + z - ez, -ez)
        return -ll.sum()

    def grad(theta):
        mu, b, log_s = theta[0], theta[1:k + 1], theta[-1]
        s = np.exp(log_s)
        z = (t - mu - X @ b) / s
        ez = np.exp(np.clip(z, -50, 50))
        # d ll / d z
        dz = np.where(event, 1 - ez, -ez)
        g_mu = -(dz / s).sum()
        g_b = -(X * (dz / s)[:, None]).sum(axis=0)
        g_ls = (np.where(event, -1.0, 0.0) - dz * z).sum()
        return -np.concatenate([[g_mu], g_b, [g_ls]])

    theta0 = np.concatenate([[t.mean()], np.zeros(k), [np.log(t.std() + 1e-3)]])
    res = minimize(nll, theta0, jac=grad, method="L-BFGS-B", options={"maxiter": 5000, "ftol": 1e-12, "gtol": 1e-8})
    theta = res.x
    # observed information via numerical Hessian of the gradient
    eps = 1e-5
    H = np.zeros((len(theta), len(theta)))
    for i in range(len(theta)):
        e = np.zeros(len(theta)); e[i] = eps
        H[:, i] = (grad(theta + e) - grad(theta - e)) / (2 * eps)
    cov = np.linalg.pinv((H + H.T) / 2)
    se = np.sqrt(np.clip(np.diag(cov), 0, None))
    b, se_b = theta[1:k + 1], se[1:k + 1]
    return pd.DataFrame({
        "term": names,
        "coef": b,
        "time_ratio": np.exp(b),
        "tr_lo95": np.exp(b - 1.96 * se_b),
        "tr_hi95": np.exp(b + 1.96 * se_b),
        "sigma": np.exp(theta[-1]),
        "converged": res.success,
    })
