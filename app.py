from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, send_from_directory

from backend.data_loader import get_game_summary, load_game
from backend.predictor import build_prediction

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(__name__, static_folder=str(FRONTEND_DIR / "static"), template_folder=str(FRONTEND_DIR))


@app.get("/")
def index():
    return send_from_directory(str(FRONTEND_DIR), "index.html")


@app.get("/api/health")
def health_check():
    return jsonify({
        "status": "ok",
        "project": "deep_lottery-predictor",
        "games": ["euromillions", "bonoloto"],
    })


@app.get("/api/lottery/<game>")
def lottery_data(game: str):
    allowed_games = {"euromillions", "bonoloto"}
    if game not in allowed_games:
        return jsonify({"error": "Juego no soportado."}), 400

    df = load_game(game)
    latest_draw = df.iloc[-1].to_dict()
    return jsonify({
        "game": game,
        "summary": get_game_summary(game),
        "latest_draw": latest_draw,
        "prediction": build_prediction(game),
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
