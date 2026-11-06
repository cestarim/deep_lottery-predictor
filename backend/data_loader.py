from __future__ import annotations

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
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
    """Raised when draw data is missing fields or contains invalid values."""


def dataset_path(game: str) -> Path:
    if game not in GAME_FILES:
        raise ValueError(f"Juego no soportado: {game}")
    uploaded = UPLOAD_DIR / f"{game}.csv"
    return uploaded if uploaded.is_file() else GAME_FILES[game]


def dataset_source(game: str) -> str:
    return "uploaded_csv" if dataset_path(game).parent == UPLOAD_DIR else "synthetic_sample"


def validate_draws(game: str, df: pd.DataFrame, source_name: str = "CSV") -> pd.DataFrame:
    if game not in GAME_FILES:
        raise ValueError(f"Juego no soportado: {game}")
    required = ["date", *MAIN_COLUMNS[game], *SECONDARY_COLUMNS[game]]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise DataValidationError(f"Faltan columnas en {source_name}: {', '.join(missing)}")
    if df.empty:
        raise DataValidationError(f"{source_name} no contiene sorteos.")

    result = df[required].copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    if result["date"].isna().any():
        raise DataValidationError("La columna date debe contener fechas válidas (YYYY-MM-DD).")

    for column in [*MAIN_COLUMNS[game], *SECONDARY_COLUMNS[game]]:
        values = pd.to_numeric(result[column], errors="coerce")
        if values.isna().any() or (values % 1 != 0).any():
            raise DataValidationError(f"La columna {column} debe contener números enteros.")
        result[column] = values.astype(int)

    main_low, main_high = RANGES[game]["main"]
    for row_index, row in result.iterrows():
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

    return result.sort_values("date").reset_index(drop=True)


def load_game(game: str) -> pd.DataFrame:
    path = dataset_path(game)
    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo de datos: {path}")
    try:
        df = pd.read_csv(path)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise DataValidationError(f"No se pudo leer el CSV de {game}: {exc}") from exc
    return validate_draws(game, df, path.name)


def get_game_summary(game: str, df: pd.DataFrame | None = None) -> dict:
    draws = df if df is not None else load_game(game)
    return {
        "game": game,
        "draw_count": int(len(draws)),
        "latest_date": draws["date"].max().strftime("%Y-%m-%d"),
        "columns": list(draws.columns),
        "source": dataset_source(game),
    }
