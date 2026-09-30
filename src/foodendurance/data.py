"""Calibration data: turns the official tables in data/raw/ into the per-capita
quantities the simulator needs.

All energy quantities are expressed PER CAPITA:
    flows  -> kcal per person per day
    stocks -> kcal per person (divide by a daily requirement to get "days")

Sources (see data/README.md for full citations):
    fbs_2022_moa.csv          MOA Food Balance Sheet 2022: item-level energy, protein, quantities
    fa01_food_supply_2015_2025.csv  MOA FA01 (糧食供給量-按糧食產品別), food-group quantities
                              2015-2025; used to update the 2022 item table to the latest year
    feed_2022_moa.csv         FBS 2022 feed use + standard energy/protein densities
    rice_county_2025_afa.csv  AFA Rice Production Survey 2025, 1st and 2nd crop, by county
    population_county.csv     MOI county population, Dec 2025 (pop_latest)
    agriculture_county_2024_dgbas.csv  DGBAS county farmland 2024 (cultivated, paddy, dry field)
    national_constants.csv    MOI / MOA / USDA / CSIS headline constants
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"

DAYS_PER_MONTH = 365.0 / 12.0

FBS_BASE_YEAR = 2022   # year of the item-level food balance sheet
FBS_YEAR = 2025        # calibration year: item table scaled to FA01 food-group totals
# Food-cereal items keep their 2022 per-capita energy: FA01 cereal supply is dominated by
# feed corn, and rice is set separately from the latest per-capita rice consumption.
KEEP_2022_KCAL = {"rice", "wheat", "corn_food", "other_cereals"}

# Food-balance-sheet pools used by the simulator
POOLS = ["RICE", "DOM_PERISH", "DOM_STOR", "FISH", "LIVESTOCK", "IMP_BULK", "IMP_OTHER", "IMP_PERISH"]

# Rice: FBS 2022 food supply and domestic supply (1,000 t, brown-rice basis)
RICE_FOOD_KT_2022 = 1139.1
RICE_SUPPLY_KT_2022 = 1204.0

# Crop calendar (day-of-year, 0 = 1 January). Harvest windows follow the usual
# Taiwan pattern (1st crop: early June - early August; 2nd crop: mid Oct - end Nov).
CROP1_HARVEST = (155, 215)
CROP2_HARVEST = (285, 335)
CROP1_GROWTH_DAYS = 135     # transplant (~mid Feb) -> harvest (~end Jun)
CROP2_GROWTH_DAYS = 100     # transplant (~early Aug) -> harvest (~mid Nov)

SWEET_POTATO_KCAL_PER_KG = 1021.0   # implied by FBS 2022 (23.30 kcal/day for 8.33 kg/yr)


@dataclass
class Base:
    """Per-capita baseline structure of Taiwan's food supply."""
    population: float
    pool_kcal: dict            # kcal/person/day by pool (normal times)
    pool_protein: dict         # g/person/day by pool
    total_kcal: float          # normal food supply, kcal/person/day
    total_protein: float
    rice_consumption: float    # kcal/person/day (2024 per-capita rice use)
    meat_kcal: float           # kcal/person/day of meat (frozen-stock reference)
    feed_raw_kcal: float       # human-edible-equivalent energy of feed flow if eaten raw
    feed_protein: float        # g/person/day in the feed flow
    feed_items: pd.DataFrame
    crop1_kcal_pc: float       # kcal/person delivered by the 1st rice crop (food use)
    crop2_kcal_pc: float
    rice_kcal_per_kg_brown: float
    county: pd.DataFrame = field(default=None)
    fbs: pd.DataFrame = field(default=None)
    constants: dict = field(default_factory=dict)
    fbs_year: int = FBS_BASE_YEAR
    fa01_ratios: pd.DataFrame = field(default=None)

    def rho(self, pool: str) -> float:
        """Protein density of a pool, g protein per kcal."""
        k = self.pool_kcal[pool]
        return self.pool_protein[pool] / k if k > 0 else 0.0


