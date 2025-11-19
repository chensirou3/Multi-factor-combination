"""
Data loading and merging module for joint factor analysis
"""

from .loader import (
    load_ofi_4h,
    load_manip_4h,
    normalize_ofi_columns,
    normalize_manip_columns,
)
from .merger import (
    merge_manip_ofi,
    build_merged_for_symbol,
)
from .validators import (
    validate_data_quality,
    check_missing_rate,
    check_time_continuity,
    check_column_existence,
)

__all__ = [
    # Loader
    "load_ofi_4h",
    "load_manip_4h",
    "normalize_ofi_columns",
    "normalize_manip_columns",
    # Merger
    "merge_manip_ofi",
    "build_merged_for_symbol",
    # Validators
    "validate_data_quality",
    "check_missing_rate",
    "check_time_continuity",
    "check_column_existence",
]

