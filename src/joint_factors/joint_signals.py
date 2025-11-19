"""
Joint signal generation combining ManipScore and OFI

This module implements two main approaches:
1. Filter Mode: Use one factor to filter, another to generate signals
2. Score Mode: Combine factors into a weighted composite score
"""

from dataclasses import dataclass
from typing import Optional

import pandas as pd
import numpy as np

from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class FilterSignalConfig:
    """Configuration for filter mode signal generation"""
    # Filter settings (OFI)
    ofi_abs_z_max: float = 1.0  # Only trade when |OFI_z| < this
    
    # Signal settings (ManipScore)
    manip_z_entry: float = 2.0  # ManipScore threshold for entry
    
    # Direction logic
    direction: str = 'reversal'  # 'reversal' or 'continuation'
    
    # Holding period
    holding_bars: int = 3


@dataclass
class ScoreSignalConfig:
    """Configuration for score mode signal generation"""
    # Factor weights
    weight_manip: float = 0.7
    weight_ofi: float = 0.3
    
    # Composite score threshold
    composite_z_entry: float = 2.0
    
    # Direction logic
    direction: str = 'reversal'
    
    # Holding period
    holding_bars: int = 3


def generate_filter_signal(
    df: pd.DataFrame,
    config: FilterSignalConfig,
) -> pd.DataFrame:
    """
    Generate trading signals using filter mode
    
    Filter Mode Logic:
    1. Filter: Only trade when OFI is NOT extreme (|OFI_z| < threshold)
       - This filters out periods of extreme one-sided order flow
       - Hypothesis: Manipulation signals work better in balanced markets
    
    2. Signal: Use ManipScore for entry
       - High ManipScore → manipulation detected
       - Direction depends on config.direction:
         * 'reversal': High ManipScore → expect reversal → SHORT
         * 'continuation': High ManipScore → expect continuation → LONG
    
    Args:
        df: Merged DataFrame with ManipScore_z and OFI_z
        config: Filter signal configuration
        
    Returns:
        DataFrame with added signal columns
    """
    df = df.copy()
    
    # Check required columns
    required = ['ManipScore_z', 'OFI_z', 'OFI_abs_z']
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Initialize signal
    df['raw_signal'] = 0
    
    # Step 1: Apply OFI filter
    # Only consider periods with balanced order flow
    ofi_filter = df['OFI_abs_z'] < config.ofi_abs_z_max
    
    logger.info(
        f"OFI filter: {ofi_filter.sum()} / {len(df)} bars "
        f"({ofi_filter.sum()/len(df)*100:.1f}%) pass filter"
    )
    
    # Step 2: Generate ManipScore signals (only where filter passes)
    manip_z = df['ManipScore_z']
    
    if config.direction == 'reversal':
        # High ManipScore → expect reversal → short
        # Low ManipScore → expect reversal → long
        df.loc[ofi_filter & (manip_z > config.manip_z_entry), 'raw_signal'] = -1
        df.loc[ofi_filter & (manip_z < -config.manip_z_entry), 'raw_signal'] = 1
    
    elif config.direction == 'continuation':
        # High ManipScore → expect continuation → long
        # Low ManipScore → expect continuation → short
        df.loc[ofi_filter & (manip_z > config.manip_z_entry), 'raw_signal'] = 1
        df.loc[ofi_filter & (manip_z < -config.manip_z_entry), 'raw_signal'] = -1
    
    else:
        raise ValueError(f"Unknown direction: {config.direction}")
    
    # Step 3: Shift signal to avoid look-ahead bias
    df['signal'] = df['raw_signal'].shift(1).fillna(0)
    
    # Step 4: Add holding period logic (optional, for backtest)
    df['holding_bars'] = config.holding_bars
    
    n_signals = (df['signal'] != 0).sum()
    logger.info(
        f"Generated {n_signals} signals ({n_signals/len(df)*100:.2f}% of bars)"
    )

    return df


