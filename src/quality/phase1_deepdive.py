"""Additional Phase 1 inspections written to interim CSVs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"


def main() -> None:
    comps = pd.read_csv(RAW / "competitions.csv")
    matches = pd.read_csv(RAW / "matches.csv")
    bbb = pd.read_csv(RAW / "ball_by_ball.csv")
    xi = pd.read_csv(RAW / "playing_eleven.csv")
    mapping = pd.read_csv(RAW / "competition_team_player_mapping.csv")
    ms = pd.read_csv(INTERIM / "matches_with_scope.csv")
    recon = pd.read_csv(INTERIM / "innings_reconciliation.csv")
    rev = pd.read_csv(INTERIM / "revised_matches_inspection.csv")

    ipl = comps[comps.comp_name.str.contains("IPL|Indian Premier", case=False, na=False)]
    ipl.to_csv(INTERIM / "ipl_competitions.csv", index=False)
    other = ms[ms.scope_group == "Other T20"][
        ["comp_id", "comp_name", "match_format", "season"]
    ].drop_duplicates()
    other.to_csv(INTERIM / "other_t20_competitions.csv", index=False)
    comps[~comps.comp_id.isin(matches.comp_id)].to_csv(
        INTERIM / "competitions_with_no_matches.csv", index=False
    )

    no_bbb = matches[~matches.match_id.isin(bbb.match_id)].merge(
        ms[["match_id", "scope_group", "comp_name"]], on="match_id"
    )
    no_bbb.to_csv(INTERIM / "matches_without_bbb.csv", index=False)

    no_xi = matches[~matches.match_id.isin(xi.match_id)].merge(
        ms[["match_id", "scope_group", "comp_name"]], on="match_id"
    )
    no_xi.to_csv(INTERIM / "matches_without_xi.csv", index=False)

    byr = recon[recon.result_by_runs.fillna(False)]
    miss_c = byr[~byr.win_by_runs_match_c.fillna(False)]
    miss_c.to_csv(INTERIM / "reconciliation_by_runs_misses_C.csv", index=False)

    oth = bbb[bbb.extras_type == "other"].copy()
    oth.to_csv(INTERIM / "extras_type_other_rows.csv", index=False)

    nb = bbb[bbb.extras_type == "Overstep"].copy()
    nb_xtab = (
        nb.groupby(["runs", "extras1_runs", "extras_2_runs", "is_four", "is_six"], dropna=False)
        .size()
        .reset_index(name="n")
    )
    nb_xtab.to_csv(INTERIM / "overstep_runs_crosstab.csv", index=False)

    wd = bbb[bbb.extras_type == "wide"]
    pd.DataFrame({"extras1_runs": wd.extras1_runs.value_counts().sort_index().index, "n": wd.extras1_runs.value_counts().sort_index().values}).to_csv(
        INTERIM / "wide_extras1_distribution.csv", index=False
    )
    wd[wd.is_wicket == True][["match_id", "innings", "overid", "over_ball_num", "dismissal_type", "dismissed_player_id", "striker_id", "non_striker_id", "extras1_runs"]].to_csv(
        INTERIM / "wides_with_wickets.csv", index=False
    )

    lb = bbb[bbb.extras_type == "legbyes"]
    lb[lb.runs != 0][["match_id", "innings", "overid", "runs", "extras1_runs", "extras_2_runs", "is_four", "is_wicket"]].to_csv(
        INTERIM / "legbye_nonzero_runs.csv", index=False
    )

    work = bbb.copy()
    fam = work.extras_type.fillna("none").astype(str)
    work["is_illegal"] = fam.str.lower().eq("wide") | fam.eq("Overstep")
    g = (
        work[work.innings.isin([1, 2])]
        .groupby(["match_id", "innings"], as_index=False)
        .agg(n=("runs", "size"), max_innings_ball=("innings_ball_num", "max"), illegal=("is_illegal", "sum"))
    )
    g["max_eq_n"] = g["max_innings_ball"] == g["n"]
    g.to_csv(INTERIM / "innings_ball_num_vs_rowcount.csv", index=False)

    bbb[bbb.dismissed_player_id.notna() & (bbb.is_wicket != True)].to_csv(
        INTERIM / "dismissed_player_without_is_wicket.csv", index=False
    )
    bbb[(bbb.is_wicket == True) & bbb.dismissed_player_id.isna()].to_csv(
        INTERIM / "wicket_without_dismissed_player.csv", index=False
    )

    names = pd.concat(
        [
            bbb[["striker_id", "striker_name"]].rename(columns={"striker_id": "player_id", "striker_name": "player_name"}),
            bbb[["bowler_id", "bowler_name"]].rename(columns={"bowler_id": "player_id", "bowler_name": "player_name"}),
            mapping[["player_id", "player_name"]],
        ],
        ignore_index=True,
    ).dropna()
    n1 = names.groupby("player_id").player_name.nunique()
    names[names.player_id.isin(n1[n1 > 1].index)].drop_duplicates().to_csv(
        INTERIM / "player_id_multiple_names.csv", index=False
    )
    n2 = names.groupby("player_name").player_id.nunique()
    names[names.player_name.isin(n2[n2 > 1].index)].drop_duplicates().sort_values(["player_name", "player_id"]).to_csv(
        INTERIM / "player_name_multiple_ids.csv", index=False
    )

    # Revised: compare allocation vs observed legal balls and result
    rev2 = rev.merge(ms[["match_id", "scope_group", "result", "comp_name"]], on="match_id", how="left", suffixes=("", "_ms"))
    rev2.to_csv(INTERIM / "revised_matches_with_result.csv", index=False)

    # Super over detail
    so_ids = [34429, 40725, 45512, 48027, 48029, 50359]
    so = bbb[bbb.match_id.isin(so_ids) & bbb.innings.isin([3, 4])]
    so_sum = (
        so.groupby(["match_id", "innings", "batting_team_id"], as_index=False)
        .agg(rows=("runs", "size"), runs=("runs", "sum"), extras1=("extras1_runs", "sum"), extras2=("extras_2_runs", "sum"))
    )
    so_sum.to_csv(INTERIM / "super_over_innings_summary.csv", index=False)
    matches[matches.match_id.isin(so_ids)][["match_id", "match_date", "comp_id", "result", "win_team_id"]].merge(
        ms[["match_id", "scope_group", "comp_name"]], on="match_id"
    ).to_csv(INTERIM / "super_over_match_results.csv", index=False)

    # Playing XI duplicate keys
    key = ["match_id", "team_id", "player_id"]
    dup = xi[xi.duplicated(key, keep=False)].sort_values(key)
    dup.to_csv(INTERIM / "playing_xi_duplicate_keys.csv", index=False)

    # IPL seasons match counts
    ipl_matches = ms[ms.scope_group == "IPL"].groupby(["season", "comp_name"], as_index=False).agg(n_matches=("match_id", "nunique"))
    ipl_matches.to_csv(INTERIM / "ipl_season_match_counts.csv", index=False)
    t20i_season = ms[ms.scope_group == "T20I"].groupby("season", as_index=False).agg(n_matches=("match_id", "nunique"))
    t20i_season.to_csv(INTERIM / "t20i_season_match_counts.csv", index=False)

    # Knockouts / result missing
    print("no_bbb", len(no_bbb), "results", no_bbb.result.fillna("(na)").value_counts().to_dict())
    print("no_xi", len(no_xi), no_xi.match_id.tolist())
    print("miss_c", len(miss_c))
    print("innings_ball max_eq_n", float(g.max_eq_n.mean()), int(g.max_eq_n.sum()), len(g))
    print("wide wickets", int((wd.is_wicket == True).sum()))
    print("overstep n", len(nb), "fours", int(nb.is_four.sum()), "sixes", int(nb.is_six.sum()))
    print("other extras", len(oth), "runs mean", float(oth.runs.mean()), "extras1 mean", float(oth.extras1_runs.mean()))
    print("duplicate xi groups", dup.groupby(key).ngroups)
    print("rev inn1 legal eq int balls", int(rev.inn1_legal_eq_int_balls.fillna(False).sum()), "of", len(rev))
    print("rev first unique", sorted(rev.first_inn_revised_overs.dropna().unique().tolist()))
    print("win_team missing", int(matches.win_team_id.isna().sum()))
    print("result missing", int(matches.result.isna().sum()))
    print("result sample uniques", matches.result.nunique(dropna=False))


if __name__ == "__main__":
    main()
