"""Generate the 3-page PressureIQ Final Analytical Brief & IPL 2027 Auction Recommendations.

Outputs:
  1. reports/submission/PressureIQ_RR_IPL2027_Analytical_Brief.pdf
  2. reports/submission/PressureIQ_RR_IPL2027_Analytical_Brief.docx
"""

from __future__ import annotations

from pathlib import Path

import docx
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]
SUBMISSION_DIR = ROOT / "reports" / "submission"
SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)

PDF_PATH = SUBMISSION_DIR / "PressureIQ_RR_IPL2027_Analytical_Brief.pdf"
DOCX_PATH = SUBMISSION_DIR / "PressureIQ_RR_IPL2027_Analytical_Brief.docx"

DASHBOARD_URL = "https://rajasthanroyalipldashboard.streamlit.app/"

# Palette (Navy, White, Restrained Teal, Amber for pressure/caution, Slate Grey)
C_NAVY = colors.HexColor("#14243A")
C_NAVY_SOFT = colors.HexColor("#1E3A5F")
C_TEAL = colors.HexColor("#0D9488")
C_TEAL_DARK = colors.HexColor("#0F766E")
C_TEAL_BG = colors.HexColor("#F0FDFA")
C_AMBER = colors.HexColor("#D97706")
C_AMBER_DARK = colors.HexColor("#92400E")
C_AMBER_BG = colors.HexColor("#FFFBEB")
C_CORAL = colors.HexColor("#B91C1C")
C_SLATE = colors.HexColor("#334155")
C_MUTED = colors.HexColor("#64748B")
C_LIGHT_BG = colors.HexColor("#F8FAFC")
C_BORDER = colors.HexColor("#CBD5E1")
C_WHITE = colors.HexColor("#FFFFFF")


# ---------------------------------------------------------------------------
# Verified Data Constants (Cross-checked against data/analytical/*.parquet)
# ---------------------------------------------------------------------------
TOP10_BATTERS = [
    ("1", "Yashasvi Jaiswal", "LHB Opener (Ord 1.0) · RR / IND", "+15.73", "+24.65", "+20.56", "[+13.19, +36.11]", "67.3%", "397 (55)", "179.6 / 139.2", "3.78"),
    ("2", "Tim David", "RHB Finisher (Ord 6.0) · MI / AUS", "+13.48", "+23.22", "+0.71", "[+10.72, +35.72]", "56.5%", "455 (46)", "180.9 / 137.2", "4.40"),
    ("3", "Suryakumar Yadav", "RHB No. 3–4 Batter · MI / IND", "+11.55", "+19.11", "−7.57", "[+9.40, +28.83]", "65.2%", "857 (69)", "156.8 / 133.0", "4.20"),
    ("4", "Abhishek Sharma", "LHB Opener (Ord 2.0) · SRH / IND", "+8.94", "+18.06", "−18.62", "[+6.35, +29.77]", "55.3%", "630 (76)", "171.3 / 136.3", "5.56"),
    ("5", "Heinrich Klaasen", "RHB WK-Mid (Ord 5.0) · SRH / SA", "+8.91", "+16.98", "−4.23", "[+6.62, +27.35]", "60.5%", "452 (38)", "154.4 / 135.9", "3.54"),
    ("6", "Rajat Patidar", "RHB No. 4 Batter · RCB (IPL)", "+8.86", "+17.95", "+0.01", "[+6.28, +29.62]", "65.2%", "326 (23)", "155.2 / 131.1", "3.07"),
    ("7", "Andre Russell", "RHB Pace AR (Ord 7.0) · KKR / WI", "+8.07", "+17.94", "+0.03", "[+5.27, +30.61]", "59.4%", "318 (32)", "172.0 / 138.1", "5.35"),
    ("8", "Pathum Nissanka", "RHB Opener (Ord 1.0) · SL / DC", "+6.57", "+15.69", "+18.75", "[+3.99, +27.38]", "58.8%", "406 (34)", "153.2 / 132.8", "3.45"),
    ("9", "Riyan Parag", "RHB No. 4 AR (Ord 4.0) · RR / IND", "+6.43", "+14.51", "+16.14", "[+4.14, +24.88]", "60.5%", "483 (38)", "154.2 / 137.8", "4.35"),
    ("10", "Josh Inglis", "RHB WK Top/Mid (Ord 3.0) · AUS / PBKS", "+5.78", "+15.87", "+3.17", "[+2.92, +28.82]", "65.4%", "241 (26)", "163.5 / 130.5", "4.98"),
]

TOP10_BOWLERS = [
    ("1", "Jasprit Bumrah", "Right-arm Fast · MI / IND", "+1.13", "+2.65", "−2.35", "[+0.70, +4.61]", "76.9%", "641 (52)", "7.82 / 9.57", "3.12 (20)"),
    ("2", "Sunil Narine", "Right-arm Offbreak · KKR (IPL)", "+0.82", "+2.43", "−2.83", "[+0.36, +4.49]", "68.3%", "503 (41)", "7.31 / 9.06", "3.58 (18)"),
    ("3", "Ravichandran Ashwin", "Right-arm Offbreak · RR / CSK", "+0.62", "+2.07", "+0.15", "[+0.21, +3.93]", "69.4%", "478 (36)", "7.91 / 9.08", "3.35 (16)"),
    ("4", "Mustafizur Rahman", "Left-arm Med-Fast · BAN / DC", "+0.50", "+1.84", "−1.21", "[+0.12, +3.55]", "60.4%", "555 (48)", "8.45 / 9.45", "3.24 (18)"),
    ("5", "Axar Patel", "Slow Left-arm Orthodox AR · DC / IND", "+0.46", "+1.86", "+1.55", "[+0.07, +3.65]", "65.3%", "823 (75)", "7.84 / 8.74", "4.62 (38)"),
    ("6", "Richard Ngarava", "Left-arm Fast-Med · ZIM (T20I)", "+0.27", "+1.77", "+1.62", "[−0.15, +3.70]", "60.6%", "422 (33)", "7.72 / 8.77", "5.21 (22)"),
    ("7", "Tim Southee", "Right-arm Med-Fast · NZ / KKR", "+0.23", "+1.90", "+2.31", "[−0.24, +4.04]", "72.0%", "312 (25)", "7.44 / 8.76", "6.73 (21)"),
    ("8", "Maheesh Theekshana", "Right-arm Offbreak · SL / CSK / RR", "+0.23", "+1.58", "−0.53", "[−0.16, +3.31]", "62.9%", "826 (70)", "7.99 / 8.81", "4.12 (34)"),
    ("9", "Rashid Khan", "Right-arm Leg-Break · GT / AFG", "+0.21", "+1.70", "−1.84", "[−0.21, +3.61]", "67.2%", "718 (61)", "7.96 / 8.85", "4.74 (34)"),
    ("10", "Haris Rauf", "Right-arm Fast · PAK (T20I)", "+0.13", "+1.66", "+3.41", "[−0.30, +3.62]", "71.8%", "459 (39)", "8.37 / 9.20", "6.97 (32)"),
]

