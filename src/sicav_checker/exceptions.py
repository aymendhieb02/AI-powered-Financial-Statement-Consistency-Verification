from __future__ import annotations


class FinVerifyError(Exception):
    """Base class for expected FinVerify application errors."""


class ExtractionError(FinVerifyError):
    """Raised when a PDF cannot be extracted into a financial document."""


class NormalizationError(FinVerifyError):
    """Raised when extracted content cannot be normalized."""


class ValidationError(FinVerifyError):
    """Raised when validation cannot be completed."""


class ComparisonError(FinVerifyError):
    """Raised when cross-year comparison cannot be completed."""


class StorageError(FinVerifyError):
    """Raised when persistence fails."""


class ReportingError(FinVerifyError):
    """Raised when report generation fails."""