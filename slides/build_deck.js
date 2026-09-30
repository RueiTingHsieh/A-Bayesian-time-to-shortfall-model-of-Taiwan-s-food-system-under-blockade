// Build the 15-slide deck (English or Traditional Chinese) from outputs/slide_data.json.
//   node slides/build_deck.js en out.pptx
//   node slides/build_deck.js zh out.pptx
// Charts are native PowerPoint charts (editable); the county tile map and the title
// artwork are images rendered by the Python pipeline.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa6");
const gi = require("react-icons/gi");

const LANG = process.argv[2] || "en";
const OUT = process.argv[3] || `deck_${LANG}.pptx`;
const ROOT = path.resolve(__dirname, "..");
const D = JSON.parse(fs.readFileSync(path.join(ROOT, "outputs", "slide_data.json"), "utf8"));
const FIG = path.join(ROOT, "outputs", "figures");
const ZH = LANG === "zh";

const C = {
  navy: "0E2841", navy2: "173A61", ink: "1B2A3A", ink2: "4F5B66", muted: "7E878F",
  amber: "E3A21A", amberD: "B07A05", amberL: "FBF1DA", card: "F2F5F8", line: "D5DCE3", white: "FFFFFF",
  ice: "CADCFC", blue: "2A78D6", orange: "EB6834", aqua: "1BAF7A", yellow: "EDA100", gray: "9A968C",
  s1: "86B6EF", s2: "2A78D6", s3: "104281", blueL: "B7D3F6", navyL: "9DB1CB",
  harvest: "F4E7C5", grid: "E6E4DD",
};
const F = ZH ? { head: "Microsoft JhengHei", body: "Microsoft JhengHei" } : { head: "Cambria", body: "Calibri" };
const W = 13.333, H = 7.5, MX = 0.6;
const TOTAL = 15;

// ------------------------------------------------------------------------------------------
const L = (en, zh) => (ZH ? zh : en);
const fmt = (v, d = 0) => Number(v).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
const pct = (v) => `${Math.round(v * 100)}%`;
const S = (s, lv) => D.summary[`${s}|${lv}`];
const G = (s, lv) => D.gains[`${s}|${lv}`];
const A = (s, t) => D.aft[`${s}|${t}`];
const days = (v) => (v === null || v >= 365 ? L("≥ 1 year", "≥ 1 年") : L(`${fmt(v)} days`, `${fmt(v)} 天`));
const MONTH_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const monthName = (i) => (ZH ? `${i + 1}月` : MONTH_EN[i]);
const argMin = (a) => a.indexOf(Math.min(...a));
const argMax = (a) => a.indexOf(Math.max(...a));
const ISL = ["KIN", "PEN", "LIE"], METRO = ["TPE", "NTP", "KEE"], RICEBELT = ["CHA", "YUN", "CYQ", "HUA", "TTT"];
const cMed = (variant, code) => D.county[variant].find((r) => r.code === code).median;
const cAvg = (variant, codes) => Math.round(codes.reduce((a, c) => a + cMed(variant, c), 0) / codes.length);
const cRange = (variant, codes) => { const v = codes.map((c) => cMed(variant, c)); return [Math.min(...v), Math.max(...v)]; };
const rng = ([a, b]) => (a === b ? fmt(a) : `${fmt(a)}–${fmt(b)}`);
const round5 = (v) => fmt(Math.round(v / 5) * 5);
const FBSY = D.fbs_year;

async function icon(Comp, color = "FFFFFF", size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: `#${color}`, size: `${size}px` }));
  const buf = await sharp(Buffer.from(svg)).resize(size, size).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

function text(slide, t, o = {}) {
  slide.addText(t, Object.assign({
    isTextBox: true, margin: 0, fontFace: F.body, fontSize: 13, color: C.ink, valign: "top",
    paraSpaceAfter: 0, fit: "none", lang: ZH ? "zh-TW" : "en-US",
  }, o));
}

function header(slide, kicker, title, takeaway) {
  text(slide, kicker, { x: MX, y: 0.34, w: 10.5, h: 0.3, fontSize: 11, bold: true, color: C.amberD, charSpacing: ZH ? 1 : 2 });
  text(slide, title, { x: MX, y: 0.62, w: 12.1, h: 0.72, fontFace: F.head, fontSize: ZH ? 26 : 29, bold: true, color: C.navy, valign: "middle" });
  if (takeaway) text(slide, takeaway, { x: MX, y: 1.36, w: 12.1, h: 0.42, fontSize: ZH ? 14 : 15, color: C.ink2 });
}

function footer(slide, n, src) {
  if (src) text(slide, src, { x: MX, y: 7.03, w: 11.0, h: 0.3, fontSize: 8.5, color: C.muted, valign: "middle" });
  text(slide, `${n} / ${TOTAL}`, { x: 11.9, y: 7.03, w: 0.83, h: 0.3, fontSize: 9, color: C.muted, align: "right", valign: "middle" });
}

function card(slide, x, y, w, h, fill = C.card, line = null) {
  slide.addShape("roundRect", { x, y, w, h, fill: { color: fill }, line: line ? { color: line, width: 0.75 } : { type: "none" }, rectRadius: 0.08 });
}

function circleIcon(slide, img, x, y, d, fill) {
  slide.addShape("ellipse", { x, y, w: d, h: d, fill: { color: fill }, line: { type: "none" } });
  const p = d * 0.25;
  slide.addImage({ data: img, x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p });
}

function chartBase(extra = {}) {
  return Object.assign({
    catAxisLabelFontFace: F.body, valAxisLabelFontFace: F.body, legendFontFace: F.body, titleFontFace: F.body,
    dataLabelFontFace: F.body, catAxisLabelColor: C.ink2, valAxisLabelColor: C.ink2, catAxisLabelFontSize: 11,
    valAxisLabelFontSize: 10, legendFontSize: 11, legendColor: C.ink, titleColor: C.ink,
    valGridLine: { color: C.grid, size: 0.75 }, catGridLine: { style: "none" },
    catAxisLineColor: "C3C2B7", valAxisLineColor: "C3C2B7", showLegend: false,
  }, extra);
}

