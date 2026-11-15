"""Load original source CSVs without mutation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

SOURCE_FILES = {
    "competitions": "competitions.csv",
    "teams": "teams.csv",
    "matches": "matches.csv",
    "ball_by_ball": "ball_by_ball.csv",
    "player_mapping": "competition_team_player_mapping.csv",
    "playing_eleven": "playing_eleven.csv",
}


def load_raw_tables(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    base = Path(raw_dir) if raw_dir else RAW_DIR
    tables: dict[str, pd.DataFrame] = {}
    for name, filename in SOURCE_FILES.items():
        path = base / filename
        if not path.exists():
            raise FileNotFoundError(f"Required source file missing: {path}")
        tables[name] = pd.read_csv(path)
    return tables
