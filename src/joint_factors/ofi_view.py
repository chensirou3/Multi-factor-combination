"""
OFI factor view and derived features
"""

import pandas as pd
import numpy as np

from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


def get_ofi_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract OFI-related features from merged DataFrame
    
    Args:
        df: Merged DataFrame with OFI columns
        
    Returns:
        DataFrame with OFI features
    """
    features = pd.DataFrame(index=df.index)
    
    # Raw OFI (if available)
    if 'OFI_raw' in df.columns:
        features['OFI_raw'] = df['OFI_raw']
    
    # Standardized OFI
    if 'OFI_z' in df.columns:
        features['OFI_z'] = df['OFI_z']
    else:
        logger.warning("OFI_z not found in DataFrame")
        return features
    
    # Absolute z-score
    if 'OFI_abs_z' in df.columns:
        features['OFI_abs_z'] = df['OFI_abs_z']
    else:
        features['OFI_abs_z'] = features['OFI_z'].abs()
    
    # Extreme flags (one-sided order flow)
    features['is_extreme_ofi'] = features['OFI_abs_z'] > 2.0
    features['is_very_extreme_ofi'] = features['OFI_abs_z'] > 3.0
    
    # Balanced order flow flag (for filtering)
    features['is_balanced_ofi'] = features['OFI_abs_z'] < 0.5
    features['is_moderate_ofi'] = features['OFI_abs_z'] < 1.0
    
    # Direction flags
    features['is_buying_pressure'] = features['OFI_z'] > 1.0
    features['is_selling_pressure'] = features['OFI_z'] < -1.0
    
    # Quantile ranks
    features['OFI_rank'] = features['OFI_z'].rank(pct=True)
    features['OFI_abs_rank'] = features['OFI_abs_z'].rank(pct=True)
    
    # Rolling statistics
    for window in [20, 50]:
        features[f'OFI_z_ma{window}'] = features['OFI_z'].rolling(window).mean()
        features[f'OFI_z_std{window}'] = features['OFI_z'].rolling(window).std()
        features[f'OFI_abs_z_ma{window}'] = features['OFI_abs_z'].rolling(window).mean()
    
    logger.debug(f"Extracted {len(features.columns)} OFI features")
    
    return features


def compute_ofi_signal(
    df: pd.DataFrame,
    threshold: float = 2.0,
    direction: str = 'momentum',
) -> pd.Series:
    """
    Generate trading signal based on OFI
    
    Args:
        df: DataFrame with OFI_z
        threshold: Z-score threshold for signal
        direction: 'momentum' or 'reversal'
        
    Returns:
        Signal series: +1 (long), -1 (short), 0 (no position)
    """
    signal = pd.Series(0, index=df.index)
    
    if 'OFI_z' not in df.columns:
        logger.warning("OFI_z not found, returning zero signal")
        return signal
    
    ofi_z = df['OFI_z']
    
    if direction == 'momentum':
        # Positive OFI → buying pressure → long
        # Negative OFI → selling pressure → short
        signal[ofi_z > threshold] = 1
        signal[ofi_z < -threshold] = -1
    
    elif direction == 'reversal':
        # Positive OFI → overbought → short
        # Negative OFI → oversold → long
        signal[ofi_z > threshold] = -1
        signal[ofi_z < -threshold] = 1
    
    else:
        raise ValueError(f"Unknown direction: {direction}")
    
    return signal

