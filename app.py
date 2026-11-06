from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from backend.backtest import run_frequency_backtest
from backend.data_loader import (
    DataValidationError,
    UPLOAD_DIR,
    dataset_source,
    get_game_summary,
    load_game,
    validate_draws,
)
from backend.models import get_available_models, get_model_instance
from backend.predictor import build_prediction

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
app = Flask(__name__, static_folder=str(FRONTEND_DIR / "static"))
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
SUPPORTED_GAMES = {"euromillions", "bonoloto"}


@app.errorhandler(413)
def upload_too_large(_error):
    return jsonify({"error": "El CSV supera el límite de 5 MB."}), 413


@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/api/health")
def health_check():
    return jsonify({"status": "ok", "project": "deep_lottery-predictor"})


@app.get("/api/models")
def model_catalog():
    return jsonify({"models": {
        name: {
            "display_name": spec.display_name,
            "description": spec.description,
            "status": spec.status,
            "dependencies": spec.dependencies,
        }
        for name, spec in get_available_models().items()
    }})


@app.post("/api/lottery/<game>/upload")
def upload_draws(game: str):
    if game not in SUPPORTED_GAMES:
        return jsonify({"error": "Juego no soportado."}), 404
    uploaded_file = request.files.get("file")
    if uploaded_file is None or not uploaded_file.filename:
        return jsonify({"error": "Selecciona un archivo CSV."}), 400
    if not uploaded_file.filename.lower().endswith(".csv"):
        return jsonify({"error": "El archivo debe tener extensión .csv."}), 400
    try:
        parsed = __import__("pandas").read_csv(uploaded_file)
        validated = validate_draws(game, parsed, uploaded_file.filename)
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        target = UPLOAD_DIR / f"{game}.csv"
        # Save only after successful validation; use canonical column order.
        validated.assign(date=validated["date"].dt.strftime("%Y-%m-%d")).to_csv(target, index=False)
        return jsonify({
            "status": "uploaded",
            "game": game,
            "source": dataset_source(game),
            "summary": get_game_summary(game, validated),
            "message": "CSV validado y activado para este juego.",
        }), 201
    except (ValueError, DataValidationError, UnicodeDecodeError, OSError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/api/lottery/<game>")
def lottery_data(game: str):
    if game not in SUPPORTED_GAMES:
        return jsonify({"error": "Juego no soportado. Usa euromillions o bonoloto."}), 404
    try:
        draws = load_game(game)
        latest = draws.iloc[-1].to_dict()
        latest["date"] = latest["date"].strftime("%Y-%m-%d")
        return jsonify({
            "game": game,
            "sample_data": dataset_source(game) == "synthetic_sample",
            "summary": get_game_summary(game, draws),
            "latest_draw": latest,
            "prediction": build_prediction(game, draws),
            "backtest": run_frequency_backtest(game, draws),
            "models": {name: spec.display_name for name, spec in get_available_models().items()},
        })
    except (DataValidationError, FileNotFoundError, ValueError) as exc:
        app.logger.warning("No se pudieron cargar o evaluar los datos de %s: %s", game, exc)
        return jsonify({"error": str(exc)}), 500


@app.get("/api/lottery/<game>/model/<model_name>")
def model_run(game: str, model_name: str):
    if game not in SUPPORTED_GAMES:
        return jsonify({"error": "Juego no soportado."}), 404
    try:
        draws = load_game(game)
        model = get_model_instance(model_name)
        if model_name == "frequency_baseline":
            return jsonify({"game": game, "model": model_name, "status": "ok", "result": model.predict(draws)})
        return jsonify({
            "game": game,
            "model": model_name,
            "status": "planned",
            "message": "Este modelo aún no está implementado para entrenamiento ni predicción.",
        })
    except (ValueError, FileNotFoundError, DataValidationError) as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