def _constants() -> dict:
    c = pd.read_csv(RAW / "national_constants.csv")
    return {k: float(v) for k, v in zip(c["key"], c["value"])}


def load_fa01() -> pd.DataFrame:
    """MOA FA01 food-group quantities, 2015-2025 (tidy; see scripts/import_official_data.py)."""
    return pd.read_csv(RAW / "fa01_food_supply_2015_2025.csv")


def fa01_ratios(year: int, const: dict | None = None) -> pd.DataFrame:
    """Food-group ratios year / 2022 for production, imports, exports, total supply and
    per-capita supply (2022 population from the FBS; 2025 population from MOI, Dec 2025)."""
    const = const or _constants()
    f = load_fa01()
    a = f[f["year"] == FBS_BASE_YEAR].set_index("group")
    b = f[f["year"] == year].set_index("group")
    if b.empty:
        raise ValueError(f"FA01 has no data for {year}")
    pop_a = const["population_2022_mid"]
    pop_b = const.get(f"population_{year}_12", const["population_2026_05"])
    r = pd.DataFrame({"prod": b["production_t"] / a["production_t"],
                      "imp": b["imports_t"] / a["imports_t"],
                      "exp": b["exports_t"] / a["exports_t"],
                      "sup": b["domestic_supply_kt"] / a["domestic_supply_kt"]})
    r["sup_pc"] = r["sup"] * pop_a / pop_b
    r["pop_year"] = pop_b
    return r.drop(index=[g for g in ["alcohol_ref"] if g in r.index])


def load_fbs(year: int = FBS_YEAR, const: dict | None = None) -> pd.DataFrame:
    """Item-level food balance sheet with the domestic share of each item.

    year = 2022 returns the published 2022 table. For a later year, each item is scaled with
    its food group's FA01 ratios: quantities by the group's production / import / export /
    supply ratios, per-capita energy and protein by the group's per-capita supply ratio
    (food cereals excepted, see KEEP_2022_KCAL). The domestic share then follows from the
    scaled production / supply, so it moves with the group (e.g. more imported meat)."""
    fbs = pd.read_csv(RAW / "fbs_2022_moa.csv")
    fbs["fbs_year"] = FBS_BASE_YEAR
    if year != FBS_BASE_YEAR:
        r = fa01_ratios(year, const)
        for g, row in r.iterrows():
            m = fbs["group"] == g
            fbs.loc[m, "production_kt"] *= row["prod"]
            fbs.loc[m, "imports_kt"] *= row["imp"]
            fbs.loc[m, "exports_kt"] *= row["exp"]
            fbs.loc[m, "domestic_supply_kt"] *= row["sup"]
            mk = m & ~fbs["item"].isin(KEEP_2022_KCAL)
            fbs.loc[mk, ["kcal_pc_day", "protein_pc_day"]] *= row["sup_pc"]
        fbs["fbs_year"] = year
    share = fbs["production_kt"] / fbs["domestic_supply_kt"]
    # residual items (no quantities) are fully assigned to their pool
    share = share.where(fbs["production_kt"].notna(), 1.0)
    fbs["domestic_share"] = share.clip(0, 1)
    return fbs