# Actionable Top 10 RR Auction Recommendations:
# Explicitly links every candidate to one of RR's 4 verified squad requirements (Req A, B, C, D)
# while excluding incumbent RR 2025 players (#1 Jaiswal, #9 Parag, #8 Theekshana),
# lifelong single-franchise untouchables (#1 Bumrah, #2 Narine, #3 Suryakumar — used as valuation benchmarks),
# redundant openers (#4 Abhishek, #8 Nissanka, #12 Sudharsan), IPL-ineligible (#10 Haris Rauf), and retired (#3 Ashwin, #7 Southee).
RR_AUCTION_TOP10 = [
    (
        "1",
        "Tim David\n(RHB Death Finisher, No. 6 · Bat #2)",
        "RPR +13.48 | APR +23.22\nPRD +0.71 | Succ 56.5%\n455b (46m) | SR 180.9 (Exp 137.2)",
        "#1 death-over pressure finisher in dataset: +44.59 CABV/100b across 225 death balls and +43.24 across 193 middle balls (out/100b = 4.40).",
        "Solves RR Req A (Death Batting): Fixes RR's IPL 2025 death collapse (−9.53 CABV/100b, where No. 6–7 options Hetmyer −18.47 & Dubey −35.45 failed).",
        "Core Target\n(Req A · Finisher)",
        "Overseas slot; high price tier if released into auction pool.",
    ),
    (
        "2",
        "Axar Patel\n(SLA Spin All-Rounder · Bowl #5)",
        "RPR +0.46 | APR +1.86\nPRD +1.55 | Succ 65.3%\n823 legal b (75m) | Econ 7.84",
        "Largest pressure sample in Top 5 (75m), rises under pressure (PRD +1.55), and takes 38 pressure wkts (4.62/100b; Middle +2.94 RP/24b on 504b).",
        "Solves RR Req C & B (Mid Spin + LHB): Replaces post-Ashwin finger-spin control (RR 2025 Middle −1.65 RP/24b, Econ 9.94) + LHB No. 5–6 stability.",
        "Core Target\n(Req C/B · 2-Way)",
        "Marquee Indian all-rounder; requires trade window or mega-auction release.",
    ),
    (
        "3",
        "Heinrich Klaasen\n(WK / Middle Enforcer, No. 5 · Bat #5)",
        "RPR +8.91 | APR +16.98\nPRD −4.23 | Succ 60.5%\n452b (38m) | Dot% 25.0%, Out 3.54",
        "Lowest dot-ball rate in Top 10 (25.0%) with elite wicket survival (3.54 outs/100b); dominates Middle (+20.45 on 305b) and Death (+41.87 on 91b).",
        "Solves RR Req B & A (Middle Spin Hitting): Erases RR's 4-year middle-over pressure drag (−9.16 CABV/100b across 1,135b) and bridges into death overs.",
        "Core Target\n(Req B/A · No. 5)",
        "Negative PRD (−4.23) reflects elite +21.22 normal baseline, not weak pressure play.",
    ),
    (
        "4",
        "Rajat Patidar\n(Indian RHB No. 4 Batter · Bat #6)",
        "RPR +8.86 | APR +17.95\nPRD +0.01 | Succ 65.2%\n326b (23m, IPL) | Out 3.07/100b",
        "Lowest dismissal rate in Top 7 (3.07 outs/100b) and +24.1 SR above expectation (155.2 vs 131.1); +39.89 CABV/100b across 177 middle-over balls.",
        "Solves RR Req B (Domestic Middle Order): Pairs with Riyan Parag (#9) to stabilise No. 4 against spin without consuming an overseas slot.",
        "Core Target\n(Req B · Domestic)",
        "23 pressure matches (wider 90% CI [+6.28, +29.62] than 50-match peers).",
    ),
    (
        "5",
        "Mustafizur Rahman\n(Left-Arm Pace & Cutter · Bowl #4)",
        "RPR +0.50 | APR +1.84\nPRD −1.21 | Succ 60.4%\n555 legal b (48m) | Econ 8.45",
        "Saves 1.00 RPO below context expectation (8.45 vs 9.45) with positive pressure value in all 3 phases (PP +1.21, Mid +8.66, Death +1.06 RP/24b).",
        "Solves RR Req D (Left-Arm & Death Pace): High-feasibility upgrade over RR's 2025 left-arm/death pace (Farooqi −20.40, Deshpande −5.97 RP/24b).",
        "Core Target\n(Req D · LA Pace)",
        "Overseas NOC windows and 16.9% boundary rate on flat tracks.",
    ),
    (
        "6",
        "Andre Russell\n(Pace Power All-Rounder, No. 7 · Bat #7)",
        "RPR +8.07 | APR +17.94\nPRD +0.03 | Succ 59.4%\n318b (32m) | SR 172.0 (Exp 138.1)",
        "Adds +33.9 SR points above context expectation with dual Middle (+43.41 on 174b) and Death (+29.26 on 144b) pressure impact.",
        "Solves RR Req A & D (Finisher + Seam Depth): Restores No. 6/7 boundary ceiling alongside 2-over hard-length pace utility.",
        "Role-Specific\n(Req A/D · Pace AR)",
        "Higher dismissal rate (5.35/100b) and age/workload management.",
    ),
    (
        "7",
        "Ravi Bishnoi\n(Indian Leg-Break Strike · Bowl #11)",
        "RPR +0.03 | APR +1.52\nPRD +1.50 | Succ 67.2%\n647 legal b (61m) | Wkt 5.87/100b",
        "Elite pressure wicket rate (5.87/100b, 38 wkts) and positive PRD (+1.50), excelling in Middle (+2.73 on 490b) and Death (+7.41 on 79b).",
        "Solves RR Req C (Domestic Wrist-Spin): Restores middle-over wicket threat (RR 2025 middle wkt rate fell to 3.17/100b post-Chahal) as an Indian spinner.",
        "Role-Specific\n(Req C · Ind Spin)",
        "Conservative RPR (+0.03) reflects leg-spin match variance (CI [−0.39, +3.43]).",
    ),
    (
        "8",
        "Rashid Khan\n(Leg-Break All-Phase Spinner · Bowl #9)",
        "RPR +0.21 | APR +1.70\nPRD −1.84 | Succ 67.2%\n718 legal b (61m) | Econ 7.96",
        "67.2% match success across 61 pressure matches with elite Middle (+4.49 RP/24b on 504b) and Death (+4.43 on 112b) containment + 34 wickets.",
        "Solves RR Req C & A (Marquee Spin + No. 8 Bat): Upgrades RR's overseas wrist-spin slot (where Hasaranga posted +0.22 RP/24b & −157.5 CABV in 2025).",
        "Role-Specific\n(Req C · OS Spin)",
        "Requires overseas slot and marquee trade/auction release.",
    ),
    (
        "9",
        "Rovman Powell\n(RHB Power Finisher, No. 5–6 · Bat #11)",
        "RPR +5.07 | APR +12.28\nPRD +5.20 | Succ 53.3%\n651b (60m) | SR 145.2 (Exp 130.9)",
        "Deepest finisher sample (651 pressure balls in 60m), rises under pressure (PRD +5.20), and posts +39.08 CABV/100b across 196 death balls.",
        "Solves RR Req A (Accessible Death Finisher): Realistic, auction-accessible alternative if #1 Tim David or #6 Andre Russell are retained.",
        "Alternative\n(Req A · Finisher)",
        "Modest middle-over rate (+2.24 CABV/100b on 377b); best deployed at Over 14+.",
    ),
    (
        "10",
        "Nathan Ellis\n(Right-Arm Death/PP Pace · Bowl #15)",
        "RPR −0.21 | APR +1.43\nPRD +0.45 | Succ 61.5%\n334 legal b (26m) | Wkt 6.59/100b",
        "Saves 1.06 RPO below expectation (8.30 vs 9.36) with 6.59 wkts/100b and positive value in PP (+2.19), Mid (+4.85) & Death (+4.70 RP/24b on 138b).",
        "Solves RR Req D (Death & PP Pace Specialist): Auction-realistic death/PP seamer (paired with #6 Richard Ngarava, RPR +0.27, PP +4.84 RP/24b).",
        "Alternative\n(Req D · Death Pace)",
        "26 pressure matches leave RPR slightly below 0 (−0.21) despite +1.43 APR.",
    ),
]

METRIC_GUIDE_LEFT = [
    ("PI — Pressure Index (0–100 Scale):", "Plain English: How difficult the match state is right now, provided the contest is still alive. Formula: PI_bat = 100 * (1 − WP_bat) * min(1, L / median(L | innings)); PI_bowl replaces (1 − WP_bat) with WP_bat. Tiers: Elevated >= 52.0 (top 35%), High >= 66.1 (top 12%)."),
    ("WP & L — Win Probability & Leverage:", "Plain English: WP_bat is the batting team's pre-delivery win chance (5-fold match-grouped CV). Leverage L measures how much the next ball can swing WP across outcomes {0,1,2,3,4,6,W}. Dead rubbers have L ≈ 0."),
    ("WV — Wicket Value at Stake (Runs):", "Plain English: Expected remaining runs lost if a wicket falls on the current ball: WV = E(u, w) − E(u, w − 1) from format-scaled Duckworth-Lewis resource curves (mean WV = 14.8 runs)."),
    ("CABV — Context-Adjusted Batting Value (/100b):", "Plain English: Runs added above a peer in the same format, innings, phase, wickets & pressure tier per 100 balls faced, minus marginal dismissal cost: ((r − E[r|ctx]) − 0.30*WV*(out − E[out|ctx])) * 100 / balls_faced."),
    ("RP — Context-Adjusted Runs Prevented (/24b):", "Plain English: Runs saved below context expectation plus marginal wicket credit per 24 bowling deliveries (one 4-over spell): ((E[c|ctx] − c) + 0.20*WV*(wkt − E[wkt|ctx])) * 24 / deliveries."),
]

METRIC_GUIDE_RIGHT = [
    ("APR — Adjusted Pressure Rating (Shrunk Mean):", "Plain English: Best point estimate of true pressure skill after Empirical Bayes (EB) shrinks noisy small samples toward the eligible cohort average: APR = mu_p + B_p * (Raw_Rate − mu_p), B_p = tau^2 / (tau^2 + SE^2)."),
    ("RPR — Reliable Pressure Rating (Official Rank):", "Plain English: The safe minimum performance floor we can trust with 90% confidence: RPR = APR − 1.2816 * SD_post. Rewards both high APR and large multi-match sample size."),
    ("PRD — Pressure Response Delta (vs Own Normal):", "Plain English: How much a player rises (>0) or drops (<0) under pressure compared with their own shrunk normal-state baseline: PRD = APR_pressure − Shrunk_Normal. Negative PRD can still coexist with #1 APR/RPR if normal form is an outlier."),
    ("Match Success % & 90% EB CI:", "Plain English: Success % = share of unique pressure matches where the player delivered net positive value (>0). 90% CI = two-sided uncertainty range [APR − 1.645*SD, APR + 1.645*SD] from 250 match-cluster bootstrap resamples."),
    ("Standard Cricket Abbreviations:", "SR = runs per 100 balls faced (excl. wides); Econ = runs conceded per 6 legal balls; RRR = required runs/over; DLS = Duckworth-Lewis-Stern; RHB/LHB = Right/Left-Hand Batter; SLA = Slow Left-Arm Orthodox; WK = Wicketkeeper; AR = All-Rounder."),
]


