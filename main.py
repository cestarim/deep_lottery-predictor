"""API FastAPI: carga/validación de CSV, estadísticas y backtesting."""
from __future__ import annotations

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .backtest import compare_with_random, frequency_predictor
from .data import load_csv
from .features import make_windows, multi_hot, temporal_split
from .games import GAMES, get_game

app = FastAPI(title="deep_lottery-predictor", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

MAX_BYTES = 20 * 1024 * 1024
_STORE: dict[str, pd.DataFrame] = {}  # datos validados en memoria, por juego

DISCLAIMER = "Los sorteos son aleatorios; ningún resultado de este proyecto garantiza premios."


def _game(key: str):
    try:
        return get_game(key)
    except ValueError as e:
        raise HTTPException(404, str(e))


def _data(key: str) -> pd.DataFrame:
    if key not in _STORE:
        raise HTTPException(409, f"No hay datos cargados para {key}. Usa POST /games/{key}/upload.")
    return _STORE[key]


@app.get("/health")
def health():
    return {"status": "ok", "disclaimer": DISCLAIMER}


@app.get("/games")
def games():
    return [
        {"key": g.key, "label": g.label, "columns": g.all_columns(),
         "groups": [{"name": x.name, "count": x.count, "range": [x.low, x.high]} for x in g.groups],
         "loaded": g.key in _STORE, "rows": len(_STORE.get(g.key, []))}
        for g in GAMES.values()
    ]


@app.post("/games/{key}/upload")
async def upload(key: str, file: UploadFile = File(...)):
    game = _game(key)
    raw = await file.read()
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, "Archivo demasiado grande (máx. 20 MB).")
    df, report = load_csv(raw, game)
    if report.ok:
        _STORE[key] = df
    return report.as_dict()


@app.get("/games/{key}/stats")
def stats(key: str, last: int | None = None):
    game, df = _game(key), _data(key)
    if last:
        df = df.tail(last)
    out = {"rows": len(df), "from": str(df["date"].min().date()), "to": str(df["date"].max().date()),
           "frequencies": {}}
    for g in game.groups:
        counts = pd.Series(df[g.columns()].to_numpy().ravel()).value_counts()
        full = pd.Series(0, index=range(g.low, g.high + 1)).add(counts, fill_value=0).astype(int)
        out["frequencies"][g.name] = {int(k): int(v) for k, v in full.items()}
    return out


@app.get("/games/{key}/dataset")
def dataset_info(key: str, window: int = 10, train: float = 0.7, val: float = 0.15):
    """Forma de los tensores de entrenamiento y la partición temporal (sin entrenar)."""
    game, df = _game(key), _data(key)
    try:
        xs, ys = make_windows(multi_hot(df, game), window)
        tr, va, te = temporal_split(len(xs), train, val)
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"X_shape": list(xs.shape), "y_shape": list(ys.shape),
            "split": {"train": tr.stop, "val": va.stop - va.start, "test": te.stop - te.start}}


@app.post("/games/{key}/backtest")
def run_backtest(key: str, lookback: int = 200, hot: bool = True,
                 test_fraction: float = 0.2, n_random: int = 20):
    """Backtest walk-forward del predictor de frecuencias frente a azar."""
    game, df = _game(key), _data(key)
    start = int(len(df) * (1 - test_fraction))
    if start < 30 or start >= len(df):
        raise HTTPException(422, "Datos insuficientes para el backtest.")
    res = compare_with_random(df, game, frequency_predictor(game, lookback, hot), start, n_random)
    res["disclaimer"] = DISCLAIMER
    return res
