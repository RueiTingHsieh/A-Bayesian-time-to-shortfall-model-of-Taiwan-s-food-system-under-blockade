# Food Endurance as Deterrence · 糧食續航力即嚇阻力

**A Bayesian time-to-shortfall model of Taiwan's food system under blockade.**
**封鎖情境下臺灣斷糧時間之貝氏存活分析**

Ruei-Ting Hsieh 謝瑞庭 · R14621208 · 農藝所生統組 碩二 (Agronomy, Biometry Division, M.S. year 2)
Final project for a course on ROC national defense policy, 2026.

This repository contains everything behind the slides: data, model, tests, analysis
scripts and the slide builder. One command reproduces every number and figure.

---

## 中文摘要

一旦臺灣遭到封鎖，糧食能撐多久？現行規範只看「稻米安全存量 ≥ 3 個月」，但稻米只占熱量約 14%。
本研究把 **斷糧時間 T**（可用糧食首度低於全民最低需求的那一天）當作存活時間，建立逐日的隨機
存量流量模型：以農業部糧食平衡表校準（2022 年品項結構，依 FA01 更新至 2025 年各類糧食供給量），
能源（天然氣、燃煤、石油）存量與封鎖強度互相連動，並對 42 個不確定參數給定附來源的事前分布，
每種情境模擬 5,000 次。接著用存活分析（Kaplan–Meier、RMST、Weibull 加速失敗時間模型）比較政策
槓桿，用 Sobol 指標找出最重要的不確定來源，再用 22 縣市模組（內政部 2025 年 12 月人口、主計總處
2024 年耕地與水田面積、農糧署 2025 年稻作產量）找出最先告急的地區。

主要發現（無新政策 → 採民生政策組合）：

| 情境 | 續航力中位數 | 撐過 180 天的機率 |
|---|---|---|
| S1 海警隔離 | 92% 情境可撐過一年 | 100% |
| S2 軍事封鎖 | 184 天 → 357 天 | 54% → 100% |
| S3 全面孤立＋能源衝擊 | 118 天 → 179 天（加護航 352 天） | 0% → 46%（加護航 100%） |

- **飼料轉糧**是最有效的民生槓桿（軍事封鎖下中位數 +64 天），其次是第一週啟動分級配給（+44 天）；公糧再增 3 個月只多約 19 天，稻穀價值卻約新臺幣 100 億元。
- **外離島**最先告急（66–74 天），其次是**北部都會區**（南北交通受阻時約 105 天；交通正常約 182 天）。
- 軍事封鎖下最重要的未知是**船運抵達比例**；全面孤立下則是**封鎖開始季節**與**民間進口在途存量**。

---

## Key results (n = 5,000 simulated futures per scenario)

| Scenario | Policy | Median endurance | RMST(365) | P(T > 180 d) | P(≥ 1 year) |
|---|---|---|---|---|---|
| S1 Quarantine (φ ≈ 75%) | no new policy | ≥ 1 year | 361 d | 100% | 92% |
| S2 Military blockade (φ ≈ 35%) | no new policy | 184 d | 189 d | 54% | 0% |
| | civil package | 357 d | 330 d | 100% | 47% |
| | civil package + convoys | ≥ 1 year | 358 d | 100% | 84% |
| S3 Total isolation + energy shock (φ ≈ 6%) | no new policy | 118 d | 117 d | 0% | 0% |
| | civil package | 179 d | 179 d | 46% | 0% |
| | civil package + convoys | 352 d | 329 d | 100% | 45% |

*Civil package* = tiered rationing + feed-to-food + surge planting + dispersed storage.

Median days gained per lever (paired, same simulated future):

| Lever | S2 blockade | S3 isolation | Weibull AFT time ratio (S2 / S3) |
|---|---|---|---|
| Tiered rationing (from day 7) | +44 | +18 | 1.30 / 1.17 |
| Feed-to-food (from day 10) | **+64** | +20 | **1.42** / 1.18 |
| Surge planting (sweet potato) | +11 | 0 | 1.07 / 1.01 |
| +3-month rice reserve | +19 | +14 | 1.11 / 1.12 |
| Dispersed storage | +4 | +7 | 1.02 / 1.06 |
| Grain convoys (from day 14) | +21 | +49 | 1.14 / **1.51** |
| Civil package | +143 | +59 | |
| Civil package + convoys | +173 | +224 | |

Other results:

