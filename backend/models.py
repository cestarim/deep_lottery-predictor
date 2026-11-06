from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from backend.data_loader import MAIN_COLUMNS, RANGES, SECONDARY_COLUMNS


@dataclass
class ModelSpec:
    name: str
    display_name: str
    description: str
    status: str = "available"
    dependencies: list[str] = field(default_factory=list)


class LotteryModel:
    name = "base"
    description = "Modelo base para el proyecto."

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or self.name
        self.status = "ready"

    def fit(self, df: pd.DataFrame) -> dict[str, Any]:
        raise NotImplementedError("El modelo debe implementar fit().")

    def predict(self, df: pd.DataFrame) -> dict[str, Any]:
        raise NotImplementedError("El modelo debe implementar predict().")

    def evaluate(self, df: pd.DataFrame) -> dict[str, Any]:
        return {"status": "not_trained", "model": self.model_name, "message": "Aún no se ha entrenado el modelo."}


class FrequencyBaseline(LotteryModel):
    name = "frequency_baseline"
    description = "Línea base por frecuencia histórica para los números principales y secundarios."

    def fit(self, df: pd.DataFrame) -> dict[str, Any]:
        from backend.predictor import build_prediction

        return {"status": "ok", "model": self.name, "prediction": build_prediction(_infer_game(df), df)}

    def predict(self, df: pd.DataFrame) -> dict[str, Any]:
        from backend.predictor import build_prediction

        return build_prediction(_infer_game(df), df)

    def evaluate(self, df: pd.DataFrame) -> dict[str, Any]:
        prediction = self.predict(df)
        return {
            "status": "ok",
            "model": self.name,
            "prediction": prediction,
            "summary": "Línea base descriptiva; útil como referencia, no como predictor fiable en sorteos aleatorios.",
        }


class LSTMModel(LotteryModel):
    name = "lstm"
    description = "Estructura de referencia para aprendizaje secuencial sobre series de números."

    def __init__(self, model_name: str | None = None):
        super().__init__(model_name or self.name)
        try:
            import torch  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            self.status = "unavailable"
            self._missing_dependency = f"torch no disponible: {exc}"
        else:
            self._missing_dependency = None

    def fit(self, df: pd.DataFrame) -> dict[str, Any]:
        if self._missing_dependency:
            return {"status": "unavailable", "model": self.name, "message": self._missing_dependency}
        return {"status": "planned", "model": self.name, "message": "Pipeline de entrenamiento LSTM preparado para un CSV real con secuencias temporales."}

    def predict(self, df: pd.DataFrame) -> dict[str, Any]:
        return {"status": "planned", "model": self.name, "message": "Predicción LSTM pendiente de entrenar con datos reales."}


class GRUModel(LotteryModel):
    name = "gru"
    description = "Versión de red recurrente para secuencias temporales de resultados."

    def __init__(self, model_name: str | None = None):
        super().__init__(model_name or self.name)
        try:
            import torch  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            self.status = "unavailable"
            self._missing_dependency = f"torch no disponible: {exc}"
        else:
            self._missing_dependency = None

    def fit(self, df: pd.DataFrame) -> dict[str, Any]:
        if self._missing_dependency:
            return {"status": "unavailable", "model": self.name, "message": self._missing_dependency}
        return {"status": "planned", "model": self.name, "message": "Pipeline GRU listo para datos de series temporales."}

    def predict(self, df: pd.DataFrame) -> dict[str, Any]:
        return {"status": "planned", "model": self.name, "message": "Predicción GRU pendiente de entrenamiento con datos reales."}


class TransformerModel(LotteryModel):
    name = "transformer"
    description = "Arquitectura basada en atención para secuencias de sorteos.",

    def __init__(self, model_name: str | None = None):
        super().__init__(model_name or self.name)
        try:
            import torch  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            self.status = "unavailable"
            self._missing_dependency = f"torch no disponible: {exc}"
        else:
            self._missing_dependency = None

    def fit(self, df: pd.DataFrame) -> dict[str, Any]:
        if self._missing_dependency:
            return {"status": "unavailable", "model": self.name, "message": self._missing_dependency}
        return {"status": "planned", "model": self.name, "message": "Pipeline Transformer listo para adaptarse a secuencias temporales del dataset real."}

    def predict(self, df: pd.DataFrame) -> dict[str, Any]:
        return {"status": "planned", "model": self.name, "message": "Predicción Transformer pendiente de entrenamiento con datos reales."}


class CNNModel(LotteryModel):
    name = "cnn"
    description = "Modelo de convolución para aprender patrones sobre secuencias de datos estructurados."

    def __init__(self, model_name: str | None = None):
        super().__init__(model_name or self.name)
        try:
            import torch  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            self.status = "unavailable"
            self._missing_dependency = f"torch no disponible: {exc}"
        else:
            self._missing_dependency = None

    def fit(self, df: pd.DataFrame) -> dict[str, Any]:
        if self._missing_dependency:
            return {"status": "unavailable", "model": self.name, "message": self._missing_dependency}
        return {"status": "planned", "model": self.name, "message": "Pipeline CNN preparado para experimentos con ventanas temporales."}

    def predict(self, df: pd.DataFrame) -> dict[str, Any]:
        return {"status": "planned", "model": self.name, "message": "Predicción CNN pendiente de entrenamiento con datos reales."}


MODEL_SPECIFICATIONS = {
    "frequency_baseline": ModelSpec(
        name="frequency_baseline",
        display_name="Línea base por frecuencia",
        description="Método descriptivo basado en la frecuencia histórica de números.",
        status="available",
    ),
    "lstm": ModelSpec(
        name="lstm",
        display_name="LSTM",
        description="Red recurrente para secuencias temporales y ventanas de sorteos.",
        status="planned",
        dependencies=["torch"],
    ),
    "gru": ModelSpec(
        name="gru",
        display_name="GRU",
        description="Versión ligera de red recurrente para secuencias temporales.",
        status="planned",
        dependencies=["torch"],
    ),
    "transformer": ModelSpec(
        name="transformer",
        display_name="Transformer",
        description="Arquitectura de atención para observar patrones temporales.",
        status="planned",
        dependencies=["torch"],
    ),
    "cnn": ModelSpec(
        name="cnn",
        display_name="CNN",
        description="Red convolucional aplicada sobre secuencias de números y ventanas temporales.",
        status="planned",
        dependencies=["torch"],
    ),
}


def _infer_game(df: pd.DataFrame) -> str:
    columns = set(df.columns)
    if {"star_1", "star_2"}.issubset(columns):
        return "euromillions"
    if {"complementary", "reintegro"}.issubset(columns):
        return "bonoloto"
    raise ValueError("No se pudo inferir el juego a partir de las columnas del CSV.")


def get_available_models() -> dict[str, ModelSpec]:
    return MODEL_SPECIFICATIONS


def get_model_instance(model_name: str) -> LotteryModel:
    registry = {
        "frequency_baseline": FrequencyBaseline,
        "lstm": LSTMModel,
        "gru": GRUModel,
        "transformer": TransformerModel,
        "cnn": CNNModel,
    }
    try:
        return registry[model_name]()
    except KeyError as exc:
        raise ValueError(f"Modelo no soportado: {model_name}") from exc


__all__ = [
    "LotteryModel",
    "FrequencyBaseline",
    "LSTMModel",
    "GRUModel",
    "TransformerModel",
    "CNNModel",
    "ModelSpec",
    "MODEL_SPECIFICATIONS",
    "get_available_models",
    "get_model_instance",
]
