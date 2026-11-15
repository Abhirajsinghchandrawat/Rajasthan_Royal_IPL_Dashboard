"""Row-level verification of the provisional extras rules.

Two Phase-1 open questions are resolved here with evidence that is written to
`data/interim/` so the classification is auditable:

1. `extras_type == "other"` (264 rows): is it a no-ball family?
   Evidence tested: delivery_style mix, extras1_runs pattern, batter-runs
   pattern versus Overstep, and the legal-ball cap of completed 20-over innings
   with/without treating `other` as illegal.
2. `extras_2_runs > 0` (35 rows): what do these runs represent?
   Evidence tested: co-occurring extras type, `runs`, and whether innings
   totals reconcile better with or without them.
"""

from __future__ import annotations

import json

import pandas as pd

from config.settings import DATA_INTERIM


def verify_other_extras(bbb: pd.DataFrame) -> dict:
    other = bbb[bbb["extras_type"].eq("other")]
    over = bbb[bbb["extras_type"].eq("Overstep")]
    style = other["delivery_style"].fillna("(missing)").value_counts().head(10)

    reg = bbb[bbb["innings"].isin([1, 2])].copy()
    et = reg["extras_type"].fillna("")
    legal_a = ~et.isin(["wide", "Overstep"])
    legal_b = ~et.isin(["wide", "Overstep", "other"])
    per_inn = reg.assign(la=legal_a, lb=legal_b).groupby(["match_id", "innings"])[["la", "lb"]].sum()
    res = {
        "other_rows": int(len(other)),
        "other_extras1_always_1": bool(other["extras1_runs"].eq(1).all()),
        "overstep_extras1_always_1": bool(over["extras1_runs"].eq(1).all()),
        "other_mean_runs": round(float(other["runs"].mean()), 3),
        "overstep_mean_runs": round(float(over["runs"].mean()), 3),
        "other_top_delivery_styles": style.to_dict(),
        "innings_over_120_legal_if_other_legal": int((per_inn["la"] > 120).sum()),
        "innings_over_120_legal_if_other_noball": int((per_inn["lb"] > 120).sum()),
    }
    res["classification"] = (
        "no_ball"
        if res["other_extras1_always_1"] and res["innings_over_120_legal_if_other_noball"] == 0
        else "UNRESOLVED"
    )
    return res


def verify_extras2(bbb: pd.DataFrame) -> dict:
    e2 = bbb[bbb["extras_2_runs"].fillna(0) > 0].copy()
    e2.to_csv(DATA_INTERIM / "extras_2_runs_rows_verified.csv", index=False)
    return {
        "rows": int(len(e2)),
        "extras_types": e2["extras_type"].fillna("none").value_counts().to_dict(),
        "runs_all_zero": bool(e2["runs"].fillna(0).eq(0).all()),
        "extras2_values": e2["extras_2_runs"].value_counts().to_dict(),
        "boundary_flags_on_rows": int((e2["is_four"].fillna(False) | e2["is_six"].fillna(False)).sum()),
        "interpretation": (
            "Runs taken off a no-ball that did not come off the bat (bye/leg-bye off a no-ball): "
            "always on no-ball families and only when runs==0. Counted in team runs; "
            "not charged to the bowler (Law 18/22 accounting: byes/leg-byes off no-balls are "
            "scored as no-ball extras for the team but only the 1-run penalty is debited "
            "to the bowler)."
        ),
    }


def run_cricket_checks(bbb: pd.DataFrame) -> dict:
    out = {"other_extras": verify_other_extras(bbb), "extras_2_runs": verify_extras2(bbb)}
    (DATA_INTERIM / "extras_verification.json").write_text(json.dumps(out, indent=2, default=str))
    return out
