"""Backtesting temporal contra una referencia aleatoria.

Métrica: aciertos medios por sorteo (cuántos de los valores de cada grupo coinciden
con la predicción). Un predictor sin información debe igualar a la referencia
aleatoria; el modelo solo aporta algo si la supera de forma consistente.
"""
from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from .games import Game

Predictor = Callable[[pd.DataFrame], dict]  # historial -> {grupo: [valores]}


def _hits(row: pd.Series, game: Game, pred: dict) -> dict:
    out = {}
    for g in game.groups:
        real = {int(row[c]) for c in g.columns()}
        out[g.name] = len(real & set(int(v) for v in pred[g.name]))
    return out


def random_predictor(game: Game, rng: np.random.Generator) -> Predictor:
    def _p(_hist: pd.DataFrame) -> dict:
        return {
            g.name: rng.choice(np.arange(g.low, g.high + 1), size=g.count, replace=False).tolist()
            for g in game.groups
        }
    return _p


def frequency_predictor(game: Game, lookback: int | None = None, hot: bool = True) -> Predictor:
    """Referencia simple: los valores más (o menos) frecuentes del historial."""
    def _p(hist: pd.DataFrame) -> dict:
        h = hist.tail(lookback) if lookback else hist
        out = {}
        for g in game.groups:
            counts = pd.Series(h[g.columns()].to_numpy().ravel()).value_counts()
            full = pd.Series(0, index=range(g.low, g.high + 1)).add(counts, fill_value=0)
            order = full.sort_values(ascending=not hot, kind="stable")
            out[g.name] = order.index[:g.count].tolist()
        return out
    return _p


def backtest(df: pd.DataFrame, game: Game, predictor: Predictor,
             start: int, step: int = 1) -> dict:
    """Walk-forward: para cada sorteo t >= start predice usando solo df[:t]."""
    if start < 1 or start >= len(df):
        raise ValueError("start fuera de rango.")
    rows = [_hits(df.iloc[t], game, predictor(df.iloc[:t])) for t in range(start, len(df), step)]
    res = pd.DataFrame(rows)
    return {"n_draws": len(res), "mean_hits": res.mean().round(4).to_dict()}


def compare_with_random(df: pd.DataFrame, game: Game, predictor: Predictor,
                        start: int, n_random: int = 20, seed: int = 0) -> dict:
    """Modelo vs. media de varias ejecuciones aleatorias, con su dispersión."""
    model = backtest(df, game, predictor, start)
    rng = np.random.default_rng(seed)
    runs = [backtest(df, game, random_predictor(game, rng), start)["mean_hits"]
            for _ in range(n_random)]
    rnd = pd.DataFrame(runs)
    return {
        "n_draws": model["n_draws"],
        "model": model["mean_hits"],
        "random_mean": rnd.mean().round(4).to_dict(),
        "random_std": rnd.std().round(4).to_dict(),
        "z_vs_random": {
            k: (None if rnd[k].std() == 0 else round((model["mean_hits"][k] - rnd[k].mean()) / rnd[k].std(), 2))
            for k in model["mean_hits"]
        },
    }
