"""
Out-of-Sample (OOS) backtest for Score mode - Single symbol

This script performs train/test split backtesting:
1. Load train/test time splits from config
2. Run full parameter grid on train set
3. Select top K parameters from train set
4. Evaluate selected parameters on test set
5. Save train and test results separately
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
from src.joint_factors.joint_signals import build_joint_score_signals
from src.backtest.engine_4h import run_simple_holding_backtest

# Setup logging
setup_logging()
logger = get_logger(__name__)


def generate_score_param_grid(params_config: dict) -> list:
    """
    Generate parameter grid for Score mode
    
    Args:
        params_config: Joint parameters configuration
        
    Returns:
        List of parameter dictionaries
    """
    score_params = params_config.get('score_mode', {})
    
    weights = score_params.get('weights', [[0.7, 0.3]])
    z_thresholds = score_params.get('composite_z_entry', [2.0])
    holding_bars_list = score_params.get('holding_bars', [3])
    
    param_grid = []
    for (w_manip, w_ofi), z_thresh, hold_bars in product(weights, z_thresholds, holding_bars_list):
        param_grid.append({
            'w_manip': w_manip,
            'w_ofi': w_ofi,
            'composite_z_entry': z_thresh,
            'holding_bars': hold_bars,
        })
    
    logger.info(f"Generated {len(param_grid)} parameter combinations for Score mode")
    return param_grid


def run_backtest_for_params(
    df: pd.DataFrame,
    params: dict,
    start_date: str = None,
    end_date: str = None,
) -> dict:
    """
    Run backtest for a single parameter set
    
    Args:
        df: Merged data DataFrame
        params: Parameter dictionary
        start_date: Start date for filtering
        end_date: End date for filtering
        
    Returns:
        Result dictionary with performance metrics
    """
    # Build signals
    df_signals = build_joint_score_signals(
        df,
        weight_manip=params['w_manip'],
        weight_ofi=params['w_ofi'],
        composite_z_entry=params['composite_z_entry'],
    )
    
    # Run backtest
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
        'w_manip': params['w_manip'],
        'w_ofi': params['w_ofi'],
        'composite_z_entry': params['composite_z_entry'],
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
    Run OOS backtest for a single symbol
    
    Args:
        symbol: Symbol name
        top_k: Number of top parameters to select from train set
        sharpe_frac: Fraction of max Sharpe for plateau selection
        config_file: Parameter config file name
    """
    logger.info(f"=" * 80)
    logger.info(f"Starting OOS backtest for {symbol}")
    logger.info(f"=" * 80)
    
    # Load configurations
    oos_config = load_oos_splits_config()
    params_config = load_joint_params_config(config_file)
    
    # Get time splits for this symbol
    if symbol not in oos_config['symbols']:
        raise ValueError(f"Symbol {symbol} not found in OOS splits config")
    
    splits = oos_config['symbols'][symbol]
    train_start = splits['train_start']
    train_end = splits['train_end']
    test_start = splits['test_start']
    test_end = splits['test_end']
    
    logger.info(f"Train period: {train_start} to {train_end}")
    logger.info(f"Test period: {test_start} to {test_end}")
    
    # Load data
    logger.info(f"Loading merged data for {symbol}...")
    df = load_merged_4h_data(symbol)
    logger.info(f"Loaded {len(df)} bars")
    
    # Generate parameter grid
    param_grid = generate_score_param_grid(params_config)
    
    # === TRAIN SET BACKTEST ===
    logger.info(f"\n{'='*80}")
    logger.info(f"TRAIN SET: Running {len(param_grid)} configurations...")
    logger.info(f"{'='*80}\n")

    train_results = []
    for i, params in enumerate(param_grid):
        if (i + 1) % 100 == 0:
            logger.info(f"Train progress: {i+1}/{len(param_grid)}")

        try:
            result = run_backtest_for_params(df, params, train_start, train_end)
            result['symbol'] = symbol
            result['timeframe'] = '4H'
            result['period'] = 'train'
            train_results.append(result)
        except Exception as e:
            logger.warning(f"Train backtest failed for params {params}: {e}")

    train_df = pd.DataFrame(train_results)

    # Save train results
    project_root = get_project_root()
    output_dir = project_root / "results" / "oos"
    output_dir.mkdir(parents=True, exist_ok=True)

    train_file = output_dir / f"score_oos_train_{symbol}_4H.csv"
    train_df.to_csv(train_file, index=False)
    logger.info(f"Saved train results to {train_file}")

    # === SELECT TOP PARAMETERS ===
    logger.info(f"\n{'='*80}")
    logger.info(f"Selecting top parameters from train set...")
    logger.info(f"{'='*80}\n")

    # Filter out invalid results
    valid_train = train_df[train_df['n_trades'] > 0].copy()

    if len(valid_train) == 0:
        logger.warning("No valid train results! Skipping test set.")
        return

    # Find max Sharpe
    max_sharpe = valid_train['sharpe'].max()
    logger.info(f"Train max Sharpe: {max_sharpe:.3f}")

    # Method 1: Top K by Sharpe
    top_k_params = valid_train.nlargest(top_k, 'sharpe')

    # Method 2: Plateau (Sharpe >= sharpe_frac * max_sharpe)
    sharpe_threshold = sharpe_frac * max_sharpe
    plateau_params = valid_train[valid_train['sharpe'] >= sharpe_threshold]

    logger.info(f"Top {top_k} params: Sharpe range [{top_k_params['sharpe'].min():.3f}, {top_k_params['sharpe'].max():.3f}]")
    logger.info(f"Plateau params (>= {sharpe_frac} * max): {len(plateau_params)} configs")

    # Use plateau if it's not too large, otherwise use top K
    if len(plateau_params) <= top_k * 2:
        candidate_params = plateau_params
        selection_method = 'plateau'
    else:
        candidate_params = top_k_params
        selection_method = 'top_k'

    logger.info(f"Selected {len(candidate_params)} candidate params using '{selection_method}' method")

    # === TEST SET BACKTEST ===
    logger.info(f"\n{'='*80}")
    logger.info(f"TEST SET: Running {len(candidate_params)} selected configurations...")
    logger.info(f"{'='*80}\n")

    test_results = []
    for i, row in candidate_params.iterrows():
        params = {
            'w_manip': row['w_manip'],
            'w_ofi': row['w_ofi'],
            'composite_z_entry': row['composite_z_entry'],
            'holding_bars': row['holding_bars'],
        }

        try:
            result = run_backtest_for_params(df, params, test_start, test_end)
            result['symbol'] = symbol
            result['timeframe'] = '4H'
            result['period'] = 'test'
            result['train_sharpe'] = row['sharpe']  # Track train performance
            test_results.append(result)
        except Exception as e:
            logger.warning(f"Test backtest failed for params {params}: {e}")

    test_df = pd.DataFrame(test_results)

    # Save test results
    test_file = output_dir / f"score_oos_test_{symbol}_4H.csv"
    test_df.to_csv(test_file, index=False)
    logger.info(f"Saved test results to {test_file}")

    # === CORE COMBO TRACKING ===
    logger.info(f"\n{'='*80}")
    logger.info(f"CORE COMBO TRACKING: w_manip=0.6, w_ofi=-0.3")
    logger.info(f"{'='*80}\n")

    # Define core combo parameters (find closest match in grid)
    core_w_manip = 0.6
    core_w_ofi = -0.3

    # Find all configs with core weights
    core_train = train_df[
        (train_df['w_manip'] == core_w_manip) &
        (train_df['w_ofi'] == core_w_ofi)
    ].copy()

    if len(core_train) > 0:
        logger.info(f"Found {len(core_train)} core combo configs in train set")

        # Run core combo on both train and test for all z/hold combinations
        core_combo_results = []

        for _, row in core_train.iterrows():
            params = {
                'w_manip': core_w_manip,
                'w_ofi': core_w_ofi,
                'composite_z_entry': row['composite_z_entry'],
                'holding_bars': row['holding_bars'],
            }

            # Train performance (already have it)
            train_result = {
                'symbol': symbol,
                'timeframe': '4H',
                'period': 'train',
                'w_manip': core_w_manip,
                'w_ofi': core_w_ofi,
                'composite_z_entry': row['composite_z_entry'],
                'holding_bars': row['holding_bars'],
                'sharpe': row['sharpe'],
                'total_return': row['total_return'],
                'win_rate': row['win_rate'],
                'n_trades': row['n_trades'],
            }
            core_combo_results.append(train_result)

            # Test performance
            try:
                test_result_dict = run_backtest_for_params(df, params, test_start, test_end)
                test_result_dict['symbol'] = symbol
                test_result_dict['timeframe'] = '4H'
                test_result_dict['period'] = 'test'
                core_combo_results.append(test_result_dict)
            except Exception as e:
                logger.warning(f"Core combo test failed for z={params['composite_z_entry']}, hold={params['holding_bars']}: {e}")

        # Save core combo results
        core_combo_df = pd.DataFrame(core_combo_results)
        core_file = output_dir / f"score_oos_core_combo_{symbol}_4H.csv"
        core_combo_df.to_csv(core_file, index=False)
        logger.info(f"Saved core combo results to {core_file}")

        # Summary of core combo
        core_train_results = core_combo_df[core_combo_df['period'] == 'train']
        core_test_results = core_combo_df[core_combo_df['period'] == 'test']

        if len(core_train_results) > 0 and len(core_test_results) > 0:
            logger.info(f"\nCore Combo (w_manip=0.6, w_ofi=-0.3) Summary:")
            logger.info(f"  Train - Best Sharpe: {core_train_results['sharpe'].max():.3f}, Mean: {core_train_results['sharpe'].mean():.3f}")
            logger.info(f"  Test  - Best Sharpe: {core_test_results['sharpe'].max():.3f}, Mean: {core_test_results['sharpe'].mean():.3f}")
            logger.info(f"  Test Sharpe > 0 ratio: {(core_test_results['sharpe'] > 0).sum() / len(core_test_results):.1%}")
    else:
        logger.warning(f"Core combo (0.6, -0.3) not found in parameter grid!")

    # === SUMMARY ===
    logger.info(f"\n{'='*80}")
    logger.info(f"OOS SUMMARY for {symbol}")
    logger.info(f"{'='*80}")
    logger.info(f"Train set:")
    logger.info(f"  Max Sharpe: {max_sharpe:.3f}")
    logger.info(f"  Mean Sharpe (all): {valid_train['sharpe'].mean():.3f}")
    logger.info(f"  Total configs: {len(valid_train)}")

    if len(test_df) > 0:
        valid_test = test_df[test_df['n_trades'] > 0]
        logger.info(f"\nTest set:")
        logger.info(f"  Max Sharpe: {valid_test['sharpe'].max():.3f}")
        logger.info(f"  Mean Sharpe: {valid_test['sharpe'].mean():.3f}")
        logger.info(f"  Sharpe > 0 ratio: {(valid_test['sharpe'] > 0).sum() / len(valid_test):.1%}")
        logger.info(f"  Total configs: {len(valid_test)}")

    logger.info(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description="Run Score mode OOS backtest for a single symbol")
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

