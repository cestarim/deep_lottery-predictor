"""Preprocesado: codificación multi-hot, ventanas de secuencia y partición temporal."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .games import Game


def multi_hot(df: pd.DataFrame, game: Game) -> np.ndarray:
    """Matriz (n_sorteos, sum(rango de cada grupo)) con 1 en los valores salidos."""
    blocks = []
    for g in game.groups:
        size = g.high - g.low + 1
        m = np.zeros((len(df), size), dtype=np.float32)
        for col in g.columns():
            idx = df[col].to_numpy() - g.low
            m[np.arange(len(df)), idx] = 1.0
        blocks.append(m)
    return np.concatenate(blocks, axis=1)


def make_windows(X: np.ndarray, window: int) -> tuple[np.ndarray, np.ndarray]:
    """Ventanas deslizantes: entrada X[i:i+window], objetivo X[i+window]."""
    if window < 1:
        raise ValueError("window debe ser >= 1")
    if len(X) <= window:
        raise ValueError(f"Se necesitan más de {window} sorteos (hay {len(X)}).")
    xs = np.stack([X[i:i + window] for i in range(len(X) - window)])
    ys = X[window:]
    return xs, ys


def temporal_split(n: int, train: float = 0.7, val: float = 0.15) -> tuple[slice, slice, slice]:
    """Partición cronológica (sin barajar): entrenamiento / validación / test."""
    if not 0 < train < 1 or not 0 <= val < 1 or train + val >= 1:
        raise ValueError("Proporciones inválidas.")
    a, b = int(n * train), int(n * (train + val))
    return slice(0, a), slice(a, b), slice(b, n)
