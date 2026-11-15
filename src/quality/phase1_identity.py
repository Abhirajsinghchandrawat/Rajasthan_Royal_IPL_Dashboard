from pathlib import Path
import pandas as pd

RAW = Path("data/raw")
INTERIM = Path("data/interim")
bbb = pd.read_csv(RAW / "ball_by_ball.csv")
mapping = pd.read_csv(RAW / "competition_team_player_mapping.csv")
matches = pd.read_csv(RAW / "matches.csv")
ms = pd.read_csv(INTERIM / "matches_with_scope.csv")

ids = [6922, 7446, 29833, 39479, 8638, 39444, 7338, 28756, 3083, 20229, 27373, 28978, 4722, 20172]
rows = []
for pid in ids:
    m = mapping[mapping.player_id == pid][["player_id", "player_name", "team_name", "comp_name"]].drop_duplicates()
    bat = bbb[bbb.striker_id == pid]
    bowl = bbb[bbb.bowler_id == pid]
    rows.append(
        {
            "player_id": pid,
            "names": " | ".join(sorted(set(m.player_name.astype(str)) | set(bat.striker_name.dropna().astype(str)) | set(bowl.bowler_name.dropna().astype(str)))),
            "teams": " | ".join(sorted(m.team_name.dropna().astype(str).unique())),
            "n_mapping_rows": len(mapping[mapping.player_id == pid]),
            "bbb_bat_balls": len(bat),
            "bbb_bowl_balls": len(bowl),
            "n_matches_bat": bat.match_id.nunique(),
            "n_matches_bowl": bowl.match_id.nunique(),
        }
    )
pd.DataFrame(rows).to_csv(INTERIM / "name_collision_player_profiles.csv", index=False)
print(pd.DataFrame(rows).to_string(index=False))

# extras other vs overstep comparison
oth = bbb[bbb.extras_type == "other"]
print("\nother extras1", oth.extras1_runs.value_counts().to_dict())
print("other runs", oth.runs.value_counts().sort_index().to_dict())
print("other is_four/six", int(oth.is_four.sum()), int(oth.is_six.sum()))
print("other is_wicket", int(oth.is_wicket.sum()), oth[oth.is_wicket].dismissal_type.value_counts().to_dict())

# legal balls in completed unrevised 20-over innings if we treat other as illegal
work = bbb.copy()
fam = work.extras_type.fillna("none")
work["illegal_strict"] = fam.isin(["wide", "Overstep"])
work["illegal_incl_other"] = fam.isin(["wide", "Overstep", "other"])
reg = work[work.innings.isin([1, 2])]
g = reg.groupby(["match_id", "innings"]).agg(
    legal_strict=("illegal_strict", lambda s: int((~s).sum())),
    legal_incl=("illegal_incl_other", lambda s: int((~s).sum())),
    max_over=("overid", "max"),
)
full = g[(g.max_over == 20)]
print("\n20-over innings n", len(full))
print("legal_strict value counts head", full.legal_strict.value_counts().sort_index().tail(8).to_dict())
print("legal_incl value counts head", full.legal_incl.value_counts().sort_index().tail(8).to_dict())
print("pct legal_incl==120", float((full.legal_incl == 120).mean()), "pct legal_strict==120", float((full.legal_strict == 120).mean()))

# result categories
res = matches.result.astype(str)
print("abandoned", int(res.str.contains("Abandoned", case=False).sum()))
print("no result", int(res.str.contains(r"No Result", case=False).sum()))
print("tie/super", int(res.str.contains(r"tie|super over", case=False).sum()))
print("win_team na", int(matches.win_team_id.isna().sum()))
print(matches.loc[matches.win_team_id.isna(), "result"].value_counts().to_dict())

# bowl_speed 0
print("bowl_speed==0", int((bbb.bowl_speed == 0).sum()), "pct", float((bbb.bowl_speed == 0).mean()))
print("motm==0", int((matches.man_of_the_match == 0).sum()))
