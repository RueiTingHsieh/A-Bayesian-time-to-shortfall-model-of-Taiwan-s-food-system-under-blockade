"""Vectorised daily stock-flow simulator of Taiwan's food system under blockade.

State (per capita, kcal):
    S_rice  rice in the system (public + private + pipeline)
    S_imp   imported storables in the pipeline (wheat, soy, oils, sugar, dairy...)
    S_house household + retail pantry (all foods)
    S_frz   cold-stored meat (normal inventory + slaughter pulses)
    S_sp    surge-planted sweet potato
    S_div   feed grain diverted to human food (feed-to-food lever)
    S_feed  feed grain for livestock (raw energy units)
    herd    livestock herd relative to normal

Each day: exogenous factors (arrivals, energy, input shortages) -> production and
arrivals -> demand (with or without rationing) -> consumption -> losses.
Endurance T is the first day on which the food system cannot provide the minimum
requirement (energy) or on which the 30-day mean protein intake falls below need.
T is right-censored at the horizon (365 days).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .data import (Base, CROP1_GROWTH_DAYS, CROP1_HARVEST, CROP2_GROWTH_DAYS, CROP2_HARVEST,
                   DAYS_PER_MONTH, SWEET_POTATO_KCAL_PER_KG, rice_stock_months)

HORIZON = 365
# electricity mix after the 2025 nuclear shutdown (EIA 2026 for 2024: gas 43%, coal 40%,
# nuclear 4%, renewables 13%, oil/other 3%); nuclear share reassigned to gas.
MIX_GAS, MIX_COAL, MIX_REN, MIX_OIL = 0.46, 0.40, 0.13, 0.01


@dataclass(frozen=True)
class Levers:
    name: str = "Baseline"
    rationing: bool = False
    feed2food: bool = False
    surge: bool = False
    rice_plus3: bool = False
    dispersed: bool = False
    convoy: bool = False


LEVERS = {
    "baseline": Levers("Baseline"),
    "rationing": Levers("Tiered rationing", rationing=True),
    "feed2food": Levers("Feed-to-food", feed2food=True),
    "surge": Levers("Surge planting", surge=True),
    "rice_plus3": Levers("+3-month rice reserve", rice_plus3=True),
    "dispersed": Levers("Dispersed storage", dispersed=True),
    "convoy": Levers("Grain convoys", convoy=True),
    "civil_package": Levers("Civil package", rationing=True, feed2food=True, surge=True, dispersed=True),
    "full_package": Levers("Civil package + convoys", rationing=True, feed2food=True, surge=True,
                           dispersed=True, convoy=True),
}

T_RATION = 7        # days to activate rationing via the distribution stations
T_FEED2FOOD = 10    # day the planned destocking / feed diversion starts
T_CONVOY = 14       # days to organise escorted grain convoys
SURGE_WINDOW = (10, 40)
ADHOC_TRIGGER_DAYS = 30   # unplanned feed diversion once food stocks < 30 days


def _phi_t(t, phi):
    """Arrivals ramp: ships already at sea arrive during the first 3 days."""
    t = np.asarray(t, dtype=float)
    return np.where(t < 3, 1 - (1 - phi) * (t / 3.0), phi)


class Exogenous:
    """Closed-form exogenous factors (independent of food stocks)."""

    def __init__(self, P: dict):
        self.P = P
        phi = P["phi"]
        denom = np.maximum(1 - phi, 1e-3)
        self.t_gas = P["D_gas"] / denom
        self.t_coal = P["D_coal"] / denom
        self.t_oil = P["D_oil"] / denom

    def energy(self, t):
        P = self.P
        ph = _phi_t(t, P["phi"])
        G = np.where(t < self.t_gas, 1.0, ph)
        C = np.where(t < self.t_coal, 1.0, ph)
        O = np.where(t < self.t_oil, 1.0, ph)
        E = MIX_REN + MIX_GAS * G + MIX_COAL * C + MIX_OIL * O
        O_ag = O + (1 - O) * P["pi_o"]
        return E, O_ag

    def m_crop(self, t):
        P = self.P
        E, O_ag = self.energy(t)
        ph = _phi_t(t, P["phi"])
        fert = np.where(t < P["d_fert"], 1.0, 1 - P["a_f"] * (1 - ph))
        return np.clip(1 - P["a_c"] * (1 - O_ag) - P["a_e"] * (1 - E), 0.1, 1.0) * fert


def feed_conversion(base: Base, P: dict):
    """Edible share and protein density of feed if diverted to people."""
    f = base.feed_items.set_index("feed_item")
    kc, pr = f["kcal_pc_day_raw"], f["protein_pc_day_raw"]
    eta = {"corn_feed": P["eta_corn"], "soybean_meal": P["eta_meal"],
           "soybean_feed": 0.8, "wheat_feed": 0.9}
    kcal_edible = sum(kc[i] * eta[i] for i in eta)
    prot_edible = sum(pr[i] * eta[i] for i in eta)
    eta_mix = kcal_edible / base.feed_raw_kcal
    rho_div = prot_edible / kcal_edible
    return eta_mix, rho_div


def simulate(base: Base, P: dict, lev: Levers, horizon: int = HORIZON, record: int = 0,
             flows: bool = False) -> dict:
    """Run the model for all parameter draws in P (dict of arrays of equal length).

    Returns dict with T (days; np.inf if no shortfall within horizon), event (0 none,
    1 energy, 2 protein) and, if record > 0, weekly stock trajectories (days of minimum
    requirement) for the first `record` draws."""
    n = len(P["phi"])
    K = base.pool_kcal
    rho = {k: base.rho(k) for k in K}
    X = Exogenous(P)
    ones = np.ones(n)

    # ---- requirements and demand ---------------------------------------------------
    m_req = (P["m_civ"] * (1 - P["s_mil"]) + P["m_mil"] * P["s_mil"]) / (1 - P["w"])
    p_req = P["p_min"] / (1 - P["w"])
    c_base = P["beta"] * base.total_kcal

    # ---- initial stocks --------------------------------------------------------------
    doy0 = np.floor(P["onset_doy"]) % 365
    rice_month = base.rice_consumption * DAYS_PER_MONTH
    S_rice = rice_stock_months(doy0, P["rice_trough"], base) * rice_month
    if lev.rice_plus3:
        S_rice = S_rice + 3 * rice_month
    S_imp = P["m_imp"] * (K["IMP_BULK"] + K["IMP_OTHER"]) * DAYS_PER_MONTH
    S_house = P["d_house"] * base.total_kcal
    S_frz = P["m_frz"] * base.meat_kcal * DAYS_PER_MONTH
    S_feed = P["d_feed"] * base.feed_raw_kcal
    S_sp = np.zeros(n)
    S_div = np.zeros(n)
    herd = ones.copy()

    eta_mix, rho_div = feed_conversion(base, P)
    rho_imp = (K["IMP_BULK"] * rho["IMP_BULK"] + K["IMP_OTHER"] * rho["IMP_OTHER"]) / (K["IMP_BULK"] + K["IMP_OTHER"])
    rho_house = base.total_protein / base.total_kcal
    rho_frz = 0.070
    rho_sp = 0.0116
    # protein densities of the proportional-draw pools (house, imp, rice, sp, div)
    rho_pools = np.stack([np.full(n, rho_house), np.full(n, rho_imp), np.full(n, rho["RICE"]),
                          np.full(n, rho_sp), rho_div])

    # surge sweet potato: energy per capita if the whole area is harvested at full yield
    sp_total = P["A_sp"] * P["Y_sp"] * 1e3 * SWEET_POTATO_KCAL_PER_KG / base.population
    sp_daily = sp_total / (SURGE_WINDOW[1] - SURGE_WINDOW[0] + 1)
    lag = np.round(P["lag_sp"])

    lam_s = P["lam_s"] * (P["disp"] if lev.dispersed else 1.0)
    t_strike = np.round(P["t_s"])

    T = np.full(n, np.inf)
    event = np.zeros(n, dtype=np.int8)
    adhoc = np.zeros(n, dtype=bool)
    prot_buf = np.zeros((30, n))
    prot_sum = np.zeros(n)
    rec = {"t": [], "stock_days": [], "intake": []} if record else None
    fl = ({"Pp": [], "Pp_crop": [], "rice_in": [], "other_in": [], "stor_crop": [], "sp_in": [],
           "keep": [], "D": []} if flows else None)
    init = {"S_rice0": S_rice.copy(), "S_other0": (S_imp + S_house + S_frz).copy()}

    crops = [(CROP1_HARVEST, base.crop1_kcal_pc, CROP1_GROWTH_DAYS),
             (CROP2_HARVEST, base.crop2_kcal_pc, CROP2_GROWTH_DAYS)]

    for t in range(horizon):
        doy = (doy0 + t) % 365
        ph = _phi_t(t, P["phi"])
        ph_bulk = np.maximum(ph, P["g"]) if (lev.convoy and t >= T_CONVOY) else ph
        E, O_ag = X.energy(t)
        mc = X.m_crop(t)
        m_fish = P["f_s"] * (1 - P["a_o"] * (1 - O_ag))
        loss_p = P["lam_c"] * (1 - E)
        m_harv = 1 - P["a_h"] * (1 - np.minimum(O_ag, E))

        # ---- one-off events ---------------------------------------------------------
        hit = (t == t_strike)
        keep = np.ones(n)
        if hit.any():
            keep = np.where(hit, 1 - lam_s, 1.0)
            S_rice, S_imp, S_frz, S_feed, S_div, S_sp = (S_rice * keep, S_imp * keep, S_frz * keep,
                                                         S_feed * keep, S_div * keep, S_sp * keep)
        pre_other = S_imp + S_sp + S_div + S_frz
        if lev.feed2food and t == T_FEED2FOOD:
            cut = P["delta"]
            S_frz = S_frz + P["eps_cold"] * cut * herd * P["B_live"]
            herd = herd * (1 - cut)
            moved = S_feed * cut
            S_feed = S_feed - moved
            S_div = S_div + moved * eta_mix

        # ---- feed and livestock -------------------------------------------------------
        feed_arr = base.feed_raw_kcal * ph_bulk
        if lev.feed2food and t >= T_FEED2FOOD:
            div = P["delta"] * ones
            eff = eta_mix
        else:
            div = adhoc.astype(float)
            eff = 0.5 * eta_mix
        S_div = S_div + feed_arr * div * eff
        if (not lev.feed2food) and adhoc.any():
            # unplanned diversion: remaining feed stock goes to people at half efficiency
            S_div = S_div + np.where(adhoc, S_feed * 0.5 * eta_mix, 0.0)
            S_feed = np.where(adhoc, 0.0, S_feed)
        avail_feed = S_feed + feed_arr * (1 - div)
        need = herd * base.feed_raw_kcal
        fed = np.minimum(avail_feed, need)
        if not lev.feed2food:
            fed = np.where(adhoc, 0.0, fed)
        S_feed = avail_feed - fed
        live_out = K["LIVESTOCK"] * fed / base.feed_raw_kcal
        under = np.where(need > 1e-9, 1 - fed / np.maximum(need, 1e-9), 0.0)
        herd_loss = herd * under * P["r_die"]
        S_frz = S_frz + herd_loss * P["B_live"] * P["eps_distress"]
        herd = herd - herd_loss

        # ---- storable inflows -----------------------------------------------------------
        rice_h = np.zeros(n)
        for (a, b), total, growth in crops:
            in_win = (doy >= a) & (doy < b)
            if not in_win.any():
                continue
            t_plant = t - growth
            ym = 1.0 if t_plant < 0 else X.m_crop(np.full(n, t_plant + growth / 2.0))
            rice_h = rice_h + in_win * (total / (b - a)) * ym
        S_rice = S_rice + rice_h * m_harv
        stor_crop = K["DOM_STOR"] * mc
        S_imp = S_imp + K["IMP_BULK"] * ph_bulk + K["IMP_OTHER"] * ph + stor_crop
        sp_gain = np.zeros(n)
        if lev.surge:
            t_p = t - lag
            planted_today_cohort = (t_p >= SURGE_WINDOW[0]) & (t_p <= SURGE_WINDOW[1])
            if planted_today_cohort.any():
                ym = X.m_crop(t_p + lag / 2.0)
                sp_gain = planted_today_cohort * sp_daily * ym * m_harv
                S_sp = S_sp + sp_gain

        other_in = S_imp + S_sp + S_div + S_frz - pre_other

        # ---- perishables ------------------------------------------------------------------
        dom_p = K["DOM_PERISH"] * mc
        fish = K["FISH"] * m_fish
        imp_p = K["IMP_PERISH"] * ph
        keep_p = 1 - loss_p
        Pp = (dom_p + fish + live_out + imp_p) * keep_p
        Pp_prot = (dom_p * rho["DOM_PERISH"] + fish * rho["FISH"] + live_out * rho["LIVESTOCK"]
                   + imp_p * rho["IMP_PERISH"]) * keep_p

        # ---- demand -----------------------------------------------------------------------
        rationed = lev.rationing and t >= T_RATION
        D = P["kappa"] * m_req + (1 - P["kappa"]) * c_base if rationed else c_base

        pools = np.stack([S_house, S_imp, S_rice, S_sp, S_div])
        St = pools.sum(axis=0) + S_frz
        A = Pp + St
        alive = ~np.isfinite(T)
        fail = alive & (A < m_req)
        T[fail] = t
        event[fail] = 1

        # ---- consumption --------------------------------------------------------------------
        C = np.minimum(D, A)
        e_p = np.minimum(Pp, C)
        rem = C - e_p
        e_f = np.minimum(S_frz, rem)
        S_frz = S_frz - e_f
        rem = rem - e_f
        tot = pools.sum(axis=0)
        take = np.minimum(rem, tot)
        frac = np.divide(take, tot, out=np.zeros(n), where=tot > 0)
        drawn = pools * frac
        pools = pools - drawn
        prot = (np.divide(e_p * Pp_prot, Pp, out=np.zeros(n), where=Pp > 0) + e_f * rho_frz
                + (drawn * rho_pools).sum(axis=0))
        # preserve a little of the perishable surplus (drying, pickling)
        pools[0] = pools[0] + 0.1 * np.maximum(Pp - e_p, 0)

        # ---- losses ---------------------------------------------------------------------------
        if t < 14 and not rationed:
            waste = P["panic"] * c_base * 0.5
            sub = pools[0] + pools[1]
            w_take = np.minimum(waste, sub)
            wf = np.divide(w_take, sub, out=np.zeros(n), where=sub > 0)
            pools[0] = pools[0] * (1 - wf)
            pools[1] = pools[1] * (1 - wf)
        S_house, S_imp, S_rice, S_sp, S_div = pools
        S_frz = S_frz * (1 - P["r0"] * (1 - E))
        S_sp = S_sp * 0.997
        S_div = S_div * 0.9995

        # ---- protein (30-day mean) ------------------------------------------------------------
        slot = t % 30
        prot_sum = prot_sum - prot_buf[slot] + prot
        prot_buf[slot] = prot
        if t >= 29:
            alive = ~np.isfinite(T)
            pfail = alive & (prot_sum / 30.0 < p_req)
            T[pfail] = t
            event[pfail] = 2

        # ---- unplanned feed diversion trigger (baseline behaviour) ----------------------------------
        if not lev.feed2food:
            stock_days = (S_house + S_imp + S_rice + S_sp + S_div + S_frz) / m_req
            adhoc = adhoc | (stock_days < ADHOC_TRIGGER_DAYS)

        if flows:
            fl["Pp"].append(Pp); fl["Pp_crop"].append(dom_p * keep_p)
            fl["rice_in"].append(rice_h * m_harv); fl["other_in"].append(other_in)
            fl["stor_crop"].append(stor_crop * ones); fl["sp_in"].append(sp_gain)
            fl["keep"].append(keep); fl["D"].append(D * ones)
        if record and (t % 7 == 0):
            sd = (S_house + S_imp + S_rice + S_sp + S_div + S_frz) / m_req
            rec["t"].append(t)
            rec["stock_days"].append(sd[:record].copy())
            rec["intake"].append((C / m_req)[:record].copy())

    out = {"T": T, "event": event, "m_req": m_req}
    if flows:
        out["flows"] = {k: np.array(v) for k, v in fl.items()}
        out["init"] = init
    if record:
        out["traj_t"] = np.array(rec["t"])
        out["traj_stock_days"] = np.array(rec["stock_days"])
        out["traj_intake"] = np.array(rec["intake"])
    return out


def endurance(res: dict, horizon: int = HORIZON) -> np.ndarray:
    """Endurance truncated at the horizon (for RMST and paired differences)."""
    return np.minimum(res["T"], horizon)