def generate_score_signal(
    df: pd.DataFrame,
    config: ScoreSignalConfig,
) -> pd.DataFrame:
    """
    Generate trading signals using score mode

    Score Mode Logic:
    1. Compute composite score as weighted combination:
       composite_z = w1 * ManipScore_z + w2 * OFI_z

    2. Generate signals based on composite score:
       - High composite_z → signal depends on direction
       - Direction logic:
         * 'reversal': High score → expect reversal → SHORT
         * 'continuation': High score → expect continuation → LONG

    3. Weight interpretation:
       - w_manip > 0, w_ofi > 0: Both factors reinforce
       - w_manip > 0, w_ofi < 0: Factors hedge each other
       - Example: w_manip=1.0, w_ofi=-0.5
         * High ManipScore + Low OFI → strong signal
         * High ManipScore + High OFI → weaker signal (OFI hedges)

    Args:
        df: Merged DataFrame with ManipScore_z and OFI_z
        config: Score signal configuration

    Returns:
        DataFrame with added signal columns
    """
    df = df.copy()

    # Check required columns
    required = ['ManipScore_z', 'OFI_z']
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Step 1: Compute composite score
    df['composite_z'] = (
        config.weight_manip * df['ManipScore_z'] +
        config.weight_ofi * df['OFI_z']
    )

    logger.info(
        f"Composite score: weights=({config.weight_manip:.2f}, {config.weight_ofi:.2f}), "
        f"mean={df['composite_z'].mean():.3f}, std={df['composite_z'].std():.3f}"
    )

    # Step 2: Initialize signal
    df['raw_signal'] = 0

    # Step 3: Generate signals based on composite score
    composite_z = df['composite_z']

    if config.direction == 'reversal':
        # High composite score → expect reversal → short
        # Low composite score → expect reversal → long
        df.loc[composite_z > config.composite_z_entry, 'raw_signal'] = -1
        df.loc[composite_z < -config.composite_z_entry, 'raw_signal'] = 1

    elif config.direction == 'continuation':
        # High composite score → expect continuation → long
        # Low composite score → expect continuation → short
        df.loc[composite_z > config.composite_z_entry, 'raw_signal'] = 1
        df.loc[composite_z < -config.composite_z_entry, 'raw_signal'] = -1

    else:
        raise ValueError(f"Unknown direction: {config.direction}")

    # Step 4: Shift signal to avoid look-ahead bias
    df['signal'] = df['raw_signal'].shift(1).fillna(0)

    # Step 5: Add holding period logic
    df['holding_bars'] = config.holding_bars

    n_signals = (df['signal'] != 0).sum()
    logger.info(
        f"Generated {n_signals} signals ({n_signals/len(df)*100:.2f}% of bars)"
    )

    return df


def generate_joint_signal_grid(
    df: pd.DataFrame,
    mode: str = 'filter',
    param_grid: dict = None,
) -> list[tuple[dict, pd.DataFrame]]:
    """
    Generate signals for a grid of parameters

    This is useful for parameter optimization and robustness testing.

    Args:
        df: Merged DataFrame
        mode: 'filter' or 'score'
        param_grid: Dictionary of parameter lists

    Returns:
        List of (params_dict, df_with_signals) tuples
    """
    if param_grid is None:
        # Default grid
        if mode == 'filter':
            param_grid = {
                'ofi_abs_z_max': [0.5, 1.0, 1.5],
                'manip_z_entry': [1.5, 2.0, 2.5],
                'holding_bars': [1, 2, 3, 5],
            }
        else:  # score
            param_grid = {
                'weight_manip': [1.0, 0.7, 0.5],
                'weight_ofi': [0.0, 0.3, 0.5],
                'composite_z_entry': [1.5, 2.0, 2.5],
                'holding_bars': [1, 2, 3, 5],
            }

    # Generate all combinations
    import itertools

    keys = list(param_grid.keys())
    values = list(param_grid.values())

    results = []

    for combination in itertools.product(*values):
        params = dict(zip(keys, combination))

        if mode == 'filter':
            config = FilterSignalConfig(**params)
            df_signals = generate_filter_signal(df.copy(), config)
        else:
            config = ScoreSignalConfig(**params)
            df_signals = generate_score_signal(df.copy(), config)

        results.append((params, df_signals))

    logger.info(f"Generated signals for {len(results)} parameter combinations")

    return results

