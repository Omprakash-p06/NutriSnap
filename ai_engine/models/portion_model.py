"""Portion Estimation Model Wrapper.

Wrapper for XGBoost portion size estimation model.
"""

import os
from typing import Any

import numpy as np


class PortionModel:
    """Wrapper for XGBoost portion estimation model.

    Attributes:
        model_path: Path to saved model file.
        model: Loaded XGBoost model.
    """

    def __init__(
        self,
        model_path: str = "./ml/weights/portion_model.joblib",
    ) -> None:
        """Initialize portion model wrapper.

        Args:
            model_path: Path to XGBoost model file.
        """
        self.model_path = model_path
        self._model = None

    @property
    def model(self) -> Any:
        """Lazy load XGBoost model."""
        if self._model is None:
            self._load_model()
        return self._model

    def _load_model(self) -> None:
        """Load XGBoost model from file."""
        if not os.path.exists(self.model_path):
            self._model = None
            return

        try:
            import joblib  # pylint: disable=import-outside-toplevel

            self._model = joblib.load(self.model_path)
        except (ImportError, Exception):  # pylint: disable=broad-exception-caught
            self._model = None

    def predict(self, features: np.ndarray) -> float:
        """Predict portion size from features.

        Args:
            features: Feature array from bounding box.

        Returns:
            Predicted portion size in grams.
        """
        if self.model is None:
            return 100.0  # Default medium portion

        if features.ndim == 1:
            features = features.reshape(1, -1)

        prediction = self.model.predict(features)
        return max(10.0, float(prediction[0]))

    def is_loaded(self) -> bool:
        """Check if model is loaded.

        Returns:
            True if model is loaded, False otherwise.
        """
        return self.model is not None
