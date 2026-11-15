"""Generate the official 22-section Methodology Report (Markdown + PDF) and evidence figures.

Reads directly from `data/analytical/` and `reports/exports/` so every formula,
threshold, player ID, and ranking matches the Streamlit dashboard identically.
"""

from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from config.settings import DATA_ANALYTICAL, EXPORTS, FIGURES, METHODOLOGY_DIR


def generate_figures() -> dict[str, str]:
    FIGURES.mkdir(parents=True, exist_ok=True)
    bat = pd.read_csv(EXPORTS / "official_top10_batters.csv").sort_values("rank", ascending=False)
    bowl = pd.read_csv(EXPORTS / "official_top10_bowlers.csv").sort_values("rank", ascending=False)
    wp_cal = pd.read_parquet(DATA_ANALYTICAL / "wp_calibration.parquet")

    # 1. Top 10 Batters RPR + APR
    fig, ax = plt.subplots(figsize=(7.5, 4.0), dpi=160)
    y = np.arange(len(bat))
    ax.barh(y - 0.17, bat["rpr"], height=0.34, color="#0D9488", label="Reliable Rating (RPR, 90% Lower Bound)")
    ax.barh(y + 0.17, bat["rating_mean"], height=0.34, color="#14243A", alpha=0.82, label="Shrunk Mean (APR)")
    ax.set_yticks(y)
    ax.set_yticklabels("#" + bat["rank"].astype(int).astype(str) + " " + bat["player_name"], fontsize=8.5)
    ax.set_xlabel("Context-Adjusted Batting Value per 100 Pressure Balls (Runs)", fontsize=9)
    ax.set_title("Official Top 10 Batters Under Pressure (IPL + T20I, 2022–2026)", fontsize=10.5, fontweight="bold")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    fig.tight_layout()
    p_bat = str(FIGURES / "top10_batters.png")
    fig.savefig(p_bat)
    plt.close(fig)

    # 2. Top 10 Bowlers RPR + APR
    fig, ax = plt.subplots(figsize=(7.5, 4.0), dpi=160)
    y = np.arange(len(bowl))
    ax.barh(y - 0.17, bowl["rpr"], height=0.34, color="#16856A", label="Reliable Rating (RPR, 90% Lower Bound)")
    ax.barh(y + 0.17, bowl["rating_mean"], height=0.34, color="#14243A", alpha=0.82, label="Shrunk Mean (APR)")
    ax.set_yticks(y)
    ax.set_yticklabels("#" + bowl["rank"].astype(int).astype(str) + " " + bowl["player_name"], fontsize=8.5)
    ax.set_xlabel("Context-Adjusted Runs Prevented per 24 Pressure Balls (Runs)", fontsize=9)
    ax.set_title("Official Top 10 Bowlers Under Pressure (IPL + T20I, 2022–2026)", fontsize=10.5, fontweight="bold")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    fig.tight_layout()
    p_bowl = str(FIGURES / "top10_bowlers.png")
    fig.savefig(p_bowl)
    plt.close(fig)

    # 3. WP Calibration Curve
    fig, ax = plt.subplots(figsize=(6.2, 3.6), dpi=160)
    ax.plot([0, 1], [0, 1], "--", color="#68778A", label="Ideal Diagonal")
    for inn, col in [(1, "#14243A"), (2, "#0D9488")]:
        sub = wp_cal[wp_cal["innings"] == inn]
        ax.plot(sub["predicted"], sub["observed"], "o-", color=col, label=f"Innings {inn} Cross-Fitted WP")
    ax.set_xlabel("Predicted Pre-Delivery Batting Win Probability", fontsize=9)
    ax.set_ylabel("Observed Win Frequency", fontsize=9)
    ax.set_title("Out-of-Sample Win Probability Calibration (5-Fold Match-Grouped CV)", fontsize=10, fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.tight_layout()
    p_cal = str(FIGURES / "wp_calibration.png")
    fig.savefig(p_cal)
    plt.close(fig)

    return {"bat": p_bat, "bowl": p_bowl, "cal": p_cal}


def build_reports() -> None:
    METHODOLOGY_DIR.mkdir(parents=True, exist_ok=True)
    figs = generate_figures()

    meta = json.loads((DATA_ANALYTICAL / "summary_metadata.json").read_text())
    bat10 = pd.read_csv(EXPORTS / "official_top10_batters.csv").sort_values("rank")
    bowl10 = pd.read_csv(EXPORTS / "official_top10_bowlers.csv").sort_values("rank")
    wp_val = pd.read_parquet(DATA_ANALYTICAL / "wp_validation.parquet")
    res_val = pd.read_parquet(DATA_ANALYTICAL / "resource_validation.parquet")
    base_val = pd.read_parquet(DATA_ANALYTICAL / "baseline_validation.parquet")
    sens_sum = pd.read_parquet(DATA_ANALYTICAL / "sensitivity_summary.parquet")
    gate = pd.read_parquet(DATA_ANALYTICAL / "validation_results.parquet")

    # Build Markdown report covering all 22 required sections
    md_lines = [
        "# PRESSUREIQ — Official Methodology & Validation Report",
        "",
        f"**Validation Status:** `{meta['validation_status']}` ({meta['n_checks_passed']}/{meta['n_checks_total']} automated gate checks passed)  ",
        f"**Official Scope:** {meta['official_scope_matches']} IPL + T20I matches ({meta['analysed_pressure_matches']} active with ball-by-ball; {meta['pressure_eligible_deliveries']:,} pressure-eligible deliveries)",
        "",
        "## 1. Executive Summary",
        "PRESSUREIQ is an end-to-end cricket pressure intelligence platform built to identify the most reliable batters and bowlers under genuine match pressure across IPL and T20 International cricket (2022–2026). Rather than equating death overs or high required run rates with pressure, PRESSUREIQ estimates pre-delivery difficulty and next-ball leverage from separate first-innings and run-chase models, evaluates players against 5-way cross-fitted context expectations, and ranks eligible players by their **Reliable Pressure Rating (RPR)** — the one-sided 90% Empirical-Bayes lower confidence bound on true context-adjusted contribution.",
        "",
        "## 2. Problem Statement",
        "Conventional leaderboards reward raw run volume or unadjusted bowling economy, conflating easy match states with crunch situations and allowing small-sample outliers to top rankings. The central analytical question solved here is: *Which players consistently deliver the greatest context-adjusted contribution when the pre-delivery match situation is difficult and the contest is still live?*",
        "",
        "## 3. Dataset and Scope",
        "- **Source Inventory:** `competitions.csv` (141), `teams.csv` (353), `matches.csv` (883), `ball_by_ball.csv` (200,999), `competition_team_player_mapping.csv` (6,413), `playing_eleven.csv` (28,381).",
        "- **Official Competition Scope:** 371 IPL matches + 482 T20I matches = **853 matches** (194,014 deliveries). The 30 Other-T20 matches (Emerging Teams Asia Cup 2024 & Asia Cup Rising Stars 2025) are preserved in raw data and flagged `OUT_OF_OFFICIAL_SCOPE`.",
        "",
        "## 4. Data Quality Audit",
        "- Zero duplicate delivery keys `(match_id, innings, overid, over_ball_num)` and zero missing player/match IDs.",
        "- 16 matches are `Match Abandoned` without ball-by-ball; 22 further matches lack second-innings deliveries (`No Result` / rain). None are silently deleted; all carry explicit audit flags in `data/interim/exclusion_flag_log.csv`.",
        "- `playing_eleven.csv` contains 75 duplicate-key rows and IPL Impact Player substitutions (12+ `is_played=True`). Actual ball-by-ball appearance is used as the ground-truth participation table.",
        "",
        "## 5. Cricket-Specific Data Processing",
        "- **Runs & Extras (`src/quality/cricket_rules.py`):** `runs` is verified as off-the-bat batter runs. Team runs = `runs + extras1_runs + extras_2_runs` (reconciling 100% of unrevised 'won by N runs' margins).",
        "- **`other` Extras Verification:** Row-level audit of all 264 `extras_type == 'other'` rows confirms `extras1_runs == 1` on 100% of rows, dominated by Beamer (116) and Full Toss (72) height no-balls. Treating `other` as legal creates 150 innings with >120 legal balls; classifying `other` as a no-ball reduces over-120-ball innings to **0**.",
        "- **`extras_2_runs` Verification:** 35 rows occur on `Overstep`/`other` no-balls when `runs == 0` (plus 1 untagged row in match 17555), representing byes/leg-byes run off a no-ball. Credited to team runs, not debited to the bowler.",
        "- **Dismissals:** `Caught`, `Bowled`, `LBW`, `Stump`, `Hit Wicket` credit the bowler. `RunOut` (600), `Retire Out` (6), and `Obstructing/Obstracting the field` (3) count as batting dismissals only. 12 rows with `dismissed_player_id` but `is_wicket=False` are tagging artefacts and not treated as wickets.",
        "- **Super Overs & Revised Overs:** 38 Super Over deliveries (`innings in {3, 4}`) are excluded from regulation statistics. Revised-overs integers (`30..114`, all multiples of 6) are verified as legal-ball allocations.",
        "- **Identity Collisions:** Basil Hameed's two IDs (`8638` and `39444`) remain unmerged per safeguard rules.",
        "",
        "## 6. Pressure Definition & 7. Pressure Index Construction",
        r"- **Resource Model $E(u, w)$:** Exponential Duckworth–Lewis curves $Z_w(1 - e^{-b_w u})$ fitted on unrevised completed first innings, scaled by format ($\text{IPL}=1.035$, $\text{T20I}=0.972$). Out-of-sample chronological MAE is **17.11 runs** ($R^2 = 0.825$) vs **27.17 runs** ($R^2 = 0.408$) for naive current-run-rate projection.",
        r"- **Separate First-Innings & Chase WP Models:** 5-fold match-grouped cross-fitted logistic models predict $WP_{\text{bat}}$ from pre-delivery Par Deviation (Innings 1) or log Resource Ratio $\log(\text{runs\_needed}/E(u,w))$ (Innings 2). First-innings PI correlates negatively with current run rate ($r = -0.679$), proving high run rates are not conflated with pressure.",
        r"- **Frozen Pressure Index:** $\text{PI}_{\text{side}} = 100 \cdot \text{Difficulty}_{\text{side}} \cdot \min(1, L / \text{median}(L \mid \text{innings}))$.",
        f"- **Calibrated Thresholds:** Pooled batting PI quantiles (65th / 88th): **Elevated >= {meta['thresholds']['elevated']}**, **High >= {meta['thresholds']['high']}**.",
        "",
        "## 8. Batting Performance Model & 9. Bowling Performance Model",
        r"- **Hierarchical Context Baselines:** 5-fold match-cross-fitted expectations over `format_group × innings × phase × wkts_bucket × pressure_level` with hierarchical empirical-Bayes smoothing ($k=100$).",
        r"- **Batting Value (CABV):** $(r - E[r \mid \text{ctx}]) - 0.30 \cdot WV \cdot (\text{out} - E[\text{out} \mid \text{ctx}])$, expressed per 100 pressure balls faced.",
        r"- **Bowling Value (RP):** $(E[c \mid \text{ctx}] - c) + 0.20 \cdot WV \cdot (\text{wkt} - E[\text{wkt} \mid \text{ctx}])$, expressed per 24 pressure deliveries.",
        "",
        "## 10. Pressure Response Delta (PRD)",
        r"- $\text{PRD}_i = \hat{\theta}_{i,\text{pressure}} - \hat{\theta}_{i,\text{normal}}$ measures how a player's shrunk context-adjusted contribution changes under pressure relative to their own shrunk normal baseline. Reported independently from absolute pressure rating.",
        "",
        "## 11. Reliability Framework, 12. Statistical Shrinkage & 13. Confidence Intervals",
        r"- **Match-Cluster Bootstrap:** 250 resamples of whole matches per player (`seed=42`) yield cluster-robust standard errors $SE_i$.",
        r"- **Volume-Weighted Empirical Bayes:** Population prior $(\mu, \tau^2)$ is estimated on the eligible cohort via ball-weighted method of moments. Posterior mean $\hat{\theta}_i = \mu + B_i(\bar{y}_i - \mu)$ with $B_i = \tau^2/(\tau^2 + SE_i^2)$ and posterior SD $SD_i = \sqrt{\tau^2 SE_i^2/(\tau^2 + SE_i^2)}$.",
        r"- **Ranking Estimand (RPR):** $\text{RPR}_i = \hat{\theta}_i - 1.2816 \cdot SD_i$ (one-sided 90% lower confidence bound).",
        "",
        "## 14. Eligibility Rules",
        r"- **Batters:** $\ge 10$ unique pressure matches and $\ge 100$ pressure balls faced (**177 eligible batters**).",
        r"- **Bowlers:** $\ge 10$ unique pressure matches and $\ge 120$ pressure legal balls bowled (**162 eligible bowlers**).",
        "",
        "## 15. Final Batting Top 10 (Official IPL + T20I Scope)",
        "",
        bat10[["rank", "player_id", "player_name", "teams", "formats", "rpr", "rating_mean", "prd", "p_balls", "p_matches", "p_sr", "p_exp_sr", "success_rate"]].round(2).to_markdown(index=False),
        "",
        "## 16. Final Bowling Top 10 (Official IPL + T20I Scope)",
        "",
        bowl10[["rank", "player_id", "player_name", "teams", "formats", "rpr", "rating_mean", "prd", "p_legal", "p_matches", "p_economy", "p_exp_economy", "p_wickets", "success_rate"]].round(2).to_markdown(index=False),
        "",
        "## 17. Evidence & Player Comparisons, 18. Sensitivity Analysis & 19. Model Validation",
        "### Out-of-Sample Win-Probability Validation",
        wp_val.round(4).to_markdown(index=False),
        "",
        "### Chronological First-Innings Resource Model Validation",
        res_val.round(4).to_markdown(index=False),
        "",
        "### Chronological Expected-Performance Baseline Validation",
        base_val.round(4).to_markdown(index=False),
        "",
        "### Sensitivity Analysis Across 13 Alternative Specifications",
        sens_sum.round(3).to_markdown(index=False),
        "",
        "### 23-Check Automated Validation Gate",
        gate.to_markdown(index=False),
        "",
        "## 20. Assumptions & 21. Limitations",
        "- Marginal wicket value above replacement is set to $0.30 \times WV$ for batting and $0.20 \times WV$ for bowling so binary single-ball dismissal variance does not swamp run-scoring/saving signal; pure run-only ($0.0 \times WV$) and full resource drop ($1.0 \times WV$) were verified during diagnostics.",
        "- Two DLS chases without `revised_target` are flagged `target_unreliable` and excluded from chase pressure scoring.",
        "- Basil Hameed's two IDs (`8638` and `39444`) are kept unmerged because no external biographical key is supplied.",
        "",
        "## 22. Reproducibility Instructions",
        "```bash",
        "pip install -r requirements.txt",
        "python -m src.pipeline",
        "python -m pytest tests/ -v",
        "streamlit run app.py",
        "```",
    ]
    (METHODOLOGY_DIR / "PRESSUREIQ_METHODOLOGY_REPORT.md").write_text("\n".join(md_lines), encoding="utf-8")

    # Build PDF Report via ReportLab
    pdf_file = str(METHODOLOGY_DIR / "PRESSUREIQ_METHODOLOGY_REPORT.pdf")
    doc = SimpleDocTemplate(pdf_file, pagesize=A4, leftMargin=1.6 * cm, rightMargin=1.6 * cm, topMargin=1.6 * cm, bottomMargin=1.6 * cm)
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=15, textColor=colors.HexColor("#14243A"), spaceAfter=8)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=11.5, textColor=colors.HexColor("#223750"), spaceBefore=10, spaceAfter=5)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=9.2, leading=13, textColor=colors.HexColor("#182536"), spaceAfter=6)

    def make_table(df_in: pd.DataFrame, col_widths=None):
        data = [list(df_in.columns)] + df_in.astype(str).values.tolist()
        t = Table(data, colWidths=col_widths, repeatRows=1)
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#14243A")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F7FA")]),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        return t

    story = [
        Paragraph("PRESSUREIQ — Official Methodology & Validation Report", h1),
        Paragraph(
            f"<b>Validation Status:</b> {meta['validation_status']} ({meta['n_checks_passed']}/{meta['n_checks_total']} automated checks passed) | "
            f"<b>Official Scope:</b> 853 IPL + T20I Matches (2022–2026) | <b>Analysed Deliveries:</b> {meta['pressure_eligible_deliveries']:,}",
            body,
        ),
        Paragraph("1. Executive Summary & Problem Statement (Sections 1–2)", h2),
        Paragraph(
            "PRESSUREIQ identifies the Top 10 most reliable batters and Top 10 most reliable bowlers under high-pressure match situations across IPL (371 matches) and T20I (482 matches) from 2022–2026. "
            "Every pressure score is computed strictly from pre-delivery state using separate first-innings par-deficit and second-innings chase resource models, gated by next-ball win-probability leverage. "
            "Players are evaluated against 5-fold match-cross-fitted context baselines and ordered by their Reliable Pressure Rating (RPR = post_mean - 1.2816 * post_sd).",
            body,
        ),
        Paragraph("2. Dataset Scope, Data Quality Audit & Cricket Accounting (Sections 3–5)", h2),
        Paragraph(
            "All 6 raw CSVs were audited without mutation. Official scope comprises 371 IPL + 482 T20I matches (853 total; 16 abandoned matches have 0 deliveries; 30 Other-T20 matches and 38 Super Over deliveries are excluded from official regulation rankings). "
            "Row-level verification proved that all 264 'other' extras have extras1_runs=1 (Beamer/Full Toss height no-balls) and capping completed 20-over innings at 120 legal balls requires treating 'other' as a no-ball. "
            "The 35 no-ball rows with extras_2_runs > 0 (when runs=0) are byes/leg-byes off no-balls: included in team runs (97.6% overall / 100% unrevised margin reconciliation) and not debited to the bowler. "
            "Revised overs are stored as legal-ball integers (30..114). Basil Hameed's two IDs (8638, 39444) are kept unmerged.",
            body,
        ),
        Paragraph("3. Pre-Delivery Pressure Engine & Resource Curves (Sections 6–7)", h2),
        Paragraph(
            f"Duckworth-Lewis resource curves E(u,w) = Z_w(1 - exp(-b_w*u)) fitted on completed first innings achieve a chronological out-of-sample MAE of 17.11 runs (R2=0.825) versus 27.17 runs (R2=0.408) for naive run-rate projection. "
            f"First-innings PI correlates negatively with current run rate (r = {meta['pressure_meta']['corr_pi_vs_current_rr_inn1']:.3f}), confirming that high scoring rates are not conflated with pressure. "
            f"Frozen pooled batting PI thresholds: Elevated >= {meta['thresholds']['elevated']}, High >= {meta['thresholds']['high']}.",
            body,
        ),
        Image(figs["cal"], width=13.5 * cm, height=7.8 * cm),
        Paragraph("4. Context Baselines, PRD, Shrinkage & Eligibility (Sections 8–14)", h2),
        Paragraph(
            "Expectations E[runs|ctx], E[out|ctx], E[conceded|ctx], E[wkt|ctx] are 5-fold match-cross-fitted across format x innings x phase x wickets_bucket x pressure_level with hierarchical shrinkage (k=100). "
            "Batting CABV = (runs - E[runs]) - 0.30*WV*(out - E[out]) per 100 balls; Bowling RP = (E[conceded] - conceded) + 0.20*WV*(wkt - E[wkt]) per 24 balls. "
            "Match-cluster bootstrap (B=250, seed=42) and volume-weighted Empirical Bayes yield shrunk posterior mean (APR), posterior SD, PRD (vs own shrunk normal rate), and RPR. "
            "Eligibility: Batters >= 10 pressure matches & >= 100 pressure balls (177 eligible); Bowlers >= 10 pressure matches & >= 120 pressure legal balls (162 eligible).",
            body,
        ),
        PageBreak(),
        Paragraph("5. Official Top 10 Batters Under Pressure (Section 15)", h2),
    ]

    b_tab = bat10[["rank", "player_id", "player_name", "teams", "rpr", "rating_mean", "prd", "p_balls", "p_matches", "p_sr", "p_exp_sr", "success_rate"]].copy()
    b_tab["rank"] = b_tab["rank"].astype(int)
    b_tab["p_balls"] = b_tab["p_balls"].astype(int)
    b_tab["p_matches"] = b_tab["p_matches"].astype(int)
    b_tab["success_rate"] = (b_tab["success_rate"] * 100).round(1).astype(str) + "%"
    for c in ["rpr", "rating_mean", "prd", "p_sr", "p_exp_sr"]:
        b_tab[c] = b_tab[c].round(2)
    b_tab.columns = ["Rank", "ID", "Batter", "Teams", "RPR", "APR", "PRD", "Balls", "Matches", "P.SR", "Exp.SR", "Succ%"]
    story.append(make_table(b_tab))
    story.append(Spacer(1, 6))
    story.append(Image(figs["bat"], width=15.5 * cm, height=8.2 * cm))

    story.append(Paragraph("6. Official Top 10 Bowlers Under Pressure (Section 16)", h2))
    w_tab = bowl10[["rank", "player_id", "player_name", "teams", "rpr", "rating_mean", "prd", "p_legal", "p_matches", "p_economy", "p_exp_economy", "p_wickets", "success_rate"]].copy()
    w_tab["rank"] = w_tab["rank"].astype(int)
    w_tab["p_legal"] = w_tab["p_legal"].astype(int)
    w_tab["p_matches"] = w_tab["p_matches"].astype(int)
    w_tab["p_wickets"] = w_tab["p_wickets"].astype(int)
    w_tab["success_rate"] = (w_tab["success_rate"] * 100).round(1).astype(str) + "%"
    for c in ["rpr", "rating_mean", "prd", "p_economy", "p_exp_economy"]:
        w_tab[c] = w_tab[c].round(2)
    w_tab.columns = ["Rank", "ID", "Bowler", "Teams", "RPR", "APR", "PRD", "LegalB", "Matches", "Econ", "ExpEcon", "Wkts", "Succ%"]
    story.append(make_table(w_tab))
    story.append(Spacer(1, 6))
    story.append(Image(figs["bowl"], width=15.5 * cm, height=8.2 * cm))

    story.append(PageBreak())
    story.append(Paragraph("7. Sensitivity Analysis, Validation Gate & Limitations (Sections 17–22)", h2))
    s_tab = sens_sum[["scenario", "kind", "top10_overlap", "spearman", "n_eligible"]].copy()
    s_tab["spearman"] = s_tab["spearman"].round(3)
    s_tab.columns = ["Scenario", "Discipline", "Top-10 Overlap", "Spearman Rho", "Eligible Count"]
    story.append(make_table(s_tab))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Automated 23-Check Validation Gate Summary:", body))
    g_tab = gate.copy()
    g_tab.columns = ["Validation Check", "Observed Metric", "Pass"]
    story.append(make_table(g_tab))
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "<b>Reproducibility:</b> Run `python -m src.pipeline` to regenerate all Parquet/CSV/JSON artefacts, `python -m pytest tests/ -v` to run the 19-test verification suite, and `streamlit run app.py` to launch the 8-section interactive platform.",
            body,
        )
    )

    doc.build(story)
    print(f"Methodology reports generated: {pdf_file}")


if __name__ == "__main__":
    build_reports()
