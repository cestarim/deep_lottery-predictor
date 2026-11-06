from __future__ import annotations

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
GAME_FILES = {
    "euromillions": DATA_DIR / "euromillions_sample.csv",
    "bonoloto": DATA_DIR / "bonoloto_sample.csv",
}
MAIN_COLUMNS = {
    "euromillions": [f"main_{i}" for i in range(1, 6)],
    "bonoloto": [f"main_{i}" for i in range(1, 7)],
}
SECONDARY_COLUMNS = {
    "euromillions": ["star_1", "star_2"],
    "bonoloto": ["complementary", "reintegro"],
}
RANGES = {
    "euromillions": {"main": (1, 50), "star": (1, 12)},
    "bonoloto": {"main": (1, 49), "complementary": (1, 49), "reintegro": (0, 9)},
}


class DataValidationError(ValueError):
    """Raised when a draw CSV is missing fields or contains invalid values."""


def load_game(game: str) -> pd.DataFrame:
    if game not in GAME_FILES:
        raise ValueError(f"Juego no soportado: {game}")
    path = GAME_FILES[game]
    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo de datos: {path}")
    try:
        df = pd.read_csv(path)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise DataValidationError(f"No se pudo leer el CSV de {game}: {exc}") from exc

    required = ["date", *MAIN_COLUMNS[game], *SECONDARY_COLUMNS[game]]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise DataValidationError(f"Faltan columnas en {path.name}: {', '.join(missing)}")
    if df.empty:
        raise DataValidationError(f"El archivo {path.name} no contiene sorteos.")
    df = df[required].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if df["date"].isna().any():
        raise DataValidationError("La columna date debe contener fechas válidas (YYYY-MM-DD).")

    for column in [*MAIN_COLUMNS[game], *SECONDARY_COLUMNS[game]]:
        values = pd.to_numeric(df[column], errors="coerce")
        if values.isna().any() or (values % 1 != 0).any():
            raise DataValidationError(f"La columna {column} debe contener números enteros.")
        df[column] = values.astype(int)

    main_low, main_high = RANGES[game]["main"]
    for row_index, row in df.iterrows():
        main = [int(row[column]) for column in MAIN_COLUMNS[game]]
        if len(set(main)) != len(main):
            raise DataValidationError(f"Fila {row_index + 2}: números principales repetidos.")
        if any(value < main_low or value > main_high for value in main):
            raise DataValidationError(f"Fila {row_index + 2}: número principal fuera de rango.")
        if game == "euromillions":
            stars = [int(row[column]) for column in SECONDARY_COLUMNS[game]]
            low, high = RANGES[game]["star"]
            if len(set(stars)) != 2 or any(value < low or value > high for value in stars):
                raise DataValidationError(f"Fila {row_index + 2}: estrellas inválidas.")
        else:
            complementary = int(row["complementary"])
            reintegro = int(row["reintegro"])
            if not main_low <= complementary <= main_high or complementary in main:
                raise DataValidationError(f"Fila {row_index + 2}: complementario inválido.")
            low, high = RANGES[game]["reintegro"]
            if not low <= reintegro <= high:
                raise DataValidationError(f"Fila {row_index + 2}: reintegro fuera de rango.")

    return df.sort_values("date").reset_index(drop=True)


def get_game_summary(game: str, df: pd.DataFrame | None = None) -> dict:
    draws = df if df is not None else load_game(game)
    return {
        "game": game,
        "draw_count": int(len(draws)),
        "latest_date": draws["date"].max().strftime("%Y-%m-%d"),
        "columns": list(draws.columns),
    }
