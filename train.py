"""Entrenamiento, evaluación temporal y predicción del siguiente sorteo."""
from __future__ import annotations

import copy
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch
from torch import nn

from .features import make_windows, multi_hot, temporal_split
from .games import Game
from .models import build_model
from .significance import summarize


@dataclass
class TrainConfig:
    kind: str = "lstm"
    window: int = 10
    epochs: int = 30
    batch_size: int = 64
    lr: float = 1e-3
    hidden: int = 64
    layers: int = 1
    dropout: float = 0.2
    patience: int = 5          # early stopping sobre la pérdida de validación
    train_frac: float = 0.7
    val_frac: float = 0.15
    seed: int = 0


def group_slices(game: Game) -> list[tuple[str, slice, int, int]]:
    """(nombre, rango en el vector multi-hot, nº de valores, valor mínimo)."""
    out, pos = [], 0
    for g in game.groups:
        size = g.high - g.low + 1
        out.append((g.name, slice(pos, pos + size), g.count, g.low))
        pos += size
    return out


def decode(scores: np.ndarray, game: Game) -> dict[str, list[int]]:
    """Top-k por grupo a partir de puntuaciones (dim,) -> valores reales."""
    res = {}
    for name, sl, k, low in group_slices(game):
        top = np.argsort(-scores[sl], kind="stable")[:k]
        res[name] = sorted(int(i) + low for i in top)
    return res


def hits_vs_random(pred_scores: np.ndarray, y: np.ndarray, game: Game) -> dict:
    """Aciertos medios por sorteo y z frente al azar (distribución hipergeométrica exacta)."""
    out = {}
    T = len(y)
    for name, sl, k, _ in group_slices(game):
        N = sl.stop - sl.start
        top = np.argsort(-pred_scores[:, sl], axis=1, kind="stable")[:, :k]
        hit = np.take_along_axis(y[:, sl], top, axis=1).sum(axis=1)  # aciertos por sorteo
        exp = k * k / N
        var = k * (k / N) * (1 - k / N) * (N - k) / (N - 1) if N > 1 else 0.0
        se = math.sqrt(var / T) if T and var > 0 else float("nan")
        mean = float(hit.mean())
        out[name] = {
            "hits": round(mean, 4),
            "random_expected": round(exp, 4),
            "z": None if not se or math.isnan(se) else round((mean - exp) / se, 2),
            "significance": summarize(int(hit.sum()), T * k, k / N),
        }
    return out


def _loader(x, y, bs, shuffle, gen=None):
    ds = torch.utils.data.TensorDataset(torch.from_numpy(x), torch.from_numpy(y))
    return torch.utils.data.DataLoader(ds, batch_size=bs, shuffle=shuffle, generator=gen)


@torch.no_grad()
def _predict(model, x, bs=256) -> np.ndarray:
    model.eval()
    outs = [model(torch.from_numpy(x[i:i + bs])) for i in range(0, len(x), bs)]
    return torch.cat(outs).numpy() if outs else np.zeros((0, x.shape[-1]), np.float32)


def _fit(cfg: TrainConfig, dim: int, x_tr, y_tr, x_va, y_va):
    """Entrena con early stopping sobre validación (o entrenamiento si no hay)."""
    torch.manual_seed(cfg.seed)
    np.random.seed(cfg.seed)
    model = build_model(cfg.kind, dim, cfg.window, cfg.hidden, cfg.layers, cfg.dropout)
    opt = torch.optim.Adam(model.parameters(), lr=cfg.lr)
    loss_fn = nn.BCEWithLogitsLoss()
    gen = torch.Generator().manual_seed(cfg.seed)
    train_dl = _loader(x_tr, y_tr, cfg.batch_size, True, gen)
    has_val = len(x_va) > 0

    def val_loss():
        with torch.no_grad():
            model.eval()
            return float(loss_fn(model(torch.from_numpy(x_va)), torch.from_numpy(y_va)))

    best, best_state, bad, hist = float("inf"), None, 0, []
    for epoch in range(1, cfg.epochs + 1):
        model.train()
        tot, n = 0.0, 0
        for xb, yb in train_dl:
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            tot += loss.item() * len(xb)
            n += len(xb)
        t_loss = tot / n
        v_loss = val_loss() if has_val else t_loss
        hist.append({"epoch": epoch, "train_loss": round(t_loss, 5), "val_loss": round(v_loss, 5)})
        if v_loss < best - 1e-6:
            best, best_state, bad = v_loss, copy.deepcopy(model.state_dict()), 0
        else:
            bad += 1
            if cfg.patience and bad >= cfg.patience:
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    return model, hist, best


