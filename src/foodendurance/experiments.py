"""Experiment grid used in the report. Every function returns tidy pandas DataFrames."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import params as prm
from .county import simulate_counties
from .data import Base, DAYS_PER_MONTH
from .model import HORIZON, LEVERS, simulate
from .survival import km, summarise, weibull_aft

SCEN = ["S1", "S2", "S3"]
LEVER_ORDER = ["baseline", "rationing", "feed2food", "surge", "rice_plus3", "dispersed", "convoy",
               "civil_package", "full_package"]


def run_grid(base: Base, n: int = 5000, seed: int = 2026) -> pd.DataFrame:
    """Scenarios x levers with common random numbers (paired draws)."""
    rows = []
    for s in SCEN:
        P = prm.sample(n, s, seed=seed)
        for lv in LEVER_ORDER:
            r = simulate(base, P, LEVERS[lv])
            rows.append(pd.DataFrame({"scenario": s, "lever": lv, "draw": np.arange(n),
                                      "T": r["T"], "event": r["event"],
                                      "onset_doy": P["onset_doy"], "phi": P["phi"]}))
    return pd.concat(rows, ignore_index=True)


def summary(grid: pd.DataFrame) -> pd.DataFrame:
    out = []
    for (s, lv), g in grid.groupby(["scenario", "lever"], sort=False):
        d = summarise(g["T"].to_numpy(), g["event"].to_numpy())
        d.update({"scenario": s, "lever": lv})
        out.append(d)
    cols = ["scenario", "lever", "median", "rmst", "p_gt_90", "p_gt_180", "p_gt_270", "p_survive_year",
            "q10", "q25", "q75", "q90", "share_protein_events", "n"]
    return pd.DataFrame(out)[cols]


def paired_gains(grid: pd.DataFrame, tau: float = HORIZON) -> pd.DataFrame:
    """Days of endurance gained by each lever vs baseline, draw by draw."""
    out = []
    for s, g in grid.groupby("scenario", sort=False):
        base_T = np.minimum(g[g.lever == "baseline"].sort_values("draw")["T"].to_numpy(), tau)
        for lv in LEVER_ORDER[1:]:
            T = np.minimum(g[g.lever == lv].sort_values("draw")["T"].to_numpy(), tau)
            d = T - base_T
            out.append({"scenario": s, "lever": lv, "mean_gain": d.mean(), "median_gain": np.median(d),
                        "q05": np.quantile(d, 0.05), "q25": np.quantile(d, 0.25),
                        "q75": np.quantile(d, 0.75), "q95": np.quantile(d, 0.95),
                        "p_positive": float(np.mean(d > 0))})
    return pd.DataFrame(out)


def aft_time_ratios(grid: pd.DataFrame, levers=None) -> pd.DataFrame:
    """Weibull AFT per scenario: log T ~ lever dummies (baseline = reference)."""
    levers = levers or ["rationing", "feed2food", "surge", "rice_plus3", "dispersed", "convoy"]
    out = []
    for s, g in grid.groupby("scenario", sort=False):
        g = g[g.lever.isin(["baseline"] + levers)]
        X = np.column_stack([(g.lever == lv).to_numpy(float) for lv in levers])
        res = weibull_aft(g["T"].to_numpy(), X, levers)
        res.insert(0, "scenario", s)
        out.append(res)
    return pd.concat(out, ignore_index=True)


def km_curves(grid: pd.DataFrame, levers=("baseline", "civil_package", "full_package")) -> pd.DataFrame:
    out = []
    for (s, lv), g in grid.groupby(["scenario", "lever"], sort=False):
        if lv not in levers:
            continue
        t, S = km(g["T"].to_numpy())
        out.append(pd.DataFrame({"scenario": s, "lever": lv, "t": t, "S": S}))
    return pd.concat(out, ignore_index=True)


def onset_effect(base: Base, n: int = 2000, seed: int = 99,
                 scenarios=("S2", "S3"), levers=("baseline", "rationing", "civil_package")) -> pd.DataFrame:
    out = []
    mid = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30]) + 14
    for s in scenarios:
        for m, doy in enumerate(mid, start=1):
            P = prm.sample(n, s, seed=seed + m, fixed={"onset_doy": doy})
            for lv in levers:
                r = simulate(base, P, LEVERS[lv])
                d = summarise(r["T"])
                out.append({"scenario": s, "lever": lv, "month": m, "onset_doy": doy,
                            "median": d["median"], "rmst": d["rmst"], "q25": d["q25"], "q75": d["q75"],
                            "p_gt_180": d["p_gt_180"]})
    return pd.DataFrame(out)


def phi_sweep(base: Base, n: int = 1000, seed: int = 5,
              levers=("baseline", "rationing", "civil_package")) -> pd.DataFrame:
    """Endurance as a function of the share of seaborne arrivals that get through.
    Other scenario parameters follow S2 (military blockade), except strikes scale with (1 - phi)."""
    out = []
    for i, phi in enumerate(np.round(np.arange(0, 1.0001, 0.05), 2)):
        P = prm.sample(n, "S2", seed=seed + i, fixed={"phi": phi})
        P["lam_s"] = P["lam_s"] * (1 - phi)
        P["f_s"] = np.clip(P["f_s"] + 0.5 * phi, 0, 1)
        for lv in levers:
            r = simulate(base, P, LEVERS[lv])
            d = summarise(r["T"])
            out.append({"phi": phi, "lever": lv, "median": d["median"], "rmst": d["rmst"],
                        "q25": d["q25"], "q75": d["q75"], "p_survive_year": d["p_survive_year"]})
    return pd.DataFrame(out)


def sobol(base: Base, scenario: str = "S3", lever: str = "baseline", N: int = 1024, seed: int = 3) -> pd.DataFrame:
    from SALib.analyze import sobol as sobol_an
    from SALib.sample import sobol as sobol_sm
    problem = prm.sobol_problem(scenario, include_levers=(lever != "baseline"))
    X = sobol_sm.sample(problem, N, calc_second_order=False, seed=seed)
    P = prm.sobol_params(X, problem, scenario)
    r = simulate(base, P, LEVERS[lever])
    Y = np.minimum(r["T"], HORIZON)
    Si = sobol_an.analyze(problem, Y, calc_second_order=False, seed=seed)
    df = pd.DataFrame({"parameter": problem["names"], "S1": Si["S1"], "S1_conf": Si["S1_conf"],
                       "ST": Si["ST"], "ST_conf": Si["ST_conf"]})
    df.insert(0, "lever", lever)
    df.insert(0, "scenario", scenario)
    return df.sort_values("ST", ascending=False).reset_index(drop=True)


COUNTY_VARIANTS = {
    # name: (lever, transport ranges, extra island stock in days)
    "baseline_normal": ("baseline", None, 0),
    "baseline_disrupted": ("baseline", "disrupted", 0),
    "package_disrupted": ("civil_package", "disrupted", 0),
    "package_disrupted_islands180": ("civil_package", "disrupted", 180),
}


def county_analysis(base: Base, scenario: str = "S2", variants=None, n: int = 2000, seed: int = 21) -> pd.DataFrame:
    from .county import TAU_DISRUPTED
    out = []
    P = prm.sample(n, scenario, seed=seed)
    nat_cache = {}
    for vname, (lv, tau_key, extra) in (variants or COUNTY_VARIANTS).items():
        if lv not in nat_cache:
            nat_cache[lv] = simulate(base, P, LEVERS[lv], flows=True)
        nat = nat_cache[lv]
        cr = simulate_counties(base, P, nat, tau_ranges=(TAU_DISRUPTED if tau_key else None),
                               island_extra_days=extra)
        Tn = np.minimum(nat["T"], HORIZON)
        for j, row in base.county.reset_index(drop=True).iterrows():
            Tc = cr["T_c"][:, j]
            d = summarise(Tc)
            out.append({"scenario": scenario, "variant": vname, "lever": lv, "county_en": row.county_en,
                        "county_zh": row.county_zh, "code": row.code, "region": row.region,
                        "population": row.population,
                        "median": d["median"], "rmst": d["rmst"], "q25": d["q25"], "q75": d["q75"],
                        "p_gt_180": d["p_gt_180"],
                        "lead_vs_national": float(np.median(Tn - np.minimum(Tc, HORIZON))),
                        "national_median": float(np.median(Tn))})
    return pd.DataFrame(out)


def headline_conversions(base: Base, m_req: float) -> dict:
    """Translate official stock claims (months of rice) into days of total minimum energy."""
    month = base.rice_consumption * DAYS_PER_MONTH
    feed = base.feed_items.set_index("feed_item")
    return {
        "m_req_median": m_req,
        "rice_month_kcal_pc": month,
        "legal_3_months_days": 3 * month / m_req,
        "public_5p5_months_days": 5.5 * month / m_req,
        "about_one_year_days": 12 * month / m_req,
        "feed_raw_kcal_pc_day": base.feed_raw_kcal,
        "corn_feed_kcal_pc_day": float(feed.loc["corn_feed", "kcal_pc_day_raw"]),
    }


def bulk_ship_arithmetic(base: Base, m_req: float) -> pd.DataFrame:
    """How much energy do the ~9 bulk grain/oilseed vessels a month carry? (USDA FAS count)
    Annual imports from the calibrated food balance sheet (FBS 2022 items scaled to the
    FA01 group totals of the calibration year); edible conversion as in the feed-to-food
    lever (central values)."""
    pop = base.population
    imp = base.fbs.set_index("item")["imports_kt"]
    items = [
        ("corn", float(imp["corn_food"]), 5.0, 3650, 0.75),
        ("soybeans", float(imp["soybeans_food"]), 2.5, 4460, 0.80),
        ("wheat", float(imp["wheat"]), 1.5, 3390, 0.95),
    ]
    rows = []
    for name, kt, vessels, kcal, eta in items:
        kcal_pc_day = kt * 1e6 * kcal * eta / (pop * 365)
        per_vessel_days = (kt * 1e6 / 12 / vessels) * kcal * eta / (pop * m_req)
        rows.append({"cargo": name, "imports_kt_year": kt, "vessels_per_month": vessels,
                     "edible_kcal_pc_day": kcal_pc_day, "share_of_minimum": kcal_pc_day / m_req,
                     "days_of_national_minimum_per_vessel": per_vessel_days})
    return pd.DataFrame(rows)
