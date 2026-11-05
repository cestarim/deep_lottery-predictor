from __future__ import annotations

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
GAME_FILES = {
    "euromillions": DATA_DIR / "euromillions_sample.csv",
    "bonoloto": DATA_DIR / "bonoloto_sample.csv",
}


def load_game(game: str) -> pd.DataFrame:
    if game not in GAME_FILES:
        raise ValueError(f"Juego no soportado: {game}")

    file_path = GAME_FILES[game]
    if not file_path.exists():
        raise FileNotFoundError(f"No se encontró el CSV para {game}: {file_path}")

    df = pd.read_csv(file_path, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def get_game_summary(game: str) -> dict:
    df = load_game(game)
    return {
        "game": game,
        "draw_count": len(df),
        "latest_date": df["date"].max().strftime("%Y-%m-%d"),
        "columns": list(df.columns),
    }
