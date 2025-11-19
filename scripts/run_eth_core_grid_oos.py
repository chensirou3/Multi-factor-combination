"""
ETH Core Strategy: Grid Search + OOS Validation

This script implements the simplified ETH core strategy with:
- Fixed weights (w_manip=0.6, w_ofi=-0.3)
- Grid search over (z_threshold, hold_bars)
- Train/test split for OOS validation
- Plateau-based parameter selection
"""

import sys
from pathlib import Path
from itertools import product
from typing import List, Dict, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
import yaml

from src.utils.logging_utils import get_logger
from src.utils.config_loader import get_project_root
from src.joint_data.loader import load_merged_4h_data
from src.joint_factors.joint_signals import build_eth_core_joint_score_signals
from src.backtest.engine_4h import run_backtest_4h, subset_df_by_date

logger = get_logger(__name__)


def load_eth_core_config() -> Dict:
    """Load ETH core strategy configuration"""
    project_root = get_project_root()
    config_path = project_root / "config" / "eth_core_params.yaml"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"Loaded ETH core config from {config_path}")
    return config


def run_train_grid_search(
    df_train: pd.DataFrame,
    config: Dict
) -> pd.DataFrame:
    """
    Run grid search on training set
    
    Args:
        df_train: Training set DataFrame
        config: Configuration dictionary
    
    Returns:
        DataFrame with training results for all parameter combinations
    """
    logger.info("=" * 80)
    logger.info("TRAINING SET GRID SEARCH")
    logger.info("=" * 80)
    
    # Extract parameters
    w_manip = config['w_manip']
    w_ofi = config['w_ofi']
    z_threshold_list = config['z_threshold_list']
    hold_bars_list = config['hold_bars_list']
    cost_bps = config.get('cost_bps', 5.0)
    
    # Generate all parameter combinations
    param_combinations = list(product(z_threshold_list, hold_bars_list))
    total_configs = len(param_combinations)
    
    logger.info(f"Total configurations: {total_configs}")
    logger.info(f"Fixed weights: w_manip={w_manip}, w_ofi={w_ofi}")
    logger.info(f"Z-threshold range: {z_threshold_list}")
    logger.info(f"Hold bars range: {hold_bars_list}")
    logger.info(f"Training set size: {len(df_train)} bars")
    
    results = []
    
    for idx, (z_threshold, hold_bars) in enumerate(param_combinations, 1):
        if idx % 5 == 0 or idx == 1:
            logger.info(f"Train progress: {idx}/{total_configs} ({100*idx/total_configs:.1f}%)")
        
        try:
            # Generate signals
            df_signals = build_eth_core_joint_score_signals(
                df_train,
                w_manip=w_manip,
                w_ofi=w_ofi,
                z_threshold=z_threshold
            )
            
            # Run backtest
            # TODO: Verify backtest function signature matches your implementation
            backtest_result = run_backtest_4h(
                df_signals,
                signal_col='signal_eth_core',
                holding_bars=hold_bars,
                cost_bps=cost_bps
            )
            
            # Store results
            results.append({
                'z_threshold': z_threshold,
                'hold_bars': hold_bars,
                'sharpe': backtest_result.get('sharpe', 0.0),
                'total_return': backtest_result.get('total_return', 0.0),
                'max_drawdown': backtest_result.get('max_drawdown', 0.0),
                'win_rate': backtest_result.get('win_rate', 0.0),
                'n_trades': backtest_result.get('n_trades', 0),
                'avg_return': backtest_result.get('avg_return', 0.0),
            })
            
        except Exception as e:
            logger.warning(f"Train backtest failed for z={z_threshold}, hold={hold_bars}: {e}")
            results.append({
                'z_threshold': z_threshold,
                'hold_bars': hold_bars,
                'sharpe': 0.0,
                'total_return': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'n_trades': 0,
                'avg_return': 0.0,
            })
    
    df_results = pd.DataFrame(results)
    logger.info(f"Training grid search completed: {len(df_results)} configurations")
    
    return df_results


