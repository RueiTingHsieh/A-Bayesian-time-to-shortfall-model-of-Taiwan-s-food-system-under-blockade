"""Reproduce every table and figure in the report.

    python scripts/run_all.py            # full run (~2-3 minutes on a laptop)
    python scripts/run_all.py --quick    # smaller Monte Carlo sizes for testing
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
warnings.filterwarnings("ignore")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from foodendurance import experiments as ex  # noqa: E402
from foodendurance import params as prm  # noqa: E402
from foodendurance import plots  # noqa: E402
from foodendurance.data import build_base, summary_table  # noqa: E402
from foodendurance.model import feed_conversion  # noqa: E402

OUT = ROOT / "outputs"
TAB = OUT / "tables"
FIG = OUT / "figures"


def main(quick: bool = False):
    t0 = time.time()
    n_grid, n_onset, n_phi, n_sobol, n_county = (5000, 2000, 1000, 1024, 2000) if not quick else (800, 300, 200, 128, 300)
    TAB.mkdir(parents=True, exist_ok=True)
    base = build_base()

    # ---- calibration summary --------------------------------------------------------------
    st = summary_table(base)
    st.to_csv(TAB / "baseline_structure.csv", index=False)
    prm.prior_table().to_csv(TAB / "priors.csv", index=False)
    base.county.to_csv(TAB / "county_inputs.csv", index=False)

    # ---- main grid ------------------------------------------------------------------------------
    print("grid ...", flush=True)
    grid = ex.run_grid(base, n=n_grid)
    grid.to_parquet(TAB / "grid_draws.parquet") if _has_parquet() else grid.to_csv(TAB / "grid_draws.csv.gz", index=False)
    summ = ex.summary(grid); summ.to_csv(TAB / "summary_by_scenario_lever.csv", index=False)
    gains = ex.paired_gains(grid); gains.to_csv(TAB / "paired_gains.csv", index=False)
    aft = ex.aft_time_ratios(grid); aft.to_csv(TAB / "aft_time_ratios.csv", index=False)
    kmdf = ex.km_curves(grid); kmdf.to_csv(TAB / "km_curves.csv", index=False)

    print("onset ...", flush=True)
    onset = ex.onset_effect(base, n=n_onset); onset.to_csv(TAB / "onset_effect.csv", index=False)
    print("phi sweep ...", flush=True)
    phis = ex.phi_sweep(base, n=n_phi); phis.to_csv(TAB / "phi_sweep.csv", index=False)
    print("sobol ...", flush=True)
    sob = pd.concat([ex.sobol(base, s, "baseline", N=n_sobol) for s in ["S2", "S3"]], ignore_index=True)
    sob.to_csv(TAB / "sobol.csv", index=False)
    print("county ...", flush=True)
    county = ex.county_analysis(base, "S2", n=n_county); county.to_csv(TAB / "county_results.csv", index=False)

    # ---- headline conversions ----------------------------------------------------------------------
    Pm = prm.sample(20000, "S2")
    m_req = float(np.median((Pm["m_civ"] * (1 - Pm["s_mil"]) + Pm["m_mil"] * Pm["s_mil"]) / (1 - Pm["w"])))
    conv = ex.headline_conversions(base, m_req)
    eta_mix, _ = feed_conversion(base, {"eta_corn": 0.75, "eta_meal": 0.45})
    conv["feed_edible_kcal"] = base.feed_raw_kcal * eta_mix
    ships = ex.bulk_ship_arithmetic(base, m_req); ships.to_csv(TAB / "bulk_ship_arithmetic.csv", index=False)
    dom_ind = sum(base.pool_kcal[k] for k in ["RICE", "DOM_PERISH", "DOM_STOR", "FISH"])
    headline = {
        "population": base.population,
        "normal_supply_kcal": base.total_kcal,
        "normal_protein_g": base.total_protein,
        "domestic_feed_independent_share": dom_ind / base.total_kcal,
        "livestock_share": base.pool_kcal["LIVESTOCK"] / base.total_kcal,
        "conversions": conv,
        "bulk_ships": ships.to_dict(orient="records"),
        "summary": summ.to_dict(orient="records"),
        "gains": gains.to_dict(orient="records"),
        "runtime_s": None,
    }

    # ---- figures (EN + ZH) ----------------------------------------------------------------------------
    plots.fig_hero(grid, FIG)
    for lang in ["en", "zh"]:
        o = FIG / lang
        plots.fig_diet(base, conv, o, lang)
        plots.fig_rice_days(conv, o, lang)
        plots.fig_phi_priors(o, lang)
        plots.fig_km(kmdf, summ, o, lang)
        plots.fig_onset(onset, o, lang)
        plots.fig_phi_sweep(phis, o, lang)
        for v in ["baseline_disrupted", "package_disrupted", "baseline_normal"]:
            plots.fig_county(county, o, lang, v)
        plots.fig_levers(gains, o, lang)
        plots.fig_sobol(sob, o, lang)

    headline["runtime_s"] = round(time.time() - t0, 1)
    with open(OUT / "headline.json", "w", encoding="utf-8") as f:
        json.dump(headline, f, ensure_ascii=False, indent=2, default=float)
    print(f"done in {headline['runtime_s']} s")


def _has_parquet() -> bool:
    try:
        import pyarrow  # noqa: F401
        return True
    except Exception:
        return False


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    main(**vars(ap.parse_args()))
