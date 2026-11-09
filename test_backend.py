import io

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.backtest import compare_with_random, frequency_predictor
from app.data import load_csv, validate_frame
from app.features import make_windows, multi_hot, temporal_split
from app.games import BONOLOTO, EUROMILLIONS
from app.main import _STORE, app


def synth(game, n=300, seed=1, sep=","):
    rng = np.random.default_rng(seed)
    rows = []
    for d in pd.date_range("2015-01-02", periods=n, freq="3D"):
        row = {"fecha": d.strftime("%Y-%m-%d")}
        for g in game.groups:
            vals = rng.choice(np.arange(g.low, g.high + 1), size=g.count, replace=False)
            for c, v in zip(g.columns(), vals):
                row[c] = int(v)
        rows.append(row)
    return pd.DataFrame(rows)


def test_valid_euromillions():
    df, rep = validate_frame(synth(EUROMILLIONS), EUROMILLIONS)
    assert rep.ok and rep.rows_ok == 300 and df["date"].is_monotonic_increasing


def test_valid_bonoloto_reintegro_zero_allowed():
    raw = synth(BONOLOTO)
    raw.loc[0, "reintegro"] = 0
    _, rep = validate_frame(raw, BONOLOTO)
    assert rep.ok and rep.rows_ok == 300


def test_aliases_and_semicolon_and_accents():
    raw = synth(EUROMILLIONS).rename(columns={"n_1": "N1", "n_2": "n2", "star_1": "Estrella 1", "fecha": "Fecha"})
    csv = raw.to_csv(sep=";", index=False).encode()
    df, rep = load_csv(csv, EUROMILLIONS)
    assert rep.ok, rep.errors


def test_invalid_rows_dropped_with_reasons():
    raw = synth(EUROMILLIONS)
    raw.loc[0, "n_1"] = 99            # fuera de rango
    raw.loc[1, "n_2"] = raw.loc[1, "n_1"]  # repetido
    raw.loc[2, "fecha"] = "no-fecha"
    raw.loc[3, "star_1"] = np.nan
    df, rep = validate_frame(raw, EUROMILLIONS)
    assert rep.ok and rep.rows_ok == 296
    assert "Se descartaron 4 filas" in rep.warnings[0]


def test_missing_columns_reported():
    raw = synth(EUROMILLIONS).drop(columns=["star_2"])
    _, rep = validate_frame(raw, EUROMILLIONS)
    assert not rep.ok and any("star_2" in e for e in rep.errors)


def test_duplicate_dates():
    raw = synth(EUROMILLIONS)
    raw.loc[5, "fecha"] = raw.loc[4, "fecha"]
    df, rep = validate_frame(raw, EUROMILLIONS)
    assert rep.rows_ok == 299 and any("duplicadas" in w for w in rep.warnings)


def test_multi_hot_and_windows():
    df, _ = validate_frame(synth(EUROMILLIONS, 50), EUROMILLIONS)
    X = multi_hot(df, EUROMILLIONS)
    assert X.shape == (50, 50 + 12)
    assert X[:, :50].sum(axis=1).tolist() == [5] * 50
    assert X[:, 50:].sum(axis=1).tolist() == [2] * 50
    xs, ys = make_windows(X, 10)
    assert xs.shape == (40, 10, 62) and ys.shape == (40, 62)
    assert np.array_equal(xs[0][-1], X[9]) and np.array_equal(ys[0], X[10])
    with pytest.raises(ValueError):
        make_windows(X, 50)


def test_temporal_split_is_chronological():
    tr, va, te = temporal_split(100)
    assert (tr.start, tr.stop, va.start, va.stop, te.start, te.stop) == (0, 70, 70, 85, 85, 100)


def test_backtest_no_lookahead_and_close_to_random():
    df, _ = validate_frame(synth(EUROMILLIONS, 400), EUROMILLIONS)
    seen = []

    def spy(hist):
        seen.append(len(hist))
        return {"n": [1, 2, 3, 4, 5], "star": [1, 2]}

    from app.backtest import backtest
    backtest(df, EUROMILLIONS, spy, start=300)
    assert seen[0] == 300 and seen[-1] == 399  # solo historial previo
    res = compare_with_random(df, EUROMILLIONS, frequency_predictor(EUROMILLIONS, 100), 300, n_random=15)
    # en datos aleatorios no debe haber ventaja sistemática
    assert all(abs(z) < 4 for z in res["z_vs_random"].values() if z is not None)


def test_api_flow():
    _STORE.clear()
    c = TestClient(app)
    assert c.get("/health").status_code == 200
    assert c.get("/games/euromillions/stats").status_code == 409
    assert c.get("/games/nope/stats").status_code == 404
    csv = synth(EUROMILLIONS).to_csv(index=False).encode()
    r = c.post("/games/euromillions/upload", files={"file": ("d.csv", csv, "text/csv")})
    assert r.json()["ok"] and r.json()["rows_ok"] == 300
    s = c.get("/games/euromillions/stats").json()
    assert s["rows"] == 300 and sum(s["frequencies"]["n"].values()) == 1500
    d = c.get("/games/euromillions/dataset?window=12").json()
    assert d["X_shape"] == [288, 12, 62]
    b = c.post("/games/euromillions/backtest?lookback=100").json()
    assert "z_vs_random" in b and "disclaimer" in b
    bad = c.post("/games/bonoloto/upload", files={"file": ("d.csv", csv, "text/csv")}).json()
    assert not bad["ok"]
    assert c.get("/games/bonoloto/stats").status_code == 409