- **Reconciling published estimates.** Median endurance rises with the share of normal seaborne
  arrivals that get through (φ): about 4 months at φ = 0, about 6 months at φ = 35% (matching
  *Parameters* 2023), and at least a year from φ ≈ 65% (matching the CSIS finding that "food was
  not a problem" and the minister's "about one year"). With the civil package, φ ≈ 35% is enough for a year.
- **Timing.** The start date shifts median endurance by up to 47 days. The worst starts are December
  under blockade and February under isolation.
- **Counties** (S2, transport disrupted): Kinmen, Matsu and Penghu run short first (66–74 days vs 184
  nationally). Taipei, New Taipei and Keelung follow at about 105 days; with normal north–south transport
  they last about 182 days. Farm counties (Changhua, Yunlin, Chiayi, Hualien, Taitung) last about 232 days.
  Pre-positioning 6 months of stock on the islands raises them to 252–276 days.
- **Sensitivity** (Sobol total-order): under blockade, φ dominates (0.61). Under isolation, the start
  season (0.38) and the private import pipeline (0.31) dominate.
- **Rice arithmetic.** 3 months of rice equals about 16 days of the whole population's minimum
  energy need; 5.5 months equals about 30 days; about 12 months equals about 64 days.

---

## Quick start

```bash
pip install -r requirements.txt
python tests/test_model.py          # 7 sanity tests (or: python -m pytest -q)
python scripts/run_all.py           # full analysis, about 1 minute; add --quick for a smoke test
python scripts/export_slide_data.py # numbers + county maps used by the slides
```

If you download newer official files, put them in `data/raw/official/` and run
`python scripts/import_official_data.py` first (see "Updating the data").

Outputs:

- `outputs/tables/*.csv`: every table (summary, paired gains, AFT, KM curves, onset, φ sweep, Sobol, counties, priors)
- `outputs/figures/{en,zh}/*.png`: English and Traditional Chinese figures
- `outputs/headline.json`, `outputs/slide_data.json`: headline numbers

Chinese figure labels need a Traditional Chinese font. If `Noto Sans CJK TC` or `Microsoft JhengHei`
is not installed, put `NotoSansCJKtc-Regular.otf` and `NotoSansCJKtc-Bold.otf` in `./fonts/` or point
`FE_FONT_DIR` to their folder.

Build the slide decks (Node.js ≥ 18):

```bash
cd slides
npm install
node build_deck.js en deck_en.pptx
node build_deck.js zh deck_zh.pptx
```

---

## Model

A daily, vectorised stock–flow simulator (`src/foodendurance/model.py`) tracks per-capita food energy
(kcal) and protein for 365 days.

- **Calibration**: the item-level MOA Food Balance Sheet 2022 (32 items) is updated to 2025 with the
  MOA FA01 series (糧食供給量-按糧食產品別, 2015–2025): each item's quantities follow its food group's
  production, import, export and supply ratios, and its per-capita energy and protein follow the
  group's per-capita supply ratio. Food cereals keep their 2022 per-capita use (FA01 cereal supply is
  mostly feed corn) and rice uses 2024 per-capita consumption. Normal supply is about 2,860 kcal per
  person per day; 24% of it needs no imported inputs.
- **Stocks**: rice (public + private), imported-food pipeline, household and retail pantry, cold-stored
  meat, feed grain, livestock herd, surge-planted sweet potato.
- **Inflows**: rice harvests on the Taiwan crop calendar (AFA 2025 county yields); seaborne arrivals ×
  φ; domestic vegetables, fruit and fish scaled by fuel, electricity and fertilizer shortages; livestock
  output, which needs imported feed.
- **Energy coupling**: LNG, coal and oil run out after about D / (1 − φ) days (D ≈ 10 days, 7 weeks and
  20 weeks; CSIS 2025). The power mix (gas 46%, coal 40%, renewables 13%) drives cold-chain losses and
  crop yields.
- **Demand**: unrationed consumption or tiered rationing. The minimum need is the Sphere 2,100 kcal
  planning figure plus mobilized forces and distribution losses (about 2,330 kcal per person per day).
- **Event**: T is the first day on which available food falls below the minimum need, or the 30-day
  mean protein intake falls below need. T is right-censored at 365 days.
- **Uncertainty**: 42 inputs with sourced priors (`params.py`, listed in `outputs/tables/priors.csv`).
  Monte Carlo uses common random numbers, so each lever is compared on the same simulated futures.