def train_model(df: pd.DataFrame, game: Game, cfg: TrainConfig):
    """Entrena con partición cronológica. Devuelve (modelo, informe)."""
    X = multi_hot(df, game)
    xs, ys = make_windows(X, cfg.window)
    tr, va, te = temporal_split(len(xs), cfg.train_frac, cfg.val_frac)
    if tr.stop < cfg.batch_size // 4 or (te.stop - te.start) < 5:
        raise ValueError("Datos insuficientes para esta partición; usa más sorteos o una ventana menor.")
    model, hist, best = _fit(cfg, X.shape[1], xs[tr], ys[tr], xs[va], ys[va])
    scores = _predict(model, xs[te])
    report = {
        "config": cfg.__dict__,
        "epochs_run": len(hist),
        "stopped_early": len(hist) < cfg.epochs,
        "best_val_loss": round(best, 5),
        "history": hist,
        "split": {"train": tr.stop, "val": va.stop - va.start, "test": te.stop - te.start},
        "test": hits_vs_random(scores, ys[te], game),
    }
    return model, report


def walk_forward(df: pd.DataFrame, game: Game, cfg: TrainConfig,
                 folds: int = 3, gap: int = 0, test_frac: float = 0.3) -> dict:
    """Validación walk-forward con ventana expansiva y hueco (gap) entre entrenamiento y test.

    El tramo final (test_frac) se divide en `folds` bloques consecutivos. Para cada bloque se
    reentrena solo con sorteos anteriores a (inicio_del_bloque - gap); la validación para el
    early stopping es el último val_frac del entrenamiento. Se agregan los aciertos de todos los
    folds y se contrasta el total frente al azar.
    """
    if folds < 1 or gap < 0 or not 0.05 <= test_frac <= 0.6:
        raise ValueError("Parámetros inválidos (folds>=1, gap>=0, 0.05<=test_frac<=0.6).")
    X = multi_hot(df, game)
    n, w = len(X), cfg.window
    t0 = int(n * (1 - test_frac))
    edges = np.linspace(t0, n, folds + 1).astype(int)
    if edges[1] - edges[0] < 5 or t0 - gap - w < 60:
        raise ValueError("Datos insuficientes para este número de folds, gap o ventana.")

    fold_rows, agg = [], {name: [0, 0, 0.0] for name, *_ in group_slices(game)}
    for f in range(folds):
        a, b = int(edges[f]), int(edges[f + 1])
        tr_end = a - gap
        xs, ys = make_windows(X[:tr_end], w)
        cut = int(len(xs) * (1 - cfg.val_frac))
        model, hist, _ = _fit(cfg, X.shape[1], xs[:cut], ys[:cut], xs[cut:], ys[cut:])
        x_te = np.stack([X[t - w:t] for t in range(a, b)])
        y_te = X[a:b]
        scores = _predict(model, x_te)
        res = hits_vs_random(scores, y_te, game)
        fold_rows.append({"fold": f + 1, "train_draws": tr_end, "test_draws": b - a, "gap": gap,
                          "epochs_run": len(hist),
                          "test": {g: {"hits": v["hits"], "z": v["z"]} for g, v in res.items()}})
        for name, sl, k, _ in group_slices(game):
            N = sl.stop - sl.start
            top = np.argsort(-scores[:, sl], axis=1, kind="stable")[:, :k]
            agg[name][0] += int(np.take_along_axis(y_te[:, sl], top, axis=1).sum())
            agg[name][1] += (b - a) * k
            agg[name][2] = k / N
    return {"config": cfg.__dict__, "folds": fold_rows,
            "pooled": {g: summarize(h, t, p0) for g, (h, t, p0) in agg.items()}}


def predict_next(model, df: pd.DataFrame, game: Game, window: int) -> dict:
    """Puntuaciones del siguiente sorteo a partir de los últimos `window` sorteos."""
    X = multi_hot(df.tail(window), game)
    if len(X) < window:
        raise ValueError(f"Se necesitan al menos {window} sorteos.")
    logits = _predict(model, X[None])[0]
    probs = 1 / (1 + np.exp(-logits))
    return {"numbers": decode(logits, game),
            "probabilities": {name: {int(i) + low: round(float(probs[sl][i]), 4)
                                     for i in range(sl.stop - sl.start)}
                              for name, sl, _, low in group_slices(game)}}
