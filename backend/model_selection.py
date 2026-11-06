from __future__ import annotations

from typing import Any

from backend.data_loader import MAIN_COLUMNS, RANGES, SECONDARY_COLUMNS
from backend.models import get_model_instance


def validate_model_selection(model_name: str, game: str) -> dict[str, Any]:
    """Return metadata for the selected model and validate whether it is feasible for the current game."""
    model = get_model_instance(model_name)
    if game == "euromillions" and model_name in {"cnn", "transformer", "lstm", "gru"}:
        return {
            "status": "planned",
            "model": model_name,
            "game": game,
            "message": "Se preparará una pipeline temporal para EuroMillions con ventanas de datos y validación cruzada.",
        }
    if game == "bonoloto" and model_name in {"cnn", "transformer", "lstm", "gru"}:
        return {
            "status": "planned",
            "model": model_name,
            "game": game,
            "message": "Se preparará una pipeline temporal para Bonoloto con validación por historia y comparación con la referencia aleatoria.",
        }
    return {
        "status": "ok",
        "model": model_name,
        "game": game,
        "message": "La línea base está disponible para inspección y comparación.",
    }


__all__ = ["validate_model_selection"]