- **Scenarios**: S1 quarantine φ ~ Beta(0.75, sd 0.08); S2 military blockade φ ~ Beta(0.35, 0.08);
  S3 total isolation φ ~ Beta(0.06, 0.03), each with its own fishing and strike-loss priors.
- **Survival analysis** (`survival.py`, written from scratch): Kaplan–Meier, median, RMST, P(T > t),
  and a censored Weibull AFT model fitted by maximum likelihood with an analytic gradient.
- **Sensitivity**: Sobol total-order indices with SALib (N = 1,024 base samples).
- **Counties** (`county.py`): 22 counties share national flows through a transfer capacity τ (west,
  east, outlying islands), with separate "normal" and "disrupted" transport ranges. Demand, imports,
  fish and livestock products follow population (MOI, Dec 2025); rice follows AFA 2025 county output;
  other crops follow cultivated area and surge planting follows paddy land not planted to rice
  (DGBAS 2024). Local crops stay in their county, so islands keep their own produce.

### Main assumptions and limits

- The food balance keeps the 2022 item detail and moves each food group to its 2025 FA01 total. FA01
  gives quantities only, so energy per item is scaled rather than re-measured. Sugar supply is not
  published in FA01 and is estimated as production + imports − exports.
- The import pipeline, household stocks, rationing compliance and several behavioural parameters use
  stated assumptions. They are the natural targets for structured expert elicitation (SHELF).
- County output beyond rice is allocated by cultivated area (a proxy until county output by crop is
  used); fish from island fisheries is not modelled separately.
- County population is December 2025 and farmland 2024, the latest releases; both change by well under
  1% a year, and the national total uses the May 2026 figure.
- No price, trade-policy or panic-buying dynamics are modelled beyond the unrationed-consumption prior.
- The model is a planning tool for comparing policies under uncertainty. It is not a forecast of any
  specific conflict.

---

## Repository layout

```text
data/raw/                 calibration inputs (CSV, with sources)   -> see data/README.md
data/raw/official/        the official files as downloaded (FA01, MOI, DGBAS)
src/foodendurance/
  data.py                 food balance calibration, rice calendar, county table
  params.py               42 priors, 3 scenarios, Sobol problem definition
  model.py                daily stock-flow simulator and policy levers
  survival.py             Kaplan-Meier, RMST, Weibull AFT (no lifelines dependency)
  county.py               22-county allocation with transfer capacity
  experiments.py          scenario x lever grid, onset, phi sweep, Sobol, county analysis
  plots.py                bilingual figures
scripts/import_official_data.py  converts the official files into tidy CSVs
scripts/run_all.py        reproduces every table and figure
scripts/export_slide_data.py  collects slide numbers and county maps
slides/build_deck.js      builds the 15-slide decks (pptxgenjs, native charts)
tests/test_model.py       calibration and sanity tests
```

## Updating the data

1. Put the newer files in `data/raw/official/` (same names, or edit the three file names at the top of
   `scripts/import_official_data.py`): the FA01 export (years in rows, same columns), the MOI county
   population CSV and the DGBAS county agriculture CSV.
2. Run `python scripts/import_official_data.py`. It rewrites `fa01_food_supply_2015_2025.csv`,
   the `pop_latest` column of `population_county.csv` and `agriculture_county_2024_dgbas.csv`.
3. To calibrate to a newer FA01 year, set `FBS_YEAR` in `src/foodendurance/data.py` and add that year's
   population to `national_constants.csv` as `population_<year>_12`.
4. Re-run `python scripts/run_all.py` and `python scripts/export_slide_data.py`.

## Sources

See `data/README.md` for full citations and links. Main sources: MOA Food Balance Sheet 2022 and FA01
food supply series 2015–2025; AFA Rice Production Survey 2025; MOI county population (Dec 2025);
DGBAS county agriculture overview (2024); USDA FAS GAIN TW2024-0030; CSIS, *Lights Out? Wargaming a
Chinese Blockade of Taiwan* (2025); Ferreira & Critelli, *Parameters* 53(2) (2023); EIA Taiwan
Analysis Brief (2026); Sphere Handbook (2018); MND 2019 National Defense Report and 2021 Quadrennial
Defense Review; RAND RR-1757-OSD (2017).

## License

Code: MIT (see `LICENSE`). Government data in `data/raw/` stays under its original terms (for
example, the Open Government Data License, version 1.0, for Taiwan government data).