# ---------------------------------------------------------------------------
# PDF Generation (ReportLab — Strictly 3 Pages)
# ---------------------------------------------------------------------------
def _draw_page_chrome(canvas, doc):
    canvas.saveState()
    w, h = A4
    if doc.page > 1:
        canvas.setFillColor(C_NAVY)
        canvas.rect(0, h - 10 * mm, w, 10 * mm, fill=1, stroke=0)
        canvas.setFillColor(C_TEAL)
        canvas.rect(0, h - 10.8 * mm, w, 0.8 * mm, fill=1, stroke=0)
        canvas.setFont("Helvetica-Bold", 7.2)
        canvas.setFillColor(C_WHITE)
        canvas.drawString(12 * mm, h - 6.5 * mm, "PRESSUREIQ — BEYOND PLAYER STATISTICS · RAJASTHAN ROYALS IPL 2027 BRIEF")
        canvas.drawRightString(w - 12 * mm, h - 6.5 * mm, f"VALIDATED SUBMISSION · PAGE {doc.page} OF 3")

    canvas.setStrokeColor(C_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(12 * mm, 9.5 * mm, w - 12 * mm, 9.5 * mm)
    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(C_MUTED)
    canvas.drawString(
        12 * mm,
        5.8 * mm,
        "PressureIQ · Official Scope: 853 Matches (371 IPL + 482 T20I, 2022–2026) · 23/23 Validation Checks Passed",
    )
    canvas.setFillColor(C_TEAL_DARK)
    canvas.drawRightString(w - 12 * mm, 5.8 * mm, f"{DASHBOARD_URL}  |  Page {doc.page} of 3")
    canvas.restoreState()


def build_pdf() -> None:
    w, h = A4
    doc = BaseDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=11 * mm,
        bottomMargin=12 * mm,
        title="PRESSUREIQ — Beyond Player Statistics (Rajasthan Royals IPL 2027 Auction Brief)",
        author="PressureIQ Cricket Analytics",
    )
    frame_p1 = Frame(12 * mm, 11.5 * mm, w - 24 * mm, h - 20 * mm, id="f1", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    frame_p2 = Frame(12 * mm, 11.5 * mm, w - 24 * mm, h - 24 * mm, id="f2", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates(
        [
            PageTemplate(id="p1", frames=[frame_p1], onPage=_draw_page_chrome),
            PageTemplate(id="p2", frames=[frame_p2], onPage=_draw_page_chrome),
        ]
    )

    ss = getSampleStyleSheet()
    st_h1 = ParagraphStyle("H1", parent=ss["Normal"], fontName="Helvetica-Bold", fontSize=9.2, leading=11.0, textColor=C_NAVY, spaceBefore=3.0, spaceAfter=2.0)
    st_h2 = ParagraphStyle("H2", parent=ss["Normal"], fontName="Helvetica-Bold", fontSize=8.0, leading=9.8, textColor=C_TEAL_DARK, spaceBefore=2.0, spaceAfter=1.2)
    st_body = ParagraphStyle("Body", parent=ss["Normal"], fontName="Helvetica", fontSize=7.3, leading=9.4, textColor=C_SLATE, alignment=TA_JUSTIFY, spaceAfter=2.0)
    st_small = ParagraphStyle("Small", parent=ss["Normal"], fontName="Helvetica", fontSize=6.6, leading=8.2, textColor=C_SLATE)
    st_th = ParagraphStyle("TH", parent=ss["Normal"], fontName="Helvetica-Bold", fontSize=6.4, leading=7.6, textColor=C_WHITE, alignment=TA_CENTER)
    st_th_l = ParagraphStyle("THL", parent=st_th, alignment=TA_LEFT)
    st_td = ParagraphStyle("TD", parent=ss["Normal"], fontName="Helvetica", fontSize=6.3, leading=7.5, textColor=C_SLATE, alignment=TA_CENTER)
    st_td_l = ParagraphStyle("TDL", parent=st_td, alignment=TA_LEFT)
    st_td_b = ParagraphStyle("TDB", parent=st_td, fontName="Helvetica-Bold", textColor=C_NAVY)
    st_foot = ParagraphStyle("Foot", parent=ss["Normal"], fontName="Helvetica", fontSize=6.0, leading=7.3, textColor=C_SLATE, spaceAfter=1.0)

    story = []

    # ==================== PAGE 1 ====================
    hdr_html = (
        "<font name='Helvetica-Bold' size='13.2' color='#FFFFFF'>PRESSUREIQ — Beyond Player Statistics</font><br/>"
        "<font name='Helvetica' size='8.1' color='#CCFBF1'><i>Identifying Reliable Performers Under Pressure and Evaluating Their Value for Rajasthan Royals' IPL 2027 Auction</i></font><br/>"
        "<font name='Helvetica-Bold' size='6.6' color='#FDE68A'>DATA → METHODOLOGY → PLAIN-ENGLISH METRICS → MODEL TRADE-OFFS → RR SQUAD GAPS → TOP 10 AUCTION TARGETS  |  VALIDATED (23/23)</font>"
    )
    hdr_tbl = Table([[Paragraph(hdr_html, ParagraphStyle("Hdr", leading=12.0))]], colWidths=[186 * mm])
    hdr_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), C_NAVY),
                ("TOPPADDING", (0, 0), (-1, -1), 5.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("LINEBELOW", (0, 0), (-1, -1), 2.0, C_TEAL),
            ]
        )
    )
    story.append(hdr_tbl)
    story.append(Spacer(1, 2.8))

    # KPI Strip
    kpi_cells = [
        ("OFFICIAL SCOPE", "853 Matches", "371 IPL + 482 T20I (837 active)"),
        ("ANALYSED BALLS", "193,842", "99.9% of 193,988 reg. balls"),
        ("PRESSURE SHARE", "35.0% Bat / 34.4% Bowl", "67,868 bat · 66,671 bowl balls"),
        ("1ST-INN PAR vs RR", "r = −0.80 vs −0.73", "Raw run rate inverts pressure"),
        ("ELIGIBLE COHORT", "177 Bat / 162 Bowl", "≥10 pressure matches & ≥100/120b"),
        ("RANK STABILITY", "ρ = 0.90 Bat / 0.89 Bowl", "Median Spearman across 13 specs"),
    ]
    kpi_row = [
        Paragraph(
            f"<font name='Helvetica-Bold' size='5.6' color='#0F766E'>{lbl}</font><br/>"
            f"<font name='Helvetica-Bold' size='8.0' color='#14243A'>{val}</font><br/>"
            f"<font name='Helvetica' size='5.5' color='#64748B'>{sub}</font>",
            ParagraphStyle("K", leading=7.8),
        )
        for lbl, val, sub in kpi_cells
    ]
    kpi_tbl = Table([kpi_row], colWidths=[31 * mm] * 6)
    kpi_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), C_LIGHT_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, C_BORDER),
                ("LINEABOVE", (0, 0), (-1, 0), 1.6, C_TEAL),
                ("TOPPADDING", (0, 0), (-1, -1), 2.8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.8),
                ("LEFTPADDING", (0, 0), (-1, -1), 3.5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
            ]
        )
    )
    story.append(kpi_tbl)
    story.append(Spacer(1, 2.5))

    # Section 1: The Decision Problem & Plain-English Metric Decoder
    story.append(Paragraph("1. THE DECISION PROBLEM & PLAIN-ENGLISH METRIC DECODER", st_h1))
    story.append(
        Paragraph(
            "Franchise scouting must answer a practical question: <b>who can be trusted when match conditions become difficult, and how should Rajasthan Royals translate that evidence into IPL 2027 squad decisions?</b> Raw batting averages, strike rates (SR) and economy rates fail because they pool dead-rubber blowouts with crunch moments—in first-innings cricket, raw current run rate actually correlates <b>negatively</b> with pressure (<b>r = −0.73</b>), as batting at 160/1 in Over 16 is a low-pressure cruise (PI = <b>15.6</b>) while rebuilding from 45/4 in Over 7 is genuine pressure (PI = <b>59.5</b>). PressureIQ separates four distinct questions:",
            st_body,
        )
    )
    decoder_rows = [
        [
            Paragraph("<b>1. Raw Context Value (CABV / RP)</b><br/><i>\"How did the player perform against par in this exact state?\"</i><br/><b>Bat (CABV/100b):</b> Runs added above context expectation minus marginal wicket cost per 100 balls.<br/><b>Bowl (RP/24b):</b> Runs saved below expectation plus wicket credit per 24 deliveries (one 4-over spell).", st_small),
            Paragraph("<b>2. Shrunk Pressure Skill (APR)</b><br/><i>\"What is our best estimate of true pressure skill after removing luck?\"</i><br/><b>Adjusted Pressure Rating (APR)</b> uses Empirical Bayes (EB) to pull noisy small-sample rates toward the cohort average. It represents expected output under pressure.", st_small),
            Paragraph("<b>3. Reliable Floor (RPR — Official Rank)</b><br/><i>\"What minimum output can we bank on with 90% confidence?\"</i><br/><b>Reliable Pressure Rating (RPR)</b> = APR − 1.2816 × SD. Penalises high variance and small match counts so one-off cameos cannot top the rankings.", st_small),
            Paragraph("<b>4. Pressure Elevation (PRD) & Repeatability</b><br/><i>\"Does the player rise or dip vs their own normal form, and how often?\"</i><br/><b>PRD</b> = APR_pressure − Shrunk_Normal. <b>Match Success %</b> = share of pressure matches with net value > 0.", st_small),
        ]
    ]
    dec_tbl = Table(decoder_rows, colWidths=[46.5 * mm] * 4)
    dec_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), C_TEAL_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, C_TEAL),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, C_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3.2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(dec_tbl)
    story.append(Spacer(1, 2.5))

    # Section 2: Methodology
    story.append(Paragraph("2. METHODOLOGY — HOW PRESSUREIQ EVALUATES & VALIDATES PERFORMANCE", st_h1))
    meth_data = [
        [Paragraph("Layer", st_th_l), Paragraph("Implemented Analytical Specification & Cricket Rationale", st_th_l), Paragraph("Verified Audit / Validation Evidence", st_th_l)],
        [
            Paragraph("<b>1. Data Scope & Exclusions</b>", st_td_b),
            Paragraph("<b>853 official matches</b> (371 IPL + 482 T20I, 2022–2026; 194,014 balls). Excludes 30 Other-T20 matches (Emerging Asia Cup / Rising Stars), 16 abandoned 0-ball matches, and <b>38 Super Over balls</b> (innings 3–4 across 6 ties) from regulation rankings.", st_td_l),
            Paragraph("<b>837 active matches</b>; <b>193,988</b> regulation balls; <b>193,842</b> pressure-eligible balls (146 balls in 2 unrevised-target DLS chases excluded).", st_td_l),
        ],
        [
            Paragraph("<b>2. Law 18/22 Accounting</b>", st_td_b),
            Paragraph("Separates <b>batter_runs</b>, <b>team_runs</b> (runs+extras1+extras2), and <b>bowler_conceded</b> (batter_runs + 1-run penalty on wides/no-balls; <b>36 extras_2_runs</b> rows verified as no-ball byes/leg-byes not debited to bowler). Legal balls exclude wides and no-balls (including <b>264 row-verified 'other'</b> beamer/full-toss no-balls). Only Caught, Bowled, LBW, Stump & Hit Wicket credit <b>bowler_wicket</b> (600 RunOuts, 6 Retire Outs, 3 Obstructing Field excluded). Keyed by <b>player_id</b> (Basil Hameed IDs 8638 & 39444 unmerged).", st_td_l),
            Paragraph("<b>100%</b> margin reconciliation on unrevised 'won by N runs' matches (97.6% overall). Zero innings exceed 120 legal balls once 'other' is classified as no-ball.", st_td_l),
        ],
        [
            Paragraph("<b>3 & 4. Pre-Delivery PI & Innings Split</b>", st_td_b),
            Paragraph("Strict pre-delivery state (zero outcome leakage). <b>1st Innings:</b> Format-scaled Duckworth–Lewis curves E(u,w) = Z_w(1−e^(−b_w·u)) (IPL=1.035, T20I=0.972) compute Par Deviation and Wicket Value <b>WV = E(u,w)−E(u,w−1)</b>. <b>2nd Innings:</b> Evaluates log(runs_needed/E(u,w)), RRR, wickets & balls left (honouring revised DLS legal-ball allocations). 5-fold match-grouped CV estimates <b>WP_bat</b> and 7-outcome next-ball leverage <b>L</b>: <b>PI_bat = 100·(1−WP_bat)·min(1, L/med(L|inn))</b>; <b>PI_bowl = 100·WP_bat·min(1, L/med(L|inn))</b>.", st_td_l),
            Paragraph("1st-Inn Resource MAE = <b>16.47 runs</b> vs <b>25.10</b> naive RR (R²=0.825). Out-of-sample WP Brier = <b>0.214</b> (Inn 1) & <b>0.145</b> (Inn 2). Thresholds: <b>Elevated ≥ 52.0</b> (top 35%), <b>High ≥ 66.1</b> (top 12%).", st_td_l),
        ],
        [
            Paragraph("<b>5–7. Context Baselines, CABV & RP</b>", st_td_b),
            Paragraph("5-fold match-grouped hierarchical EB baselines (k=100 balls) across <b>format × innings × phase × wickets_bucket × pressure_level</b>.<br/><b>Batting CABV (/100b):</b> [(r − E[r|ctx]) − 0.30·WV·(striker_out − E[out|ctx])] × 100 / balls_faced.<br/><b>Bowling RP (/24b):</b> [(E[c|ctx] − c) + 0.20·WV·(bowler_wkt − E[wkt|ctx])] × 24 / deliveries.", st_td_l),
            Paragraph("Chronological split (trained 2022–24 → tested 2025–26) confirms positive out-of-sample skill across all 4 targets (runs, outs, conceded, wickets).", st_td_l),
        ],
        [
            Paragraph("<b>8 & 9. EB Shrinkage & RPR Ranking</b>", st_td_b),
            Paragraph("<b>Eligibility:</b> ≥10 unique pressure matches and ≥100 pressure balls (batters, n=177) or ≥120 legal balls (bowlers, n=162). <b>250 match-cluster bootstrap resamples</b> (seed=42) estimate SE_i. Ball-weighted EB shrinks raw rates toward eligible prior: <b>APR = mu + B_i(Raw − mu)</b>, B_i = tau²/(tau²+SE_i²). Official rank uses <b>RPR = APR − 1.2816 × SD_post</b>.", st_td_l),
            Paragraph("23/23 automated validation checks pass. Across 13 sensitivity specs, median Spearman rank correlation is <b>ρ = 0.90 (Bat)</b> and <b>0.89 (Bowl)</b>.", st_td_l),
        ],
    ]
    meth_tbl = Table(meth_data, colWidths=[23 * mm, 109 * mm, 54 * mm], repeatRows=1)
    meth_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), C_NAVY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_LIGHT_BG]),
                ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, C_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 2.3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.3),
                ("LEFTPADDING", (0, 0), (-1, -1), 3.0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3.0),
            ]
        )
    )
    story.append(meth_tbl)
    story.append(Spacer(1, 2.5))

    # Section 2B: Model Trade-Offs & Limitations (Priority #3)
    story.append(Paragraph("3. MODEL TRADE-OFFS, DESIGN CHOICES & KNOWN LIMITATIONS", st_h1))
    trade_html = (
        "<font name='Helvetica' size='6.8' color='#182536'>"
        "<b>1. Conservatism vs Breakout Talent (RPR Lower Bound & 10-Match Gate):</b> Ordering by the 90% lower bound (<b>RPR</b>) intentionally penalises smaller match counts to prevent flukes. For example, <b>#6 Rajat Patidar</b> has a higher shrunk mean (APR <b>+17.95</b>) than <b>#5 Heinrich Klaasen</b> (APR <b>+16.98</b>), but ranks one spot lower on RPR (+8.86 vs +8.91) because 23 pressure matches carry wider uncertainty than 38. Similarly, emerging RR opener <b>Vaibhav Sooryavanshi</b> posts APR <b>+13.52</b> across 160 balls (23m) but sits at #19 on RPR (+1.87). Scouts evaluating young talent should pair <b>APR</b> with <b>RPR</b>.<br/>"
        "<b>2. Differential Shrinkage in PRD (Why Elite Outliers Show Negative PRD):</b> T20 cricket has ~2× more normal balls (65%) than pressure balls (35%), and between-player variance is 2.2× larger in normal states (tau²_norm / tau²_press = 2.24 in bowling). Thus normal rates retain more signal (median B_norm = 0.56 vs B_press = 0.26). For historic normal-state outliers like <b>#1 Jasprit Bumrah</b> (+7.00 raw / +5.00 shrunk normal vs +5.97 raw / +2.65 shrunk pressure) and <b>#3 Suryakumar Yadav</b> (+26.68 normal vs +19.11 pressure), negative PRD (<b>−2.35</b> and <b>−7.57</b>) reflects a high normal ceiling and stronger pressure shrinkage—<b>not</b> poor pressure play.<br/>"
        "<b>3. Observable State vs Micro-Venue Conditions:</b> Baselines stratify by format, innings, phase, wickets and pressure tier (with format par multipliers IPL=1.035, T20I=0.972) rather than venue-specific pitch wear or dew radar, trading micro-venue granularity for out-of-sample stability.<br/>"
        "<b>4. Fixed Marginal Wicket Weights (0.30·WV Bat / 0.20·WV Bowl):</b> Charging the full resource drop (~14.8 runs) would let binary single-ball dismissal luck swamp run-scoring/saving skill; marginal replacement weights (~3–5 runs) stabilise player signal (verified across 0.15–0.50 sensitivity specs).<br/>"
        "<b>5. Pooled IPL + T20I Scope Requires Squad-Fit Filtering:</b> Combining IPL and T20I doubles pressure sample depth, but raw leaderboards include incumbent RR players, redundant roles, and T20I-only players ineligible for the IPL—requiring the separate Section 5 auction filter."
        "</font>"
    )
    trade_box = Table([[Paragraph(trade_html, ParagraphStyle("TB", leading=8.6))]], colWidths=[186 * mm])
    trade_box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), C_AMBER_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, C_AMBER),
                ("LINEBEFORE", (0, 0), (0, -1), 2.8, C_AMBER),
                ("TOPPADDING", (0, 0), (-1, -1), 3.2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(trade_box)

    # ==================== PAGE 2 ====================
    story.append(NextPageTemplate("p2"))
    story.append(PageBreak())

    story.append(Paragraph("4. VALIDATED TOP-10 PERFORMERS UNDER PRESSURE (COMBINED IPL + T20I, 2022–2026)", st_h1))
    story.append(
        Paragraph(
            "Ordered strictly by <b>Reliable Pressure Rating (RPR = APR − 1.2816 × SD_post)</b>. Each row separates four distinct concepts: <b>RPR</b> (90% lower-bound ranking floor), <b>Shrunk APR</b> (expected pressure rate after Empirical-Bayes smoothing), <b>PRD vs Norm</b> (elevation or drop relative to the player's own shrunk normal baseline), and <b>Match Succ%</b> (consistency across unique pressure matches).",
            st_body,
        )
    )

    # Table 4A: Top 10 Batters
    story.append(Paragraph("Table 4A · Official Top 10 Batters Under Pressure (Units: CABV Runs / 100 Pressure Balls Faced)", st_h2))
    bat_hdr = [
        Paragraph("Rk", st_th),
        Paragraph("Batter", st_th_l),
        Paragraph("Playing Role & Teams", st_th_l),
        Paragraph("RPR", st_th),
        Paragraph("Shrunk APR", st_th),
        Paragraph("PRD vs Norm", st_th),
        Paragraph("90% EB CI", st_th),
        Paragraph("Match Succ%", st_th),
        Paragraph("Balls (M)", st_th),
        Paragraph("p_SR / Exp", st_th),
        Paragraph("Out/100b", st_th),
    ]
    bat_rows = [bat_hdr]
    for r in TOP10_BATTERS:
        bat_rows.append(
            [
                Paragraph(f"<b>#{r[0]}</b>", st_td_b),
                Paragraph(f"<b>{r[1]}</b>", st_td_l),
                Paragraph(r[2], st_td_l),
                Paragraph(f"<font color='#0F766E'><b>{r[3]}</b></font>", st_td),
                Paragraph(f"<b>{r[4]}</b>", st_td),
                Paragraph(f"<font color='{'#0F766E' if r[5].startswith('+') else '#B91C1C'}'>{r[5]}</font>", st_td),
                Paragraph(r[6], st_td),
                Paragraph(r[7], st_td),
                Paragraph(r[8], st_td),
                Paragraph(r[9], st_td),
                Paragraph(r[10], st_td),
            ]
        )
    t_bat = Table(bat_rows, colWidths=[7 * mm, 24 * mm, 35 * mm, 12 * mm, 13 * mm, 13 * mm, 23 * mm, 13 * mm, 14 * mm, 19 * mm, 13 * mm], repeatRows=1)
    t_bat.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), C_NAVY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_LIGHT_BG]),
                ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, C_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 2.0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.0),
                ("LEFTPADDING", (0, 0), (-1, -1), 2.2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2.2),
            ]
        )
    )
    story.append(t_bat)
    story.append(Spacer(1, 2.2))

    # Table 4B: Top 10 Bowlers
    story.append(Paragraph("Table 4B · Official Top 10 Bowlers Under Pressure (Units: Context-Adjusted Runs Prevented / 24 Pressure Deliveries)", st_h2))
    bowl_hdr = [
        Paragraph("Rk", st_th),
        Paragraph("Bowler", st_th_l),
        Paragraph("Bowling Style & Teams", st_th_l),
        Paragraph("RPR", st_th),
        Paragraph("Shrunk APR", st_th),
        Paragraph("PRD vs Norm", st_th),
        Paragraph("90% EB CI", st_th),
        Paragraph("Match Succ%", st_th),
        Paragraph("Legal b (M)", st_th),
        Paragraph("p_Econ / Exp", st_th),
        Paragraph("Wkt/100b (W)", st_th),
    ]
    bowl_rows = [bowl_hdr]
    for r in TOP10_BOWLERS:
        bowl_rows.append(
            [
                Paragraph(f"<b>#{r[0]}</b>", st_td_b),
                Paragraph(f"<b>{r[1]}</b>", st_td_l),
                Paragraph(r[2], st_td_l),
                Paragraph(f"<font color='#0F766E'><b>{r[3]}</b></font>", st_td),
                Paragraph(f"<b>{r[4]}</b>", st_td),
                Paragraph(f"<font color='{'#0F766E' if r[5].startswith('+') else '#B91C1C'}'>{r[5]}</font>", st_td),
                Paragraph(r[6], st_td),
                Paragraph(r[7], st_td),
                Paragraph(r[8], st_td),
                Paragraph(r[9], st_td),
                Paragraph(r[10], st_td),
            ]
        )
    t_bowl = Table(bowl_rows, colWidths=[7 * mm, 25 * mm, 34 * mm, 11 * mm, 13 * mm, 13 * mm, 22 * mm, 13 * mm, 15 * mm, 18 * mm, 15 * mm], repeatRows=1)
    t_bowl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), C_NAVY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_LIGHT_BG]),
                ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, C_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 2.0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.0),
                ("LEFTPADDING", (0, 0), (-1, -1), 2.2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2.2),
            ]
        )
    )
    story.append(t_bowl)
    story.append(Spacer(1, 2.5))

    # Evidence Patterns + RR Squad Requirement Matrix (Priority #4)
    story.append(Paragraph("5. WHAT MAKES PLAYERS RELIABLE & RAJASTHAN ROYALS' 4 VERIFIED SQUAD REQUIREMENTS", st_h1))
    story.append(
        Paragraph(
            "• <b>Why the Leaders Win Pressure States:</b> Top-10 batters score <b>+18 to +44 SR points above context expectation</b> while restricting dismissals to <b>3.07–5.56 outs/100b</b> (cohort mean: 5.18). <b>#1 Yashasvi Jaiswal</b> hits 32.5% boundaries under pressure with 3.78 outs/100b (67.3% match success across 55m); <b>#5 Heinrich Klaasen</b> has the lowest dot-ball rate (<b>25.0%</b>) and <b>#6 Rajat Patidar</b> the lowest dismissal rate (<b>3.07/100b</b>). Top-10 bowlers suppress scoring by <b>0.82–1.75 RPO below context expectation</b> while striking every 14–32 legal balls, with low single-match concentration (best match = <b>8.1%</b> of career positive value for Bumrah, <b>9.9%</b> for Jaiswal).<br/>"
            "• <b>Connecting Player Evidence to Rajasthan Royals' Actual IPL Squad Needs:</b> Auditing RR's ball-by-ball record across IPL 2022–2025 and IPL 2025 reveals that RR is <b>already elite in Powerplay Batting</b> (+34.50 CABV/100b in 2025, anchored by <b>#1 Jaiswal</b>, <b>#9 Parag</b>, and <b>#19 Vaibhav Sooryavanshi</b>), but suffers from <b>four specific phase deficits</b> that define our IPL 2027 auction target requirements:",
            st_body,
        )
    )

    rr_req_rows = [
        [
            Paragraph("RR Squad Requirement", st_th_l),
            Paragraph("Verified RR Pressure Deficit (IPL Data)", st_th_l),
            Paragraph("Incumbent RR 2025 Context", st_th_l),
            Paragraph("Mapped Auction Targets (Page 3)", st_th_l),
        ],
        [
            Paragraph("<b>Req A · Death-Over Finishing (No. 5–7)</b>", st_td_b),
            Paragraph("<b>IPL 2025 Death Bat: −9.53 CABV/100b</b> (SR 146.6, dismissal rate <b>8.27 outs/100b</b> across 133 pressure balls).", st_td_l),
            Paragraph("Dhruv Jurel (+13.78/100b) was positive, but Shimron Hetmyer (<b>−18.47</b>), Nitish Rana (<b>−18.14</b>) & Shubham Dubey (<b>−35.45</b>) struggled.", st_td_l),
            Paragraph("<b>#1 Tim David</b> (Core), <b>#6 Andre Russell</b> (Role-Specific), <b>#9 Rovman Powell</b> (Alternative).", st_td_l),
        ],
        [
            Paragraph("<b>Req B · Middle-Over Spin Hitting (No. 4–5)</b>", st_td_b),
            Paragraph("<b>IPL 2022–25 Middle Bat: −9.16 CABV/100b</b> (SR 123.6, dismissal rate 4.41/100b across 1,135 pressure balls).", st_td_l),
            Paragraph("<b>#9 Riyan Parag</b> (+18.87 Middle CABV/100b career; +90.85 in 2025) carried the middle order; Sanju Samson posted −16.38 in 2025.", st_td_l),
            Paragraph("<b>#3 Heinrich Klaasen</b> (Core WK/No. 5), <b>#4 Rajat Patidar</b> (Core Domestic No. 4), <b>#2 Axar Patel</b> (LHB floater).", st_td_l),
        ],
        [
            Paragraph("<b>Req C · Middle-Over Spin Control & Strike</b>", st_td_b),
            Paragraph("<b>IPL 2025 Middle Bowl: −1.65 RP/24b</b> (Econ <b>9.94 RPO</b>, wicket rate just <b>3.17 wkts/100b</b> across 221 legal balls).", st_td_l),
            Paragraph("Post-2024 exit of Ashwin (#3) & Chahal left a void; <b>#8 Maheesh Theekshana</b> posted −4.85 RP/24b for RR in 2025 & Hasaranga +0.22.", st_td_l),
            Paragraph("<b>#2 Axar Patel</b> (Core SLA AR), <b>#7 Ravi Bishnoi</b> (Domestic Leg-Spin), <b>#8 Rashid Khan</b> (Marquee Spin).", st_td_l),
        ],
        [
            Paragraph("<b>Req D · Powerplay & Death Pace Execution</b>", st_td_b),
            Paragraph("<b>IPL 2025 Pace Drop: PP −2.18 RP/24b</b> (Econ 10.32) and <b>Death −1.97 RP/24b</b> (Econ <b>13.01 RPO</b>).", st_td_l),
            Paragraph("Sandeep Sharma (+5.64 RP/24b) and Madhwal (+3.13) held firm, but Farooqi (<b>−20.40</b>), Deshpande (<b>−5.97</b>) & Archer (<b>−0.74</b>) leaked runs.", st_td_l),
            Paragraph("<b>#5 Mustafizur Rahman</b> (Core Left-Arm/Death), <b>#10 Nathan Ellis</b> / <b>Richard Ngarava</b> (Death/PP Pace).", st_td_l),
        ],
    ]
    t_rr_req = Table(rr_req_rows, colWidths=[34 * mm, 50 * mm, 54 * mm, 48 * mm], repeatRows=1)
    t_rr_req.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), C_AMBER_DARK),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_AMBER_BG, C_WHITE]),
                ("BOX", (0, 0), (-1, -1), 0.5, C_AMBER),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, C_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 2.2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
                ("LEFTPADDING", (0, 0), (-1, -1), 3.0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3.0),
            ]
        )
    )
    story.append(t_rr_req)

    # ==================== PAGE 3 ====================
    story.append(PageBreak())

    story.append(Paragraph("6. TOP 10 — DATA-BACKED AUCTION RECOMMENDATIONS FOR RAJASTHAN ROYALS (IPL 2027)", st_h1))
    story.append(
        Paragraph(
            "<b>Label:</b> <i>Performance-led auction targets, subject to final squad composition, availability and auction budget.</i> "
            "<b>Why This Shortlist Differs From the Raw Pressure Leaderboard:</b> A credible auction recommendation must filter out players who cannot solve an external RR need: "
            "(1) <b>Incumbent RR 2025 Core (Retain, Do Not Re-Buy):</b> <b>#1 Yashasvi Jaiswal</b>, <b>#9 Riyan Parag</b>, and <b>#8 Maheesh Theekshana</b>; "
            "(2) <b>Single-Franchise Untouchable Icons (Valuation Benchmarks Only):</b> <b>#1 Jasprit Bumrah</b> (RPR +1.13), <b>#2 Sunil Narine</b> (+0.82), and <b>#3 Suryakumar Yadav</b> (+11.55) serve as ceiling benchmarks rather than realistic open-auction targets; "
            "(3) <b>Role-Redundant Openers:</b> <b>#4 Abhishek Sharma</b>, <b>#8 Nissanka</b>, <b>#12 Sudharsan</b>, and <b>#10 Josh Inglis</b> (99% PP/Mid sample) duplicate RR's strongest phase; and "
            "(4) <b>Ineligible / Retired Pool:</b> <b>#10 Haris Rauf</b> (Pakistan T20I, ineligible for IPL) and retired IPL veterans <b>#3 R. Ashwin</b> & <b>#7 Tim Southee</b>.",
            st_body,
        )
    )

    rec_hdr = [
        Paragraph("#", st_th),
        Paragraph("Recommended Player & Role", st_th_l),
        Paragraph("Verified PressureIQ Evidence", st_th_l),
        Paragraph("Why This Player (Data Advantage)", st_th_l),
        Paragraph("RR Squad Requirement & Tactical Fit", st_th_l),
        Paragraph("Priority", st_th),
        Paragraph("Key Caveat / Trade-Off", st_th_l),
    ]
    rec_rows = [rec_hdr]
    for r in RR_AUCTION_TOP10:
        rec_rows.append(
            [
                Paragraph(f"<b>{r[0]}</b>", st_td_b),
                Paragraph(f"<b>{r[1].splitlines()[0]}</b><br/><font size='5.7' color='#475569'>{r[1].splitlines()[1]}</font>", st_td_l),
                Paragraph(r[2].replace("\n", "<br/>"), st_td_l),
                Paragraph(r[3], st_td_l),
                Paragraph(r[4], st_td_l),
                Paragraph(f"<b>{r[5].splitlines()[0]}</b><br/><font size='5.6' color='#0F766E'>{r[5].splitlines()[1]}</font>", st_td),
                Paragraph(r[6], st_td_l),
            ]
        )
    t_rec = Table(rec_rows, colWidths=[6 * mm, 29 * mm, 33 * mm, 37 * mm, 39 * mm, 17 * mm, 25 * mm], repeatRows=1)
    t_rec.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), C_NAVY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_LIGHT_BG]),
                ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, C_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 2.0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.0),
                ("LEFTPADDING", (0, 0), (-1, -1), 2.2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2.2),
            ]
        )
    )
    story.append(t_rec)
    story.append(Spacer(1, 2.4))

    # Two-column block: Section 7 (Decision Value) + Section 8 (Dashboard Verification)
    dec_html = (
        "<font name='Helvetica-Bold' size='7.8' color='#14243A'>7. DECISION VALUE — WHAT PRESSUREIQ ENABLES</font><br/>"
        "<font name='Helvetica' size='6.6' color='#334155'>"
        "PressureIQ makes complex recruitment decisions transparent and defensible by connecting: "
        "(1) <b>pre-delivery match-state context</b>, (2) <b>pressure-specific performance</b>, (3) <b>context-adjusted contribution (CABV & RP)</b>, (4) <b>match-to-match repeatability (Success % & IQR)</b>, (5) <b>sample strength & EB uncertainty bounds (APR & RPR)</b>, and (6) <b>phase-specific RR role alignment (Reqs A–D)</b>. Historical pressure reliability reduces valuation error but does not predict or guarantee future IPL 2027 outcomes.<br/>"
        "<font color='#0F766E'><b>Closing Insight:</b> <i>The best auction decision is not necessarily selecting the player with the strongest overall statistics. It is identifying the player whose demonstrated performance, reliability and role best address the team's needs.</i></font>"
        "</font>"
    )
    dash_html = (
        "<font name='Helvetica-Bold' size='7.8' color='#0F766E'>8. EXPLORE AND CROSS-CHECK THE ANALYSIS</font><br/>"
        f"<font name='Helvetica-Bold' size='7.0' color='#14243A'>Interactive PressureIQ Dashboard: <a href='{DASHBOARD_URL}' color='#0D9488'><u>{DASHBOARD_URL}</u></a></font><br/>"
        "<font name='Helvetica' size='6.6' color='#334155'>"
        "The interactive dashboard allows readers to explore player rankings, pressure conditions, performance metrics, reliability evidence and methodology. The figures and recommendations in this brief can be cross-checked against the corresponding dashboard views."
        "</font>"
    )
    mid_tbl = Table(
        [[Paragraph(dec_html, ParagraphStyle("D1", leading=8.2)), Paragraph(dash_html, ParagraphStyle("D2", leading=8.2))]],
        colWidths=[114 * mm, 72 * mm],
    )
    mid_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), C_LIGHT_BG),
                ("BACKGROUND", (1, 0), (1, 0), C_TEAL_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, C_TEAL),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3.0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.0),
                ("LEFTPADDING", (0, 0), (-1, -1), 4.5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4.5),
            ]
        )
    )
    story.append(mid_tbl)
    story.append(Spacer(1, 2.4))

    # Mandatory Footer: METRIC & FORMULA GUIDE (Two-Column Reference Strip)
    left_items = "<br/>".join([f"<b>{k}</b> {v}" for k, v in METRIC_GUIDE_LEFT])
    right_items = "<br/>".join([f"<b>{k}</b> {v}" for k, v in METRIC_GUIDE_RIGHT])
    fg_hdr = [
        Paragraph("<b>METRIC & FORMULA GUIDE — PLAIN-ENGLISH DEFINITIONS, EXACT IMPLEMENTED FORMULAS & CRICKET ABBREVIATIONS</b>", ParagraphStyle("FGH", fontName="Helvetica-Bold", fontSize=6.5, leading=7.8, textColor=C_WHITE)),
        Paragraph("", st_th),
    ]
    fg_tbl = Table(
        [
            fg_hdr,
            [Paragraph(left_items, st_foot), Paragraph(right_items, st_foot)],
        ],
        colWidths=[93 * mm, 93 * mm],
    )
    fg_tbl.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (1, 0)),
                ("BACKGROUND", (0, 0), (-1, 0), C_NAVY_SOFT),
                ("BACKGROUND", (0, 1), (-1, 1), C_LIGHT_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
                ("INNERGRID", (0, 1), (-1, 1), 0.4, C_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 2.2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(fg_tbl)

    doc.build(story)


# ---------------------------------------------------------------------------
# DOCX Generation (python-docx — Editable Word Document)
# ---------------------------------------------------------------------------
def _set_cell_bg(cell, hex_color: str) -> None:
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def _add_hyperlink(paragraph, url: str, text: str, color_hex: str = "0D9488") -> None:
    part = paragraph.part
    r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    new_run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    c = OxmlElement("w:color")
    c.set(qn("w:val"), color_hex)
    rPr.append(c)
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rPr.append(u)
    b = OxmlElement("w:b")
    rPr.append(b)
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "18")
    rPr.append(sz)
    new_run.append(rPr)
    t = OxmlElement("w:t")
    t.text = text
    new_run.append(t)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)


