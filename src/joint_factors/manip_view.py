"""
ManipScore factor view and derived features
"""

import pandas as pd
import numpy as np

from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


def get_manip_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract ManipScore-related features from merged DataFrame
    
    Args:
        df: Merged DataFrame with ManipScore columns
        
    Returns:
        DataFrame with ManipScore features
    """
    features = pd.DataFrame(index=df.index)
    
    # Raw ManipScore (if available)
    if 'ManipScore' in df.columns:
        features['ManipScore'] = df['ManipScore']
    
    # Standardized ManipScore
    if 'ManipScore_z' in df.columns:
        features['ManipScore_z'] = df['ManipScore_z']
    else:
        logger.warning("ManipScore_z not found in DataFrame")
        return features
    
    # Absolute z-score
    features['ManipScore_abs_z'] = features['ManipScore_z'].abs()
    
    # Extreme flags (high manipulation signal)
    features['is_extreme_manip'] = features['ManipScore_abs_z'] > 2.0
    features['is_very_extreme_manip'] = features['ManipScore_abs_z'] > 3.0
    
    # Direction flags
    features['is_positive_manip'] = features['ManipScore_z'] > 0
    features['is_negative_manip'] = features['ManipScore_z'] < 0
    
    # Quantile ranks
    features['ManipScore_rank'] = features['ManipScore_z'].rank(pct=True)
    
    # Rolling statistics (for regime detection)
    for window in [20, 50]:
        features[f'ManipScore_z_ma{window}'] = features['ManipScore_z'].rolling(window).mean()
        features[f'ManipScore_z_std{window}'] = features['ManipScore_z'].rolling(window).std()
    
    logger.debug(f"Extracted {len(features.columns)} ManipScore features")
    
    return features


def compute_manip_signal(
    df: pd.DataFrame,
    threshold: float = 2.0,
    direction: str = 'reversal',
) -> pd.Series:
    """
    Generate trading signal based on ManipScore
    
    Args:
        df: DataFrame with ManipScore_z
        threshold: Z-score threshold for signal
        direction: 'reversal' or 'continuation'
        
    Returns:
        Signal series: +1 (long), -1 (short), 0 (no position)
    """
    signal = pd.Series(0, index=df.index)
    
    if 'ManipScore_z' not in df.columns:
        logger.warning("ManipScore_z not found, returning zero signal")
        return signal
    
    manip_z = df['ManipScore_z']
    
    if direction == 'reversal':
        # High ManipScore → expect reversal → short
        # Low ManipScore → expect reversal → long
        signal[manip_z > threshold] = -1
        signal[manip_z < -threshold] = 1
    
    elif direction == 'continuation':
        # High ManipScore → expect continuation → long
        # Low ManipScore → expect continuation → short
        signal[manip_z > threshold] = 1
        signal[manip_z < -threshold] = -1
    
    else:
        raise ValueError(f"Unknown direction: {direction}")
    
    return signal

