"""Convert the official files in data/raw/official/ into the tidy CSVs the model reads.

    python scripts/import_official_data.py

Inputs (downloaded by hand; kept unchanged):
    糧食供給量-按糧食產品別.xlsx        MOA agricultural statistics, FA01, 104-114 (2015-2025)
    114年12月行政區人口統計_縣市.csv      MOI, SEGIS: county population, Dec 2025
    113年行政區農業概況統計_縣市.csv      DGBAS, SEGIS: county farmland and rice, 2024

Outputs:
    data/raw/fa01_food_supply_2015_2025.csv   year x food group: production, imports, exports,
                                              stock change, domestic supply
    data/raw/population_county.csv            adds column pop_latest (Dec 2025)
    data/raw/agriculture_county_2024_dgbas.csv  cultivated, paddy and dry-field area, rice
"""
from __future__ import annotations

from pathlib import Path

import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OFF = RAW / "official"

GROUPS = {  # FA01 group name -> model group used in fbs_2022_moa.csv
    "穀類": "cereals", "薯類": "starchy_roots", "糖及蜂蜜": "sugars", "子仁及油籽類": "pulses_oilseeds",
    "蔬菜類": "vegetables", "果品類": "fruits", "肉類": "meat", "蛋類": "eggs", "水產類": "fish",
    "乳品類": "milk", "油脂類": "oils_fats", "酒類(參考)": "alcohol_ref",
}
VARS = {"國內生產量(公噸)": "production_t", "糧食進口量(公噸)": "imports_t", "糧食出口量(公噸)": "exports_t",
        "存貨變動量(千公噸)": "stock_change_kt", "國內供給量(千公噸)": "domestic_supply_kt"}


def _num(v):
    if v is None or (isinstance(v, str) and v.strip() in {"…", "...", "-", ""}):
        return float("nan")
    return float(v)


def fa01() -> pd.DataFrame:
    ws = openpyxl.load_workbook(OFF / "糧食供給量-按糧食產品別.xlsx", data_only=True).worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    h1, h2 = rows[1], rows[2]
    cols, cur = [], None
    for j in range(1, len(h2)):
        cur = h1[j] if h1[j] is not None else cur
        cols.append((j, VARS[cur], GROUPS[h2[j]]))
    out = []
    for r in rows[3:]:
        if not r[0]:
            continue
        roc = int(str(r[0]).replace("年", ""))
        rec = {}
        for j, var, grp in cols:
            rec.setdefault(grp, {})[var] = _num(r[j])
        for grp, vals in rec.items():
            out.append({"year": roc + 1911, "year_roc": roc, "group": grp, **vals})
    df = pd.DataFrame(out)
    # supply is not published for sugar & honey: use production + imports - exports
    miss = df["domestic_supply_kt"].isna()
    df.loc[miss, "domestic_supply_kt"] = (df.loc[miss, "production_t"] + df.loc[miss, "imports_t"]
                                          - df.loc[miss, "exports_t"]) / 1e3
    df["supply_note"] = ""
    df.loc[miss, "supply_note"] = "production + imports - exports (supply not published)"
    return df


def population() -> pd.DataFrame:
    raw = pd.read_csv(OFF / "114年12月行政區人口統計_縣市.csv", skiprows=[1], dtype={"COUNTY_ID": str})
    raw = raw.rename(columns={"COUNTY": "county_zh", "P_CNT": "pop_latest", "INFO_TIME": "pop_latest_time"})
    pop = pd.read_csv(RAW / "population_county.csv")
    pop = pop.drop(columns=[c for c in ["pop_latest", "pop_latest_time"] if c in pop.columns])
    pop = pop.merge(raw[["county_zh", "pop_latest", "pop_latest_time"]], on="county_zh", how="left")
    assert pop["pop_latest"].notna().all(), "county name mismatch"
    return pop


def agriculture() -> pd.DataFrame:
    raw = pd.read_csv(OFF / "113年行政區農業概況統計_縣市.csv", skiprows=[1], dtype={"COUNTY_ID": str})
    ren = {"COUNTY": "county_zh", "COLUMN2": "rice_harvest_ha", "COLUMN3": "rice_t", "COLUMN4": "cultivated_ha",
           "COLUMN5": "paddy_ha", "COLUMN6": "dry_ha", "INFO_TIME": "time"}
    df = raw.rename(columns=ren)[list(ren.values())]
    for c in ["rice_harvest_ha", "rice_t", "cultivated_ha", "paddy_ha", "dry_ha"]:
        df[c] = pd.to_numeric(df[c].astype(str).str.strip(), errors="coerce").fillna(0.0)
    return df


def main():
    f = fa01()
    f.to_csv(RAW / "fa01_food_supply_2015_2025.csv", index=False)
    p = population()
    p.to_csv(RAW / "population_county.csv", index=False)
    a = agriculture()
    a.to_csv(RAW / "agriculture_county_2024_dgbas.csv", index=False)
    print(f"FA01: {f.year.min()}-{f.year.max()}, {f.group.nunique()} groups")
    print(f"population: total {p.pop_latest.sum():,.0f} ({p.pop_latest_time.iloc[0]})")
    print(f"agriculture: cultivated {a.cultivated_ha.sum():,.0f} ha, paddy {a.paddy_ha.sum():,.0f} ha, "
          f"rice {a.rice_t.sum():,.0f} t ({a.time.iloc[0]})")


if __name__ == "__main__":
    main()
