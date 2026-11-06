from __future__ import annotations

from collections import Counter

import pandas as pd

from backend.data_loader import MAIN_COLUMNS, RANGES, SECONDARY_COLUMNS, load_game


def _ranked(values: list[int], low: int, high: int, count: int) -> list[int]:
    frequencies = Counter(values)
    return sorted(range(low, high + 1), key=lambda number: (-frequencies[number], number))[:count]


def build_prediction(game: str, df: pd.DataFrame | None = None) -> dict:
    """Return a deterministic frequency summary, not a future outcome forecast."""
    if game not in MAIN_COLUMNS:
        raise ValueError(f"Juego no soportado: {game}")
    draws = df if df is not None else load_game(game)
    if draws.empty:
        raise ValueError("No hay sorteos disponibles para calcular frecuencias.")
    low, high = RANGES[game]["main"]
    main_values = [int(value) for column in MAIN_COLUMNS[game] for value in draws[column].tolist()]
    result = {
        "method": "frequency_baseline",
        "game": game,
        "main_numbers": sorted(_ranked(main_values, low, high, len(MAIN_COLUMNS[game]))),
        "historic_draws": int(len(draws)),
        "warning": "Análisis descriptivo; la frecuencia histórica no permite predecir el siguiente sorteo aleatorio.",
    }
    if game == "euromillions":
        low, high = RANGES[game]["star"]
        values = [int(value) for column in SECONDARY_COLUMNS[game] for value in draws[column].tolist()]
        result["secondary_numbers"] = sorted(_ranked(values, low, high, 2))
    else:
        values = [int(value) for value in draws["complementary"].tolist()]
        result["complementary"] = _ranked(values, *RANGES[game]["complementary"], 1)[0]
        values = [int(value) for value in draws["reintegro"].tolist()]
        result["reintegro"] = _ranked(values, *RANGES[game]["reintegro"], 1)[0]
    return result
