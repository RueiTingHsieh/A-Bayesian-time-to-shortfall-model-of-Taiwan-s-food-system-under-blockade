"""Sanity tests:  python -m pytest -q   (or  python tests/test_model.py)"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from foodendurance import params as prm  # noqa: E402
from foodendurance.county import simulate_counties  # noqa: E402
from foodendurance.data import build_base  # noqa: E402
from foodendurance.model import LEVERS, simulate  # noqa: E402

BASE = build_base()


def test_calibration_totals():
    # published FBS 2022 (2,789 kcal) with rice scaled to 2024 consumption
    b22 = build_base(fbs_year=2022)
    assert abs(b22.total_kcal - 2783.6) < 1.0
    # default calibration: 2022 items scaled to FA01 2025 food-group totals
    assert BASE.fbs_year == 2025
    assert 2800 < BASE.total_kcal < 2950
    dom = sum(BASE.pool_kcal[k] for k in ["RICE", "DOM_PERISH", "DOM_STOR", "FISH"]) / BASE.total_kcal
    assert 0.22 < dom < 0.27


def test_fa01_matches_fbs_2022():
    # FA01 2022 group totals agree with the item-level FBS 2022 for well-covered groups
    import pandas as pd
    from foodendurance.data import RAW, load_fa01
    f = load_fa01()
    f22 = f[f.year == 2022].set_index("group")
    items = pd.read_csv(RAW / "fbs_2022_moa.csv").groupby("group").sum(numeric_only=True)
    for g in ["vegetables", "fruits", "fish", "milk", "meat"]:
        assert abs(items.loc[g, "production_kt"] / (f22.loc[g, "production_t"] / 1e3) - 1) < 0.01, g
        assert abs(items.loc[g, "domestic_supply_kt"] / f22.loc[g, "domestic_supply_kt"] - 1) < 0.01, g


def test_county_shares():
    c = BASE.county
    for col in ["pop_share", "crop_share", "idle_share", "crop1_share", "crop2_share"]:
        assert abs(c[col].sum() - 1) < 1e-9, col
    assert abs(c["population"].sum() - 23299132) < 1  # MOI, Dec 2025


def test_no_blockade_no_shortfall():
    P = prm.sample(1000, "S1", fixed={"phi": 1.0, "lam_s": 0.0, "f_s": 1.0})
    r = simulate(BASE, P, LEVERS["baseline"])
    assert np.isfinite(r["T"]).sum() == 0


def test_more_shipping_longer_endurance():
    meds = []
    for phi in [0.0, 0.2, 0.4, 0.6]:
        P = prm.sample(600, "S2", seed=1, fixed={"phi": phi})
        meds.append(np.median(np.minimum(simulate(BASE, P, LEVERS["baseline"])["T"], 365)))
    assert all(a <= b for a, b in zip(meds, meds[1:]))


def test_levers_do_not_hurt():
    P = prm.sample(1500, "S2", seed=3)
    tb = np.minimum(simulate(BASE, P, LEVERS["baseline"])["T"], 365)
    for lv in ["rationing", "feed2food", "rice_plus3", "dispersed", "civil_package"]:
        tl = np.minimum(simulate(BASE, P, LEVERS[lv])["T"], 365)
        assert np.mean(tl >= tb - 1) > 0.99, lv


def test_county_pooling_matches_national():
    import foodendurance.county as C
    P = prm.sample(400, "S2", seed=5)
    nat = simulate(BASE, P, LEVERS["baseline"], flows=True)
    full = {"west": (1, 1), "east": (1, 1), "island": (1, 1)}
    cr = simulate_counties(BASE, P, nat, tau_ranges=full)
    tn = np.median(np.minimum(nat["T"], 365))
    tc = np.median(np.minimum(cr["T_c"], 365), axis=0)
    # with unlimited transport no county runs short much earlier than the nation, and the
    # population-weighted county median matches the national one (farm counties that keep
    # part of their own harvest may last longer)
    assert tc.min() >= tn - 10
    assert abs(np.average(tc, weights=BASE.county["pop_share"]) - tn) < 10


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("PASS", name)
