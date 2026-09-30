"""Prior distributions for every uncertain input, and the three blockade scenarios.

Each prior carries its source or the reason it is an assumption. Anything marked
"assumption" is a candidate for expert elicitation (SHELF) or official data (see README).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Prior:
    name: str
    lo: float
    hi: float
    dist: str = "uniform"     # "uniform" or "beta" (beta uses mean=lo, sd=hi)
    source: str = "assumption"
    note: str = ""

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        if self.dist == "uniform":
            return rng.uniform(self.lo, self.hi, n)
        if self.dist == "beta":
            m, s = self.lo, self.hi
            k = m * (1 - m) / s**2 - 1
            return rng.beta(m * k, (1 - m) * k, n)
        raise ValueError(self.dist)

    def bounds(self) -> tuple[float, float]:
        """Uniform bounds used for Sobol analysis (beta -> its 5-95% range)."""
        if self.dist == "uniform":
            return self.lo, self.hi
        m, s = self.lo, self.hi
        k = m * (1 - m) / s**2 - 1
        from scipy.stats import beta
        return tuple(beta(m * k, (1 - m) * k).ppf([0.05, 0.95]))


# --------------------------------------------------------------------------------------
# Common priors (all scenarios)
# --------------------------------------------------------------------------------------
COMMON = [
    # demand side
    Prior("beta", 0.90, 1.00, source="assumption", note="unrationed consumption as share of normal FBS supply"),
    Prior("m_civ", 2000, 2200, source="Sphere Handbook 2018 (2,100 kcal planning figure) +/-5%", note="civilian minimum intake, kcal/day"),
    Prior("m_mil", 3000, 3600, source="assumption (field ration standards)", note="mobilised personnel intake, kcal/day"),
    Prior("s_mil", 0.013, 0.039, source="Legislative Yuan 2024: 710,569 mobilisable reservists + active force", note="share of population in uniform"),
    Prior("w", 0.05, 0.12, source="assumption", note="distribution + household losses under rationing"),
    Prior("p_min", 40, 50, source="FAO/WHO/UNU 2007 safe protein level (~0.83 g/kg)", note="population-average protein need, g/day"),
    Prior("panic", 0.0, 0.15, source="assumption (COVID-19 panic buying)", note="extra drawdown in first 14 days, share of demand"),
    # stocks at onset
    Prior("rice_trough", 4.0, 6.5, source="MOA Mar 2025: public stocks 5.5 months; 8-9 after harvest; ~1 year incl. private", note="total rice stock on 1 June, months of use"),
    Prior("m_imp", 1.0, 2.5, source="assumption; USDA FAS: grain arrives monthly (5 corn, 2.5 soy, 1.5 wheat vessels/month)", note="imported storables in the pipeline, months"),
    Prior("d_house", 5, 14, source="assumption", note="household + retail pantry, days of normal diet"),
    Prior("m_frz", 0.5, 1.5, source="assumption", note="cold-store meat inventory, months of meat use"),
    Prior("d_feed", 30, 60, source="assumption; limited silo capacity (USDA FAS)", note="feed grain stocks, days of feed use"),
    Prior("B_live", 25000, 38000, source="MOA: 5.24 M pigs (May 2023), 126.9 kg carcass; poultry standing stock", note="edible energy in standing herds, kcal/person"),
    Prior("r_die", 0.01, 0.03, source="assumption", note="daily herd loss per unit feed shortfall"),
    Prior("eps_distress", 0.1, 0.4, source="assumption", note="share of distress-slaughter meat that is eaten"),
    # energy (CSIS 2025: gas ~10 days, coal ~7 weeks, oil ~20 weeks without resupply)
    Prior("D_gas", 9, 12, source="CSIS Lights Out? (2025) p.xii; MOEA 2026 via EIA (10-11 days)", note="LNG stock, days"),
    Prior("D_coal", 42, 56, source="CSIS Lights Out? (2025): ~7 weeks", note="coal stock, days"),
    Prior("D_oil", 120, 160, source="CSIS Lights Out? (2025): ~20 weeks", note="oil stock, days"),
    Prior("pi_o", 0.0, 0.3, source="assumption", note="share of fuel shortfall shielded for agri-food"),
    Prior("a_c", 0.3, 0.6, source="assumption", note="crop output sensitivity to fuel shortage"),
    Prior("a_e", 0.05, 0.2, source="assumption", note="crop output sensitivity to power shortage (pumps, cold chain)"),
    Prior("a_f", 0.10, 0.35, source="assumption", note="yield loss per unit fertilizer import shortfall"),
    Prior("d_fert", 60, 180, source="assumption", note="fertilizer stocks, days"),
    Prior("a_o", 0.4, 0.8, source="assumption", note="fishing sensitivity to fuel shortage"),
    Prior("a_h", 0.1, 0.4, source="assumption", note="harvest/drying/milling sensitivity to fuel & power"),
    Prior("lam_c", 0.2, 0.6, source="assumption", note="perishable loss per unit power shortfall (cold chain)"),
    Prior("r0", 0.01, 0.05, source="assumption", note="daily frozen-stock decay per unit power shortfall"),
    # blockade onset (any day of the year)
    Prior("onset_doy", 0, 365, source="design", note="day of year the blockade begins"),
    Prior("t_s", 3, 30, source="assumption", note="day of strikes on ports/warehouses"),
    # policy levers
    Prior("kappa", 0.75, 0.95, source="assumption", note="rationing compliance"),
    Prior("delta", 0.5, 0.8, source="assumption", note="herd reduction under planned feed-to-food"),
    Prior("eta_corn", 0.6, 0.9, source="assumption", note="edible yield when feed corn is milled for people"),
    Prior("eta_meal", 0.3, 0.6, source="assumption", note="edible yield of soybean meal as food"),
    Prior("eps_cold", 0.6, 0.9, source="assumption", note="share of planned-slaughter meat preserved"),
    Prior("A_sp", 20000, 60000, source="assumption; 10-30% of paddy land not in rice (188k ha in 1st-crop, 263k ha in 2nd-crop season: DGBAS 2024 paddy area minus AFA 2025 rice area)", note="surge sweet-potato area, ha"),
    Prior("Y_sp", 12, 22, source="MOA county yields 2019: 10-25 t/ha", note="surge sweet-potato yield, t/ha"),
    Prior("lag_sp", 120, 165, source="MOA sweet-potato calendar (4-6 months)", note="planting-to-harvest, days"),
    Prior("g", 0.3, 0.6, source="assumption; CSIS: escorted convoys kept Taiwan supplied", note="guaranteed bulk-grain arrival with convoys"),
    Prior("disp", 0.2, 0.4, source="assumption", note="strike-loss multiplier with dispersed storage"),
]

# --------------------------------------------------------------------------------------
# Scenario-specific priors
#   phi   : share of normal seaborne arrivals that reach Taiwan (food, feed, fuel)
#   f_s   : fishing activity factor
#   lam_s : one-off share of stored food/feed destroyed by strikes
# --------------------------------------------------------------------------------------
SCENARIOS = {
    "S1": {
        "label_en": "Quarantine (coast-guard inspections)",
        "label_zh": "海警隔離（臨檢）",
        "short_en": "Quarantine", "short_zh": "隔離",
        "priors": [
            Prior("phi", 0.75, 0.08, dist="beta", source="CSIS 2025: boarding-only blockade - most merchant traffic continued"),
            Prior("f_s", 0.85, 1.0, source="assumption"),
            Prior("lam_s", 0.0, 0.0, source="no kinetic strikes"),
        ],
    },
    "S2": {
        "label_en": "Military blockade (submarines & mines)",
        "label_zh": "軍事封鎖（潛艦與水雷）",
        "short_en": "Blockade", "short_zh": "封鎖",
        "priors": [
            Prior("phi", 0.35, 0.08, dist="beta", source="CSIS 2025: without U.S. intervention 40% of inbound ships destroyed; plus deterred sailings"),
            Prior("f_s", 0.35, 0.70, source="assumption"),
            Prior("lam_s", 0.0, 0.10, source="assumption"),
        ],
    },
    "S3": {
        "label_en": "Total isolation + energy shock",
        "label_zh": "全面孤立＋能源衝擊",
        "short_en": "Isolation", "short_zh": "孤立",
        "priors": [
            Prior("phi", 0.06, 0.03, dist="beta", source="assumption: near-total interdiction"),
            Prior("f_s", 0.20, 0.50, source="assumption"),
            Prior("lam_s", 0.03, 0.20, source="assumption"),
        ],
    },
}


def priors_for(scenario: str) -> list[Prior]:
    return COMMON + SCENARIOS[scenario]["priors"]


def sample(n: int, scenario: str, seed: int = 2026, fixed: dict | None = None) -> dict:
    """Draw n parameter vectors. The same seed gives the same draws for every lever
    (common random numbers), so lever effects are paired comparisons."""
    rng = np.random.default_rng(seed)
    out = {p.name: p.sample(n, rng) for p in priors_for(scenario)}
    if fixed:
        for k, v in fixed.items():
            out[k] = np.full(n, float(v)) if np.isscalar(v) else np.asarray(v, dtype=float)
    return out


# Parameters varied in the Sobol analysis (lever parameters excluded for the baseline run)
SOBOL_EXCLUDE = {"kappa", "delta", "eta_corn", "eta_meal", "eps_cold", "A_sp", "Y_sp", "lag_sp", "g", "disp"}


def sobol_problem(scenario: str, include_levers: bool = False) -> dict:
    ps = [p for p in priors_for(scenario) if (include_levers or p.name not in SOBOL_EXCLUDE)]
    ps = [p for p in ps if p.bounds()[1] > p.bounds()[0]]
    return {"num_vars": len(ps), "names": [p.name for p in ps], "bounds": [list(p.bounds()) for p in ps]}


def sobol_params(X: np.ndarray, problem: dict, scenario: str, seed: int = 7) -> dict:
    """Parameter dict from a Sobol design matrix; parameters not in the design are drawn
    from their priors (they are not attributed any variance)."""
    n = X.shape[0]
    P = sample(n, scenario, seed=seed)
    for j, name in enumerate(problem["names"]):
        P[name] = X[:, j]
    return P


def prior_table() -> pd.DataFrame:
    rows = []
    for p in COMMON:
        rows.append({"parameter": p.name, "scenario": "all", "dist": p.dist, "lo_or_mean": p.lo,
                     "hi_or_sd": p.hi, "source": p.source, "note": p.note})
    for s, d in SCENARIOS.items():
        for p in d["priors"]:
            rows.append({"parameter": p.name, "scenario": s, "dist": p.dist, "lo_or_mean": p.lo,
                         "hi_or_sd": p.hi, "source": p.source, "note": p.note})
    return pd.DataFrame(rows)
