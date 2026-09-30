"""Figures for the report, in English ('en') and Traditional Chinese ('zh').

Chart conventions (house style): white chart surface, thin marks (2 px lines), hairline
solid gridlines, legend for >= 2 series plus selective direct labels, text in ink colours
(never in series colours), no dual axes. Palettes validated with the dataviz validator.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

# ---------------------------------------------------------------------------------------------
# palette & ink
# ---------------------------------------------------------------------------------------------
INK = "#1B2A3A"
INK2 = "#52514E"
MUTED = "#898781"
GRID = "#E6E4DD"
AXIS = "#C3C2B7"
SURF = "#FFFFFF"
NAVY = "#0E2841"
AMBER = "#E3A21A"
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
SCEN_COL = {"S1": "#86b6ef", "S2": "#2a78d6", "S3": "#104281"}          # ordinal ramp (validated)
LEVER_COL = {"baseline": "#9A968C", "rationing": ORANGE, "civil_package": AQUA, "full_package": BLUE}
SEQ_ORANGE = ["#fdeadf", "#f9c7a6", "#f29f6e", "#e2733f", "#b8501f", "#7f3312"]

FONTS = {"en": ["Calibri", "Carlito", "Liberation Sans", "DejaVu Sans"],
         "zh": ["Noto Sans CJK TC", "Microsoft JhengHei", "PingFang TC", "Heiti TC", "Calibri", "Carlito",
                "DejaVu Sans"]}


def _register_fonts():
    """Optionally register extra font files (e.g. Noto Sans CJK TC .otf) from $FE_FONT_DIR or ./fonts."""
    import os
    dirs = [os.environ.get("FE_FONT_DIR", ""), str(Path(__file__).resolve().parents[2] / "fonts")]
    for d in dirs:
        if d and Path(d).is_dir():
            for f in list(Path(d).glob("*.otf")) + list(Path(d).glob("*.ttf")):
                try:
                    font_manager.fontManager.addfont(str(f))
                except Exception:
                    pass


_register_fonts()

T = {  # translations
    "en": {
        "days": "days", "days_since": "Days since blockade began", "p_food": "Probability food still meets minimum need",
        "baseline": "No new policy", "rationing": "Tiered rationing", "civil_package": "Civil package",
        "full_package": "Civil package + grain convoys", "median": "median",
        "S1": "Quarantine", "S2": "Military blockade", "S3": "Total isolation",
        "S1_long": "Quarantine (coast-guard inspections)", "S2_long": "Military blockade (submarines & mines)",
        "S3_long": "Total isolation + energy shock",
        "rmst": "mean endurance (1-yr window)", "year": "≥ 1 year",
        "phi_x": "Share of normal seaborne arrivals that get through", "median_T": "Median food endurance (days)",
        "onset_x": "Month the blockade begins", "harvest": "rice harvest",
        "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "gain_x": "Days of endurance gained vs no new policy (median, 50% and 90% ranges)",
        "sobol_x": "Share of uncertainty in endurance explained (total-order Sobol index)",
        "density": "prior density",
    },
    "zh": {
        "days": "天", "days_since": "封鎖開始後天數", "p_food": "糧食仍能滿足最低需求的機率",
        "baseline": "無新政策", "rationing": "分級配給", "civil_package": "民生政策組合",
        "full_package": "政策組合＋穀物護航", "median": "中位數",
        "S1": "隔離", "S2": "軍事封鎖", "S3": "全面孤立",
        "S1_long": "海警隔離（臨檢）", "S2_long": "軍事封鎖（潛艦與水雷）", "S3_long": "全面孤立＋能源衝擊",
        "rmst": "平均續航天數（1年內）", "year": "≥ 1 年",
        "phi_x": "正常海運量中仍能抵達的比例", "median_T": "糧食續航力中位數（天）",
        "onset_x": "封鎖開始月份", "harvest": "稻米收穫期",
        "months": ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"],
        "gain_x": "相較無新政策增加的續航天數（中位數、50%與90%區間）",
        "sobol_x": "可解釋的續航力不確定性比例（Sobol 總效應指標）",
        "density": "事前機率密度",
    },
}

LEVER_LABEL = {
    "en": {"rationing": "Tiered rationing", "feed2food": "Feed-to-food (destock, eat feed grain)",
           "surge": "Surge planting (sweet potato)", "rice_plus3": "+3-month rice reserve",
           "dispersed": "Dispersed storage", "convoy": "Escorted grain convoys",
           "civil_package": "Civil package (first four)", "full_package": "Civil package + convoys"},
    "zh": {"rationing": "分級配給", "feed2food": "飼料轉糧（減養、飼料穀物轉供人食）",
           "surge": "休耕地搶種甘藷", "rice_plus3": "公糧再增3個月",
           "dispersed": "分散儲存", "convoy": "穀物船隊護航",
           "civil_package": "民生政策組合（前四項）", "full_package": "政策組合＋護航"},
}

PARAM_LABEL = {
    "en": {"phi": "Shipping that gets through", "m_imp": "Imported food in pipeline/stock",
           "onset_doy": "Blockade start date (season)", "beta": "Unrationed consumption level",
           "rice_trough": "Rice stock level", "d_house": "Household & retail pantry",
           "lam_s": "Strike losses on stores", "m_frz": "Cold-store meat", "lam_c": "Cold-chain losses",
           "d_feed": "Feed-grain stocks", "a_h": "Harvest fuel sensitivity",
           "eps_distress": "Distress-slaughter recovery", "m_civ": "Minimum civilian intake",
           "w": "Distribution losses", "panic": "Panic buying", "B_live": "Livestock on hand",
           "f_s": "Fishing activity", "a_c": "Crop fuel sensitivity", "D_oil": "Oil stock days",
           "D_coal": "Coal stock days", "D_gas": "LNG stock days", "r0": "Frozen-stock decay",
           "p_min": "Protein need", "s_mil": "Mobilised share", "m_mil": "Military ration",
           "a_f": "Fertilizer sensitivity", "d_fert": "Fertilizer stocks", "a_o": "Fishing fuel sensitivity",
           "a_e": "Crop power sensitivity", "pi_o": "Fuel priority for food", "t_s": "Strike timing",
           "r_die": "Herd die-off rate"},
    "zh": {"phi": "船運抵達比例", "m_imp": "進口糧食在途與庫存", "onset_doy": "封鎖起始時間（季節）",
           "beta": "未配給時的消費水準", "rice_trough": "稻米庫存水準", "d_house": "家戶與零售存糧",
           "lam_s": "倉儲遭攻擊損失", "m_frz": "冷凍肉品庫存", "lam_c": "冷鏈損失", "d_feed": "飼料庫存",
           "a_h": "收穫對燃料的敏感度", "eps_distress": "緊急屠宰回收率", "m_civ": "民眾最低熱量需求",
           "w": "配送損耗", "panic": "恐慌搶購", "B_live": "在養畜禽量", "f_s": "漁業活動",
           "a_c": "作物對燃料的敏感度", "D_oil": "石油存量天數", "D_coal": "燃煤存量天數",
           "D_gas": "天然氣存量天數", "r0": "冷凍庫存劣化", "p_min": "蛋白質需求", "s_mil": "動員人口比例",
           "m_mil": "軍用口糧熱量", "a_f": "肥料短缺敏感度", "d_fert": "肥料庫存", "a_o": "漁業燃料敏感度",
           "a_e": "作物電力敏感度", "pi_o": "糧食部門燃料優先", "t_s": "攻擊時點", "r_die": "畜禽死亡率"},
}

# Tile-grid map of Taiwan's 22 counties/cities (col, row); row 0 = north
TILES = {
    "LIE": (0.4, 0.2), "KIN": (-1.0, 3.2), "PEN": (-0.2, 6.2),
    "KEE": (4.0, 0.0),
    "TPE": (3.0, 1.0), "NTP": (4.0, 1.0),
    "TYN": (2.0, 1.5), "ILA": (4.5, 2.0),
    "HSZ": (1.0, 2.5), "HSQ": (2.0, 2.5),
    "MIA": (1.5, 3.5), "TXG": (2.5, 4.0), "HUA": (3.8, 4.3),
    "CHA": (1.5, 4.8), "NAN": (2.7, 5.2),
    "YUN": (1.2, 5.9), "CYQ": (2.3, 6.5), "CYI": (1.2, 7.0), "TTT": (3.4, 6.8),
    "TNN": (1.5, 8.1), "KHH": (2.6, 8.3),
    "PIF": (2.9, 9.4),
}
SHORT = {
    "en": {"LIE": "Matsu", "KIN": "Kinmen", "PEN": "Penghu", "KEE": "Keelung", "TPE": "Taipei", "NTP": "N. Taipei",
           "TYN": "Taoyuan", "ILA": "Yilan", "HSZ": "Hsinchu C.", "HSQ": "Hsinchu Co.", "MIA": "Miaoli",
           "TXG": "Taichung", "HUA": "Hualien", "CHA": "Changhua", "NAN": "Nantou", "YUN": "Yunlin",
           "CYI": "Chiayi C.", "CYQ": "Chiayi Co.", "TTT": "Taitung", "TNN": "Tainan", "KHH": "Kaohsiung",
           "PIF": "Pingtung"},
    "zh": {"LIE": "連江", "KIN": "金門", "PEN": "澎湖", "KEE": "基隆", "TPE": "臺北", "NTP": "新北",
           "TYN": "桃園", "ILA": "宜蘭", "HSZ": "竹市", "HSQ": "竹縣", "MIA": "苗栗", "TXG": "臺中",
           "HUA": "花蓮", "CHA": "彰化", "NAN": "南投", "YUN": "雲林", "CYI": "嘉市", "CYQ": "嘉縣",
           "TTT": "臺東", "TNN": "臺南", "KHH": "高雄", "PIF": "屏東"},
}


def setup(lang: str):
    fams = [f for f in FONTS[lang] if any(f == x.name for x in font_manager.fontManager.ttflist)]
    plt.rcParams.update({
        "font.family": fams or ["DejaVu Sans"],
        "font.size": 11, "axes.titlesize": 12, "axes.labelsize": 11,
        "axes.edgecolor": AXIS, "axes.linewidth": 0.8, "axes.labelcolor": INK2,
        "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
        "axes.spines.top": False, "axes.spines.right": False,
        "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
        "legend.frameon": False, "legend.fontsize": 10, "text.color": INK,
        "axes.unicode_minus": False, "svg.fonttype": "none", "axes.axisbelow": True,
    })


def _save(fig, out: Path, name: str):
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{name}.png", dpi=220, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


def _fmt_days(v, lang):
    if not np.isfinite(v) or v >= 365:
        return T[lang]["year"]
    return f"{v:.0f} {T[lang]['days']}" if lang == "en" else f"{v:.0f} 天"


# ---------------------------------------------------------------------------------------------
def fig_hero(grid: pd.DataFrame, out: Path):
    """Title-slide background: survival 'strands' of simulated futures (no text)."""
    fig = plt.figure(figsize=(16, 9), dpi=160)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(NAVY); fig.patch.set_facecolor(NAVY)
    rng = np.random.default_rng(4)
    t = np.linspace(0, 365, 400)
    for s, col, alpha in [("S3", "#3d7fb8", 0.10), ("S2", "#5fa0d6", 0.08), ("S2", AMBER, 0.05)]:
        Ts = grid[(grid.scenario == s) & (grid.lever == "baseline")]["T"].to_numpy()
        Ts = np.minimum(Ts, 420)
        for _ in range(70):
            sub = rng.choice(Ts, 60)
            S = (sub[None, :] > t[:, None]).mean(axis=1)
            ax.plot(t, S * 0.78 + 0.12 + rng.normal(0, 0.004), color=col, alpha=alpha, lw=1.0)
    Ts = grid[(grid.scenario == "S2") & (grid.lever == "baseline")]["T"].to_numpy()
    S = (np.minimum(Ts, 420)[None, :] > t[:, None]).mean(axis=1)
    ax.plot(t, S * 0.78 + 0.12, color=AMBER, lw=3.0, alpha=0.95)
    ax.set_xlim(-330, 385); ax.set_ylim(-0.02, 1.0)
    ax.axis("off")
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "hero.png", dpi=160, facecolor=NAVY)
    plt.close(fig)


def fig_diet(base, conv: dict, out: Path, lang: str):
    setup(lang)
    K = base.pool_kcal
    dom_ind = K["RICE"] + K["DOM_PERISH"] + K["DOM_STOR"] + K["FISH"]
    segs = [(dom_ind, AQUA), (K["LIVESTOCK"], YELLOW), (K["IMP_BULK"] + K["IMP_OTHER"], BLUE), (K["IMP_PERISH"], ORANGE)]
    lab = {"en": ["Domestic, no imported inputs", "Domestic livestock (imported feed)", "Imported storables",
                  "Imported perishables"],
           "zh": ["國產（不依賴進口投入）", "國產畜產品（依賴進口飼料）", "進口耐儲糧食", "進口生鮮"]}[lang]
    fig, ax = plt.subplots(figsize=(9.6, 3.4))
    left = 0
    for (v, c), l in zip(segs, lab):
        ax.barh(1, v - 6, left=left + 3, height=0.46, color=c, edgecolor="none")
        share = v / base.total_kcal
        ax.text(left + v / 2, 1.34, f"{share:.0%}", ha="center", va="bottom", fontsize=11, color=INK)
        left += v
    feed_edible = conv["feed_edible_kcal"]
    ax.barh(0, feed_edible, height=0.46, color="#C9C4B8", edgecolor="none")
    m = conv["m_req_median"]
    ax.axvline(m, color=INK, lw=1.3)
    ax.text(m + 25, -0.55, ({"en": f"Minimum need ≈ {m:,.0f} kcal", "zh": f"最低需求 ≈ {m:,.0f} 大卡"}[lang]),
            fontsize=10, color=INK, va="center")
    ax.set_yticks([1, 0])
    ax.set_yticklabels({"en": [f"Normal food supply\n{base.total_kcal:,.0f} kcal/person/day", "Imported feed grain,\nif eaten directly"],
                        "zh": [f"平時糧食供給\n每人每日 {base.total_kcal:,.0f} 大卡", "進口飼料穀物\n若直接供人食用"]}[lang])
    ax.text(feed_edible + 30, 0, f"≈ {feed_edible:,.0f} kcal" if lang == "en" else f"≈ {feed_edible:,.0f} 大卡",
            va="center", fontsize=10, color=INK2)
    ax.set_xlim(0, 3000); ax.set_ylim(-0.8, 1.8)
    ax.set_xlabel({"en": f"kcal per person per day (food balance {base.fbs_year}; rice at 2024 level)",
                   "zh": f"每人每日大卡（{base.fbs_year}年糧食平衡；稻米以2024年水準）"}[lang])
    ax.grid(axis="y", visible=False)
    handles = [Rectangle((0, 0), 1, 1, color=c) for _, c in segs]
    ax.legend(handles, lab, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.32), fontsize=9.5,
              handlelength=1.0, columnspacing=1.2)
    _save(fig, out, "diet_structure")


def fig_rice_days(conv: dict, out: Path, lang: str):
    setup(lang)
    rows = [("legal_3_months_days", {"en": "3 months of rice\n(legal minimum reserve)", "zh": "3個月稻米\n（法定最低安全存量）"}),
            ("public_5p5_months_days", {"en": "5.5 months of rice\n(public stocks, Mar 2025)", "zh": "5.5個月稻米\n（公糧，2025年3月）"}),
            ("about_one_year_days", {"en": "~12 months of rice\n(incl. private, after harvest)", "zh": "約12個月稻米\n（含民間，收穫後）"})]
    fig, ax = plt.subplots(figsize=(6.4, 3.3))
    ys = np.arange(len(rows))[::-1]
    for y, (k, lab) in zip(ys, rows):
        v = conv[k]
        ax.barh(y, v, height=0.42, color=AMBER, edgecolor="none")
        ax.text(v + 1.5, y, (f"{v:.0f} days" if lang == "en" else f"{v:.0f} 天"), va="center", fontsize=12,
                color=INK, fontweight="bold")
    ax.set_yticks(ys); ax.set_yticklabels([r[1][lang] for r in rows], fontsize=10.5)
    ax.set_xlim(0, 85)
    ax.set_xlabel({"en": "Days of the whole population's minimum calorie need",
                   "zh": "可支應全體國人最低熱量需求的天數"}[lang])
    ax.grid(axis="y", visible=False)
    _save(fig, out, "rice_months_vs_days")


def fig_phi_priors(out: Path, lang: str):
    from scipy.stats import beta as B
    from .params import SCENARIOS
    setup(lang)
    fig, ax = plt.subplots(figsize=(6.2, 2.9))
    x = np.linspace(0, 1, 500)
    for s in ["S3", "S2", "S1"]:
        p = SCENARIOS[s]["priors"][0]
        m, sd = p.lo, p.hi
        k = m * (1 - m) / sd**2 - 1
        y = B(m * k, (1 - m) * k).pdf(x)
        ax.fill_between(x * 100, y, color=SCEN_COL[s], alpha=0.10, lw=0)
        ax.plot(x * 100, y, color=SCEN_COL[s], lw=2)
        ax.text(m * 100, y.max() * 1.04, T[lang][s], ha="center", va="bottom", fontsize=10.5, color=INK)
    ax.set_xlabel(T[lang]["phi_x"] + " (%)")
    ax.set_yticks([]); ax.set_ylabel(T[lang]["density"])
    ax.set_xlim(0, 100); ax.set_ylim(0, None)
    ax.grid(axis="y", visible=False)
    _save(fig, out, "phi_priors")


def fig_km(kmdf: pd.DataFrame, summ: pd.DataFrame, out: Path, lang: str):
    setup(lang)
    fig, axes = plt.subplots(1, 3, figsize=(12.4, 3.9), sharey=True)
    for ax, s in zip(axes, ["S1", "S2", "S3"]):
        for lv in ["baseline", "civil_package", "full_package"]:
            d = kmdf[(kmdf.scenario == s) & (kmdf.lever == lv)]
            t = np.concatenate([d.t.to_numpy(), [365]])
            S = np.concatenate([d.S.to_numpy(), [d.S.to_numpy()[-1]]])
            ax.step(t, S, where="post", color=LEVER_COL[lv], lw=2.2 if lv == "baseline" else 2.0,
                    label=T[lang][lv])
        ax.set_title(T[lang][s + "_long"], fontsize=11.5, color=INK, loc="left")
        for lv in ["baseline", "civil_package", "full_package"]:
            med = summ[(summ.scenario == s) & (summ.lever == lv)]["median"].iloc[0]
            if np.isfinite(med) and med < 365:
                ax.plot(med, 0.5, "o", color=LEVER_COL[lv], ms=7, mec=SURF, mew=2, zorder=5)
                ax.text(med + 6, 0.53, f"{med:.0f}", fontsize=10, color=INK, zorder=6)
        if s == "S1":
            ax.text(0.04, 0.12, {"en": "≥ 95% of futures: food lasts\nat least one year", "zh": "≥ 95% 的情境：糧食\n可支撐至少一年"}[lang],
                    transform=ax.transAxes, fontsize=10, color=INK2)
        ax.set_xlim(0, 365); ax.set_ylim(-0.02, 1.03)
        ax.set_xticks([0, 90, 180, 270, 365])
        ax.set_xlabel(T[lang]["days_since"])
    axes[0].set_ylabel(T[lang]["p_food"])
    axes[0].set_yticks([0, 0.25, 0.5, 0.75, 1.0]); axes[0].set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    h, l = axes[1].get_legend_handles_labels()
    fig.legend(h, l, ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.06), fontsize=10.5)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _save(fig, out, "km_scenarios")


def fig_onset(on: pd.DataFrame, out: Path, lang: str):
    setup(lang)
    fig, ax = plt.subplots(figsize=(6.6, 3.5))
    for a, b in [(5.6, 7.9), (9.9, 11.9)]:
        ax.axvspan(a, b, color="#F4E7C5", lw=0, zorder=0)
    ax.text(6.75, 380, T[lang]["harvest"], ha="center", fontsize=9, color=INK2)
    ax.text(10.9, 380, T[lang]["harvest"], ha="center", fontsize=9, color=INK2)
    for s in ["S2", "S3"]:
        d = on[(on.scenario == s) & (on.lever == "baseline")].sort_values("month")
        y = np.minimum(d["median"].to_numpy(), 365)
        ax.plot(d.month, y, color=SCEN_COL[s], lw=2.2, marker="o", ms=5, mec=SURF, mew=1.5, label=T[lang][s])
        ax.text(12.25, y[-1], T[lang][s], va="center", fontsize=10, color=INK)
    ax.set_xticks(range(1, 13)); ax.set_xticklabels(T[lang]["months"], fontsize=9.5)
    ax.set_xlim(0.6, 13.4); ax.set_ylim(0, 400)
    ax.set_ylabel(T[lang]["median_T"]); ax.set_xlabel(T[lang]["onset_x"])
    ax.legend(loc="lower left", ncol=2)
    _save(fig, out, "onset_month")


def fig_phi_sweep(ps: pd.DataFrame, out: Path, lang: str):
    setup(lang)
    fig, ax = plt.subplots(figsize=(7.6, 4.1))
    for lv in ["baseline", "rationing", "civil_package"]:
        d = ps[ps.lever == lv].sort_values("phi")
        y = np.minimum(d["median"].to_numpy(), 365)
        if lv == "baseline":
            ax.fill_between(d.phi * 100, np.minimum(d.q25, 365), np.minimum(d.q75, 365), color=LEVER_COL[lv],
                            alpha=0.15, lw=0)
        ax.plot(d.phi * 100, y, color=LEVER_COL[lv], lw=2.4, label=T[lang][lv])
    ax.axhline(365, color=AXIS, lw=1)
    ax.text(101, 365, T[lang]["year"], va="center", fontsize=10, color=INK2)
    ann = {
        "en": [(5, 125, "Total isolation:\n~4 months", "left"),
               (33, 186, "Parameters 2023:\n'~6 months'", "left"),
               (68, 330, "CSIS 2025: 'food was\nnot a problem' (shipping\ncontinues / convoys)", "left")],
        "zh": [(5, 125, "全面孤立：\n約4個月", "left"),
               (33, 186, "Parameters 2023：\n「約6個月」", "left"),
               (68, 330, "CSIS 2025：「糧食\n不是問題」（航運持續／護航）", "left")],
    }[lang]
    pts = [(0, 119), (35, 190), (65, 365)]
    for (x, y, txt, ha), (px, py) in zip(ann, pts):
        ax.plot(px, min(py, 365), "o", color=INK, ms=5)
        ax.annotate(txt, (px, min(py, 365)), xytext=(x + 3, y - 60 if px < 60 else y - 110),
                    fontsize=9.5, color=INK, ha=ha,
                    arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.set_xlim(0, 100); ax.set_ylim(0, 400)
    ax.set_xlabel(T[lang]["phi_x"] + " (%)"); ax.set_ylabel(T[lang]["median_T"])
    ax.legend(loc="upper left")
    _save(fig, out, "phi_sweep")


def fig_county(ca: pd.DataFrame, out: Path, lang: str, variant: str = "baseline_disrupted"):
    setup(lang)
    d = ca[ca.variant == variant].copy()
    d["Tm"] = np.minimum(d["median"], 365)
    nat = float(d["national_median"].iloc[0])
    d["early"] = np.maximum(nat - d["Tm"], 0)
    fig = plt.figure(figsize=(12.0, 6.2))
    ax = fig.add_axes([0.0, 0.02, 0.47, 0.96])
    bins = [0, 5, 20, 40, 70, 110, 1e9]
    for _, r in d.iterrows():
        x, y = TILES[r.code]
        k = np.searchsorted(bins, r.early, side="right") - 1
        col = SEQ_ORANGE[min(k, len(SEQ_ORANGE) - 1)]
        ax.add_patch(FancyBboxPatch((x - 0.46, -y - 0.42), 0.92, 0.84, boxstyle="round,pad=0,rounding_size=0.12",
                                    fc=col, ec=SURF, lw=2))
        dark = k >= 3
        fs = 8.0 if lang == "en" else 9.0
        ax.text(x, -y + 0.13, SHORT[lang][r.code], ha="center", va="center", fontsize=fs,
                color=SURF if dark else INK, fontweight="bold")
        ax.text(x, -y - 0.2, f"{r.Tm:.0f}" if r.Tm < 365 else "365+", ha="center", va="center", fontsize=fs + 0.4,
                color=SURF if dark else INK2)
    ax.set_xlim(-1.7, 5.2); ax.set_ylim(-10.6, 0.7); ax.set_aspect("equal"); ax.axis("off")
    ax.text(-1.6, -10.35, {"en": "Tile = county; number = median days of food", "zh": "每格為一縣市；數字為糧食續航天數中位數"}[lang],
            fontsize=8.8, color=INK2)
    # legend for the ramp
    lx, ly = -1.0, -8.0
    lab_bins = {"en": ["< 5", "5–20", "20–40", "40–70", "70–110", "> 110"], "zh": ["< 5", "5–20", "20–40", "40–70", "70–110", "> 110"]}[lang]
    ax.text(lx - 0.35, ly + 0.55, {"en": "days earlier\nthan national", "zh": "較全國平均\n提早斷糧天數"}[lang], fontsize=8.4, color=INK2)
    for i, (c, lb) in enumerate(zip(SEQ_ORANGE, lab_bins)):
        ax.add_patch(Rectangle((lx - 0.3, ly - 0.36 * i - 0.3), 0.32, 0.26, fc=c, ec="none"))
        ax.text(lx + 0.12, ly - 0.36 * i - 0.17, lb, fontsize=8.2, va="center", color=INK2)
    # ranked bars
    ax2 = fig.add_axes([0.58, 0.10, 0.41, 0.86])
    d = d.sort_values("Tm")
    names = [SHORT[lang][c] for c in d.code]
    cols = [SEQ_ORANGE[min(np.searchsorted(bins, e, side="right") - 1, 5)] for e in d.early]
    ax2.barh(range(len(d)), d.Tm, color=cols, height=0.62, edgecolor="none")
    ax2.axvline(nat, color=INK, lw=1.2)
    ax2.text(nat + 3, len(d) - 0.6, ({"en": f"national median {nat:.0f} d", "zh": f"全國中位數 {nat:.0f} 天"}[lang]),
             fontsize=9, color=INK)
    ax2.set_yticks(range(len(d))); ax2.set_yticklabels(names, fontsize=9)
    ax2.set_xlim(0, 380)
    ax2.set_xlabel(T[lang]["median_T"])
    ax2.grid(axis="y", visible=False)
    _save(fig, out, f"county_{variant}")


def fig_levers(gains: pd.DataFrame, out: Path, lang: str):
    setup(lang)
    order = ["rationing", "feed2food", "surge", "rice_plus3", "dispersed", "convoy", "civil_package", "full_package"]
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.6), sharey=True)
    for ax, s in zip(axes, ["S2", "S3"]):
        g = gains[gains.scenario == s].set_index("lever").loc[order]
        ys = np.arange(len(order))[::-1]
        for y, (lv, r) in zip(ys, g.iterrows()):
            pk = lv in ("civil_package", "full_package")
            ax.plot([r.q05, r.q95], [y, y], color=SCEN_COL[s], lw=1.2, alpha=0.55, solid_capstyle="round")
            ax.plot([r.q25, r.q75], [y, y], color=SCEN_COL[s], lw=5, alpha=0.9, solid_capstyle="round")
            ax.plot(r.median_gain, y, "o", color=SURF, mec=SCEN_COL[s], mew=2, ms=8 if pk else 7)
            ax.text(r.q95 + 4, y, f"+{r.median_gain:.0f}", va="center", fontsize=10,
                    color=INK, fontweight="bold" if pk else "normal")
        ax.axhline(1.5, color=AXIS, lw=0.8)
        ax.set_title(T[lang][s + "_long"], loc="left", fontsize=11.5, color=INK)
        ax.set_xlim(-5, 300)
        ax.axvline(0, color=AXIS, lw=0.8)
        ax.set_yticks(ys); ax.set_yticklabels([LEVER_LABEL[lang][o] for o in order], fontsize=10)
        ax.grid(axis="y", visible=False)
    fig.supxlabel(T[lang]["gain_x"], fontsize=10.5, color=INK2, y=0.02)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    _save(fig, out, "lever_gains")


def fig_sobol(sob: pd.DataFrame, out: Path, lang: str, top: int = 7):
    setup(lang)
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 3.9))
    for ax, s in zip(axes, ["S2", "S3"]):
        d = sob[sob.scenario == s].sort_values("ST", ascending=False).head(top)[::-1]
        ax.barh(range(len(d)), d.ST.clip(lower=0), color=SCEN_COL[s], height=0.55, edgecolor="none")
        for i, v in enumerate(d.ST):
            ax.text(v + 0.01, i, f"{v:.2f}", va="center", fontsize=9.5, color=INK)
        ax.set_yticks(range(len(d))); ax.set_yticklabels([PARAM_LABEL[lang].get(p, p) for p in d.parameter], fontsize=10)
        ax.set_xlim(0, max(0.7, d.ST.max() + 0.12))
        ax.set_title(T[lang][s + "_long"], loc="left", fontsize=11.5, color=INK)
        ax.grid(axis="y", visible=False)
    fig.supxlabel(T[lang]["sobol_x"], fontsize=10.5, color=INK2, y=0.02)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    _save(fig, out, "sobol")


def fig_county_map(ca: pd.DataFrame, out: Path, lang: str, variant: str = "baseline_disrupted"):
    """Tile map only (used next to a native bar chart in the slides)."""
    setup(lang)
    d = ca[ca.variant == variant].copy()
    d["Tm"] = np.minimum(d["median"], 365)
    nat = float(d["national_median"].iloc[0])
    d["early"] = np.maximum(nat - d["Tm"], 0)
    bins = [0, 5, 20, 40, 70, 110, 1e9]
    fig = plt.figure(figsize=(5.0, 7.2))
    ax = fig.add_axes([0, 0, 1, 1])
    for _, r in d.iterrows():
        x, y = TILES[r.code]
        k = np.searchsorted(bins, r.early, side="right") - 1
        col = SEQ_ORANGE[min(k, len(SEQ_ORANGE) - 1)]
        ax.add_patch(FancyBboxPatch((x - 0.46, -y - 0.42), 0.92, 0.84, boxstyle="round,pad=0,rounding_size=0.12",
                                    fc=col, ec=SURF, lw=2))
        dark = k >= 3
        fs = 8.4 if lang == "en" else 10.0
        ax.text(x, -y + 0.19, SHORT[lang][r.code], ha="center", va="center", fontsize=fs,
                color=SURF if dark else INK, fontweight="bold")
        ax.text(x, -y - 0.17, f"{r.Tm:.0f}" if r.Tm < 365 else "365+", ha="center", va="center",
                fontsize=13, fontweight="bold", color=SURF if dark else INK)
    lx, ly = -1.1, -8.2
    lab_bins = ["< 5", "5–20", "20–40", "40–70", "70–110", "> 110"]
    ax.text(lx - 0.3, ly + 0.62, {"en": "Number = median days\nColor = days earlier\nthan national median",
                                  "zh": "數字＝中位斷糧天數\n顏色＝較全國中位數\n提早的天數"}[lang],
            fontsize=9.5, color=INK2, va="bottom", linespacing=1.25)
    for i, (c, lb) in enumerate(zip(SEQ_ORANGE, lab_bins)):
        ax.add_patch(Rectangle((lx - 0.3, ly - 0.34 * i - 0.3), 0.34, 0.26, fc=c, ec="none"))
        ax.text(lx + 0.14, ly - 0.34 * i - 0.17, lb, fontsize=9.5, va="center", color=INK2)
    ax.set_xlim(-1.7, 5.2); ax.set_ylim(-10.3, 0.7); ax.set_aspect("equal"); ax.axis("off")
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"county_map_{variant}.png", dpi=260, transparent=False)
    plt.close(fig)
