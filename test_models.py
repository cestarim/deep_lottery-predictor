import numpy as np
import pytest

torch = pytest.importorskip("torch")
from fastapi.testclient import TestClient

from app.data import validate_frame
from app.games import BONOLOTO, EUROMILLIONS
from app.main import _MODELS, _STORE, app
from app.models import KINDS, build_model
from app.train import TrainConfig, decode, group_slices, hits_vs_random, predict_next, train_model
from tests.test_backend import synth


@pytest.mark.parametrize("kind", KINDS)
def test_forward_shape(kind):
    m = build_model(kind, dim=62, window=8, hidden=16)
    assert m(torch.zeros(3, 8, 62)).shape == (3, 62)


@pytest.mark.parametrize("kind", KINDS)
def test_train_each_kind(kind):
    df, _ = validate_frame(synth(EUROMILLIONS, 200), EUROMILLIONS)
    cfg = TrainConfig(kind=kind, window=6, epochs=3, hidden=16, patience=0)
    model, rep = train_model(df, EUROMILLIONS, cfg)
    assert rep["epochs_run"] == 3 and set(rep["test"]) == {"n", "star"}
    out = predict_next(model, df, EUROMILLIONS, 6)
    assert len(out["numbers"]["n"]) == 5 and len(set(out["numbers"]["n"])) == 5
    assert all(1 <= v <= 50 for v in out["numbers"]["n"]) and all(1 <= v <= 12 for v in out["numbers"]["star"])


def test_early_stopping_triggers():
    df, _ = validate_frame(synth(EUROMILLIONS, 250), EUROMILLIONS)
    cfg = TrainConfig(kind="lstm", window=6, epochs=60, hidden=32, lr=5e-3, patience=2)
    _, rep = train_model(df, EUROMILLIONS, cfg)
    assert rep["stopped_early"] and rep["epochs_run"] < 60  # el azar no se puede aprender


def test_reproducible_with_seed():
    df, _ = validate_frame(synth(EUROMILLIONS, 150), EUROMILLIONS)
    cfg = TrainConfig(kind="gru", window=5, epochs=2, hidden=16, patience=0, seed=3)
    _, a = train_model(df, EUROMILLIONS, cfg)
    _, b = train_model(df, EUROMILLIONS, cfg)
    assert a["history"] == b["history"]


def test_decode_bonoloto_reintegro_range():
    scores = np.random.default_rng(0).normal(size=sum(s.stop - s.start for _, s, _, _ in group_slices(BONOLOTO)))
    d = decode(scores, BONOLOTO)
    assert len(d["n"]) == 6 and len(d["complementario"]) == 1 and 0 <= d["reintegro"][0] <= 9


def test_hits_vs_random_perfect_predictor_has_high_z():
    df, _ = validate_frame(synth(EUROMILLIONS, 100), EUROMILLIONS)
    from app.features import multi_hot
    y = multi_hot(df, EUROMILLIONS)
    r = hits_vs_random(y * 1.0, y, EUROMILLIONS)  # "oráculo": conoce el resultado
    assert r["n"]["hits"] == 5 and r["n"]["z"] > 10
    rnd = hits_vs_random(np.random.default_rng(1).normal(size=y.shape), y, EUROMILLIONS)
    assert abs(rnd["n"]["z"]) < 4


def test_api_train_predict():
    _STORE.clear(); _MODELS.clear()
    c = TestClient(app)
    assert c.post("/games/euromillions/train").status_code == 409
    csv = synth(EUROMILLIONS, 220).to_csv(index=False).encode()
    c.post("/games/euromillions/upload", files={"file": ("d.csv", csv, "text/csv")})
    assert c.get("/games/euromillions/predict").status_code == 409
    assert c.post("/games/euromillions/train?kind=xx").status_code == 422
    r = c.post("/games/euromillions/train?kind=transformer&window=6&epochs=2&hidden=16&patience=0")
    assert r.status_code == 200, r.text
    assert "disclaimer" in r.json() and "z" in r.json()["test"]["n"]
    p = c.get("/games/euromillions/predict").json()
    assert len(p["numbers"]["n"]) == 5


def test_walk_forward_gap_and_pooling():
    from app.train import walk_forward
    df, _ = validate_frame(synth(EUROMILLIONS, 400), EUROMILLIONS)
    cfg = TrainConfig(kind="gru", window=6, epochs=2, hidden=16, patience=0)
    r = walk_forward(df, EUROMILLIONS, cfg, folds=3, gap=5, test_frac=0.3)
    assert len(r["folds"]) == 3 and all(f["gap"] == 5 for f in r["folds"])
    # entrenamiento siempre anterior al bloque de test menos el gap, y expansivo
    assert [f["train_draws"] for f in r["folds"]] == sorted(f["train_draws"] for f in r["folds"])
    tests = sum(f["test_draws"] for f in r["folds"])
    assert r["pooled"]["n"]["trials"] == tests * 5 and r["pooled"]["star"]["trials"] == tests * 2
    assert r["pooled"]["n"]["contains_chance"]  # datos aleatorios


def test_walk_forward_validation_errors():
    from app.train import walk_forward
    df, _ = validate_frame(synth(EUROMILLIONS, 100), EUROMILLIONS)
    with pytest.raises(ValueError):
        walk_forward(df, EUROMILLIONS, TrainConfig(window=6), folds=3, gap=50)


def test_api_walkforward():
    _STORE.clear(); _MODELS.clear()
    c = TestClient(app)
    csv = synth(EUROMILLIONS, 300).to_csv(index=False).encode()
    c.post("/games/euromillions/upload", files={"file": ("d.csv", csv, "text/csv")})
    r = c.post("/games/euromillions/walkforward?kind=cnn&window=6&epochs=2&hidden=16&patience=0&folds=2&gap=3")
    assert r.status_code == 200, r.text
    assert "p_value" in r.json()["pooled"]["n"] and "disclaimer" in r.json()
    assert c.post("/games/euromillions/walkforward?folds=99").status_code == 422