// ------------------------------------------------------------------------------------------
async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.author = "謝瑞庭";
  pres.title = L("Food Endurance as Deterrence", "糧食續航力即嚇阻力");

  const I = {
    wheat: await icon(fa.FaWheatAwn), ship: await icon(fa.FaShip), bolt: await icon(fa.FaBolt),
    file: await icon(fa.FaFileLines), users: await icon(fa.FaUsers), shield: await icon(fa.FaShieldHalved),
    flask: await icon(fa.FaFlask), chess: await icon(fa.FaChessKnight), landmark: await icon(fa.FaLandmark),
    clock: await icon(fa.FaClock), map: await icon(fa.FaMapLocationDot), scale: await icon(fa.FaScaleBalanced),
    list: await icon(fa.FaListCheck), gears: await icon(fa.FaGears), corn: await icon(gi.GiCorn, C.amberD),
    wheatA: await icon(gi.GiWheat, C.amberD), peas: await icon(gi.GiPeas, C.amberD), bullseye: await icon(fa.FaBullseye),
    anchor: await icon(fa.FaAnchor), chart: await icon(fa.FaMagnifyingGlassChart), code: await icon(fa.FaCode),
    warehouse: await icon(fa.FaWarehouse), bowl: await icon(fa.FaBowlRice),
  };

  // =========================================================================================
  // 1. Title
  // =========================================================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.navy };
    s.addImage({ path: path.join(FIG, "hero.png"), x: 0, y: 0, w: W, h: H });
    text(s, L("FINAL PRESENTATION  ·  NATIONAL DEFENSE POLICY", "期末報告　·　國防政策"),
      { x: 0.8, y: 1.35, w: 7.5, h: 0.35, fontSize: 12, bold: true, color: C.amber, charSpacing: ZH ? 2 : 3 });
    text(s, L("Food Endurance\nas Deterrence", "糧食續航力\n即嚇阻力"),
      { x: 0.8, y: 1.8, w: 7.4, h: 1.95, fontFace: F.head, fontSize: ZH ? 46 : 50, bold: true, color: C.white, valign: "top" });
    text(s, L("How long can Taiwan feed itself under blockade, and which policies buy the most time? A Bayesian time-to-shortfall model for all-out defense mobilization.",
      "封鎖下臺灣能養活自己多久？哪些政策最能爭取時間？——以貝氏「斷糧時間」模型支援全民防衛動員"),
      { x: 0.8, y: 3.85, w: 6.9, h: 1.0, fontSize: ZH ? 16 : 17, color: C.ice });
    card(s, 0.8, 5.15, 5.6, 1.5, C.navy2);
    const rows = ZH
      ? [["姓名", "謝瑞庭"], ["學號", "R14621208"], ["系級", "農藝所生統組 碩二"]]
      : [["Name 姓名", "謝瑞庭"], ["Student ID 學號", "R14621208"], ["Program 系級", "農藝所生統組 碩二"]];
    rows.forEach(([k, v], i) => {
      text(s, k, { x: 1.05, y: 5.3 + i * 0.42, w: 1.9, h: 0.36, fontSize: 13, color: C.amber, bold: true, valign: "middle" });
      text(s, v, { x: 3.0, y: 5.3 + i * 0.42, w: 3.3, h: 0.36, fontSize: 15, color: C.white, bold: true, valign: "middle", fontFace: "Microsoft JhengHei" });
    });
    text(s, L("Each strand: share of simulated futures that still have enough food, day by day. Gold = military blockade; blue = total isolation.",
      "每條曲線：模擬未來中糧食仍足夠的比例（逐日）。金色＝軍事封鎖；藍色＝全面孤立。"),
    { x: 7.2, y: 6.72, w: 5.53, h: 0.45, fontSize: 10, color: C.navyL, align: "right" });
    s.addNotes(L("Title. The question: how long can Taiwan's food system last under a blockade, and which policies extend it most? The analysis turns the midterm proposal into a working, open-source model.",
      "標題。核心問題：封鎖下臺灣的糧食系統能撐多久？哪些政策最能延長？本報告把期中計畫實際做成可重現的開源模型。"));
  }

  // =========================================================================================
  // 2. Motivation: timeline + stats
  // =========================================================================================
  {
    const s = pres.addSlide();
    header(s, L("01 · WHY FOOD, WHY NOW", "01 · 為何是糧食、為何是現在"),
      L("Blockade is the PLA's most-rehearsed coercive option", "封鎖已是共軍演練最頻繁的脅迫選項"),
      L("Each drill since 2022 has moved closer to cutting Taiwan's ports, fuel and supply lines.", "2022年以來，每一次演習都更接近切斷臺灣的港口、能源與補給線。"));
    const ev = ZH ? [
      ["2022.08", "裴洛西訪臺後大規模演習", "首次形成環臺封控範本"],
      ["2023.04", "聯合利劍", "環島封控與精準打擊演練"],
      ["2024.05", "聯合利劍-2024A", "賴總統就職後環臺演習"],
      ["2024.10", "聯合利劍-2024B", "海警環臺「執法巡查」；演練「要港要域封控」"],
      ["2025.04", "海峽雷霆-2025A", "聯合封控；模擬打擊港口與能源設施（目標酷似永安液化天然氣接收站）"],
      ["2025.12", "正義使命-2025", "演練要港要域封控；27枚火箭彈落於基隆東北、臺南以西海域"],
      ["2026.08", "漢光42號（我方）", "軍民同一想定整合演練，首度模擬行動網路中斷"],
    ] : [
      ["Aug 2022", "Drills after the Pelosi visit", "first encirclement template"],
      ["Apr 2023", "Joint Sword", "encirclement and precision-strike rehearsal"],
      ["May 2024", "Joint Sword-2024A", "encirclement after President Lai's inauguration"],
      ["Oct 2024", "Joint Sword-2024B", "coast-guard 'law-enforcement' patrols circle Taiwan; blockade of key ports rehearsed"],
      ["Apr 2025", "Strait Thunder-2025A", "joint blockade; mock strikes on ports and energy sites (one resembled Yong'an LNG terminal)"],
      ["Dec 2025", "Justice Mission-2025", "'blockade of key ports'; 27 rockets land NE of Keelung and W of Tainan"],
      ["Aug 2026", "Han Kuang 42 (Taiwan)", "civil and military drills under one scenario; first mobile-internet slowdown"],
    ];
    const y0 = 2.05, dy = 0.67;
    s.addShape("line", { x: 1.83, y: y0 + 0.14, w: 0, h: dy * (ev.length - 1), line: { color: C.line, width: 1.5 } });
    ev.forEach(([d, n, t], i) => {
      const y = y0 + i * dy;
      const last = i === ev.length - 1;
      text(s, d, { x: MX, y: y, w: 1.05, h: 0.3, fontSize: 12, bold: true, color: last ? C.aqua : C.amberD });
      s.addShape("ellipse", { x: 1.745, y: y + 0.055, w: 0.17, h: 0.17, fill: { color: last ? C.aqua : C.navy }, line: { color: C.white, width: 1.5 } });
      text(s, [{ text: n, options: { bold: true, color: C.navy } }, { text: ZH ? `　${t}` : `  —  ${t}`, options: { color: C.ink2 } }],
        { x: 2.1, y: y - 0.02, w: 5.9, h: 0.55, fontSize: ZH ? 12.5 : 13 });
    });
    const st = [
      [I.wheat, "30.7%", L("calorie self-sufficiency in 2024 (MOA)", "2024年熱量自給率（農業部）"), C.navy],
      [I.ship, "~70%", L("of Taiwan's calories are imported", "熱量仰賴進口"), C.navy],
      [I.bolt, L("10–11 days", "10–11天"), L("of LNG in stock (MOEA via EIA, 2026)", "天然氣存量（經濟部，2026）"), C.amberD],
    ];
    st.forEach(([img, big, lab, col], i) => {
      const y = 2.0 + i * 1.62;
      card(s, 8.45, y, 4.28, 1.45);
      circleIcon(s, img, 8.7, y + 0.37, 0.72, col);
      text(s, big, { x: 9.65, y: y + 0.18, w: 2.95, h: 0.68, fontFace: F.head, fontSize: 34, bold: true, color: col, valign: "middle" });
      text(s, lab, { x: 9.65, y: y + 0.86, w: 2.95, h: 0.5, fontSize: 12, color: C.ink2 });
    });
    footer(s, 2, L("Sources: CSIS ChinaPower; SCMP (Apr 2025); CNA (30 Dec 2025); Taipei Times (22 Jul 2026); MOA (Nov 2025); EIA Taiwan Analysis Brief (Apr 2026).",
      "資料來源：CSIS ChinaPower；SCMP（2025.4）；中央社（2025.12.30）；Taipei Times（2026.7.22）；農業部（2025.11）；EIA Taiwan Analysis Brief（2026.4）。"));
    s.addNotes(L("Since 2022 every major PLA drill has rehearsed parts of a blockade - key ports, energy sites, coast-guard 'law-enforcement' patrols. Taiwan imports about 70% of its calories and holds only 10-11 days of LNG. Food is the slow variable nobody has quantified.",
      "2022年以來，共軍每次大型演習都在演練封鎖的一部分：要港封控、能源設施、海警「執法巡查」。臺灣約七成熱量仰賴進口，天然氣只有10–11天存量。糧食是還沒有人量化的慢變數。"));
  }

  // =========================================================================================
  // 3. Policy frame
  // =========================================================================================
  {
    const s = pres.addSlide();
    header(s, L("02 · POLICY FRAME", "02 · 政策脈絡"),
      L("All-out defense has plans and stations, but no endurance metric", "全民防衛動員有計畫、有配售站，卻沒有「續航力」指標"));
    const docs = ZH ? [
      [I.file, "《108年國防報告書》", "整合軍民總體力量，實踐全民國防"],
      [I.file, "《110年四年期國防總檢討》", "中共可封鎖我重要港口、切斷海上交通線"],
      [I.users, "RAND（Easton et al., 2017）", "可信的後備戰力使北京面對「壓倒性抵抗」"],
      [I.shield, "《114年QDR》· 全社會防衛韌性委員會", "提高外離島戰備口糧儲備；「重要民生物資盤整暨配送」為主軸"],
    ] : [
      [I.file, "2019 National Defense Report", "All-out defense integrates total civil and military power"],
      [I.file, "2021 Quadrennial Defense Review", "PRC could blockade vital ports and sever sea lines of communication"],
      [I.users, "RAND (Easton et al., 2017)", "Credible reserves confront Beijing with 'overwhelming resistance'"],
      [I.shield, "2025 QDR · Resilience Committee (2024)", "More combat rations on outlying islands; essential-supplies distribution as a pillar"],
    ];
    docs.forEach(([img, t, d], i) => {
      const y = 1.72 + i * 1.28;
      card(s, MX, y, 6.35, 1.12);
      circleIcon(s, img, MX + 0.22, y + 0.25, 0.62, C.navy);
      text(s, t, { x: MX + 1.05, y: y + 0.14, w: 5.1, h: 0.38, fontSize: 14, bold: true, color: C.navy });
      text(s, d, { x: MX + 1.05, y: y + 0.52, w: 5.1, h: 0.5, fontSize: 12.5, color: C.ink2 });
    });
    const chain = ZH
      ? ["行政院全民防衛動員準備業務會報", "經濟部　物資經濟動員準備方案（9項分類計畫）", "農業部　糧食動員準備計畫", "143處公糧配售站", "民眾與動員兵力"]
      : ["Executive Yuan mobilization council", "MOEA: materiel & economic mobilization (9 plans)", "MOA: Food Mobilization Preparation Plan", "143 public-grain distribution stations", "Citizens and mobilized forces"];
    const cx = 7.35, cw = 5.38, bh = 0.6, gap = 0.2;
    chain.forEach((t, i) => {
      const y = 1.72 + i * (bh + gap);
      const hi = i === 2;
      s.addShape("roundRect", { x: cx, y, w: cw, h: bh, rectRadius: 0.06, fill: { color: hi ? C.navy : C.white }, line: { color: hi ? C.navy : C.line, width: 1 } });
      text(s, t, { x: cx + 0.2, y, w: cw - 0.4, h: bh, fontSize: 13, bold: hi, color: hi ? C.white : C.ink, valign: "middle", align: "center" });
      if (i < chain.length - 1) s.addShape("downArrow", { x: cx + cw / 2 - 0.12, y: y + bh + 0.02, w: 0.24, h: gap - 0.04, fill: { color: C.navyL }, line: { type: "none" } });
    });
    card(s, cx, 5.8, cw, 1.02, C.amberL);
    text(s, [
      { text: L("Today's rule is an input: ", "現行規範是投入型："), options: { bold: true, color: C.ink } },
      { text: L("rice reserve ≥ 3 months. ", "稻米安全存量 ≥ 3個月。"), options: { color: C.ink } },
      { text: L("Missing: how many days does the whole diet last?", "缺少的是：整體飲食能撐幾天？"), options: { bold: true, color: C.amberD } },
    ], { x: cx + 0.22, y: 5.9, w: cw - 0.44, h: 0.84, fontSize: 13, valign: "middle" });
    footer(s, 3, L("Sources: MND 2019 NDR; MND 2021 & 2025 QDR; RAND RR-1757-OSD; Presidential Office (2024); All-out Defense Mobilization Agency; MOA (Mar 2025).",
      "資料來源：國防部108年國防報告書；110年、114年四年期國防總檢討；RAND RR-1757-OSD；總統府（2024）；全民防衛動員署；農業部（2025.3）。"));
    s.addNotes(L("Course readings frame the problem: the NDR defines all-out defense, the 2021 QDR names the blockade threat, and RAND argues deterrence comes from credible resistance. The mobilization chain exists down to 143 distribution stations - but the only standard is an input: three months of rice.",
      "課程文本界定了問題：國防報告書定義全民國防，110年QDR點出封鎖威脅，RAND主張嚇阻來自可信的抵抗。動員體系一路到143處配售站都在，但唯一的標準是投入型的「3個月稻米」。"));
  }

  // =========================================================================================
  // 4. Evidence gap
  // =========================================================================================
  {
    const s = pres.addSlide();
    header(s, L("03 · THE EVIDENCE GAP", "03 · 實證缺口"),
      L("Three authoritative answers, and none comes with uncertainty", "三個權威答案，都沒有附帶不確定性"));
    const claims = ZH ? [
      [I.flask, "Parameters（2023）", "「除稻米外，存糧約可撐6個月」", "美國陸軍戰爭學院期刊"],
      [I.chess, "CSIS 兵棋推演（2025）", "「糧食不是問題」", "26場封鎖兵推"],
      [I.landmark, "農業部長（2025年3月）", "「公糧5.5個月；含民間約1年」", "立法院答詢"],
    ] : [
      [I.flask, "Parameters (2023)", "“Food stocks (except rice) last ~6 months”", "U.S. Army War College quarterly"],
      [I.chess, "CSIS wargames (2025)", "“Food was not a problem”", "26 blockade wargames"],
      [I.landmark, "Minister of Agriculture (Mar 2025)", "“5.5 months of public grain; ~1 year incl. private”", "Legislative Yuan"],
    ];
    claims.forEach(([img, src, q, ctx], i) => {
      const x = MX + i * 4.1;
      card(s, x, 1.75, 3.9, 1.8);
      circleIcon(s, img, x + 0.22, 1.95, 0.56, C.navy);
      text(s, src, { x: x + 0.95, y: 1.97, w: 2.8, h: 0.5, fontSize: 13, bold: true, color: C.navy, valign: "middle" });
      text(s, q, { x: x + 0.22, y: 2.6, w: 3.5, h: 0.62, fontSize: ZH ? 14.5 : 15, bold: true, color: C.ink, fontFace: F.head });
      text(s, ctx, { x: x + 0.22, y: 3.18, w: 3.5, h: 0.3, fontSize: 11, color: C.muted });
    });
    const cv = D.conv;
    const labs = ZH
      ? ["3個月稻米（法定最低安全存量）", "5.5個月稻米（公糧，2025年3月）", "約12個月稻米（含民間，收穫後）"]
      : ["3 months of rice (legal minimum)", "5.5 months of rice (public, Mar 2025)", "~12 months of rice (incl. private, post-harvest)"];
    const vals = [cv.legal_3_months_days, cv.public_5p5_months_days, cv.about_one_year_days].map((v) => Math.round(v));
    s.addChart(pres.charts.BAR, [{ name: L("Days", "天數"), labels: labs.slice().reverse(), values: vals.slice().reverse() }],
      chartBase({ x: MX, y: 3.85, w: 7.6, h: 3.0, barDir: "bar", chartColors: [C.amber], barGapWidthPct: 55,
        showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: ZH ? '0" 天"' : '0" days"', dataLabelFontSize: 13,
        dataLabelFontBold: true, dataLabelColor: C.ink, valAxisHidden: true, valGridLine: { style: "none" }, valAxisMaxVal: 80, valAxisMinVal: 0,
        catAxisLabelFontSize: 12, showTitle: true, title: L("Months of rice converted to days of the whole diet's minimum need", "把「稻米月數」換算成「全民最低熱量需求天數」"),
        titleFontSize: 13, titleBold: true }));
    card(s, 8.55, 3.95, 4.18, 2.85, C.navy);
    const share = D.diet.rice / D.diet.total;
    text(s, `≈ ${Math.round(share * 100)}%`, { x: 8.85, y: 4.15, w: 3.6, h: 0.85, fontFace: F.head, fontSize: 44, bold: true, color: C.amber, valign: "middle" });
    text(s, L(`Rice supplies only ~${Math.round(share * 100)}% of calories. Reading "months of rice" as months of food overstates endurance about ${Math.round(90 / cv.legal_3_months_days)}-fold.`,
      `稻米只占熱量約${Math.round(share * 100)}%。把「稻米月數」當成「糧食月數」，會把續航力高估約${Math.round(90 / cv.legal_3_months_days)}倍。`),
      { x: 8.85, y: 5.05, w: 3.62, h: 1.6, fontSize: 14, color: C.white });
    footer(s, 4, L("Sources: Ferreira & Critelli, Parameters 53(2) (2023); Cancian, Cancian & Heginbotham, CSIS (2025) p.xii; CNA (26 Mar 2025). Minimum need ≈ 2,328 kcal/person/day (model median).",
      "資料來源：Ferreira & Critelli（2023）；Cancian, Cancian & Heginbotham, CSIS（2025）；中央社（2025.3.26）。最低需求≈每人每日2,328大卡（模型中位數）。"));
    s.addNotes(L(`Three credible sources give three different answers because they measure different things. Converting 'months of rice' into days of the whole population's minimum calorie need shows why: rice is only about ${Math.round(share * 100)}% of calories.`,
      `三個可信來源給出三種答案，因為衡量的東西不同。把「稻米月數」換算成全體國人最低熱量需求的天數，就看得出原因：稻米只占熱量約${Math.round(share * 100)}%。`));
  }

  // =========================================================================================
  // 5. RQs & framework
  // =========================================================================================
  {
    const s = pres.addSlide();
    header(s, L("04 · QUESTIONS & FRAMEWORK", "04 · 研究問題與架構"),
      L("Treat the island's food system like a patient cohort", "把全島糧食系統當作一個「病人世代」來分析"));
    const rqs = ZH ? [
      [I.clock, "RQ1　能撐多久？", "三種封鎖型態下糧食續航力的機率分布，以及封鎖開始季節的影響"],
      [I.map, "RQ2　何處先告急？", "哪些縣市最先斷糧：外離島、都會區，還是稻作區？"],
      [I.scale, "RQ3　何者最有效？", "配給、飼料轉糧、搶種、增儲、分散、護航各能多撐幾天？"],
      [I.list, "RQ4　如何制度化？", "把指標、啟動門檻與演習狀況注入寫進動員計畫"],
    ] : [
      [I.clock, "RQ1  How long?", "Distribution of food endurance under three blockade types, and the effect of the season it starts"],
      [I.map, "RQ2  Where first?", "Which counties run short first: outlying islands, metros, or the rice belt?"],
      [I.scale, "RQ3  What works best?", "Days gained by rationing, feed-to-food, surge planting, reserves, dispersal, convoys"],
      [I.list, "RQ4  How to institutionalize?", "Metric, triggers and exercise injects for the mobilization plans"],
    ];
    rqs.forEach(([img, t, d], i) => {
      const y = 1.72 + i * 1.28;
      card(s, MX, y, 6.2, 1.12);
      circleIcon(s, img, MX + 0.22, y + 0.25, 0.62, i === 0 ? C.amberD : C.navy);
      text(s, t, { x: MX + 1.05, y: y + 0.13, w: 4.95, h: 0.38, fontSize: 15, bold: true, color: C.navy });
      text(s, d, { x: MX + 1.05, y: y + 0.52, w: 4.95, h: 0.52, fontSize: 12.5, color: C.ink2 });
    });
    const hdr = (t) => ({ text: t, options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 13 } });
    const rows = ZH ? [
      [hdr("臨床試驗"), hdr("糧食續航力模型")],
      ["病人", "一個模擬的未來（每情境5,000個）"],
      ["死亡事件", "可用糧食首度低於最低需求（熱量或蛋白質）"],
      ["追蹤結束", "365天時設限（右設限）"],
      ["治療組", "政策槓桿與其組合"],
      ["存活曲線、中位數、RMST", "糧食「存活」曲線、中位續航天數、一年內平均天數"],
      ["加速失敗時間模型", "時間比：政策使續航力放大幾倍"],
    ] : [
      [hdr("Clinical trial"), hdr("Food-endurance model")],
      ["Patient", "One simulated future (5,000 per scenario)"],
      ["Death / event", "First day available food < minimum need (energy or protein)"],
      ["End of follow-up", "Right-censored at 365 days"],
      ["Treatment arm", "Policy lever or package"],
      ["Survival curve, median, RMST", "Food 'survival' curve, median days, mean days within a year"],
      ["Accelerated failure time", "Time ratio: how much a policy stretches endurance"],
    ];
    s.addTable(rows.map((r, i) => r.map((c) => (typeof c === "string" ? { text: c, options: { color: C.ink, fill: { color: i % 2 ? C.white : C.card } } } : c))),
      { x: 7.15, y: 1.72, w: 5.58, colW: [2.1, 3.48], rowH: 0.62, fontFace: F.body, fontSize: 12.5, valign: "middle",
        border: { type: "solid", pt: 0.5, color: C.line }, margin: [0.04, 0.1, 0.04, 0.1] });
    text(s, L("Estimands: S(t), median T, RMST(365) = E[min(T, 365)], P(T > 180 days), paired days gained, Weibull AFT time ratios.",
      "估計量：S(t)、T中位數、RMST(365)=E[min(T,365)]、P(T>180天)、配對增加天數、Weibull AFT時間比。"),
      { x: 7.15, y: 6.2, w: 5.58, h: 0.6, fontSize: 11, color: C.muted });
    footer(s, 5);
    s.addNotes(L("Four research questions. The statistical idea: endurance T is a time-to-event variable, exactly like survival time in a clinical trial. Each simulated future is a 'patient'; policies are 'treatment arms'.",
      "四個研究問題。統計上的核心想法：續航力T是「事件發生時間」，就像臨床試驗的存活時間。每一個模擬的未來是一位「病人」，政策就是「治療組」。"));
  }

  // =========================================================================================
  // 6. Data: calorie structure + bulk ships
  // =========================================================================================
  {
    const s = pres.addSlide();
    const di = D.diet;
    const sh = (v) => Math.round((v / di.total) * 100);
    header(s, L("05 · DATA", "05 · 資料"),
      L("Three-quarters of Taiwan's calories depend on imports", "臺灣四分之三的熱量依賴進口"),
      L(`Only ${sh(di.dom_ind)}% of the normal diet needs no imported inputs; livestock (${sh(di.livestock)}%) runs on imported feed.`,
        `平時飲食只有${sh(di.dom_ind)}%完全不靠進口投入；畜產品（${sh(di.livestock)}%）依賴進口飼料。`));
    const cats = ZH
      ? [`平時糧食供給 ${fmt(di.total)} 大卡`, `最低需求 ${fmt(di.m_req)} 大卡`, `進口飼料若直接食用 ≈${fmt(di.feed_edible, 0)} 大卡`]
      : [`Normal food supply  ${fmt(di.total)} kcal`, `Minimum need  ${fmt(di.m_req)} kcal`, `Feed grain if eaten  ≈${fmt(di.feed_edible)} kcal`];
    const ser = [
      [L(`Domestic, no imported inputs (${sh(di.dom_ind)}%)`, `國產、不靠進口投入（${sh(di.dom_ind)}%）`), [di.dom_ind, 0, 0], C.aqua],
      [L(`Domestic livestock, imported feed (${sh(di.livestock)}%)`, `國產畜產品、依賴進口飼料（${sh(di.livestock)}%）`), [di.livestock, 0, 0], C.yellow],
      [L(`Imported storables (${sh(di.imp_stor)}%)`, `進口耐儲糧食（${sh(di.imp_stor)}%）`), [di.imp_stor, 0, 0], C.blue],
      [L(`Imported perishables (${sh(di.imp_perish)}%)`, `進口生鮮（${sh(di.imp_perish)}%）`), [di.imp_perish, 0, 0], C.orange],
      [L("Minimum need (Sphere 2,100 kcal + forces + losses)", "最低需求（Sphere 2,100大卡＋兵力＋損耗）"), [0, di.m_req, 0], C.ink],
      [L("Imported feed grain, as human food", "進口飼料穀物（轉供人食）"), [0, 0, di.feed_edible], C.gray],
    ];
    s.addChart(pres.charts.BAR, ser.map(([n, v]) => ({ name: n, labels: cats.slice().reverse(), values: v.slice().reverse().map((x) => Math.round(x)) })),
      chartBase({ x: MX, y: 1.95, w: 7.9, h: 4.85, barDir: "bar", barGrouping: "stacked", chartColors: ser.map((x) => x[2]),
        barGapWidthPct: 45, valAxisMaxVal: 3000, valAxisMinVal: 0, valAxisMajorUnit: 500, showLegend: true, legendPos: "b",
        legendFontSize: 10.5, catAxisLabelFontSize: 11.5, valAxisLabelFormatCode: "#,##0", showValAxisTitle: true,
        valAxisTitle: L(`kcal per person per day (food balance ${FBSY}; rice at 2024 level)`, `每人每日大卡（${FBSY}年糧食平衡；稻米以2024年水準）`),
        valAxisTitleFontSize: 10, valAxisTitleColor: C.ink2, valAxisTitleFontFace: F.body }));
    card(s, 8.85, 1.95, 3.88, 4.85, C.card);
    text(s, L("≈ 9 bulk grain carriers a month", "每月約9艘散裝穀物船"), { x: 9.1, y: 2.08, w: 3.4, h: 0.45, fontSize: 16, bold: true, color: C.navy, fontFace: F.head });
    const ships = D.ships;
    const shipIcons = { corn: I.corn, soybeans: I.peas, wheat: I.wheatA };
    const shipName = { corn: L("corn", "玉米"), soybeans: L("soybean", "黃豆"), wheat: L("wheat", "小麥") };
    ships.forEach((r, i) => {
      const y = 2.72 + i * 0.95;
      s.addImage({ data: shipIcons[r.cargo], x: 9.1, y: y + 0.05, w: 0.55, h: 0.55 });
      text(s, L(`${fmt(r.vessels_per_month, r.vessels_per_month % 1 ? 1 : 0)} ${shipName[r.cargo]} carriers`, `${shipName[r.cargo]}船 ${fmt(r.vessels_per_month, r.vessels_per_month % 1 ? 1 : 0)} 艘`),
        { x: 9.8, y: y, w: 2.8, h: 0.34, fontSize: 13.5, bold: true, color: C.ink });
      text(s, L(`each ≈ ${fmt(r.days_of_national_minimum_per_vessel, 1)} days of the island's minimum need`, `每艘≈全民最低需求 ${fmt(r.days_of_national_minimum_per_vessel, 1)} 天`),
        { x: 9.8, y: y + 0.34, w: 2.8, h: 0.5, fontSize: 11.5, color: C.ink2 });
    });
    const tot = ships.reduce((a, r) => a + r.edible_kcal_pc_day, 0) / di.m_req;
    card(s, 9.05, 5.6, 3.48, 1.0, C.navy);
    text(s, L(`Together ≈ ${fmt(tot, 1)}× the minimum need, if the grain feeds people, not pigs`, `合計≈最低需求的 ${fmt(tot, 1)} 倍——前提是穀物給人吃，而不是餵豬`),
      { x: 9.22, y: 5.66, w: 3.15, h: 0.88, fontSize: 12.5, bold: true, color: C.white, valign: "middle" });
    footer(s, 6, L(`Sources: MOA Food Balance Sheet 2022 items scaled to FA01 ${FBSY} food-group totals; USDA FAS GAIN TW2024-0030 (vessels/month); edible conversion: corn 75%, soybean 80%, wheat 95%.`,
      `資料來源：農業部2022年糧食平衡表品項，依FA01 ${FBSY}年各類糧食供給量調整；USDA FAS GAIN TW2024-0030（每月船數）；可食轉換率：玉米75%、黃豆80%、小麥95%。`));
    s.addNotes(L(`Calibration uses the official food balance sheet, updated to ${FBSY} with the FA01 series. Only about a quarter of calories need no imported inputs. But the grain Taiwan imports - about nine bulk carriers a month of corn, soybeans and wheat - would cover about ${fmt(tot, 1)} times the whole population's minimum need if people ate it directly; the feed grain alone would supply about ${fmt(di.feed_edible)} kcal per person per day.`,
      `校準使用官方糧食平衡表，並以FA01序列更新至${FBSY}年。只有約四分之一的熱量不依賴進口投入。但臺灣每月約9艘散裝船進口的玉米、黃豆與小麥，若直接供人食用，約為全民最低需求的${fmt(tot, 1)}倍；其中飼料穀物單獨就可提供每人每日約${fmt(di.feed_edible)}大卡。`));
  }

  // =========================================================================================
  // 7. Model
  // =========================================================================================
  {
    const s = pres.addSlide();
    header(s, L("06 · METHOD", "06 · 研究方法"),
      L("A stochastic stock–flow model, run 5,000 times per scenario", "隨機存量流量模型：每種情境模擬5,000次"));
    const inflow = ZH
      ? ["稻米收穫（農糧署2025縣市產量、作物曆）", "海運到港 × 抵達比例 φ", "國產蔬果、漁獲 × 燃料／電力／肥料乘數", "畜產品產出（需要進口飼料）"]
      : ["Rice harvests (AFA 2025, crop calendar)", "Seaborne arrivals × share φ getting through", "Domestic produce & fish × fuel / power / fertilizer", "Livestock output (needs imported feed)"];
    inflow.forEach((t, i) => {
      const y = 1.85 + i * 0.98;
      s.addShape("roundRect", { x: MX, y, w: 2.9, h: 0.8, rectRadius: 0.06, fill: { color: C.white }, line: { color: C.line, width: 1 } });
      text(s, t, { x: MX + 0.12, y, w: 2.66, h: 0.8, fontSize: 12, color: C.ink, valign: "middle" });
      s.addShape("rightArrow", { x: MX + 2.98, y: y + 0.28, w: 0.42, h: 0.24, fill: { color: C.navyL }, line: { type: "none" } });
    });
    s.addShape("roundRect", { x: 4.05, y: 1.85, w: 2.75, h: 3.74, rectRadius: 0.1, fill: { color: C.navy }, line: { type: "none" } });
    circleIcon(s, I.warehouse, 4.95, 2.02, 0.9, C.amberD);
    text(s, L("Food stocks\n(per person)", "糧食存量\n（每人）"), { x: 4.2, y: 3.0, w: 2.45, h: 0.72, fontSize: 15, bold: true, color: C.white, align: "center" });
    text(s, L("rice · import pipeline · pantry · cold store · feed grain", "稻米、進口在途、家戶存糧、冷凍庫存、飼料"),
      { x: 4.25, y: 3.78, w: 2.35, h: 1.4, fontSize: 12, color: C.ice, align: "center" });
    const outs = ZH ? ["消費：未配給，或分級配給", "損耗：攻擊、冷鏈失效、腐損"] : ["Consumption: unrationed or tiered rationing", "Losses: strikes, cold-chain failure, spoilage"];
    outs.forEach((t, i) => {
      const y = 2.35 + i * 1.5;
      s.addShape("rightArrow", { x: 6.88, y: y + 0.33, w: 0.42, h: 0.24, fill: { color: C.navyL }, line: { type: "none" } });
      s.addShape("roundRect", { x: 7.38, y, w: 2.05, h: 0.9, rectRadius: 0.06, fill: { color: C.white }, line: { color: C.line, width: 1 } });
      text(s, t, { x: 7.48, y, w: 1.85, h: 0.9, fontSize: 12, color: C.ink, valign: "middle" });
    });
    card(s, MX, 5.82, 8.83, 1.0, C.amberL);
    text(s, [
      { text: L("Energy module: ", "能源模組："), options: { bold: true } },
      { text: L("LNG ~10 days · coal ~7 weeks · oil ~20 weeks without resupply (CSIS 2025). ", "無補給時天然氣約10天、燃煤約7週、石油約20週（CSIS 2025）。") },
      { text: L("Shortfall = first day food available < minimum need (≈2,330 kcal/person incl. forces & losses) or 30-day protein < need.", "斷糧＝可用糧食首度低於最低需求（每人約2,330大卡，含兵力與損耗），或30日平均蛋白質低於需求。"), options: { bold: true, color: C.amberD } },
    ], { x: MX + 0.2, y: 5.88, w: 8.43, h: 0.88, fontSize: 12, color: C.ink, valign: "middle" });
    card(s, 9.75, 1.85, 2.98, 4.97, C.card);
    circleIcon(s, I.gears, 9.97, 2.02, 0.56, C.navy);
    text(s, L("Estimation", "估計方法"), { x: 10.65, y: 2.08, w: 1.95, h: 0.45, fontSize: 15, bold: true, color: C.navy, valign: "middle" });
    const est = ZH ? [
      "5,000次蒙地卡羅 × 3種情境 × 9種政策組合（共同隨機數、配對比較）",
      "Kaplan–Meier曲線、中位數、RMST(365)、P(T>180天)",
      "Weibull加速失敗時間模型：時間比",
      "Sobol全域敏感度分析（N=1,024）",
      "縣市模組：22縣市、跨區調撥能力 τ",
    ] : [
      "5,000 Monte Carlo draws × 3 scenarios × 9 policy sets (common random numbers)",
      "Kaplan–Meier curves, median, RMST(365), P(T > 180 d)",
      "Weibull accelerated-failure-time model: time ratios",
      "Sobol global sensitivity analysis (N = 1,024)",
      "County module: 22 counties, transfer capacity τ",
    ];
    text(s, est.map((t, i) => ({ text: t, options: { bullet: { indent: 12 }, breakLine: i < est.length - 1 } })),
      { x: 9.95, y: 2.75, w: 2.62, h: 3.2, fontSize: 11.5, color: C.ink, paraSpaceAfter: 7 });
    text(s, L("Python · open data · full run ≈ 1 minute on a laptop", "Python · 開放資料 · 筆電全部重跑約1分鐘"), { x: 9.95, y: 6.12, w: 2.62, h: 0.55, fontSize: 10.5, color: C.muted, italic: true });
    footer(s, 7);
    s.addNotes(L("The simulator tracks per-person food stocks day by day. Inflows depend on harvest timing, how much shipping gets through, and fuel, power and fertilizer shortages. The outcome is the first day food falls below the minimum requirement.",
      "模擬器逐日追蹤每人糧食存量。流入取決於收穫時間、船運抵達比例，以及燃料、電力、肥料短缺。結果變數是糧食首度低於最低需求的那一天。"));
  }

  // =========================================================================================
  // 8. Scenarios & priors
  // =========================================================================================
  {
    const s = pres.addSlide();
    header(s, L("07 · SCENARIOS & PRIORS", "07 · 情境與事前分布"),
      L("Three blockade archetypes and 42 uncertain inputs, each sourced", "三種封鎖型態、42個不確定參數，皆附來源或假設說明"));
    const px = D.prior_x;
    s.addChart(pres.charts.SCATTER, [{ name: "X", values: px },
      { name: L("Quarantine", "隔離"), values: D.priors.S1 }, { name: L("Military blockade", "軍事封鎖"), values: D.priors.S2 },
      { name: L("Total isolation", "全面孤立"), values: D.priors.S3 }],
    chartBase({ x: MX, y: 1.8, w: 6.0, h: 2.75, lineSize: 2.25, lineDataSymbol: "none", chartColors: [C.s1, C.s2, C.s3],
      valAxisHidden: true, valGridLine: { style: "none" }, catAxisMinVal: 0, catAxisMaxVal: 100, catAxisMajorUnit: 20,
      valAxisMinVal: 0, valAxisMaxVal: 1.08, valAxisLabelFormatCode: "0", showLegend: true, legendPos: "t", showCatAxisTitle: true,
      catAxisTitle: L("Share of normal seaborne arrivals that get through, φ (%)", "正常海運量中仍能抵達的比例 φ（%）"), catAxisTitleFontSize: 10.5,
      catAxisTitleColor: C.ink2, catAxisTitleFontFace: F.body }));
    const sc = ZH ? [
      [C.s1, "S1　海警隔離", "臨檢登檢；φ 約75%（CSIS：多數商船仍能抵達）"],
      [C.s2, "S2　軍事封鎖", "潛艦與水雷；φ 約35%（CSIS：無美方介入時40%來臺船舶遭擊沉）"],
      [C.s3, "S3　全面孤立＋能源衝擊", "φ 約6%；港口與倉儲遭攻擊"],
    ] : [
      [C.s1, "S1  Quarantine", "coast-guard boarding; φ ≈ 75% (CSIS: most merchant traffic continued)"],
      [C.s2, "S2  Military blockade", "submarines & mines; φ ≈ 35% (CSIS: 40% of inbound ships sunk without U.S. help)"],
      [C.s3, "S3  Total isolation + energy shock", "φ ≈ 6%; strikes on ports and stores"],
    ];
    sc.forEach(([col, t, d], i) => {
      const y = 4.72 + i * 0.7;
      s.addShape("roundRect", { x: MX, y: y + 0.06, w: 0.34, h: 0.34, rectRadius: 0.05, fill: { color: col }, line: { type: "none" } });
      text(s, [{ text: t, options: { bold: true, color: C.navy, breakLine: true } }, { text: d, options: { color: C.ink2, fontSize: 11.5 } }],
        { x: MX + 0.5, y: y - 0.02, w: 5.55, h: 0.66, fontSize: 12.5 });
    });
    const hd = (t) => ({ text: t, options: { bold: true, color: C.white, fill: { color: C.navy } } });
    const rows = ZH ? [
      [hd("參數"), hd("事前範圍"), hd("來源")],
      ["稻米總庫存低點（6月1日）", "4.0–6.5 個月", "農業部：2025.3公糧5.5個月"],
      ["進口糧食在途與庫存", "1.0–2.5 個月", "USDA：散裝船每月到港"],
      ["家戶與零售存糧", "5–14 天", "假設"],
      ["飼料穀物庫存", "30–60 天", "假設（筒倉容量有限）"],
      ["民眾最低熱量攝取", "2,000–2,200 大卡", "Sphere手冊（2,100）"],
      ["動員人員占人口", "1.3–3.9%", "立法院2024：可教召後備71萬人"],
      ["天然氣／燃煤／石油存量", "9–12天／6–8週／17–23週", "CSIS 2025；經濟部"],
      ["配給遵從率", "75–95%", "假設（待專家引導）"],
    ] : [
      [hd("Parameter"), hd("Prior range"), hd("Source")],
      ["Total rice stock at 1 June low", "4.0–6.5 months", "MOA: public 5.5 mo (Mar 2025)"],
      ["Imported food pipeline & stock", "1.0–2.5 months", "USDA: monthly bulk arrivals"],
      ["Household & retail pantry", "5–14 days", "assumption"],
      ["Feed-grain stocks", "30–60 days", "assumption (limited silos)"],
      ["Minimum civilian intake", "2,000–2,200 kcal", "Sphere Handbook (2,100)"],
      ["Mobilized share of population", "1.3–3.9%", "LY 2024: 710,569 callable reservists"],
      ["LNG / coal / oil stocks", "9–12 d / 6–8 wk / 17–23 wk", "CSIS 2025; MOEA"],
      ["Rationing compliance", "75–95%", "assumption (for elicitation)"],
    ];
    s.addTable(rows.map((r, i) => r.map((c) => (typeof c === "string" ? { text: c, options: { color: C.ink, fill: { color: i % 2 ? C.white : C.card } } } : c))),
      { x: 6.95, y: 1.8, w: 5.78, colW: [2.2, 1.68, 1.9], rowH: 0.5, fontFace: F.body, fontSize: 11, valign: "middle",
        border: { type: "solid", pt: 0.5, color: C.line }, margin: [0.03, 0.08, 0.03, 0.08] });
    text(s, L("Full list with sources: outputs/tables/priors.csv. Assumptions are candidates for structured expert elicitation (SHELF).",
      "完整清單與來源見 outputs/tables/priors.csv；標示「假設」者為結構化專家意見徵詢（SHELF）的對象。"),
      { x: 6.95, y: 6.45, w: 5.78, h: 0.45, fontSize: 10.5, color: C.muted });
    footer(s, 8, L("Scenario anchors: CSIS, Lights Out? (2025) p.xi; stock priors: MOA (2025), USDA FAS (2024). Curves show prior densities of φ (scaled).",
      "情境錨點：CSIS（2025）；存量事前分布：農業部（2025）、USDA（2024）。曲線為φ的事前密度（已標準化）。"));
    s.addNotes(L("Three scenarios differ mainly in the share of shipping that gets through, anchored on the CSIS wargames. Every uncertain input has a prior with a source or a stated assumption, so the uncertainty is carried into every result.",
      "三種情境主要差在船運抵達比例，以CSIS兵推為錨點。每個不確定參數都有附來源或假設說明的事前分布，不確定性因此一路傳遞到每個結果。"));
  }

  // =========================================================================================
  // 9. RQ1: KM curves
  // =========================================================================================
  {
    const s = pres.addSlide();
    header(s, L("08 · RQ1 · HOW LONG?", "08 · RQ1 · 能撐多久？"),
      L("No new policy: ~6 months under blockade, ~4 under isolation", "無新政策下：軍事封鎖約6個月，全面孤立約4個月"));
    const dd = D.km_days.filter((d, i) => i % 3 === 0 || d === 365);
    const pick = (arr) => D.km_days.map((d, i) => [d, arr[i]]).filter(([d]) => d % 3 === 0 || d === 365).map(([, v]) => Math.round(v * 1000) / 10);
    const names = ZH ? ["無新政策", "民生政策組合", "政策組合＋穀物護航"] : ["No new policy", "Civil package", "Civil package + grain convoys"];
    const scen = [["S1", L("Quarantine", "海警隔離")], ["S2", L("Military blockade", "軍事封鎖")], ["S3", L("Total isolation + energy shock", "全面孤立＋能源衝擊")]];
    scen.forEach(([sc, lab], i) => {
      const x = MX + i * 4.1;
      text(s, lab, { x: x + 0.1, y: 1.85, w: 3.8, h: 0.35, fontSize: 14, bold: true, color: C.navy });
      s.addChart(pres.charts.SCATTER, [{ name: "X", values: dd },
        { name: names[0], values: pick(D.km[sc].baseline) }, { name: names[1], values: pick(D.km[sc].civil_package) },
        { name: names[2], values: pick(D.km[sc].full_package) }],
      chartBase({ x, y: 2.18, w: 3.95, h: 3.05, lineSize: 2.25, lineDataSymbol: "none", chartColors: [C.gray, C.aqua, C.blue],
        catAxisMinVal: 0, catAxisMaxVal: 360, catAxisMajorUnit: 90, valAxisMinVal: 0, valAxisMaxVal: 100, valAxisMajorUnit: 25,
        valAxisLabelFormatCode: "0", showValAxisTitle: i === 0, valAxisTitle: L("% of futures with enough food", "糧食足夠的情境比例（%）"),
        valAxisTitleFontSize: 10, valAxisTitleColor: C.ink2, valAxisTitleFontFace: F.body,
        showCatAxisTitle: true, catAxisTitle: L("days since blockade began", "封鎖開始後天數"), catAxisTitleFontSize: 10,
        catAxisTitleColor: C.ink2, catAxisTitleFontFace: F.body }));
    });
    // legend row
    names.forEach((n, i) => {
      const x = 3.2 + i * 2.6;
      s.addShape("line", { x, y: 5.46, w: 0.45, h: 0, line: { color: [C.gray, C.aqua, C.blue][i], width: 2.5 } });
      text(s, n, { x: x + 0.55, y: 5.31, w: 2.0, h: 0.3, fontSize: 11.5, color: C.ink, valign: "middle" });
    });
    const s1 = S("S1", "baseline"), s2b = S("S2", "baseline"), s2c = S("S2", "civil_package"), s2f = S("S2", "full_package");
    const s3b = S("S3", "baseline"), s3c = S("S3", "civil_package"), s3f = S("S3", "full_package");
    const stats = [
      [pct(s1.p_survive_year), L("of futures: food lasts at least one year with no new policy", "的情境：無新政策也能撐過一年")],
      [days(s2b.median), L(`median with no new policy → ${days(s2c.median)} with the civil package; ${pct(s2f.p_survive_year)} last a year with convoys`,
        `無新政策中位數 → 民生政策組合 ${days(s2c.median)}；加護航 ${pct(s2f.p_survive_year)} 可撐一年`)],
      [days(s3b.median), L(`median → ${days(s3c.median)} with the civil package → ${days(s3f.median)} with convoys`,
        `中位數 → 民生政策組合 ${days(s3c.median)} → 加護航 ${days(s3f.median)}`)],
    ];
    stats.forEach(([big, lab], i) => {
      const x = MX + i * 4.1;
      card(s, x, 5.78, 3.9, 1.08);
      text(s, big, { x: x + 0.18, y: 5.86, w: 1.45, h: 0.9, fontFace: F.head, fontSize: 25, bold: true, color: i === 0 ? C.aqua : C.navy, valign: "middle" });
      text(s, lab, { x: x + 1.62, y: 5.86, w: 2.18, h: 0.92, fontSize: 11, color: C.ink2, valign: "middle" });
    });
    footer(s, 9, L("Civil package = tiered rationing + feed-to-food + surge planting + dispersed storage. Kaplan–Meier curves from 5,000 draws per scenario, censored at 365 days.",
      "民生政策組合＝分級配給＋飼料轉糧＋休耕地搶種＋分散儲存。每情境5,000次模擬的Kaplan–Meier曲線，365天設限。"));
    s.addNotes(L("Kaplan-Meier curves of food endurance. A quarantine is survivable. Under a military blockade the median is about six months; under total isolation about four. The civil package nearly doubles the blockade case; convoys are decisive under isolation.",
      "糧食續航力的Kaplan–Meier曲線。隔離情境可撐過；軍事封鎖中位數約6個月、全面孤立約4個月。民生政策組合讓封鎖情境幾乎倍增；在全面孤立下，護航是關鍵。"));
  }

  // =========================================================================================
  // 10. Why estimates disagree: phi sweep + onset
  // =========================================================================================
  {
    const s = pres.addSlide();
    header(s, L("09 · RQ1 · WHY ESTIMATES DISAGREE", "09 · RQ1 · 為何各方估計不同"),
      L("The answer hinges on shipping and on timing", "答案取決於船運，也取決於封鎖開始的時間"));
    const xs = D.phi_x.map((v) => Math.round(v * 100));
    const nm = ZH ? ["無新政策", "分級配給", "民生政策組合"] : ["No new policy", "Tiered rationing", "Civil package"];
    s.addChart(pres.charts.SCATTER, [{ name: "X", values: xs },
      { name: nm[0], values: D.phi.baseline }, { name: nm[1], values: D.phi.rationing }, { name: nm[2], values: D.phi.civil_package }],
    chartBase({ x: MX, y: 1.8, w: 6.6, h: 3.55, lineSize: 2.5, lineDataSymbol: "circle", lineDataSymbolSize: 5, chartColors: [C.gray, C.orange, C.aqua],
      catAxisMinVal: 0, catAxisMaxVal: 100, catAxisMajorUnit: 20, valAxisMinVal: 0, valAxisMaxVal: 400, valAxisMajorUnit: 100,
      valAxisLabelFormatCode: "0", showLegend: true, legendPos: "t", showCatAxisTitle: true,
      catAxisTitle: L("Share of normal seaborne arrivals that get through, φ (%)", "正常海運量中仍能抵達的比例 φ（%）"), catAxisTitleFontSize: 10.5,
      catAxisTitleColor: C.ink2, catAxisTitleFontFace: F.body, showValAxisTitle: true, valAxisTitle: L("median endurance (days; 365 = ≥ 1 year)", "續航力中位數（天；365＝≥1年）"),
      valAxisTitleFontSize: 10, valAxisTitleColor: C.ink2, valAxisTitleFontFace: F.body }));
    const thr = (arr) => { const i = arr.findIndex((v) => v >= 365); return i >= 0 ? xs[i] : null; };
    const tb = thr(D.phi.baseline), tc = thr(D.phi.civil_package);
    const b0 = D.phi.baseline[0], b35 = D.phi.baseline[xs.indexOf(35)];
    const mp = ZH ? [
      ["0%", `約${Math.round(b0 / 30.44)}個月：全面孤立`],
      ["35%", `約${Math.round(b35 / 30.44)}個月 ↔ Parameters 2023「約6個月」`],
      [`≥${tb}%`, "≥1年 ↔ CSIS「不是問題」、農業部「約1年」"],
      [`≥${tc}%`, "採民生政策組合即可撐 ≥1年"],
    ] : [
      ["0%", `~${Math.round(b0 / 30.44)} months: total isolation`],
      ["35%", `~${Math.round(b35 / 30.44)} months ↔ Parameters 2023 "~6 months"`],
      [`≥ ${tb}%`, `≥ 1 year ↔ CSIS "not a problem", MOA "~1 year"`],
      [`≥ ${tc}%`, "enough for ≥ 1 year with the civil package"],
    ];
    mp.forEach(([k, v], i) => {
      const y = 5.5 + i * 0.34;
      text(s, k, { x: MX, y, w: 0.85, h: 0.32, fontSize: 12, bold: true, color: i === 3 ? C.aqua : C.navy });
      text(s, v, { x: MX + 0.9, y, w: 5.7, h: 0.32, fontSize: 12, color: C.ink });
    });
    const months = ZH ? ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"] : ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"];
    const hv = [0, 0, 0, 0, 0, 400, 400, 0, 0, 400, 400, 0];
    s.addChart([
      { type: pres.charts.BAR, data: [{ name: L("Rice harvest months", "稻米收穫月份"), labels: months, values: hv }], options: { chartColors: [C.harvest], barGapWidthPct: 0 } },
      { type: pres.charts.LINE, data: [{ name: L("Military blockade", "軍事封鎖"), labels: months, values: D.onset.S2.baseline },
        { name: L("Total isolation", "全面孤立"), labels: months, values: D.onset.S3.baseline }],
        options: { chartColors: [C.s2, C.s3], lineSize: 2.25, lineDataSymbol: "circle", lineDataSymbolSize: 6 } },
    ], chartBase({ x: 7.55, y: 1.8, w: 5.18, h: 3.2, valAxisMinVal: 0, valAxisMaxVal: 400, valAxisMajorUnit: 100, showLegend: true, legendPos: "t",
      legendFontSize: 10.5, catAxisLabelFontSize: ZH ? 9.5 : 10.5, showTitle: true, title: L("Median endurance by start month (no new policy)", "依封鎖開始月份的續航力中位數（無新政策）"),
      titleFontSize: 12, titleBold: true }));
    const o2 = D.onset.S2.baseline, o3 = D.onset.S3.baseline;
    card(s, 7.55, 5.2, 5.18, 1.66, C.amberL);
    text(s, [
      { text: L(`Timing shifts endurance by up to ${fmt(Math.max(Math.max(...o2) - Math.min(...o2), Math.max(...o3) - Math.min(...o3)))} days. `,
        `開始時間可讓續航力相差達${fmt(Math.max(Math.max(...o2) - Math.min(...o2), Math.max(...o3) - Math.min(...o3)))}天。`), options: { bold: true, color: C.amberD } },
      { text: L(`The worst start is ${monthName(argMin(o2))} under blockade (${fmt(Math.min(...o2))} vs ${fmt(Math.max(...o2))} days for ${monthName(argMax(o2))}) and ${monthName(argMin(o3))} under isolation (${fmt(Math.min(...o3))} vs ${fmt(Math.max(...o3))} for ${monthName(argMax(o3))}). What matters is whether stocks last until the June rice harvest.`,
        `軍事封鎖以${monthName(argMin(o2))}開始最糟（${fmt(Math.min(...o2))}天；${monthName(argMax(o2))}開始為${fmt(Math.max(...o2))}天），全面孤立以${monthName(argMin(o3))}最糟（${fmt(Math.min(...o3))}天；${monthName(argMax(o3))}為${fmt(Math.max(...o3))}天）。關鍵在於存糧能否撐到6月的一期稻作收穫。`), options: { color: C.ink } },
    ], { x: 7.75, y: 5.3, w: 4.8, h: 1.48, fontSize: 12, valign: "middle" });
    footer(s, 10, L("φ sweep: S2 structure with φ fixed from 0 to 100% (1,000 draws each); onset: 2,000 draws per month. Shaded bars mark rice-harvest months.",
      "φ敏感度：S2結構、φ固定於0–100%（各1,000次）；起始月份：每月2,000次。底色長條為稻米收穫月份。"));
    s.addNotes(L(`The three published estimates are all consistent with the model - they sit at different points on the shipping curve. Timing also matters, by up to ${fmt(Math.max(Math.max(...o2) - Math.min(...o2), Math.max(...o3) - Math.min(...o3)))} days: what counts is whether stocks last until the June rice harvest.`,
      `三個已發表的估計都和模型一致，只是位在船運曲線的不同位置。時間點也很重要，最多可相差${fmt(Math.max(Math.max(...o2) - Math.min(...o2), Math.max(...o3) - Math.min(...o3)))}天：關鍵在存糧能否撐到6月的一期稻作收穫。`));
  }

  // =========================================================================================
  // 11. RQ2: counties
  // =========================================================================================
  {
    const s = pres.addSlide();
    header(s, L("10 · RQ2 · WHERE FIRST?", "10 · RQ2 · 何處先告急？"),
      L("Outlying islands first, then the northern metros", "外離島最先告急，其次是北部都會區"));
    s.addImage({ path: path.join(FIG, LANG, "county_map_baseline_disrupted.png"), x: MX + 0.15, y: 1.72, w: 3.55, h: 5.11 });
    const nat = D.county.baseline_disrupted[0].national_median;
    const islR = cRange("baseline_disrupted", ISL), isl180 = cRange("package_disrupted_islands180", ISL);
    const metroD = cAvg("baseline_disrupted", METRO), riceB = cAvg("baseline_disrupted", RICEBELT);
    const cards = [
      [L("Kinmen · Matsu · Penghu", "金門 · 馬祖 · 澎湖"), L(`${rng(islR)} days`, `${rng(islR)} 天`),
        L(`vs ${fmt(nat)} nationally: supply depends on sea and air links that a blockade cuts first`, `全國為${fmt(nat)}天：補給仰賴最先被切斷的海空運輸`), "7F3312"],
      [L("Taipei · New Taipei · Keelung", "臺北 · 新北 · 基隆"), L(`~${fmt(metroD)} days`, `約${fmt(metroD)} 天`),
        L("little farmland; vulnerable if the north–south corridor is disrupted", "耕地少；南北交通受阻時最脆弱"), "E2733F"],
      [L("Rice belt: Changhua, Yunlin, Chiayi, Hualien, Taitung", "稻作區：彰化、雲林、嘉義、花蓮、臺東"), L(`~${fmt(riceB)} days`, `約${fmt(riceB)} 天`),
        L("local harvests and farmland carry these counties well past the national median", "在地收穫與農地讓這些縣市撐得比全國中位數久"), "C9C4B8"],
      [L("Islands with 6 months pre-positioned", "外離島預置6個月存糧"), L(`→ ${rng(isl180)} days`, `→ ${rng(isl180)} 天`),
        L("with the civil package; the 2025 QDR stocks combat rations there for troops, civilians need the same", "搭配民生政策組合；114年QDR已提高外離島部隊戰備口糧，民眾同樣需要"), C.aqua],
    ];
    cards.forEach(([t, big, d, col], i) => {
      const x = 4.75 + (i % 2) * 4.05, y = 1.72 + Math.floor(i / 2) * 2.25;
      card(s, x, y, 3.9, 2.1);
      s.addShape("ellipse", { x: x + 0.22, y: y + 0.27, w: 0.26, h: 0.26, fill: { color: col }, line: { type: "none" } });
      text(s, t, { x: x + 0.6, y: y + 0.18, w: 3.15, h: 0.48, fontSize: 12.5, bold: true, color: C.navy, valign: "middle" });
      text(s, big, { x: x + 0.22, y: y + 0.7, w: 3.5, h: 0.62, fontFace: F.head, fontSize: 28, bold: true, color: C.ink, valign: "middle" });
      text(s, d, { x: x + 0.22, y: y + 1.36, w: 3.5, h: 0.7, fontSize: 11.5, color: C.ink2 });
    });
    const mN = D.county.baseline_normal, mD = D.county.baseline_disrupted;
    const metroAvg = (arr) => Math.round(["TPE", "NTP", "KEE"].reduce((acc, c) => acc + arr.find((r) => r.code === c).median, 0) / 3);
    card(s, 4.75, 6.22, 7.95, 0.61, C.amberL);
    text(s, [
      { text: L("Keep the corridor open: ", "確保南北走廊暢通："), options: { bold: true, color: C.amberD } },
      { text: L(`with normal north–south transport, Taipei, New Taipei and Keelung last ~${fmt(metroAvg(mN))} days instead of ~${fmt(metroAvg(mD))}.`,
        `交通正常時，臺北、新北、基隆可撐約${fmt(metroAvg(mN))}天，而非約${fmt(metroAvg(mD))}天。`), options: { color: C.ink } },
    ], { x: 4.97, y: 6.22, w: 7.55, h: 0.61, fontSize: 12.5, valign: "middle" });
    footer(s, 11, L("S2, no new policy, transport disrupted (τ: west 0.3–0.6, east 0.1–0.4, islands 0–0.15). Rice: AFA 2025; population: MOI Dec 2025; other crops by cultivated area, surge planting by idle paddy (DGBAS 2024).",
      "S2、無新政策、交通受阻（τ：西部0.3–0.6、東部0.1–0.4、離島0–0.15）。稻米：農糧署2025；人口：內政部2025年12月；其他作物依耕地面積、搶種依未種稻水田分配（主計總處2024）。"));
    const islAvg = cAvg("baseline_disrupted", ISL);
    s.addNotes(L(`With transport disrupted, the outlying islands run out about ${round5(nat - islAvg)} days before the national median, and the northern metros about ${round5(nat - metroD)} days before. Farm counties last longest. Pre-positioning six months of stock on the islands closes most of the gap.`,
      `交通受阻時，外離島比全國中位數早約${round5(nat - islAvg)}天斷糧，北部都會區早約${round5(nat - metroD)}天；農業縣市撐最久。外離島預置6個月存糧可補上大部分缺口。`));
  }

  // =========================================================================================
  // 12. RQ3: levers
  // =========================================================================================
  {
    const s = pres.addSlide();
    header(s, L("11 · RQ3 · WHAT WORKS BEST?", "11 · RQ3 · 何者最有效？"),
      L("Design beats stockpiling: feed-to-food is the top civil lever", "政策設計勝過囤糧：飼料轉糧是最有效的民生槓桿"));
    const order = ["rationing", "feed2food", "surge", "rice_plus3", "dispersed", "convoy", "civil_package", "full_package"];
    const lab = ZH
      ? { rationing: "分級配給", feed2food: "飼料轉糧", surge: "休耕地搶種甘藷", rice_plus3: "公糧再增3個月", dispersed: "分散儲存", convoy: "穀物船隊護航", civil_package: "民生政策組合", full_package: "組合＋護航" }
      : { rationing: "Tiered rationing", feed2food: "Feed-to-food", surge: "Surge planting", rice_plus3: "+3-month rice reserve", dispersed: "Dispersed storage", convoy: "Grain convoys", civil_package: "Civil package", full_package: "Package + convoys" };
    const mkChart = (sc, y, title, dark, light) => {
      const cats = [], segs = [[], [], [], [], [], []];
      order.slice().reverse().forEach((lv) => {
        const g = G(sc, lv);
        const h = 1.2;
        const a = g.q05, b = g.q25, m = g.median_gain, c = g.q75, d = g.q95;
        cats.push(`${lab[lv]}   +${fmt(m)}`);
        const s0 = a, s1 = Math.max(b - a, 0), s2 = Math.max(m - h - b, 0), s3 = 2 * h;
        const s4 = Math.max(c - (m + h), 0), s5 = Math.max(d - Math.max(c, m + h), 0);
        [s0, s1, s2, s3, s4, s5].forEach((v, i) => segs[i].push(Math.round(v * 10) / 10));
      });
      text(s, title, { x: MX, y, w: 8.3, h: 0.3, fontSize: 12.5, bold: true, color: C.ink, align: "center", valign: "middle" });
      s.addChart(pres.charts.BAR, segs.map((v, i) => ({ name: `seg${i}`, labels: cats, values: v })),
        chartBase({ x: MX, y: y + 0.3, w: 8.3, h: 2.15, barDir: "bar", barGrouping: "stacked", chartColors: [C.white, light, dark, C.white, dark, light],
          barGapWidthPct: 55, valAxisMinVal: 0, valAxisMaxVal: 300, valAxisMajorUnit: 50, valGridLine: { style: "none" },
          catAxisLabelFontSize: ZH ? 9 : 11, catAxisLabelFrequency: 1, valAxisLabelFontSize: 9.5 }));
    };
    mkChart("S2", 1.72, L("Military blockade: days gained vs no new policy", "軍事封鎖：相較無新政策增加的天數"), C.s2, C.blueL);
    mkChart("S3", 4.27, L("Total isolation + energy shock: days gained", "全面孤立＋能源衝擊：增加的天數"), C.s3, C.navyL);
    text(s, L("Dark bar = middle 50% of futures; light = 90%; white tick = median (also shown as +days).",
      "深色＝中間50%的情境；淺色＝90%；白色刻線＝中位數（即標籤上的＋天數）。"), { x: MX, y: 6.75, w: 8.3, h: 0.25, fontSize: 9.5, color: C.muted });
    card(s, 9.2, 1.72, 3.53, 3.05, C.card);
    text(s, L("Time ratios (Weibull AFT)", "時間比（Weibull AFT）"), { x: 9.4, y: 1.82, w: 3.2, h: 0.36, fontSize: 13, bold: true, color: C.navy });
    const trs = ["feed2food", "rationing", "convoy", "rice_plus3", "surge", "dispersed"];
    const hd = (t) => ({ text: t, options: { bold: true, color: C.white, fill: { color: C.navy }, align: "center" } });
    const rows = [[hd(L("Lever", "槓桿")), hd(L("Blockade", "封鎖")), hd(L("Isolation", "孤立"))]].concat(
      trs.map((t, i) => [{ text: lab[t], options: { color: C.ink } }, { text: `×${A("S2", t).time_ratio.toFixed(2)}`, options: { align: "center", color: C.ink, bold: t === "feed2food" } },
        { text: `×${A("S3", t).time_ratio.toFixed(2)}`, options: { align: "center", color: C.ink, bold: t === "convoy" } }].map((c) => { c.options.fill = { color: i % 2 ? C.card : C.white }; return c; })));
    s.addTable(rows, { x: 9.35, y: 2.25, w: 3.25, colW: [1.55, 0.85, 0.85], rowH: 0.34, fontFace: F.body, fontSize: 10.5, valign: "middle",
      border: { type: "solid", pt: 0.5, color: C.line }, margin: [0.02, 0.06, 0.02, 0.06] });
    card(s, 9.2, 4.95, 3.53, 1.9, C.navy);
    const riceDays = G("S2", "rice_plus3").median_gain;
    text(s, [
      { text: L("Cost check  ", "成本檢核　"), options: { bold: true, color: C.amber, breakLine: true } },
      { text: L(`+3 months of rice ≈ NT$10 bn of paddy (NT$26/kg) for ~${fmt(riceDays)} days. Feed-to-food needs plans and milling contracts, not warehouses.`,
        `公糧再增3個月≈稻穀價值約新臺幣100億元（每公斤26元），只換得約${fmt(riceDays)}天；飼料轉糧需要的是預案與碾製合約，而不是倉庫。`), options: { color: C.white } },
    ], { x: 9.4, y: 5.05, w: 3.15, h: 1.72, fontSize: 11.5, valign: "middle" });
    footer(s, 12, L("Paired comparisons with common random numbers (5,000 draws). Cost: 3 months ≈ 301 kt brown rice ≈ 376 kt paddy × NT$26/kg (MOA 2025 planned-procurement price, japonica dry paddy).",
      "共同隨機數配對比較（5,000次）。成本：3個月≈301千公噸糙米≈376千公噸稻穀×每公斤26元（農業部2025年計畫收購價，蓬萊稻乾穀）。"));
    s.addNotes(L("Days gained by each lever, draw by draw. Feed-to-food - cutting herds early and milling feed corn and soybean meal for people - is the strongest civil lever. Rationing is next. Adding three months of rice buys only about three weeks. Convoys dominate under isolation.",
      "各槓桿逐次配對比較增加的天數。飼料轉糧（提早減少畜禽、把飼料玉米與豆粕碾製供人食用）是最強的民生槓桿，其次是配給。公糧再增3個月只換得約三週；全面孤立下以護航效果最大。"));
  }

  // =========================================================================================
  // 13. Sensitivity
  // =========================================================================================
  {
    const s = pres.addSlide();
    header(s, L("12 · WHAT DRIVES THE UNCERTAINTY?", "12 · 不確定性從何而來？"),
      L("Know the ships, the season and the private import pipeline", "掌握船運、季節與民間進口在途存量"));
    const PL = ZH
      ? { phi: "船運抵達比例", m_imp: "進口糧食在途與庫存", onset_doy: "封鎖起始季節", beta: "未配給時的消費水準", rice_trough: "稻米庫存水準", d_house: "家戶與零售存糧", lam_s: "倉儲遭攻擊損失", a_e: "作物電力敏感度", m_frz: "冷凍肉品庫存", lam_c: "冷鏈損失" }
      : { phi: "Shipping that gets through", m_imp: "Import pipeline & stocks", onset_doy: "Season the blockade starts", beta: "Unrationed consumption", rice_trough: "Rice stock level", d_house: "Household pantry", lam_s: "Strike losses on stores", a_e: "Crop power sensitivity", m_frz: "Cold-store meat", lam_c: "Cold-chain losses" };
    [["S2", L("Military blockade", "軍事封鎖"), C.s2], ["S3", L("Total isolation + energy shock", "全面孤立＋能源衝擊"), C.s3]].forEach(([sc, t, col], i) => {
      const rows = D.sobol[sc].slice().reverse();
      s.addChart(pres.charts.BAR, [{ name: "ST", labels: rows.map((r) => PL[r.parameter] || r.parameter), values: rows.map((r) => Math.round(r.ST * 100) / 100) }],
        chartBase({ x: MX + i * 6.15, y: 1.75, w: 5.95, h: 3.35, barDir: "bar", chartColors: [col], barGapWidthPct: 50, showValue: true,
          dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", dataLabelFontSize: 11, dataLabelColor: C.ink, valAxisMinVal: 0, valAxisMaxVal: 0.75,
          valAxisMajorUnit: 0.25, valAxisLabelFormatCode: "0.00", catAxisLabelFontSize: 11.5, catAxisLabelFrequency: 1, showTitle: true, title: t, titleFontSize: 13, titleBold: true }));
    });
    text(s, L("Bars: total-order Sobol index = share of variance in endurance explained by each input, including its interactions (N = 1,024 base samples).",
      "長條：Sobol總效應指標＝各參數（含交互作用）可解釋的續航力變異比例（基礎樣本N=1,024）。"), { x: MX, y: 5.15, w: 12.1, h: 0.3, fontSize: 10, color: C.muted });
    const so2 = D.sobol.S2, so3 = D.sobol.S3;
    const f = (arr, p) => ((arr.find((r) => r.parameter === p) || { ST: 0 }).ST).toFixed(2);
    const bLo = Math.min(f(so2, "beta"), f(so3, "beta")).toFixed(2), bHi = Math.max(f(so2, "beta"), f(so3, "beta")).toFixed(2);
    const imp = [
      [I.anchor, L("Blockade: shipping", "封鎖：船運"), L(`Arrivals dominate (total index ${f(so2, "phi")}) → port defense, convoys, war-risk insurance guarantees`, `抵達比例居首（總效應 ${f(so2, "phi")}）→ 港口防護、護航、戰爭險保證`)],
      [I.chart, L("Isolation: season & pipeline", "孤立：季節與在途存量"), L(`Season ${f(so3, "onset_doy")}, import pipeline ${f(so3, "m_imp")} → monitor and publish pipeline stocks`, `季節 ${f(so3, "onset_doy")}、進口在途存量 ${f(so3, "m_imp")} → 監測並定期公布在途庫存`)],
      [I.bowl, L("Behavior", "消費行為"), L(`Unrationed consumption ${bLo}–${bHi} → start rationing early`, `未配給消費水準 ${bLo}–${bHi} → 儘早啟動配給`)],
    ];
    imp.forEach(([img, t, d], i) => {
      const x = MX + i * 4.1;
      card(s, x, 5.55, 3.9, 1.3);
      circleIcon(s, img, x + 0.2, 5.75, 0.5, C.navy);
      text(s, t, { x: x + 0.85, y: 5.66, w: 2.9, h: 0.36, fontSize: 13, bold: true, color: C.navy });
      text(s, d, { x: x + 0.85, y: 6.02, w: 2.95, h: 0.78, fontSize: 11, color: C.ink2 });
    });
    footer(s, 13);
    s.addNotes(L("Which unknowns matter most? Under a blockade, how much shipping gets through dominates. Under isolation, the season and the size of private import stocks dominate - information the government can collect now.",
      "哪些未知最重要？軍事封鎖下，船運抵達比例主導一切；全面孤立下，季節與民間進口在途存量最關鍵——這些是政府現在就能蒐集的資訊。"));
  }

  // =========================================================================================
  // 14. RQ4: recommendations
  // =========================================================================================
  {
    const s = pres.addSlide();
    header(s, L("13 · RQ4 · INSTITUTIONALIZE", "13 · RQ4 · 制度化"),
      L("Five recommendations for the Food Mobilization Preparation Plan", "給《糧食動員準備計畫》的五項建議"));
    card(s, MX, 1.72, 4.75, 5.12, C.navy);
    text(s, L("Proposed indicator", "建議指標"), { x: MX + 0.25, y: 1.85, w: 4.3, h: 0.3, fontSize: 11, bold: true, color: C.amber, charSpacing: 1 });
    text(s, L("P(food endurance > 180 days)", "P（糧食續航力 > 180天）"), { x: MX + 0.25, y: 2.15, w: 4.3, h: 0.5, fontSize: 19, bold: true, color: C.white, fontFace: F.head });
    const bars = [
      [L("Quarantine", "海警隔離"), [[L("no new policy", "無新政策"), S("S1", "baseline").p_gt_180]]],
      [L("Military blockade", "軍事封鎖"), [[L("no new policy", "無新政策"), S("S2", "baseline").p_gt_180], [L("civil package", "民生政策組合"), S("S2", "civil_package").p_gt_180]]],
      [L("Total isolation", "全面孤立"), [[L("no new policy", "無新政策"), S("S3", "baseline").p_gt_180], [L("civil package", "民生政策組合"), S("S3", "civil_package").p_gt_180], [L("+ convoys", "＋護航"), S("S3", "full_package").p_gt_180]]],
    ];
    let y = 2.85;
    bars.forEach(([t, arr]) => {
      text(s, t, { x: MX + 0.25, y, w: 4.2, h: 0.3, fontSize: 12.5, bold: true, color: C.ice });
      y += 0.33;
      arr.forEach(([lb, v], j) => {
        text(s, lb, { x: MX + 0.25, y, w: 1.35, h: 0.26, fontSize: 10.5, color: C.ice, valign: "middle" });
        s.addShape("rect", { x: MX + 1.62, y: y + 0.04, w: 2.3, h: 0.18, fill: { color: C.navy2 }, line: { type: "none" } });
        if (v > 0.005) s.addShape("rect", { x: MX + 1.62, y: y + 0.04, w: 2.3 * v, h: 0.18, fill: { color: j === 0 ? C.gray : j === 1 ? C.aqua : C.s1 }, line: { type: "none" } });
        text(s, pct(v), { x: MX + 4.0, y, w: 0.6, h: 0.26, fontSize: 11, bold: true, color: C.white, valign: "middle" });
        y += 0.31;
      });
      y += 0.14;
    });
    text(s, L("Report it yearly next to 'months of rice'.", "每年與「稻米月數」並列公布。"), { x: MX + 0.25, y: 6.35, w: 4.3, h: 0.35, fontSize: 11, italic: true, color: C.ice });
    const islA = cAvg("baseline_disrupted", ISL), islB = cAvg("package_disrupted_islands180", ISL);
    const mD = cAvg("baseline_disrupted", METRO), mN = cAvg("baseline_normal", METRO);
    const gR = fmt(G("S2", "rationing").median_gain), gF = fmt(G("S2", "feed2food").median_gain);
    const perVessel = D.ships.reduce((a, r) => a + r.vessels_per_month * r.days_of_national_minimum_per_vessel, 0)
      / D.ships.reduce((a, r) => a + r.vessels_per_month, 0);
    const carriers = Math.round(30.44 * (1 - D.diet.dom_ind / D.diet.m_req) / perVessel);
    const recs = ZH ? [
      ["在國防報告書與動員計畫中並列結果型指標", "除「稻米月數」外，公布P（續航力 > 180天）及其不確定區間。"],
      ["預先規劃飼料轉糧", `減養程序、飼料玉米與豆粕碾製合約、農民補償機制；模型中軍事封鎖下增加約${gF}天。`],
      ["第一週即啟動分級配給", `封鎖7天內經143處公糧配售站啟動配給；模型中單此一項即增加約${gR}天。`],
      ["預置存糧、確保南北走廊", `外離島預置≥6個月存糧（約${fmt(islA)} → ${fmt(islB)}天）；走廊暢通時北部都會由約${fmt(mD)}天升至${fmt(mN)}天。`],
      ["規劃穀物護航並納入演習", `每月約${carriers}艘散裝船即可補足缺口；將斷糧狀況注入漢光與城鎮韌性演習。`],
    ] : [
      ["Report an outcome metric", "Publish P(endurance > 180 days) with its uncertainty in the NDR and mobilization plans."],
      ["Pre-plan feed-to-food", `Destocking protocol, milling contracts for feed corn and soybean meal, farmer compensation: +${gF} days under blockade.`],
      ["Pre-authorize rationing in week 1", `Start tiered rationing through the 143 public-grain stations within 7 days: +${gR} days on its own.`],
      ["Pre-position; keep the corridor open", `≥ 6 months on outlying islands (~${fmt(islA)} → ~${fmt(islB)} days); an open north–south corridor lifts the northern metros from ~${fmt(mD)} to ~${fmt(mN)} days.`],
      ["Plan grain convoys; exercise them", `~${carriers} bulk carriers a month close the gap; inject food shortfalls into Han Kuang and Urban Resilience drills.`],
    ];
    recs.forEach(([t, d], i) => {
      const yy = 1.72 + i * 1.03;
      card(s, 5.65, yy, 7.08, 0.9);
      s.addShape("ellipse", { x: 5.85, y: yy + 0.2, w: 0.5, h: 0.5, fill: { color: C.amber }, line: { type: "none" } });
      text(s, String(i + 1), { x: 5.85, y: yy + 0.2, w: 0.5, h: 0.5, fontSize: 16, bold: true, color: C.navy, align: "center", valign: "middle", fontFace: F.head });
      text(s, t, { x: 6.55, y: yy + 0.08, w: 6.0, h: 0.34, fontSize: 13.5, bold: true, color: C.navy });
      text(s, d, { x: 6.55, y: yy + 0.42, w: 6.0, h: 0.44, fontSize: 11.5, color: C.ink2 });
    });
    footer(s, 14, L("Indicator values from the model (5,000 draws per scenario). Convoy arithmetic: bulk-carrier cargo if milled for people (see slide 6).",
      "指標數值來自模型（每情境5,000次）。護航估算：散裝船貨物若碾製供人食用（見第6頁）。"));
    s.addNotes(L("To institutionalize the result: report an outcome metric, plan feed-to-food in advance, pre-authorize rationing in the first week, pre-position stocks where the map says food runs out first, and treat grain convoys as a defense task to be exercised.",
      "制度化的做法：公布結果型指標、預先規劃飼料轉糧、第一週即啟動配給、依地圖在最先告急處預置存糧，並把穀物護航視為需要演練的國防任務。"));
  }

  // =========================================================================================
  // 15. Conclusions + references + QR
  // =========================================================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.navy };
    text(s, L("14 · CONCLUSIONS", "14 · 結論"), { x: MX, y: 0.34, w: 8, h: 0.3, fontSize: 11, bold: true, color: C.amber, charSpacing: ZH ? 1 : 2 });
    text(s, L("Food endurance is measurable, and policy can double it", "糧食續航力可以量化，政策可以讓它倍增"),
      { x: MX, y: 0.62, w: 12.1, h: 0.72, fontFace: F.head, fontSize: ZH ? 26 : 29, bold: true, color: C.white, valign: "middle" });
    const s2b = S("S2", "baseline"), s3b = S("S3", "baseline"), s3f = S("S3", "full_package");
    const concl = [
      [I.chart, L("Measurable", "可以量化"), L(`With no new policy: ~${Math.round(s2b.median / 30.44)} months under blockade, ~${Math.round(s3b.median / 30.44)} under isolation; a quarantine is survivable.`,
        `無新政策：軍事封鎖約${Math.round(s2b.median / 30.44)}個月、全面孤立約${Math.round(s3b.median / 30.44)}個月；隔離情境可撐過。`)],
      [I.scale, L("Design beats stockpiles", "設計勝過囤積"), L(`The civil package adds ~${fmt(G("S2", "civil_package").median_gain)} days under blockade; feed-to-food alone ~${fmt(G("S2", "feed2food").median_gain)}.`,
        `民生政策組合在封鎖下增加約${fmt(G("S2", "civil_package").median_gain)}天；單靠飼料轉糧約${fmt(G("S2", "feed2food").median_gain)}天。`)],
      [I.anchor, L("Food is also a naval task", "糧食也是海軍任務"), L(`Grain convoys + civil package → ~${fmt(s3f.median)} days even under near-total isolation.`,
        `穀物護航＋民生政策組合 → 即使近乎全面孤立也有約${fmt(s3f.median)}天。`)],
    ];
    concl.forEach(([img, t, d], i) => {
      const x = MX + i * 2.95;
      card(s, x, 1.7, 2.8, 2.35, C.navy2);
      circleIcon(s, img, x + 0.2, 1.88, 0.55, C.amberD);
      text(s, t, { x: x + 0.2, y: 2.52, w: 2.45, h: 0.42, fontSize: 14, bold: true, color: C.white });
      text(s, d, { x: x + 0.2, y: 2.95, w: 2.45, h: 1.05, fontSize: 11.5, color: C.ice });
    });
    card(s, MX, 4.2, 8.65, 1.05, C.navy2);
    text(s, [
      { text: L("Limits & next steps  ", "限制與下一步　"), options: { bold: true, color: C.amber } },
      { text: L(`Pipeline stocks and behavior use assumed priors; county output beyond rice is allocated by farmland, not measured; food balance = 2022 item detail scaled to ${FBSY} group totals; next: SHELF expert elicitation and back-testing on the 2021 drought and COVID-19 panic buying.`,
        `在途存量與行為參數為假設性事前分布；稻米以外的縣市產量依耕地面積分配、非實測值；糧食平衡＝2022年品項結構依${FBSY}年類別總量調整；下一步：SHELF專家意見徵詢、以2021年旱災與COVID-19搶購潮回測。`), options: { color: C.ice } },
    ], { x: MX + 0.22, y: 4.28, w: 8.25, h: 0.9, fontSize: 11, valign: "middle" });
    const refs = [
      "MND (2019). 2019 National Defense Report. MND (2021, 2025). Quadrennial Defense Review.",
      "Easton, I., Stokes, M., Cooper, C. A., III, & Chan, A. (2017). Transformation of Taiwan's Reserve Force. RAND, RR-1757-OSD.",
      "Ferreira, G. F., & Critelli, J. A. (2023). Taiwan's food resiliency—or not—in a conflict with China. Parameters, 53(2).",
      "Cancian, Mark F., Cancian, Matthew F., & Heginbotham, E. (2025). Lights Out? Wargaming a Chinese Blockade of Taiwan. CSIS.",
      "MOA. Food Balance Sheet 2022; FA01 food supply by product, 2015–2025. AFA (2025). Rice production survey. MOI. County population, Dec 2025. DGBAS. County agriculture, 2024.",
      "USDA FAS (2024). Taiwan Food Security Situation Overview, TW2024-0030. EIA (2026). Taiwan Analysis Brief. Sphere Association (2018). The Sphere Handbook.",
    ];
    text(s, [{ text: L("References", "參考文獻"), options: { bold: true, color: C.amber, breakLine: true } }].concat(
      refs.map((r, i) => ({ text: r, options: { color: C.ice, breakLine: i < refs.length - 1, fontFace: "Calibri" } }))),
    { x: MX, y: 5.42, w: 8.65, h: 1.55, fontSize: 9, paraSpaceAfter: 1.5 });
    // QR placeholder (replace with your GitHub QR code)
    s.addShape("roundRect", { x: 9.85, y: 1.7, w: 2.88, h: 3.55, rectRadius: 0.1, fill: { color: C.navy2 }, line: { type: "none" } });
    s.addShape("roundRect", { x: 10.19, y: 1.95, w: 2.2, h: 2.2, rectRadius: 0.06, fill: { color: C.white }, line: { type: "none" } });
    text(s, "QR", { x: 10.19, y: 1.95, w: 2.2, h: 2.2, fontSize: 20, color: "C8CDD3", align: "center", valign: "middle", bold: true });
    circleIcon(s, I.code, 10.05, 4.35, 0.42, C.amberD);
    text(s, L("Code & data (GitHub)", "程式碼與資料（GitHub）"), { x: 10.55, y: 4.33, w: 2.1, h: 0.46, fontSize: 12.5, bold: true, color: C.white, valign: "middle" });
    text(s, L("Scan to reproduce every figure", "掃描即可重現所有圖表"), { x: 10.05, y: 4.8, w: 2.6, h: 0.35, fontSize: 10.5, color: C.ice });
    text(s, L("Thank you  ·  Questions welcome", "謝謝聆聽　·　歡迎提問"), { x: 9.85, y: 5.55, w: 2.88, h: 0.6, fontSize: 14, bold: true, color: C.amber, align: "center", valign: "middle", fontFace: F.head });
    text(s, `15 / ${TOTAL}`, { x: 11.9, y: 7.03, w: 0.83, h: 0.3, fontSize: 9, color: C.navyL, align: "right", valign: "middle" });
    s.addNotes(L("Three conclusions: endurance is measurable; policy design beats stockpiling; and food security is also a convoy problem for the Navy. The QR code links to the open-source code that reproduces every figure.",
      "三個結論：續航力可以量化；政策設計勝過囤積；糧食安全也是海軍的護航問題。QR code連到可重現所有圖表的開源程式碼。"));
  }

  // pptxgenjs writes only <a:latin> for chart text; add the East Asian font so Chinese chart
  // labels use the same typeface (otherwise viewers fall back to a Simplified-Chinese face).
  const JSZip = require(require.resolve("jszip", { paths: [path.dirname(require.resolve("pptxgenjs"))] }));
  const zip = await JSZip.loadAsync(await pres.write({ outputType: "nodebuffer" }));
  const EA = ZH ? F.body : "Microsoft JhengHei";
  for (const name of Object.keys(zip.files).filter((n) => /^ppt\/charts\/chart\d+\.xml$/.test(n))) {
    let xml = await zip.file(name).async("string");
    xml = xml.replace(/<a:latin typeface="([^"]+)"\/>(?!<a:ea)/g, (m, f) => `<a:latin typeface="${f}"/><a:ea typeface="${EA}"/>`);
    if (ZH) xml = xml.replace(/lang="en-US"/g, 'lang="zh-TW"');
    zip.file(name, xml);
  }
  fs.writeFileSync(OUT, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
  console.log("wrote", OUT);
}

main().catch((e) => { console.error(e); process.exit(1); });
