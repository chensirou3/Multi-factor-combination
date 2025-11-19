"""
Out-of-Sample (OOS) backtest for Filter mode - Single symbol

TODO: This is a skeleton implementation for Filter mode OOS backtest.
The structure mirrors the Score mode OOS implementation but is not yet fully implemented.

To complete this implementation:
1. Implement generate_filter_param_grid() to create parameter combinations
2. Implement run_backtest_for_params() for Filter mode
3. Add core combo tracking for Filter mode (if applicable)
4. Test with actual data

Current status: SKELETON - NOT READY FOR PRODUCTION USE
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from itertools import product

from src.utils.config_loader import (
    load_oos_splits_config,
    load_joint_params_config,
    get_project_root
)
from src.utils.logging_utils import setup_logging, get_logger
from src.joint_data.loader import load_merged_4h_data
from src.joint_factors.joint_signals import generate_filter_signal, FilterSignalConfig
from src.backtest.engine_4h import run_simple_holding_backtest

# Setup logging
setup_logging()
logger = get_logger(__name__)


def generate_filter_param_grid(params_config: dict) -> list:
    """
    Generate parameter grid for Filter mode
    
    TODO: Implement this function based on filter_mode config
    
    Args:
        params_config: Joint parameters configuration
        
    Returns:
        List of parameter dictionaries
    """
    filter_params = params_config.get('filter_mode', {})
    
    ofi_max_list = filter_params.get('ofi_abs_z_max', [1.0])
    manip_entry_list = filter_params.get('manip_z_entry', [2.0])
    holding_bars_list = filter_params.get('holding_bars', [3])
    
    param_grid = []
    for ofi_max, manip_entry, hold_bars in product(ofi_max_list, manip_entry_list, holding_bars_list):
        param_grid.append({
            'ofi_abs_z_max': ofi_max,
            'manip_z_entry': manip_entry,
            'holding_bars': hold_bars,
        })
    
    logger.info(f"Generated {len(param_grid)} parameter combinations for Filter mode")
    return param_grid


def run_backtest_for_params(
    df: pd.DataFrame,
    params: dict,
    start_date: str = None,
    end_date: str = None,
) -> dict:
    """
    Run backtest for a single parameter set (Filter mode)
    
    TODO: Implement this function for Filter mode
    
    Args:
        df: Merged data DataFrame
        params: Parameter dictionary
        start_date: Start date for filtering
        end_date: End date for filtering
        
    Returns:
        Result dictionary with performance metrics
    """
    # Build signals using Filter mode
    config = FilterSignalConfig(
        ofi_abs_z_max=params['ofi_abs_z_max'],
        manip_z_entry=params['manip_z_entry'],
        direction='reversal',
        holding_bars=params['holding_bars'],
    )
    
    df_signals = generate_filter_signal(df, config)
    
    # Run backtest with date filtering
    result = run_simple_holding_backtest(
        df_signals,
        signal_col='signal',
        holding_bars=params['holding_bars'],
        start_date=start_date,
        end_date=end_date,
    )
    
    # Extract metrics
    stats = result.stats
    return {
        'ofi_abs_z_max': params['ofi_abs_z_max'],
        'manip_z_entry': params['manip_z_entry'],
        'holding_bars': params['holding_bars'],
        'sharpe': stats.get('sharpe_ratio', 0),
        'total_return': stats.get('total_return', 0),
        'win_rate': stats.get('win_rate', 0),
        'max_drawdown': stats.get('max_drawdown', 0),
        'n_trades': stats.get('n_trades', 0),
        'avg_return_per_trade': stats.get('avg_return_per_trade', 0),
    }


def run_oos_for_symbol(
    symbol: str,
    top_k: int = 20,
    sharpe_frac: float = 0.7,
    config_file: str = "joint_params_fine.yaml"
):
    """
    Run OOS backtest for a single symbol (Filter mode)
    
    TODO: Complete implementation following Score mode pattern
    
    Args:
        symbol: Symbol name
        top_k: Number of top parameters to select from train set
        sharpe_frac: Fraction of max Sharpe for plateau selection
        config_file: Parameter config file name
    """
    logger.warning("=" * 80)
    logger.warning("FILTER MODE OOS - SKELETON IMPLEMENTATION")
    logger.warning("This is not yet fully implemented!")
    logger.warning("=" * 80)
    
    # TODO: Implement full OOS workflow similar to Score mode
    # 1. Load configurations
    # 2. Load data
    # 3. Run train set backtest
    # 4. Select top parameters
    # 5. Run test set backtest
    # 6. Save results
    # 7. Generate summary
    
    logger.info(f"Symbol: {symbol}")
    logger.info(f"Config file: {config_file}")
    logger.info("Implementation pending...")


def main():
    parser = argparse.ArgumentParser(description="Run Filter mode OOS backtest for a single symbol (SKELETON)")
    parser.add_argument('--symbol', type=str, required=True, help='Symbol to backtest')
    parser.add_argument('--top_k', type=int, default=20, help='Number of top params to select from train')
    parser.add_argument('--sharpe_frac', type=float, default=0.7, help='Sharpe fraction for plateau selection')
    parser.add_argument('--config', type=str, default='joint_params_fine.yaml', help='Parameter config file')
    
    args = parser.parse_args()
    
    run_oos_for_symbol(
        symbol=args.symbol,
        top_k=args.top_k,
        sharpe_frac=args.sharpe_frac,
        config_file=args.config
    )


if __name__ == '__main__':
    main()

