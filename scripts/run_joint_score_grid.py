"""
Run joint score mode backtest with parameter grid

This script tests the Score mode strategy:
- Weighted combination: composite_z = w1 * ManipScore_z + w2 * OFI_z
- Signal based on composite_z threshold

Usage:
    python scripts/run_joint_score_grid.py
    python scripts/run_joint_score_grid.py --symbol BTCUSD
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config_loader import load_symbols_config, load_paths_config, load_joint_params_config
from src.utils.logging_utils import setup_logging, get_logger
from src.utils.io_utils import read_parquet, write_csv, ensure_dir
from src.joint_factors import generate_score_signal, ScoreSignalConfig
from src.backtest import run_simple_holding_backtest

# Setup logging
setup_logging()
logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Run score mode backtest grid")
    parser.add_argument('--symbol', type=str, default='BTCUSD', help='Symbol to backtest')
    parser.add_argument('--timeframe', type=str, default='4H', help='Timeframe')
    parser.add_argument('--config', type=str, default='joint_params.yaml',
                        help='Config file to use (default: joint_params.yaml)')

    args = parser.parse_args()

    logger.info(f"Running score mode backtest for {args.symbol} {args.timeframe}")
    logger.info(f"Using config: {args.config}")

    # Load merged data
    paths_cfg = load_paths_config()
    merged_dir = Path(paths_cfg['merged_4h_dir'])
    merged_file = merged_dir / f"{args.symbol}_{args.timeframe}_merged.parquet"

    if not merged_file.exists():
        logger.error(f"Merged data not found: {merged_file}")
        logger.error("Please run scripts/build_merged_data.py first")
        return 1

    logger.info(f"Loading data from {merged_file}")
    df = read_parquet(merged_file)
    logger.info(f"Loaded {len(df)} rows")

    # Load parameter grid from specified config file
    params_cfg = load_joint_params_config(args.config)
    score_params = params_cfg['score_mode']
    
    # Build parameter grid
    weights = score_params['weights']
    composite_z_entries = score_params['composite_z_entry']
    holding_bars_list = score_params['holding_bars']
    
    logger.info(f"Parameter grid:")
    logger.info(f"  weights: {weights}")
    logger.info(f"  composite_z_entry: {composite_z_entries}")
    logger.info(f"  holding_bars: {holding_bars_list}")
    
    # Run grid search
    results = []
    
    import itertools
    for (w_manip, w_ofi), composite_z, hold_bars in itertools.product(
        weights,
        composite_z_entries,
        holding_bars_list,
    ):
        config = ScoreSignalConfig(
            weight_manip=w_manip,
            weight_ofi=w_ofi,
            composite_z_entry=composite_z,
            direction='reversal',  # Reversal logic
            holding_bars=hold_bars,
        )
        
        logger.info(
            f"\nTesting: w_manip={w_manip}, w_ofi={w_ofi}, "
            f"composite_z={composite_z}, hold={hold_bars}"
        )
        
        # Generate signals
        df_signals = generate_score_signal(df.copy(), config)
        
        # Run backtest
        bt_result = run_simple_holding_backtest(
            df_signals,
            signal_col='signal',
            holding_bars=hold_bars,
            cost_bps=5.0,
        )
        
        # Store results
        results.append({
            'symbol': args.symbol,
            'timeframe': args.timeframe,
            'weight_manip': w_manip,
            'weight_ofi': w_ofi,
            'composite_z_entry': composite_z,
            'holding_bars': hold_bars,
            **bt_result.stats,
        })
    
    # Convert to DataFrame and save
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('sharpe_ratio', ascending=False)
    
    # Save results
    output_dir = Path(paths_cfg['backtests_dir'])
    ensure_dir(output_dir)
    # Add suffix based on config file
    suffix = "_fine" if "fine" in args.config else ""
    output_file = output_dir / f"score_grid_{args.symbol}_{args.timeframe}{suffix}.csv"
    write_csv(results_df, output_file)
    
    logger.info(f"\n{'='*60}")
    logger.info("Top 10 Configurations by Sharpe Ratio")
    logger.info(f"{'='*60}")
    
    for idx, row in results_df.head(10).iterrows():
        logger.info(
            f"w_manip={row['weight_manip']:.1f}, w_ofi={row['weight_ofi']:.1f}, "
            f"z={row['composite_z_entry']:.1f}, hold={row['holding_bars']}: "
            f"Sharpe={row['sharpe_ratio']:.2f}, Return={row['total_return']*100:.2f}%, "
            f"Trades={row['n_trades']}"
        )
    
    logger.info(f"\nResults saved to: {output_file}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

