import unittest

from app import app
from backend.backtest import run_frequency_backtest
from backend.data_loader import load_game
from backend.predictor import build_prediction


class LotteryAppTests(unittest.TestCase):
    def test_sample_data_and_prediction(self):
        for game, expected_count in (("euromillions", 5), ("bonoloto", 6)):
            with self.subTest(game=game):
                draws = load_game(game)
                prediction = build_prediction(game, draws)
                self.assertGreater(len(draws), 0)
                self.assertEqual(len(prediction["main_numbers"]), expected_count)
                self.assertEqual(len(set(prediction["main_numbers"])), expected_count)

    def test_backtest_runs_for_both_games(self):
        for game in ("euromillions", "bonoloto"):
            with self.subTest(game=game):
                result = run_frequency_backtest(game, load_game(game), min_train=2)
                self.assertGreater(result["test_draws"], 0)
                self.assertGreaterEqual(result["main_average_hits"], 0)
                self.assertGreaterEqual(result["secondary_average_hits"], 0)
                if game == "bonoloto":
                    self.assertIn("reintegro_average_hits", result)

    def test_api_routes(self):
        client = app.test_client()
        self.assertEqual(client.get("/api/health").status_code, 200)
        self.assertEqual(client.get("/").status_code, 200)
        for game in ("euromillions", "bonoloto"):
            with self.subTest(game=game):
                response = client.get(f"/api/lottery/{game}")
                self.assertEqual(response.status_code, 200)
                payload = response.get_json()
                self.assertTrue(payload["sample_data"])
                self.assertIn("backtest", payload)
        self.assertEqual(client.get("/api/lottery/unknown").status_code, 404)


if __name__ == "__main__":
    unittest.main()
