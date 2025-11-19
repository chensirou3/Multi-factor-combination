"""
Out-of-Sample (OOS) Plateau Analysis

This module provides functions to analyze parameter robustness by examining
"plateau regions" - parameter sets that perform well in training and their
stability in testing.

The key insight: A single "best" parameter may be overfit. A robust strategy
should have a plateau of good parameters that maintain performance OOS.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional

from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


def analyze_plateau_stability(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    sharpe_frac: float = 0.7,
    sharpe_thresholds: list = [0.0, 0.3, 0.5]
) -> Dict:
    """
    Analyze stability of parameter plateau from train to test
    
    The "plateau" is defined as parameters with Sharpe >= sharpe_frac * max_sharpe_train.
    We then examine how these parameters perform in the test set.
    
    Args:
        train_df: Training set results DataFrame
        test_df: Test set results DataFrame (should contain same params as plateau)
        sharpe_frac: Fraction of max Sharpe to define plateau (default: 0.7)
        sharpe_thresholds: List of Sharpe thresholds to compute ratios for
        
    Returns:
        Dictionary with plateau analysis metrics
    """
    logger.info(f"Analyzing plateau stability (sharpe_frac={sharpe_frac})")
    
    # Filter valid results (must have trades)
    valid_train = train_df[train_df['n_trades'] > 0].copy()
    valid_test = test_df[test_df['n_trades'] > 0].copy()
    
    if len(valid_train) == 0:
        logger.warning("No valid train results!")
        return {'error': 'no_valid_train_results'}
    
    if len(valid_test) == 0:
        logger.warning("No valid test results!")
        return {'error': 'no_valid_test_results'}
    
    # Find train plateau
    max_sharpe_train = valid_train['sharpe'].max()
    sharpe_threshold = sharpe_frac * max_sharpe_train
    
    plateau_train = valid_train[valid_train['sharpe'] >= sharpe_threshold].copy()
    
    logger.info(f"Train max Sharpe: {max_sharpe_train:.3f}")
    logger.info(f"Plateau threshold: {sharpe_threshold:.3f}")
    logger.info(f"Plateau size: {len(plateau_train)} / {len(valid_train)} configs")
    
    # Match plateau params in test set
    # Create param signature for matching
    param_cols = ['w_manip', 'w_ofi', 'composite_z_entry', 'holding_bars']
    
    # Ensure all param columns exist
    for col in param_cols:
        if col not in plateau_train.columns or col not in valid_test.columns:
            logger.warning(f"Missing parameter column: {col}")
            return {'error': f'missing_column_{col}'}
    
    # Create unique key for matching
    plateau_train['param_key'] = plateau_train[param_cols].apply(
        lambda row: f"{row['w_manip']}_{row['w_ofi']}_{row['composite_z_entry']}_{row['holding_bars']}",
        axis=1
    )
    valid_test['param_key'] = valid_test[param_cols].apply(
        lambda row: f"{row['w_manip']}_{row['w_ofi']}_{row['composite_z_entry']}_{row['holding_bars']}",
        axis=1
    )
    
    # Get plateau params in test set
    plateau_keys = set(plateau_train['param_key'])
    plateau_test = valid_test[valid_test['param_key'].isin(plateau_keys)].copy()
    
    if len(plateau_test) == 0:
        logger.warning("No plateau params found in test set!")
        return {'error': 'no_plateau_in_test'}
    
    logger.info(f"Matched {len(plateau_test)} plateau params in test set")
    
    # Compute plateau test statistics
    plateau_test_sharpe = plateau_test['sharpe']
    
    analysis = {
        # Train metrics
        'train_max_sharpe': max_sharpe_train,
        'train_mean_sharpe': valid_train['sharpe'].mean(),
        'train_median_sharpe': valid_train['sharpe'].median(),
        'train_total_configs': len(valid_train),
        
        # Plateau train metrics
        'plateau_threshold': sharpe_threshold,
        'plateau_size': len(plateau_train),
        'plateau_train_mean_sharpe': plateau_train['sharpe'].mean(),
        'plateau_train_median_sharpe': plateau_train['sharpe'].median(),
        
        # Plateau test metrics
        'plateau_test_size': len(plateau_test),
        'plateau_test_mean_sharpe': plateau_test_sharpe.mean(),
        'plateau_test_median_sharpe': plateau_test_sharpe.median(),
        'plateau_test_std_sharpe': plateau_test_sharpe.std(),
        'plateau_test_min_sharpe': plateau_test_sharpe.min(),
        'plateau_test_max_sharpe': plateau_test_sharpe.max(),
        
        # Percentiles
        'plateau_test_p25_sharpe': plateau_test_sharpe.quantile(0.25),
        'plateau_test_p75_sharpe': plateau_test_sharpe.quantile(0.75),
        
        # Stability ratios
        'plateau_test_sharpe_gt0_ratio': (plateau_test_sharpe > 0).sum() / len(plateau_test),
    }
    
    # Add threshold-based ratios
    for thresh in sharpe_thresholds:
        ratio = (plateau_test_sharpe > thresh).sum() / len(plateau_test)
        analysis[f'plateau_test_sharpe_gt{thresh}_ratio'] = ratio
    
    # Degradation metrics
    analysis['sharpe_degradation_mean'] = (
        plateau_train['sharpe'].mean() - plateau_test_sharpe.mean()
    )
    analysis['sharpe_degradation_median'] = (
        plateau_train['sharpe'].median() - plateau_test_sharpe.median()
    )
    
    # Log summary
    logger.info(f"\nPlateau Test Performance:")
    logger.info(f"  Mean Sharpe: {analysis['plateau_test_mean_sharpe']:.3f}")
    logger.info(f"  Median Sharpe: {analysis['plateau_test_median_sharpe']:.3f}")
    logger.info(f"  Sharpe > 0 ratio: {analysis['plateau_test_sharpe_gt0_ratio']:.1%}")
    logger.info(f"  Sharpe degradation (mean): {analysis['sharpe_degradation_mean']:.3f}")
    
    return analysis


def compare_single_best_vs_plateau(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    sharpe_frac: float = 0.7
) -> Dict:
    """
    Compare single best parameter vs plateau approach
    
    Args:
        train_df: Training set results
        test_df: Test set results
        sharpe_frac: Plateau threshold fraction
        
    Returns:
        Comparison metrics dictionary
    """
    valid_train = train_df[train_df['n_trades'] > 0].copy()
    valid_test = test_df[test_df['n_trades'] > 0].copy()
    
    if len(valid_train) == 0 or len(valid_test) == 0:
        return {'error': 'insufficient_data'}
    
    # Find single best param in train
    best_train_idx = valid_train['sharpe'].idxmax()
    best_train_params = valid_train.loc[best_train_idx]
    
    # Create param key
    param_cols = ['w_manip', 'w_ofi', 'composite_z_entry', 'holding_bars']
    best_key = f"{best_train_params['w_manip']}_{best_train_params['w_ofi']}_" \
               f"{best_train_params['composite_z_entry']}_{best_train_params['holding_bars']}"
    
    # Find same param in test
    valid_test['param_key'] = valid_test[param_cols].apply(
        lambda row: f"{row['w_manip']}_{row['w_ofi']}_{row['composite_z_entry']}_{row['holding_bars']}",
        axis=1
    )
    
    best_test = valid_test[valid_test['param_key'] == best_key]
    
    # Get plateau analysis
    plateau_analysis = analyze_plateau_stability(train_df, test_df, sharpe_frac)
    
    comparison = {
        'best_train_sharpe': best_train_params['sharpe'],
        'best_test_sharpe': best_test['sharpe'].iloc[0] if len(best_test) > 0 else np.nan,
        'plateau_mean_test_sharpe': plateau_analysis.get('plateau_test_mean_sharpe', np.nan),
        'plateau_median_test_sharpe': plateau_analysis.get('plateau_test_median_sharpe', np.nan),
    }
    
    return comparison

