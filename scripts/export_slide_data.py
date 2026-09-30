"""Collect the numbers the slide decks need into outputs/slide_data.json (no re-simulation)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import beta as B  # noqa: E402

from foodendurance import plots  # noqa: E402
from foodendurance.data import build_base  # noqa: E402
from foodendurance.params import SCENARIOS  # noqa: E402
from foodendurance.survival import km_at  # noqa: E402

TAB = ROOT / "outputs" / "tables"


def main():
    base = build_base()
    head = json.load(open(ROOT / "outputs" / "headline.json", encoding="utf-8"))
    summ = pd.read_csv(TAB / "summary_by_scenario_lever.csv")
    gains = pd.read_csv(TAB / "paired_gains.csv")
    aft = pd.read_csv(TAB / "aft_time_ratios.csv")
    kmdf = pd.read_csv(TAB / "km_curves.csv")
    onset = pd.read_csv(TAB / "onset_effect.csv")
    phis = pd.read_csv(TAB / "phi_sweep.csv")
    sob = pd.read_csv(TAB / "sobol.csv")
    county = pd.read_csv(TAB / "county_results.csv")
    ships = pd.read_csv(TAB / "bulk_ship_arithmetic.csv")

    days = np.arange(0, 366)
    km = {}
    for (s, lv), g in kmdf.groupby(["scenario", "lever"]):
        t, S = g["t"].to_numpy(), g["S"].to_numpy()
        km.setdefault(s, {})[lv] = [round(float(v), 4) for v in km_at(t, S, days)]

    xs = np.arange(0, 101)
    priors = {}
    for s in ["S1", "S2", "S3"]:
        p = SCENARIOS[s]["priors"][0]
        k = p.lo * (1 - p.lo) / p.hi**2 - 1
        y = B(p.lo * k, (1 - p.lo) * k).pdf(np.clip(xs / 100, 1e-6, 1 - 1e-6))
        priors[s] = [round(float(v), 4) for v in y / y.max()]

    def cap(v):
        return float(min(v, 365)) if np.isfinite(v) else 365.0

    K = base.pool_kcal
    data = {
        "diet": {
            "dom_ind": K["RICE"] + K["DOM_PERISH"] + K["DOM_STOR"] + K["FISH"],
            "livestock": K["LIVESTOCK"], "imp_stor": K["IMP_BULK"] + K["IMP_OTHER"], "imp_perish": K["IMP_PERISH"],
            "total": base.total_kcal, "rice": K["RICE"],
            "m_req": head["conversions"]["m_req_median"], "feed_edible": head["conversions"]["feed_edible_kcal"],
        },
        "conv": head["conversions"],
        "ships": ships.to_dict(orient="records"),
        "summary": {f"{r.scenario}|{r.lever}": {k: (None if (isinstance(v, float) and not np.isfinite(v)) else v)
                                                for k, v in r._asdict().items()} for r in summ.itertuples(index=False)},
        "gains": {f"{r.scenario}|{r.lever}": r._asdict() for r in gains.itertuples(index=False)},
        "aft": {f"{r.scenario}|{r.term}": r._asdict() for r in aft.itertuples(index=False)},
        "km": km, "km_days": days.tolist(),
        "priors": priors, "prior_x": xs.tolist(),
        "onset": {s: {lv: [cap(v) for v in onset[(onset.scenario == s) & (onset.lever == lv)].sort_values("month")["median"]]
                      for lv in onset.lever.unique()} for s in onset.scenario.unique()},
        "phi": {lv: [cap(v) for v in phis[phis.lever == lv].sort_values("phi")["median"]] for lv in phis.lever.unique()},
        "phi_x": sorted(phis.phi.unique().tolist()),
        "sobol": {s: sob[sob.scenario == s].sort_values("ST", ascending=False).head(7)[["parameter", "ST"]].to_dict(orient="records")
                  for s in ["S2", "S3"]},
        "county": {v: county[county.variant == v][["code", "county_en", "county_zh", "region", "median", "national_median"]]
                   .assign(median=lambda d: d["median"].apply(cap)).to_dict(orient="records")
                   for v in county.variant.unique()},
        "population": base.population,
        "fbs_year": int(base.fbs_year),
        "county_pop_time": str(base.county["population_note"].iloc[0]),
        "shares": {"domestic_feed_independent": head["domestic_feed_independent_share"], "livestock": head["livestock_share"]},
    }
    with open(ROOT / "outputs" / "slide_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, default=float)
    for lang in ["en", "zh"]:
        plots.fig_county_map(county, ROOT / "outputs" / "figures" / lang, lang, "baseline_disrupted")
    print("slide_data.json written")


if __name__ == "__main__":
    main()
