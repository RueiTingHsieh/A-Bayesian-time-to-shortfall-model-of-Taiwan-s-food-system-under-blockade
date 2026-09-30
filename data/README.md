# Data

All model inputs are small CSV files in `data/raw/`. Each one records its source. The official files
exactly as downloaded are kept in `data/raw/official/`; `scripts/import_official_data.py` turns them
into the tidy CSVs below.

| File | Content | Source |
|---|---|---|
| `fbs_2022_moa.csv` | 32 food items: kcal and protein per person per day, production, imports, exports, domestic supply; mapped to model pools | Ministry of Agriculture (MOA), *Agricultural Statistics Yearbook 2023*, Food Balance Sheet 2022 |
| `fa01_food_supply_2015_2025.csv` | 11 food groups × 2015–2025: domestic production, imports, exports, stock change, domestic supply. Used to move the 2022 item table to 2025 | MOA agricultural statistics, FA01 糧食供給量-按糧食產品別 (official file: `official/糧食供給量-按糧食產品別.xlsx`) |
| `feed_2022_moa.csv` | Feed use of corn, soybean meal, soybeans and wheat, with energy and protein densities and default edible-conversion rates (scaled to 2025 with the FA01 import ratios) | Food Balance Sheet 2022 (feed use); standard food-composition values |
| `rice_county_2025_afa.csv` | Rice area and brown-rice output by county, 1st and 2nd crop 2025 (totals 904,599 t and 340,656 t) | Agriculture and Food Agency (AFA), rice production survey 2025 |
| `population_county.csv` | County code, region (west / east / island), population Dec 2025 (`pop_latest`, total 23,299,132) and the older 2019 table | MOI, SEGIS 行政區人口統計_縣市, Dec 2025 (official file: `official/114年12月行政區人口統計_縣市.csv`) |
| `agriculture_county_2024_dgbas.csv` | Cultivated, paddy and dry-field area, rice harvest area and rice output by county, 2024 (777k ha cultivated, 342k ha paddy) | DGBAS, SEGIS 行政區農業概況統計_縣市, 2024 (official file: `official/113年行政區農業概況統計_縣市.csv`) |
| `national_constants.csv` | Population, rice consumption, self-sufficiency, stock months, distribution stations, bulk vessels per month, fuel stock days, paddy price | MOI, MOA, USDA FAS, CSIS, EIA (listed row by row) |

**Data vintages.** County population (Dec 2025) and farmland (2024) are the latest releases on SEGIS.
Both move by well under 1% a year, and the model only uses them as county shares, so they stand in
for 2026 without adjustment. The national population uses the May 2026 MOI figure.

**How FA01 updates the 2022 table.** FA01 agrees with the 2022 item table to within 1% for
vegetables, fruit, meat, fish and milk (checked in `tests/test_model.py`). For each food group the
item quantities are multiplied by the group's 2025/2022 ratios, and per-capita energy and protein by
the per-capita supply ratio (2022 population 23,319,977; 2025: 23,299,132). Food cereals keep 2022
per-capita use because FA01 cereal supply is mostly feed corn; rice uses 2024 per-capita
consumption (42.4 kg). FA01 does not publish sugar supply, so production + imports − exports is used.

## Key references

- MOA, calorie-based food self-sufficiency 2024 = 30.7% (published Nov 2025). <https://www.newsmarket.com.tw/blog/229404/>
- Minister of Agriculture at the Legislative Yuan, 26 Mar 2025: public grain 5.5 months, about 1 year including private stocks; 143 distribution stations. <https://www.cna.com.tw/news/ahel/202503260348.aspx>
- USDA FAS GAIN TW2024-0030, *Taiwan Food Security Situation Overview* (2024): about 5 corn, 2.5 soybean and 1.5 wheat vessels per month. <https://apps.fas.usda.gov/newgainapi/api/Report/DownloadReportByFileName?fileName=Taiwan+Food+Security+Situation+Overview_Taipei_Taiwan_TW2024-0030.pdf>
- Cancian, Mark F., Cancian, Matthew F., & Heginbotham, E. (2025). *Lights Out? Wargaming a Chinese Blockade of Taiwan*. CSIS. <https://csis-website-prod.s3.amazonaws.com/s3fs-public/2025-07/250730_Cancian_Taiwan_Blockade.pdf>
- Ferreira, G. F., & Critelli, J. A. (2023). Taiwan's food resiliency—or not—in a conflict with China. *Parameters*, 53(2). <https://press.armywarcollege.edu/parameters/vol53/iss2/10/>
- EIA, *Taiwan Analysis Brief* (Apr 2026): 10–11 days of LNG stocks; 2024 power mix. <https://www.eia.gov/international/content/analysis/countries_short/Taiwan/Taiwan.pdf>
- MOA planned-procurement price 2025: NT$26/kg dry paddy (japonica). <https://www.moa.gov.tw/theme_data.php?theme=publication&id=8527>
- Sphere Association (2018). *The Sphere Handbook*, 4th ed.: 2,100 kcal per person per day planning figure. <https://spherestandards.org/handbook/>
- Easton, I., Stokes, M., Cooper, C. A., III, & Chan, A. (2017). *Transformation of Taiwan's Reserve Force*. RAND RR-1757-OSD. <https://www.rand.org/pubs/research_reports/RR1757.html>
- Legislative Yuan Budget Center (Nov 2024): 710,569 reservists callable for refresher training. <https://www.cna.com.tw/news/aipl/202411030056.aspx>

## Data that would still improve the model

| Wanted | Why | Where to get it |
|---|---|---|
| FA01 energy and protein columns (每人每日供給熱量、蛋白質) by food group | Calibrate energy per group directly instead of scaling the 2022 values | MOA agricultural statistics, <https://agrstat.moa.gov.tw/> |
| County production of vegetables, fruit and sweet potato | Replace the cultivated-area proxy for county crop output | MOA crop reports (農情調查), <https://agrstat.moa.gov.tw/> |
| Public-grain warehouse capacity or stocks by county (if published) | Initial rice stocks by county instead of the 50/50 population–production split | AFA, <https://www.afa.gov.tw/> |
| Grain and feed imports by port | Port-level strike and closure scenarios | Customs Administration trade statistics (分港進口) |
| Storage, milling and rationing costs | Cost per endurance-day for each lever | MOA / AFA budget documents |

To update, see "Updating the data" in the main README.
