from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, send_from_directory

from backend.data_loader import DataValidationError, get_game_summary, load_game
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


@app.get("/api/lottery/<game>")
def lottery_data(game: str):
    if game not in {"euromillions", "bonoloto"}:
        return jsonify({"error": "Juego no soportado. Usa euromillions o bonoloto."}), 404

    try:
        df = load_game(game)
        latest = df.iloc[-1].to_dict()
        latest["date"] = latest["date"].strftime("%Y-%m-%d")
        return jsonify({
            "game": game,
            "sample_data": True,
            "summary": get_game_summary(game, df),
            "latest_draw": latest,
            "prediction": build_prediction(game, df),
        })
    except (DataValidationError, FileNotFoundError, ValueError) as exc:
        app.logger.exception("No se pudieron cargar los datos de %s", game)
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
