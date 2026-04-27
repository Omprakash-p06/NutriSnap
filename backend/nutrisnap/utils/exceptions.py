"""Custom exception classes for NutriSnap."""


class NutriSnapError(Exception):
    """Base exception for NutriSnap errors."""


class DataAuditError(NutriSnapError):
    """Raised when dataset audit detects critical issues."""


class ConfigError(NutriSnapError):
    """Raised when configuration loading or validation fails."""


class InferenceError(NutriSnapError):
    """Raised when pipeline inference fails."""


class SegmentationError(InferenceError):
    """Raised when food segmentation fails."""
