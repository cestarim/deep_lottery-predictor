from __future__ import annotations

import pandas as pd

from backend.data_loader import MAIN_COLUMNS, RANGES, SECONDARY_COLUMNS
from backend.predictor import build_prediction


def run_frequency_backtest(
    game: str,
    draws: pd.DataFrame,
    *,
    min_train: int = 3,
    max_holdout: int = 100,
) -> dict:
    """Walk forward and compare historical hit rates with random expectations."""
    if game not in MAIN_COLUMNS:
        raise ValueError(f"Juego no soportado: {game}")
    if min_train < 1 or max_holdout < 1:
        raise ValueError("min_train y max_holdout deben ser positivos.")
    if len(draws) <= min_train:
        raise ValueError(f"Se necesitan al menos {min_train + 1} sorteos para el backtest.")

    holdout = min(max_holdout, len(draws) - min_train)
    start = len(draws) - holdout
    columns = MAIN_COLUMNS[game]
    low, high = RANGES[game]["main"]
    count = len(columns)
    population = high - low + 1
    main_expected = count * count / population
    main_hits: list[int] = []
    secondary_hits: list[int] = []
    reintegro_hits: list[int] = []

    if game == "euromillions":
        low, high = RANGES[game]["star"]
        secondary_expected = 2 * 2 / (high - low + 1)
    else:
        secondary_expected = 1 / (population - count)
        low, high = RANGES[game]["reintegro"]
        reintegro_expected = 1 / (high - low + 1)

    for index in range(start, len(draws)):
        prediction = build_prediction(game, draws.iloc[:index])
        actual = draws.iloc[index]
        actual_main = {int(actual[column]) for column in columns}
        main_hits.append(len(set(prediction["main_numbers"]) & actual_main))
        if game == "euromillions":
            actual_secondary = {int(actual[column]) for column in SECONDARY_COLUMNS[game]}
            secondary_hits.append(len(set(prediction["secondary_numbers"]) & actual_secondary))
        else:
            secondary_hits.append(int(prediction["complementary"] == int(actual["complementary"])))
            reintegro_hits.append(int(prediction["reintegro"] == int(actual["reintegro"])))

    result = {
        "method": "walk_forward_frequency_baseline",
        "test_draws": holdout,
        "training_draws_min": min_train,
        "main_average_hits": sum(main_hits) / holdout,
        "main_random_expected_hits": main_expected,
        "main_hit_counts": main_hits,
        "secondary_average_hits": sum(secondary_hits) / holdout,
        "secondary_random_expected_hits": secondary_expected,
        "secondary_hit_counts": secondary_hits,
        "interpretation": "Evaluación histórica descriptiva frente al valor esperado aleatorio; no demuestra capacidad predictiva futura.",
    }
    if game == "bonoloto":
        result.update({
            "reintegro_average_hits": sum(reintegro_hits) / holdout,
            "reintegro_random_expected_hits": reintegro_expected,
            "reintegro_hit_counts": reintegro_hits,
        })
    return result
