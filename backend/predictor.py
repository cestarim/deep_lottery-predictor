from __future__ import annotations

from collections import Counter

import pandas as pd

from backend.data_loader import MAIN_COLUMNS, RANGES, SECONDARY_COLUMNS, load_game


def _ranked(values: list[int], low: int, high: int, count: int) -> list[int]:
    frequencies = Counter(values)
    # Tie-break deterministically by number. This is a descriptive baseline,
    # not a method that can predict a genuinely random draw.
    return sorted(range(low, high + 1), key=lambda number: (-frequencies[number], number))[:count]


def build_prediction(game: str, df: pd.DataFrame | None = None) -> dict:
    if game not in MAIN_COLUMNS:
        raise ValueError(f"Juego no soportado: {game}")
    draws = df if df is not None else load_game(game)
    main_low, main_high = RANGES[game]["main"]
    main_values = [int(value) for column in MAIN_COLUMNS[game] for value in draws[column].tolist()]
    result = {
        "method": "frequency_baseline",
        "game": game,
        "main_numbers": sorted(_ranked(main_values, main_low, main_high, len(MAIN_COLUMNS[game]))),
        "historic_draws": int(len(draws)),
        "warning": "Análisis descriptivo de datos de ejemplo; no mejora las probabilidades de ganar.",
    }

    if game == "euromillions":
        star_low, star_high = RANGES[game]["star"]
        stars = [int(value) for column in SECONDARY_COLUMNS[game] for value in draws[column].tolist()]
        result["secondary_numbers"] = sorted(_ranked(stars, star_low, star_high, 2))
    else:
        complementary_values = [int(value) for value in draws["complementary"].tolist()]
        reintegro_values = [int(value) for value in draws["reintegro"].tolist()]
        result["complementary"] = _ranked(complementary_values, main_low, main_high, 1)[0]
        result["reintegro"] = _ranked(reintegro_values, *RANGES[game]["reintegro"], 1)[0]
    return result