def _format_docx_table(table, hdr_bg: str = "14243A", font_pt: float = 7.5) -> None:
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r_idx, row in enumerate(table.rows):
        for cell in row.cells:
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            if r_idx == 0:
                _set_cell_bg(cell, hdr_bg)
            elif r_idx % 2 == 0:
                _set_cell_bg(cell, "F8FAFC")
            for p in cell.paragraphs:
                p.paragraph_format.space_before = Pt(1.5)
                p.paragraph_format.space_after = Pt(1.5)
                for run in p.runs:
                    run.font.name = "Calibri"
                    run.font.size = Pt(font_pt)
                    if r_idx == 0:
                        run.font.bold = True
                        run.font.color.rgb = RGBColor(255, 255, 255)
                    else:
                        run.font.color.rgb = RGBColor(24, 37, 54)


def build_docx() -> None:
    d = docx.Document()
    for sec in d.sections:
        sec.top_margin = Inches(0.42)
        sec.bottom_margin = Inches(0.42)
        sec.left_margin = Inches(0.48)
        sec.right_margin = Inches(0.48)

    normal_style = d.styles["Normal"]
    normal_style.font.name = "Calibri"
    normal_style.font.size = Pt(8.8)
    normal_style.font.color.rgb = RGBColor(51, 65, 85)

    # Title Banner
    t_banner = d.add_table(rows=1, cols=1)
    cell = t_banner.cell(0, 0)
    _set_cell_bg(cell, "14243A")
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    r1 = p.add_run("PRESSUREIQ — Beyond Player Statistics\n")
    r1.bold = True
    r1.font.size = Pt(14.5)
    r1.font.color.rgb = RGBColor(255, 255, 255)
    r2 = p.add_run("Identifying Reliable Performers Under Pressure and Evaluating Their Value for Rajasthan Royals' IPL 2027 Auction\n")
    r2.italic = True
    r2.font.size = Pt(9.2)
    r2.font.color.rgb = RGBColor(204, 251, 241)
    r3 = p.add_run("Data → Methodology → Plain-English Metrics → Model Trade-Offs → RR Squad Gaps → Top 10 Auction Targets  |  VALIDATED (23/23)")
    r3.bold = True
    r3.font.size = Pt(7.8)
    r3.font.color.rgb = RGBColor(253, 230, 138)

    def add_sec_hdr(txt: str):
        p_h = d.add_paragraph()
        p_h.paragraph_format.space_before = Pt(5)
        p_h.paragraph_format.space_after = Pt(2)
        run = p_h.add_run(txt)
        run.bold = True
        run.font.size = Pt(10.0)
        run.font.color.rgb = RGBColor(20, 36, 58)

    # Section 1
    add_sec_hdr("1. THE DECISION PROBLEM & PLAIN-ENGLISH METRIC DECODER")
    p1 = d.add_paragraph(
        "Conventional career averages, strike rates (SR) and economy rates pool low-leverage blowouts with crunch moments, obscuring the central recruitment question: "
        "Who can be trusted to deliver when match conditions become difficult, and how should Rajasthan Royals use that evidence when building its squad? "
        "In first-innings cricket, raw current run rate correlates negatively with pressure (r = −0.73), proving that boundary sprees from 160/1 (PI = 15.6) are low-difficulty states while rebuilding from 45/4 in Over 7 (PI = 59.5) is genuine pressure. "
        "Plain-English Decoder: (1) CABV (/100b) & RP (/24b) measure how many runs a batter added or bowler saved relative to an average peer in the exact same match context; "
        "(2) APR (Adjusted Pressure Rating) is our best point estimate of true pressure skill after Empirical Bayes (EB) shrinks small-sample luck toward the cohort average; "
        "(3) RPR (Reliable Pressure Rating) is the safe minimum floor we can bank on with 90% confidence (APR − 1.2816*SD), used as the official ranking metric; and "
        "(4) PRD (Pressure Response Delta) measures whether a player rises (>0) or drops (<0) under pressure relative to their own normal-state baseline."
    )
    p1.paragraph_format.space_after = Pt(2)

    # Section 2
    add_sec_hdr("2. METHODOLOGY — HOW PRESSUREIQ EVALUATES PERFORMANCE")
    meth_bullets = [
        ("1. Data Scope:", "853 official IPL + T20I matches (371 IPL + 482 T20I, 2022–2026; 837 active matches; 194,014 official balls; 193,842 pressure-eligible regulation balls). Excludes 30 Other-T20 matches and 38 Super Over balls from regulation rankings."),
        ("2. Law 18/22 Cricket Accounting:", "Separates batter_runs, team_runs (100% margin reconciliation on unrevised matches), and bowler_conceded (36 extras_2_runs rows verified as no-ball byes/leg-byes not charged to bowler). Legal balls exclude wides and no-balls (including 264 row-verified 'other' beamer/height no-balls). Only Caught, Bowled, LBW, Stump & Hit Wicket credit bowler_wicket (excluding 600 RunOuts, 6 Retire Outs, 3 Obstructing Field). Keyed by player_id (Basil Hameed IDs 8638 & 39444 unmerged)."),
        ("3 & 4. Pre-Delivery PI & Separate Innings Models:", "Zero outcome leakage. 1st Innings uses format-scaled Duckworth-Lewis curves E(u,w) (MAE 16.47 runs vs 25.10 naive RR, R²=0.825) for Par Deviation and Wicket Value (WV). 2nd Innings evaluates log(runs_needed/E(u,w)), RRR, wickets & balls left (WP Brier 0.145). Next-ball leverage L gates win probability: PI_bat = 100*(1−WP_bat)*min(1, L/med(L|inn)); Elevated >= 52.0 (top 35%), High >= 66.1 (top 12%)."),
        ("5–9. Context Baselines, CABV/RP, EB Shrinkage & RPR:", "5-fold hierarchical EB baselines (format × innings × phase × wickets × pressure tier, k=100) establish context expectations. 250 match-cluster bootstrap resamples + ball-weighted EB shrink raw rates across 177 eligible batters (≥10m, ≥100b) and 162 eligible bowlers (≥10m, ≥120 legal b) to produce APR, PRD, and official ranking estimand RPR (median Spearman ρ = 0.90 Bat / 0.89 Bowl across 13 sensitivity specs)."),
    ]
    for title_b, body_b in meth_bullets:
        pb = d.add_paragraph()
        pb.paragraph_format.space_before = Pt(0.5)
        pb.paragraph_format.space_after = Pt(1.2)
        rb1 = pb.add_run(f"• {title_b} ")
        rb1.bold = True
        rb1.font.size = Pt(8.1)
        rb2 = pb.add_run(body_b)
        rb2.font.size = Pt(8.1)

    # Section 3: Trade-offs
    add_sec_hdr("3. MODEL TRADE-OFFS, DESIGN CHOICES & KNOWN LIMITATIONS")
    p_tr = d.add_paragraph(
        "1. Conservatism vs Breakout Talent (RPR Lower Bound): RPR penalises smaller match counts (e.g., #6 Rajat Patidar has APR +17.95 vs #5 Klaasen +16.98, but ranks one spot lower on RPR because 23 matches carry wider uncertainty than 38; young RR opener Vaibhav Sooryavanshi has APR +13.52 across 160b but RPR +1.87 at #19). Pair APR with RPR when scouting emerging players.\n"
        "2. Differential Shrinkage in PRD: Normal states have ~2× more deliveries (65% vs 35%) and 2.2× higher between-player variance, retaining more signal (median B_norm = 0.56 vs B_press = 0.26). Historic normal-state outliers (#1 Bumrah +5.00 shrunk normal vs +2.65 pressure; #3 Suryakumar +26.68 normal vs +19.11 pressure) show negative PRD (−2.35 and −7.57) due to their extraordinary normal baseline and stronger pressure shrinkage—not weak pressure play.\n"
        "3. Macro-Context vs Micro-Pitch Tracking & Fixed Wicket Weights: Baselines use format-level par rather than single-venue pitch/dew tracking to prevent small-venue overfitting, and use marginal wicket weights (0.30*WV bat / 0.20*WV bowl) so single-ball dismissal luck does not swamp run-saving skill."
    )
    p_tr.paragraph_format.space_after = Pt(2)

    d.add_page_break()

    # Page 2: Top 10 Batters, Top 10 Bowlers & RR Squad Requirement Matrix
    add_sec_hdr("4. VALIDATED TOP-10 PERFORMERS UNDER PRESSURE (COMBINED IPL + T20I, 2022–2026)")
    tb = d.add_table(rows=1, cols=11)
    b_headers = ["Rk", "Batter", "Role & Teams", "RPR", "APR", "PRD", "90% CI", "Succ%", "Balls(M)", "p_SR/Exp", "Out/100b"]
    for i, h_txt in enumerate(b_headers):
        tb.rows[0].cells[i].text = h_txt
    for row in TOP10_BATTERS:
        cells = tb.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = val
    _format_docx_table(tb, font_pt=7.0)

    p_sp = d.add_paragraph()
    p_sp.paragraph_format.space_after = Pt(1.5)

    tw = d.add_table(rows=1, cols=11)
    w_headers = ["Rk", "Bowler", "Style & Teams", "RPR", "APR", "PRD", "90% CI", "Succ%", "Legal(M)", "p_Econ/Exp", "Wkt/100b"]
    for i, h_txt in enumerate(w_headers):
        tw.rows[0].cells[i].text = h_txt
    for row in TOP10_BOWLERS:
        cells = tw.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = val
    _format_docx_table(tw, font_pt=7.0)

    add_sec_hdr("5. WHAT MAKES PLAYERS RELIABLE & RAJASTHAN ROYALS' 4 VERIFIED SQUAD REQUIREMENTS")
    p_rr = d.add_paragraph(
        "RR's IPL 2025 roster is already elite in Powerplay Batting (+34.50 CABV/100b in 2025, led by #1 Yashasvi Jaiswal +46.99/100b and #9 Riyan Parag +90.85/100b), "
        "but exhibits four quantified pressure deficits that directly govern our IPL 2027 auction shortlist:\n"
        "• Req A — Death-Over Finishing (No. 5–7): IPL 2025 Death batting fell to −9.53 CABV/100b (SR 146.6, Out rate 8.27/100b; Hetmyer −18.47, Rana −18.14, Dubey −35.45) → Mapped to #1 Tim David, #6 Andre Russell, #9 Rovman Powell.\n"
        "• Req B — Middle-Over Spin Hitting (No. 4–5): IPL 2022–2025 Middle batting averaged −9.16 CABV/100b (SR 123.6 across 1,135 pressure balls) → Mapped to #3 Heinrich Klaasen, #4 Rajat Patidar, #2 Axar Patel.\n"
        "• Req C — Middle-Over Spin Control & Wickets: IPL 2025 Middle bowling dropped to −1.65 RP/24b (Econ 9.94, Wkt rate 3.17/100b post-Ashwin/Chahal; Theekshana −4.85 in 2025) → Mapped to #2 Axar Patel, #7 Ravi Bishnoi, #8 Rashid Khan.\n"
        "• Req D — Powerplay & Death Pace Execution: IPL 2025 Powerplay (−2.18 RP/24b, Econ 10.32) and Death (−1.97 RP/24b, Econ 13.01; Farooqi −20.40, Deshpande −5.97, Archer −0.74) → Mapped to #5 Mustafizur Rahman, #10 Nathan Ellis (paired with Richard Ngarava)."
    )
    p_rr.paragraph_format.space_after = Pt(2)

    d.add_page_break()

    # Page 3: Top 10 RR Auction Recommendations
    add_sec_hdr("6. TOP 10 — DATA-BACKED AUCTION RECOMMENDATIONS FOR RAJASTHAN ROYALS (IPL 2027)")
    p_rec_intro = d.add_paragraph(
        "Label: Performance-led auction targets, subject to final squad composition, availability and auction budget. "
        "Excludes incumbent RR 2025 core (#1 Jaiswal, #9 Parag, #8 Theekshana), lifelong single-franchise untouchables (#1 Bumrah, #2 Narine, #3 Suryakumar — used as valuation benchmarks), "
        "redundant openers (#4 Abhishek, #8 Nissanka, #12 Sudharsan, #10 Inglis), IPL-ineligible Pakistan T20I players (#10 Haris Rauf), and retired IPL veterans (#3 Ashwin, #7 Southee)."
    )
    p_rec_intro.paragraph_format.space_after = Pt(2)

    t_rec = d.add_table(rows=1, cols=7)
    r_headers = ["#", "Player & Specialist Role", "PressureIQ Evidence", "Why This Player", "RR Requirement & Fit", "Priority", "Caveat / Trade-Off"]
    for i, h_txt in enumerate(r_headers):
        t_rec.rows[0].cells[i].text = h_txt
    for row in RR_AUCTION_TOP10:
        cells = t_rec.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = val.replace("\n", " ")
    _format_docx_table(t_rec, font_pt=6.8)

    add_sec_hdr("7. DECISION VALUE & 8. EXPLORE AND CROSS-CHECK THE ANALYSIS")
    p_dv = d.add_paragraph(
        "PressureIQ moves franchise recruitment beyond raw averages by integrating pre-delivery match context, context-adjusted contribution (CABV/RP), match-to-match repeatability, Empirical-Bayes uncertainty bounds, and tactical squad-role evaluation. "
        "Closing Insight: The best auction decision is not necessarily selecting the player with the strongest overall statistics. It is identifying the player whose demonstrated performance, reliability and role best address the team's needs."
    )
    p_dv.paragraph_format.space_after = Pt(2)

    p_link = d.add_paragraph("EXPLORE AND CROSS-CHECK THE ANALYSIS — Interactive PressureIQ Dashboard: ")
    _add_hyperlink(p_link, DASHBOARD_URL, DASHBOARD_URL)
    p_link.add_run(
        "\nThe interactive dashboard allows readers to explore player rankings, pressure conditions, performance metrics, reliability evidence and methodology. The figures and recommendations in this brief can be cross-checked against the corresponding dashboard views."
    )

    add_sec_hdr("METRIC & FORMULA GUIDE (PLAIN-ENGLISH & FORMULA QUICK REFERENCE)")
    t_fg = d.add_table(rows=1, cols=2)
    t_fg.rows[0].cells[0].text = "PressureIQ Custom Metrics & Models"
    t_fg.rows[0].cells[1].text = "Reliability Estimands & Standard Cricket Terms"
    row_fg = t_fg.add_row().cells
    row_fg[0].text = "\n".join([f"{k} {v}" for k, v in METRIC_GUIDE_LEFT])
    row_fg[1].text = "\n".join([f"{k} {v}" for k, v in METRIC_GUIDE_RIGHT])
    _format_docx_table(t_fg, hdr_bg="1E3A5F", font_pt=6.8)

    d.save(str(DOCX_PATH))


if __name__ == "__main__":
    build_pdf()
    build_docx()
    print(f"Generated PDF:  {PDF_PATH} ({PDF_PATH.stat().st_size:,} bytes)")
    print(f"Generated DOCX: {DOCX_PATH} ({DOCX_PATH.stat().st_size:,} bytes)")
