"""County-level extension (RQ2: where does food run out first?).

The national simulation supplies the daily flows (perishables, rice harvest, other storable
inflows, strike losses, demand). They are allocated to the 22 counties/cities:

    rice harvest       -> county share of 2025 1st/2nd-crop production (AFA survey)
    domestic crops     -> cultivated-area share (DGBAS 2024): vegetables, fruit, sweet potato,
                          sugar, peanuts; local production, so islands keep theirs in full
    surge planting     -> share of paddy land not planted to rice (DGBAS 2024)
    other flows        -> population share (imports, fish, livestock products, diverted feed)
    initial rice stock -> 50% population share, 50% production share (assumption)
    other stocks       -> population share (dispersed storage, per MOA)

Counties that run short can receive transfers from counties with surplus, limited per day to
tau x their demand (tau = transport capacity under blockade conditions):
    west-coast corridor  tau ~ U(0.60, 0.95)
    east coast           tau ~ U(0.30, 0.80)   (Suhua / South-Link corridors)
    outlying islands     tau ~ U(0.00, 0.30)   (sea/air links under blockade); islands also
                                              receive national flows only in proportion to tau
Exporters keep a 7-day buffer of their own minimum requirement.
"""
from __future__ import annotations

import numpy as np

from .data import Base, CROP1_HARVEST, CROP2_HARVEST

TAU = {"west": (0.60, 0.95), "east": (0.30, 0.80), "island": (0.00, 0.30)}
# "transport disruption" variant: corridors damaged / fuel rationed
TAU_DISRUPTED = {"west": (0.30, 0.60), "east": (0.10, 0.40), "island": (0.00, 0.15)}
KEEP_DAYS = 7


def sample_tau(n: int, regions: np.ndarray, seed: int = 11, ranges: dict | None = None) -> np.ndarray:
    rng = np.random.default_rng(seed)
    tau = np.zeros((n, len(regions)))
    for reg, (lo, hi) in (ranges or TAU).items():
        base = rng.uniform(lo, hi, n)[:, None]
        cols = regions == reg
        jitter = rng.uniform(-0.05, 0.05, (n, cols.sum()))
        tau[:, cols] = np.clip(base + jitter, 0, 1)
    return tau


def simulate_counties(base: Base, P: dict, nat: dict, horizon: int = 365, seed: int = 11,
                      tau_ranges: dict | None = None, island_extra_days: float = 0.0) -> dict:
    """nat = output of model.simulate(..., flows=True). Returns T_c (n x 22).
    island_extra_days: extra pre-positioned stock on outlying islands (days of minimum need)."""
    df = base.county
    F = nat["flows"]
    n = F["Pp"].shape[1]
    regions = df["region"].to_numpy()
    island = regions == "island"
    w = df["pop_share"].to_numpy()
    w_crop = df["crop_share"].to_numpy()
    w_idle = df["idle_share"].to_numpy()
    s1 = df["crop1_share"].to_numpy()
    s2 = df["crop2_share"].to_numpy()
    w_prod = (df["crop1_brown_t"] + df["crop2_brown_t"]).to_numpy()
    w_prod = w_prod / w_prod.sum()
    tau = sample_tau(n, regions, seed, tau_ranges)

    S = (nat["init"]["S_rice0"][:, None] * (0.5 * w + 0.5 * w_prod)[None, :]
         + nat["init"]["S_other0"][:, None] * w[None, :])
    m_req_c = nat["m_req"][:, None] * w[None, :]
    S = S + island_extra_days * m_req_c * island[None, :]
    doy0 = np.floor(P["onset_doy"]) % 365
    flow_scale = np.where(island[None, :], tau, 1.0)   # islands get national flows only via tau

    T = np.full((n, len(w)), np.inf)
    for t in range(horizon):
        doy = ((doy0 + t) % 365)[:, None]
        in1 = (doy >= CROP1_HARVEST[0]) & (doy < CROP1_HARVEST[1])
        rice_share = np.where(in1, s1[None, :], s2[None, :])
        S = S * F["keep"][t][:, None]
        other_nat = F["other_in"][t] - F["stor_crop"][t] - F["sp_in"][t]
        S = (S + (F["rice_in"][t][:, None] * rice_share + other_nat[:, None] * w[None, :]) * flow_scale
             + F["stor_crop"][t][:, None] * w_crop[None, :] + F["sp_in"][t][:, None] * w_idle[None, :])
        Pp = ((F["Pp"][t] - F["Pp_crop"][t])[:, None] * w[None, :] * flow_scale
              + F["Pp_crop"][t][:, None] * w_crop[None, :])
        D = F["D"][t][:, None] * w[None, :]
        A = Pp + S
        # transfers
        need = np.maximum(D - A, 0.0)
        req = np.minimum(need, tau * D)
        surplus = np.maximum(A - D - KEEP_DAYS * m_req_c, 0.0)
        tot_req, tot_sur = req.sum(axis=1), surplus.sum(axis=1)
        moved = np.minimum(tot_req, tot_sur)
        r_in = np.divide(moved, tot_req, out=np.zeros(n), where=tot_req > 0)[:, None] * req
        r_out = np.divide(moved, tot_sur, out=np.zeros(n), where=tot_sur > 0)[:, None] * surplus
        A = A + r_in - r_out
        fail = ~np.isfinite(T) & (A < m_req_c)
        T[fail] = t
        C = np.minimum(D, A)
        eaten_p = np.minimum(Pp, C)
        # perishable surplus that is neither eaten nor shipped out is mostly lost (as in the
        # national model); shipments are assumed to come from the perishable surplus first
        p_left = np.maximum(Pp - eaten_p - r_out, 0.0)
        S = np.maximum(A - C - 0.9 * p_left, 0.0)
    return {"T_c": T, "tau": tau}