def build_base(population: float | None = None, rice_pc_kg: float | None = None,
               fbs_year: int = FBS_YEAR) -> Base:
    const = _constants()
    pop = population or const["population_2026_05"]
    rice_pc = rice_pc_kg or const["rice_pc_kg_2024"]
    fbs = load_fbs(fbs_year, const)
    ratios = fa01_ratios(fbs_year, const) if fbs_year != FBS_BASE_YEAR else None

    kcal = {p: 0.0 for p in POOLS}
    prot = {p: 0.0 for p in POOLS}
    for _, r in fbs.iterrows():
        d = r["domestic_share"]
        kcal[r["pool_domestic"]] += r["kcal_pc_day"] * d
        prot[r["pool_domestic"]] += r["protein_pc_day"] * d
        kcal[r["pool_imported"]] += r["kcal_pc_day"] * (1 - d)
        prot[r["pool_imported"]] += r["protein_pc_day"] * (1 - d)

    # scale rice to the latest per-capita consumption (2024: 42.4 kg vs 42.98 kg in 2022)
    f = rice_pc / const["rice_pc_kg_2022"]
    kcal["RICE"] *= f
    prot["RICE"] *= f

    total_kcal = sum(kcal.values())
    total_prot = sum(prot.values())
    meat_kcal = fbs.loc[fbs["group"] == "meat", "kcal_pc_day"].sum()

    # ---- feed flow (would-be human food) -----------------------------------------
    feed = pd.read_csv(RAW / "feed_2022_moa.csv")
    pop22 = const["population_2022_mid"]
    pop_feed = pop22
    if ratios is not None:
        # feed grain follows the FA01 import ratio of its group (corn/wheat: cereals; soy: oilseeds)
        grp = {"corn_feed": "cereals", "wheat_feed": "cereals",
               "soybean_meal": "pulses_oilseeds", "soybean_feed": "pulses_oilseeds"}
        feed["quantity_kt"] = feed["quantity_kt"] * feed["feed_item"].map(lambda i: ratios.loc[grp[i], "imp"])
        pop_feed = float(ratios["pop_year"].iloc[0])
    feed["kcal_pc_day_raw"] = feed["quantity_kt"] * 1e6 * feed["human_kcal_per_kg"] / (pop_feed * 365)
    feed["protein_pc_day_raw"] = feed["quantity_kt"] * 1e9 * feed["protein_frac"] / (pop_feed * 365)
    feed_raw = feed["kcal_pc_day_raw"].sum()
    feed_prot = feed["protein_pc_day_raw"].sum()

    # ---- rice harvests ---------------------------------------------------------------
    kcal_per_kg_food = (fbs.loc[fbs.item == "rice", "kcal_pc_day"].iloc[0] * 365 * pop22) / (RICE_FOOD_KT_2022 * 1e6)
    kcal_per_kg_brown = kcal_per_kg_food * (RICE_FOOD_KT_2022 / RICE_SUPPLY_KT_2022)
    county = load_county(pop)
    crop1 = county["crop1_brown_t"].sum() * 1e3 * kcal_per_kg_brown / pop
    crop2 = county["crop2_brown_t"].sum() * 1e3 * kcal_per_kg_brown / pop

    return Base(
        population=pop,
        pool_kcal=kcal,
        pool_protein=prot,
        total_kcal=total_kcal,
        total_protein=total_prot,
        rice_consumption=kcal["RICE"],
        meat_kcal=meat_kcal,
        feed_raw_kcal=feed_raw,
        feed_protein=feed_prot,
        feed_items=feed,
        crop1_kcal_pc=crop1,
        crop2_kcal_pc=crop2,
        rice_kcal_per_kg_brown=kcal_per_kg_brown,
        county=county,
        fbs=fbs,
        constants=const,
        fbs_year=fbs_year,
        fa01_ratios=ratios,
    )


