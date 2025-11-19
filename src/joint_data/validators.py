"""
Data quality validators
"""

from typing import Dict, Any, List

import pandas as pd
import numpy as np

from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


def check_missing_rate(
    df: pd.DataFrame,
    columns: List[str] = None,
    threshold: float = 0.2,
) -> Dict[str, Any]:
    """
    Check missing value rate for specified columns
    
    Args:
        df: DataFrame to check
        columns: Columns to check (default: all)
        threshold: Maximum allowed missing rate
        
    Returns:
        Validation result dict
    """
    if columns is None:
        columns = df.columns.tolist()
    
    missing_rates = {}
    for col in columns:
        if col in df.columns:
            missing_rate = df[col].isna().sum() / len(df)
            missing_rates[col] = missing_rate
    
    max_missing = max(missing_rates.values()) if missing_rates else 0
    
    if max_missing > threshold:
        worst_col = max(missing_rates, key=missing_rates.get)
        return {
            'status': 'FAIL',
            'message': f"High missing rate: {worst_col} = {missing_rates[worst_col]:.2%} (threshold: {threshold:.2%})",
            'details': missing_rates,
        }
    elif max_missing > threshold / 2:
        return {
            'status': 'WARNING',
            'message': f"Moderate missing rate: max = {max_missing:.2%}",
            'details': missing_rates,
        }
    else:
        return {
            'status': 'PASS',
            'message': f"Missing rate OK: max = {max_missing:.2%}",
            'details': missing_rates,
        }


def check_time_continuity(
    df: pd.DataFrame,
    expected_freq: str = '4H',
    tolerance: float = 0.1,
) -> Dict[str, Any]:
    """
    Check if time index is continuous
    
    Args:
        df: DataFrame with datetime index
        expected_freq: Expected frequency (e.g., '4H', '1D')
        tolerance: Allowed gap tolerance (fraction of expected)
        
    Returns:
        Validation result dict
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        return {
            'status': 'FAIL',
            'message': "Index is not DatetimeIndex",
            'details': {},
        }
    
    # Compute time differences
    time_diffs = df.index.to_series().diff()
    
    # Expected difference
    expected_diff = pd.Timedelta(expected_freq)
    
    # Find gaps
    gaps = time_diffs[time_diffs > expected_diff * (1 + tolerance)]
    
    if len(gaps) > 0:
        n_gaps = len(gaps)
        gap_rate = n_gaps / len(df)
        max_gap = gaps.max()
        
        if gap_rate > 0.05:  # More than 5% gaps
            return {
                'status': 'WARNING',
                'message': f"Found {n_gaps} gaps ({gap_rate:.2%}), max gap = {max_gap}",
                'details': {'n_gaps': n_gaps, 'max_gap': str(max_gap)},
            }
        else:
            return {
                'status': 'PASS',
                'message': f"Minor gaps: {n_gaps} gaps ({gap_rate:.2%})",
                'details': {'n_gaps': n_gaps, 'max_gap': str(max_gap)},
            }
    else:
        return {
            'status': 'PASS',
            'message': "Time index is continuous",
            'details': {},
        }


def check_column_existence(
    df: pd.DataFrame,
    required_columns: List[str],
) -> Dict[str, Any]:
    """
    Check if required columns exist
    
    Args:
        df: DataFrame to check
        required_columns: List of required column names
        
    Returns:
        Validation result dict
    """
    missing_cols = [col for col in required_columns if col not in df.columns]
    
    if missing_cols:
        return {
            'status': 'FAIL',
            'message': f"Missing required columns: {missing_cols}",
            'details': {'missing': missing_cols},
        }
    else:
        return {
            'status': 'PASS',
            'message': f"All {len(required_columns)} required columns present",
            'details': {},
        }


def validate_data_quality(
    df: pd.DataFrame,
    timeframe: str = '4H',
) -> Dict[str, Dict[str, Any]]:
    """
    Run all data quality checks
    
    Args:
        df: DataFrame to validate
        timeframe: Expected timeframe
        
    Returns:
        Dictionary of validation results
    """
    results = {}
    
    # Check required columns
    required_cols = ['open', 'high', 'low', 'close', 'ManipScore_z', 'OFI_z']
    results['required_columns'] = check_column_existence(df, required_cols)
    
    # Check missing rates for key columns
    key_cols = ['ManipScore_z', 'OFI_z', 'OFI_abs_z', 'close']
    results['missing_rate'] = check_missing_rate(df, key_cols, threshold=0.2)
    
    # Check time continuity
    results['time_continuity'] = check_time_continuity(df, expected_freq=timeframe)
    
    # Check for duplicates
    n_duplicates = df.index.duplicated().sum()
    if n_duplicates > 0:
        results['duplicates'] = {
            'status': 'FAIL',
            'message': f"Found {n_duplicates} duplicate timestamps",
            'details': {'n_duplicates': n_duplicates},
        }
    else:
        results['duplicates'] = {
            'status': 'PASS',
            'message': "No duplicate timestamps",
            'details': {},
        }
    
    return results

