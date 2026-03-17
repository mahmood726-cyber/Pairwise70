"""
TruthCert Validation Module

Validation framework using real Cochrane meta-analysis data.
"""

from .gold_standard import GoldStandardLoader, GoldStandardEntry
from .validator import CochraneValidator, ValidationReport

__all__ = [
    "GoldStandardLoader",
    "GoldStandardEntry",
    "CochraneValidator",
    "ValidationReport",
]
