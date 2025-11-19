"""
Out-of-Sample (OOS) backtest for Score mode - All symbols

This script runs OOS backtest for all symbols defined in oos_splits.yaml
and generates a summary report.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import argparse
import pandas as pd
from datetime import datetime

from src.utils.config_loader import load_oos_splits_config, get_project_root
from src.utils.logging_utils import setup_logging, get_logger
from run_score_oos_per_symbol import run_oos_for_symbol

# Setup logging
setup_logging()
logger = get_logger(__name__)


def run_oos_all_symbols(
    top_k: int = 20,
    sharpe_frac: float = 0.7,
    config_file: str = "joint_params_fine.yaml",
    symbols: list = None
):
    """
    Run OOS backtest for all symbols
    
    Args:
        top_k: Number of top parameters to select from train set
        sharpe_frac: Fraction of max Sharpe for plateau selection
        config_file: Parameter config file name
        symbols: List of symbols to process (None = all from config)
    """
    logger.info("=" * 80)
    logger.info("SCORE MODE OOS BACKTEST - ALL SYMBOLS")
    logger.info("=" * 80)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Config file: {config_file}")
    logger.info(f"Top K: {top_k}, Sharpe fraction: {sharpe_frac}")
    logger.info("=" * 80)
    
    # Load OOS splits config
    oos_config = load_oos_splits_config()
    
    # Get symbols to process
    if symbols is None:
        symbols = list(oos_config['symbols'].keys())
    
    logger.info(f"Processing {len(symbols)} symbols: {symbols}\n")
    
    # Run OOS for each symbol
    results_summary = []
    
    for i, symbol in enumerate(symbols):
        logger.info(f"\n{'#'*80}")
        logger.info(f"# Symbol {i+1}/{len(symbols)}: {symbol}")
        logger.info(f"{'#'*80}\n")
        
        try:
            run_oos_for_symbol(
                symbol=symbol,
                top_k=top_k,
                sharpe_frac=sharpe_frac,
                config_file=config_file
            )
            
            # Load results and compute summary
            project_root = get_project_root()
            output_dir = project_root / "results" / "oos"
            
            train_file = output_dir / f"score_oos_train_{symbol}_4H.csv"
            test_file = output_dir / f"score_oos_test_{symbol}_4H.csv"
            
            if train_file.exists() and test_file.exists():
                train_df = pd.read_csv(train_file)
                test_df = pd.read_csv(test_file)
                
                # Filter valid results
                valid_train = train_df[train_df['n_trades'] > 0]
                valid_test = test_df[test_df['n_trades'] > 0]
                
                if len(valid_train) > 0 and len(valid_test) > 0:
                    summary = {
                        'symbol': symbol,
                        'train_max_sharpe': valid_train['sharpe'].max(),
                        'train_mean_sharpe': valid_train['sharpe'].mean(),
                        'train_configs': len(valid_train),
                        'test_max_sharpe': valid_test['sharpe'].max(),
                        'test_mean_sharpe': valid_test['sharpe'].mean(),
                        'test_median_sharpe': valid_test['sharpe'].median(),
                        'test_sharpe_gt0_ratio': (valid_test['sharpe'] > 0).sum() / len(valid_test),
                        'test_sharpe_gt0.3_ratio': (valid_test['sharpe'] > 0.3).sum() / len(valid_test),
                        'test_configs': len(valid_test),
                        'test_avg_trades': valid_test['n_trades'].mean(),
                    }
                    results_summary.append(summary)
                    
        except Exception as e:
            logger.error(f"Failed to process {symbol}: {e}")
            import traceback
            traceback.print_exc()
    
    # Save summary
    if results_summary:
        summary_df = pd.DataFrame(results_summary)
        
        project_root = get_project_root()
        output_dir = project_root / "results" / "oos"
        summary_file = output_dir / "score_oos_summary_per_symbol.csv"
        summary_df.to_csv(summary_file, index=False)
        
        logger.info(f"\n{'='*80}")
        logger.info("OVERALL SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"\nSaved summary to: {summary_file}")
        logger.info(f"\nPer-symbol summary:")
        logger.info(summary_df.to_string(index=False))
        
        # Overall statistics
        logger.info(f"\n{'='*80}")
        logger.info("AGGREGATE STATISTICS")
        logger.info(f"{'='*80}")
        logger.info(f"Average train max Sharpe: {summary_df['train_max_sharpe'].mean():.3f}")
        logger.info(f"Average test mean Sharpe: {summary_df['test_mean_sharpe'].mean():.3f}")
        logger.info(f"Average test Sharpe>0 ratio: {summary_df['test_sharpe_gt0_ratio'].mean():.1%}")
        logger.info(f"Symbols with test mean Sharpe > 0: {(summary_df['test_mean_sharpe'] > 0).sum()}/{len(summary_df)}")
        
        # Save overall summary
        overall_summary = {
            'total_symbols': len(summary_df),
            'avg_train_max_sharpe': summary_df['train_max_sharpe'].mean(),
            'avg_test_mean_sharpe': summary_df['test_mean_sharpe'].mean(),
            'avg_test_sharpe_gt0_ratio': summary_df['test_sharpe_gt0_ratio'].mean(),
            'symbols_with_positive_test_sharpe': (summary_df['test_mean_sharpe'] > 0).sum(),
        }
        overall_df = pd.DataFrame([overall_summary])
        overall_file = output_dir / "score_oos_summary_overall.csv"
        overall_df.to_csv(overall_file, index=False)
        logger.info(f"\nSaved overall summary to: {overall_file}")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description="Run Score mode OOS backtest for all symbols")
    parser.add_argument('--top_k', type=int, default=20, help='Number of top params to select from train')
    parser.add_argument('--sharpe_frac', type=float, default=0.7, help='Sharpe fraction for plateau selection')
    parser.add_argument('--config', type=str, default='joint_params_fine.yaml', help='Parameter config file')
    parser.add_argument('--symbols', nargs='+', help='Specific symbols to process (default: all)')
    
    args = parser.parse_args()
    
    run_oos_all_symbols(
        top_k=args.top_k,
        sharpe_frac=args.sharpe_frac,
        config_file=args.config,
        symbols=args.symbols
    )


if __name__ == '__main__':
    main()

