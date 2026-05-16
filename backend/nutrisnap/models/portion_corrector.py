"""Portion Corrector — XGBoost residual corrector for mass estimation.

Learns systematic biases in the EfficientNetRegressor + VolumeEstimator pipeline.
Takes depth statistics as additional input signals beyond the raw mass prediction.

Architecture:
    Input features → XGBoost → corrected_mass_g

Input features (all from existing pipeline, zero new sensors):
    - predicted_mass_g   : raw EfficientNet / density-based mass estimate
    - volume_cm3         : ConvexHull volume result (normalized units scaled)
    - volume_type_enc    : 0=convex, 1=flat, 2=concave
    - depth_mean         : mean of masked depth pixels [0, 1]
    - depth_std          : std dev of masked depth pixels
    - depth_skew         : skewness of masked depth distribution
    - depth_p25          : 25th percentile of masked depth
    - depth_p75          : 75th percentile of masked depth
    - mask_pixel_ratio   : fraction of image covered by food mask

Output: corrected_mass_g (scalar, in grams)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np

from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

# Default path relative to repo root
_DEFAULT_MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "portion_corrector.joblib"

_FEATURE_ORDER = [
    "predicted_mass_g",
    "volume_cm3",
    "volume_type_enc",
    "depth_mean",
    "depth_std",
    "depth_skew",
    "depth_p25",
    "depth_p75",
    "mask_pixel_ratio",
]

_VOLUME_TYPE_ENCODING = {
    "convex": 0,
    "concave": 2,
    "flat": 1,
    "simple": 0,
    "unknown": 0,
}


class PortionCorrector:
    """XGBoost residual corrector for food mass estimation.

    Falls back to a passthrough (identity) if no trained model is found,
    so the rest of the pipeline is never broken by a missing checkpoint.

    Usage::

        corrector = PortionCorrector()
        corrected_mass = corrector.predict(
            predicted_mass_g=350.0,
            volume_cm3=280.0,
            volume_type="convex",
            depth_features={
                "depth_mean": 0.42,
                "depth_std": 0.08,
                "depth_skew": 0.3,
                "depth_p25": 0.36,
                "depth_p75": 0.49,
                "mask_pixel_ratio": 0.18,
            },
        )
    """

    def __init__(self, model_path: str | Path | None = None) -> None:
        self._model: Any = None
        self._loaded = False

        path = Path(model_path) if model_path else _DEFAULT_MODEL_PATH
        env_override = os.getenv("PORTION_CORRECTOR_PATH")
        if env_override:
            path = Path(env_override)

        self._model_path = path
        self._try_load(path)

    def _try_load(self, path: Path) -> None:
        """Attempt to load a trained corrector. Silently no-ops if missing."""
        if not path.exists():
            logger.info(
                f"PortionCorrector: no checkpoint at {path}. "
                "Running in passthrough mode (raw mass returned unchanged). "
                "Train with: python -m nutrisnap.training.train_portion_corrector"
            )
            return

        try:
            import joblib  # noqa: PLC0415

            self._model = joblib.load(path)
            self._loaded = True
            logger.info(f"PortionCorrector loaded from {path}")
        except Exception as exc:
            logger.warning(f"PortionCorrector load failed ({exc}). Passthrough mode active.")

    @property
    def is_trained(self) -> bool:
        """True if a model is loaded and corrections will be applied."""
        return self._loaded and self._model is not None

    def _build_feature_vector(
        self,
        predicted_mass_g: float,
        volume_cm3: float,
        volume_type: str,
        depth_features: dict[str, float],
    ) -> np.ndarray:
        """Build a (1, 9) feature matrix in the expected column order."""
        enc = _VOLUME_TYPE_ENCODING.get(volume_type.lower(), 0)
        row = [
            predicted_mass_g,
            volume_cm3,
            float(enc),
            depth_features.get("depth_mean", 0.5),
            depth_features.get("depth_std", 0.0),
            depth_features.get("depth_skew", 0.0),
            depth_features.get("depth_p25", 0.5),
            depth_features.get("depth_p75", 0.5),
            depth_features.get("mask_pixel_ratio", 0.1),
        ]
        return np.array([row], dtype=np.float32)

    def predict(
        self,
        predicted_mass_g: float,
        volume_cm3: float = 0.0,
        volume_type: str = "convex",
        depth_features: dict[str, float] | None = None,
    ) -> float:
        """Return corrected mass in grams.

        Args:
            predicted_mass_g: Raw mass from EfficientNet / density pipeline.
            volume_cm3:        ConvexHull volume (normalized units).
            volume_type:       Volume estimation method ("convex", "flat", "concave").
            depth_features:    Dict from VolumeEstimator.extract_depth_features().

        Returns:
            Corrected mass in grams. Same as input if no model is loaded.
        """
        if not self.is_trained:
            return float(predicted_mass_g)

        depth_features = depth_features or {}
        X = self._build_feature_vector(predicted_mass_g, volume_cm3, volume_type, depth_features)

        try:
            corrected = float(self._model.predict(X)[0])
            # Sanity clamp: never return negative or absurdly large mass
            corrected = max(1.0, min(corrected, 5000.0))
            logger.debug(
                f"PortionCorrector: {predicted_mass_g:.1f}g → {corrected:.1f}g "
                f"(Δ={corrected - predicted_mass_g:+.1f}g)"
            )
            return corrected
        except Exception as exc:
            logger.warning(f"PortionCorrector.predict failed ({exc}). Returning raw estimate.")
            return float(predicted_mass_g)


# Module-level singleton so the model loads once per process
_default_corrector: PortionCorrector | None = None


def get_default_corrector() -> PortionCorrector:
    """Return (and lazily initialize) the module-level PortionCorrector singleton."""
    global _default_corrector  # noqa: PLW0603
    if _default_corrector is None:
        _default_corrector = PortionCorrector()
    return _default_corrector
