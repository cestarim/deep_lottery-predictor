from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, send_from_directory

from backend.backtest import run_frequency_backtest
from backend.data_loader import DataValidationError, get_game_summary, load_game
from backend.models import get_available_models, get_model_instance
from backend.predictor import build_prediction

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
app = Flask(__name__, static_folder=str(FRONTEND_DIR / "static"))


@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/api/health")
def health_check():
    return jsonify({"status": "ok", "project": "deep_lottery-predictor"})


@app.get("/api/models")
def model_catalog():
    return jsonify({
        "models": {
            name: {
                "display_name": spec.display_name,
                "description": spec.description,
                "status": spec.status,
                "dependencies": spec.dependencies,
            }
            for name, spec in get_available_models().items()
        }
    })


@app.get("/api/lottery/<game>")
def lottery_data(game: str):
    if game not in {"euromillions", "bonoloto"}:
        return jsonify({"error": "Juego no soportado. Usa euromillions o bonoloto."}), 404
    try:
        draws = load_game(game)
        latest = draws.iloc[-1].to_dict()
        latest["date"] = latest["date"].strftime("%Y-%m-%d")
        return jsonify({
            "game": game,
            "sample_data": True,
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
    if game not in {"euromillions", "bonoloto"}:
        return jsonify({"error": "Juego no soportado. Usa euromillions o bonoloto."}), 404
    try:
        draws = load_game(game)
        model = get_model_instance(model_name)
        if model_name == "frequency_baseline":
            result = model.predict(draws)
            return jsonify({"game": game, "model": model_name, "status": "ok", "result": result})
        return jsonify({
            "game": game,
            "model": model_name,
            "status": "planned",
            "message": "El modelo está preparado como referencia de arquitectura; requiere un CSV real y entrenamiento adicional.",
        })
    except (ValueError, FileNotFoundError, DataValidationError) as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
