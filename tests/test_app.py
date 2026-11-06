from __future__ import annotations

import io
import unittest

from app import app
from backend.backtest import run_frequency_backtest
from backend.data_loader import load_game
from backend.predictor import build_prediction


class LotteryAppTests(unittest.TestCase):
    def test_predictions_have_unique_numbers(self):
        for game, expected in (("euromillions", 5), ("bonoloto", 6)):
            with self.subTest(game=game):
                draws = load_game(game)
                result = build_prediction(game, draws)
                self.assertEqual(len(result["main_numbers"]), expected)
                self.assertEqual(len(set(result["main_numbers"])), expected)

    def test_backtest_has_random_reference_for_each_game(self):
        for game in ("euromillions", "bonoloto"):
            with self.subTest(game=game):
                result = run_frequency_backtest(game, load_game(game), min_train=2)
                self.assertGreater(result["test_draws"], 0)
                self.assertGreaterEqual(result["main_average_hits"], 0)
                self.assertGreater(result["main_random_expected_hits"], 0)
                self.assertGreaterEqual(result["secondary_average_hits"], 0)

    def test_web_routes_models_and_backtest_payload(self):
        client = app.test_client()
        self.assertEqual(client.get("/").status_code, 200)
        self.assertEqual(client.get("/api/health").status_code, 200)
        self.assertEqual(client.get("/api/models").status_code, 200)
        for game in ("euromillions", "bonoloto"):
            with self.subTest(game=game):
                response = client.get(f"/api/lottery/{game}")
                self.assertEqual(response.status_code, 200)
                self.assertIn("backtest", response.get_json())
        self.assertEqual(client.get("/api/lottery/not-a-game").status_code, 404)

    def test_upload_rejects_bad_csv_without_activating_it(self):
        client = app.test_client()
        response = client.post(
            "/api/lottery/euromillions/upload",
            data={"file": (io.BytesIO(b"date,foo\n2024-01-01,1\n"), "bad.csv")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Faltan columnas", response.get_json()["error"])

    def test_upload_requires_csv_file(self):
        response = app.test_client().post("/api/lottery/euromillions/upload")
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