def select_plateau_params(
    df_train_results: pd.DataFrame,
    config: Dict
) -> List[Tuple[float, int]]:
    """
    Select parameters from plateau region
    
    Args:
        df_train_results: Training results DataFrame
        config: Configuration dictionary
    
    Returns:
        List of (z_threshold, hold_bars) tuples in plateau
    """
    min_trades = config.get('min_trades_train', 50)
    plateau_frac = config.get('plateau_sharpe_frac', 0.7)
    top_k = config.get('top_k', 10)
    strategy = config.get('selection_strategy', 'adaptive')
    
    # Filter by minimum trades
    valid_results = df_train_results[df_train_results['n_trades'] >= min_trades].copy()
    
    if len(valid_results) == 0:
        logger.warning(f"No configurations with >= {min_trades} trades!")
        return []
    
    logger.info(f"Configurations with >= {min_trades} trades: {len(valid_results)}/{len(df_train_results)}")
    
    # Find max Sharpe
    max_sharpe = valid_results['sharpe'].max()
    plateau_threshold = plateau_frac * max_sharpe
    
    logger.info(f"Max Sharpe in train: {max_sharpe:.3f}")
    logger.info(f"Plateau threshold ({plateau_frac:.0%} × max): {plateau_threshold:.3f}")
    
    # Get plateau region
    plateau_results = valid_results[valid_results['sharpe'] >= plateau_threshold]
    
    logger.info(f"Plateau size: {len(plateau_results)} configurations")
    
    # Apply selection strategy
    if strategy == 'plateau':
        selected = plateau_results
    elif strategy == 'top_k':
        selected = valid_results.nlargest(top_k, 'sharpe')
    elif strategy == 'adaptive':
        if len(plateau_results) <= 2 * top_k:
            selected = plateau_results
            logger.info(f"Using plateau (size {len(plateau_results)} <= 2×{top_k})")
        else:
            selected = valid_results.nlargest(top_k, 'sharpe')
            logger.info(f"Using top {top_k} (plateau too large: {len(plateau_results)})")
    else:
        raise ValueError(f"Unknown selection strategy: {strategy}")
    
    # Extract parameter tuples
    params = list(zip(selected['z_threshold'], selected['hold_bars']))
    
    logger.info(f"Selected {len(params)} parameter combinations for testing")

    return params


def run_test_validation(
    df_test: pd.DataFrame,
    selected_params: List[Tuple[float, int]],
    config: Dict
) -> pd.DataFrame:
    """
    Run validation on test set with selected parameters

    Args:
        df_test: Test set DataFrame
        selected_params: List of (z_threshold, hold_bars) tuples
        config: Configuration dictionary

    Returns:
        DataFrame with test results
    """
    logger.info("=" * 80)
    logger.info("TEST SET VALIDATION")
    logger.info("=" * 80)

    w_manip = config['w_manip']
    w_ofi = config['w_ofi']
    cost_bps = config.get('cost_bps', 5.0)
    min_trades_test = config.get('min_trades_test', 20)

    logger.info(f"Test set size: {len(df_test)} bars")
    logger.info(f"Testing {len(selected_params)} parameter combinations")

    results = []

    for idx, (z_threshold, hold_bars) in enumerate(selected_params, 1):
        logger.info(f"Test progress: {idx}/{len(selected_params)} - z={z_threshold}, hold={hold_bars}")

        try:
            # Generate signals
            df_signals = build_eth_core_joint_score_signals(
                df_test,
                w_manip=w_manip,
                w_ofi=w_ofi,
                z_threshold=z_threshold
            )

            # Run backtest
            backtest_result = run_backtest_4h(
                df_signals,
                signal_col='signal_eth_core',
                holding_bars=hold_bars,
                cost_bps=cost_bps
            )

            # Store results
            results.append({
                'z_threshold': z_threshold,
                'hold_bars': hold_bars,
                'sharpe': backtest_result.get('sharpe', 0.0),
                'total_return': backtest_result.get('total_return', 0.0),
                'max_drawdown': backtest_result.get('max_drawdown', 0.0),
                'win_rate': backtest_result.get('win_rate', 0.0),
                'n_trades': backtest_result.get('n_trades', 0),
                'avg_return': backtest_result.get('avg_return', 0.0),
            })

        except Exception as e:
            logger.warning(f"Test backtest failed for z={z_threshold}, hold={hold_bars}: {e}")
            results.append({
                'z_threshold': z_threshold,
                'hold_bars': hold_bars,
                'sharpe': 0.0,
                'total_return': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'n_trades': 0,
                'avg_return': 0.0,
            })

    df_results = pd.DataFrame(results)

    # Filter by minimum trades
    valid_results = df_results[df_results['n_trades'] >= min_trades_test]

    logger.info(f"Test validation completed: {len(df_results)} configurations")
    logger.info(f"Configurations with >= {min_trades_test} trades: {len(valid_results)}/{len(df_results)}")

    if len(valid_results) > 0:
        logger.info(f"Test set max Sharpe: {valid_results['sharpe'].max():.3f}")
        logger.info(f"Test set mean Sharpe: {valid_results['sharpe'].mean():.3f}")
        logger.info(f"Test set Sharpe > 0 ratio: {(valid_results['sharpe'] > 0).sum() / len(valid_results):.1%}")

    return df_results


