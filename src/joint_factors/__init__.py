"""
Joint factor module for multi-factor signal generation
"""

from .factor_registry import FactorRegistry, get_factor_registry
from .manip_view import get_manip_features
from .ofi_view import get_ofi_features
from .joint_signals import (
    generate_filter_signal,
    generate_score_signal,
    FilterSignalConfig,
    ScoreSignalConfig,
)

__all__ = [
    # Registry
    "FactorRegistry",
    "get_factor_registry",
    # Views
    "get_manip_features",
    "get_ofi_features",
    # Signals
    "generate_filter_signal",
    "generate_score_signal",
    "FilterSignalConfig",
    "ScoreSignalConfig",
]