def load_county(population_total: float) -> pd.DataFrame:
    """County table: population (MOI, Dec 2025), 2025 rice production (AFA) and 2024
    farmland (DGBAS).

    Shares used by the county module:
        pop_share    population share (demand, imports, fish, livestock, stocks)
        crop_share   cultivated-area share: domestic vegetables, fruit and other crops
        idle_share   share of paddy land not planted to rice (paddy area - half of the annual
                     rice harvest area): where surge planting can happen
        crop1/2_share  rice harvest shares by crop season
    If population_county.csv has no pop_latest column, the 2019 table is scaled to the
    national total instead."""
    pop = pd.read_csv(RAW / "population_county.csv")
    rice = pd.read_csv(RAW / "rice_county_2025_afa.csv")
    df = pop.merge(rice, on=["county_en", "county_zh"], how="left").fillna(0)
    if "pop_latest" in df.columns:
        df["population"] = df["pop_latest"].astype(float)
        df["population_note"] = "MOI " + df.get("pop_latest_time", pd.Series(["latest"] * len(df))).astype(str)
    else:
        df["population"] = df["pop_2019_moi"] * population_total / df["pop_2019_moi"].sum()
        df["population_note"] = "MOI 2019 scaled to 2026 national total (provisional)"
    df["pop_share"] = df["population"] / df["population"].sum()
    tot1, tot2 = df["crop1_brown_t"].sum(), df["crop2_brown_t"].sum()
    df["crop1_share"] = df["crop1_brown_t"] / tot1
    df["crop2_share"] = df["crop2_brown_t"] / tot2
    agri_file = RAW / "agriculture_county_2024_dgbas.csv"
    if agri_file.exists():
        agri = pd.read_csv(agri_file)[["county_zh", "cultivated_ha", "paddy_ha", "dry_ha", "rice_harvest_ha"]]
        df = df.merge(agri, on="county_zh", how="left").fillna({"cultivated_ha": 0, "paddy_ha": 0,
                                                                "dry_ha": 0, "rice_harvest_ha": 0})
        df["idle_paddy_ha"] = (df["paddy_ha"] - df["rice_harvest_ha"] / 2).clip(lower=0)
        df["crop_share"] = df["cultivated_ha"] / df["cultivated_ha"].sum()
        df["idle_share"] = df["idle_paddy_ha"] / df["idle_paddy_ha"].sum()
    else:
        df["crop_share"] = df["pop_share"]
        df["idle_share"] = df["pop_share"]
    return df


def rice_stock_months(doy: np.ndarray, trough_months: np.ndarray, base: Base) -> np.ndarray:
    """Total rice in the system (public + private + pipeline), in months of rice use,
    on a given day of year, from a closed annual balance: stock is lowest on 1 June
    (just before the 1st-crop harvest) at `trough_months`; harvests add, use removes.

    Calibration check: with trough = 5.5 the stock peaks at ~12.6 months in early
    August ("about one year including private stocks", MOA, Mar 2025) and is ~8.5 in
    mid-March (public stocks alone were 5.5 months then)."""
    month_kcal = base.rice_consumption * DAYS_PER_MONTH
    h1 = base.crop1_kcal_pc / month_kcal          # months added by the 1st crop
    h2 = base.crop2_kcal_pc / month_kcal
    annual_out = h1 + h2                           # closes the cycle (use + exports)
    t = (np.asarray(doy, dtype=float) - 151.0) % 365.0   # days since 1 June
    a1, b1 = CROP1_HARVEST[0] - 151.0, CROP1_HARVEST[1] - 151.0
    a2, b2 = CROP2_HARVEST[0] - 151.0, CROP2_HARVEST[1] - 151.0
    add1 = h1 * np.clip((t - a1) / (b1 - a1), 0, 1)
    add2 = h2 * np.clip((t - a2) / (b2 - a2), 0, 1)
    out = annual_out * t / 365.0
    return trough_months + add1 + add2 - out


def summary_table(base: Base) -> pd.DataFrame:
    """Readable summary of the baseline structure (used in README and slides)."""
    labels = {
        "RICE": "Rice (domestic, storable)",
        "DOM_PERISH": "Domestic fresh produce",
        "DOM_STOR": "Domestic storables (sugar, peanuts...)",
        "FISH": "Fish & seafood (domestic)",
        "LIVESTOCK": "Domestic livestock products (imported feed)",
        "IMP_BULK": "Imported bulk (wheat, soy, oils, sugar, cassava)",
        "IMP_OTHER": "Imported other storables (dairy, pulses...)",
        "IMP_PERISH": "Imported perishables (meat, fruit...)",
    }
    rows = []
    for p in POOLS:
        rows.append({"pool": p, "label": labels[p], "kcal_pc_day": base.pool_kcal[p],
                     "protein_pc_day": base.pool_protein[p],
                     "share_kcal": base.pool_kcal[p] / base.total_kcal})
    return pd.DataFrame(rows)