def track_core_combo(
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    config: Dict
) -> pd.DataFrame:
    """
    Track specific core combination on both train and test sets

    Args:
        df_train: Training set DataFrame
        df_test: Test set DataFrame
        config: Configuration dictionary

    Returns:
        DataFrame with core combo tracking results
    """
    logger.info("=" * 80)
    logger.info("CORE COMBO TRACKING")
    logger.info("=" * 80)

    core_combo = config.get('core_combo_track', {})
    z_threshold = core_combo.get('z_threshold', 2.5)
    hold_bars = core_combo.get('hold_bars', 3)

    w_manip = config['w_manip']
    w_ofi = config['w_ofi']
    cost_bps = config.get('cost_bps', 5.0)

    logger.info(f"Core combo: z_threshold={z_threshold}, hold_bars={hold_bars}")

    results = []

    # Run on train set
    try:
        df_signals_train = build_eth_core_joint_score_signals(
            df_train, w_manip=w_manip, w_ofi=w_ofi, z_threshold=z_threshold
        )
        result_train = run_backtest_4h(
            df_signals_train, signal_col='signal_eth_core',
            holding_bars=hold_bars, cost_bps=cost_bps
        )
        results.append({
            'dataset': 'train',
            'z_threshold': z_threshold,
            'hold_bars': hold_bars,
            **result_train
        })
        logger.info(f"Train - Sharpe: {result_train.get('sharpe', 0):.3f}, Trades: {result_train.get('n_trades', 0)}")
    except Exception as e:
        logger.error(f"Core combo train failed: {e}")

    # Run on test set
    try:
        df_signals_test = build_eth_core_joint_score_signals(
            df_test, w_manip=w_manip, w_ofi=w_ofi, z_threshold=z_threshold
        )
        result_test = run_backtest_4h(
            df_signals_test, signal_col='signal_eth_core',
            holding_bars=hold_bars, cost_bps=cost_bps
        )
        results.append({
            'dataset': 'test',
            'z_threshold': z_threshold,
            'hold_bars': hold_bars,
            **result_test
        })
        logger.info(f"Test  - Sharpe: {result_test.get('sharpe', 0):.3f}, Trades: {result_test.get('n_trades', 0)}")
    except Exception as e:
        logger.error(f"Core combo test failed: {e}")

    return pd.DataFrame(results)


def main():
    """Main execution function"""
    logger.info("=" * 80)
    logger.info("ETH CORE STRATEGY: GRID SEARCH + OOS VALIDATION")
    logger.info("=" * 80)

    # Load configuration
    config = load_eth_core_config()

    symbol = config['symbol']
    timeframe = config['timeframe']
    train_start = config['train_start']
    train_end = config['train_end']
    test_start = config['test_start']
    test_end = config['test_end']

    logger.info(f"Symbol: {symbol}")
    logger.info(f"Timeframe: {timeframe}")
    logger.info(f"Train period: {train_start} to {train_end}")
    logger.info(f"Test period: {test_start} to {test_end}")

    # Load data
    logger.info("Loading merged data...")
    # TODO: Adjust data loading based on your actual data structure
    df_full = load_merged_4h_data(symbol, timeframe)
    logger.info(f"Loaded {len(df_full)} bars")

    # Split into train/test
    df_train = subset_df_by_date(df_full, start_date=train_start, end_date=train_end)
    df_test = subset_df_by_date(df_full, start_date=test_start, end_date=test_end)

    logger.info(f"Train set: {len(df_train)} bars ({train_start} to {train_end})")
    logger.info(f"Test set: {len(df_test)} bars ({test_start} to {test_end})")

    if len(df_train) == 0:
        logger.error("Training set is empty! Check date range.")
        return

    if len(df_test) == 0:
        logger.error("Test set is empty! Check date range.")
        return

    # 1. Run training grid search
    df_train_results = run_train_grid_search(df_train, config)

    # Save training results
    output_dir = Path(config.get('output_dir', 'results/oos'))
    output_dir.mkdir(parents=True, exist_ok=True)

    train_output = output_dir / config['output_files']['train_grid']
    df_train_results.to_csv(train_output, index=False)
    logger.info(f"Saved training results to {train_output}")

    # 2. Select plateau parameters
    selected_params = select_plateau_params(df_train_results, config)

    if len(selected_params) == 0:
        logger.warning("No parameters selected! Skipping test validation.")
        return

    # 3. Run test validation
    df_test_results = run_test_validation(df_test, selected_params, config)

    # Save test results
    test_output = output_dir / config['output_files']['test_grid']
    df_test_results.to_csv(test_output, index=False)
    logger.info(f"Saved test results to {test_output}")

    # 4. Track core combo
    df_core_combo = track_core_combo(df_train, df_test, config)

    # Save core combo results
    core_output = output_dir / config['output_files']['core_combo_track']
    df_core_combo.to_csv(core_output, index=False)
    logger.info(f"Saved core combo tracking to {core_output}")

    # Summary
    logger.info("=" * 80)
    logger.info("ETH CORE STRATEGY OOS COMPLETED")
    logger.info("=" * 80)
    logger.info(f"Training configs: {len(df_train_results)}")
    logger.info(f"Selected params: {len(selected_params)}")
    logger.info(f"Test configs: {len(df_test_results)}")
    logger.info("")
    logger.info("Next step: Run summarize_eth_core_oos.py to analyze results")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()

