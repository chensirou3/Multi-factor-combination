"""
Summarize Out-of-Sample (OOS) Results

This script analyzes OOS backtest results and generates comprehensive
summary reports including plateau stability analysis.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import argparse
import pandas as pd
from typing import List

from src.utils.config_loader import load_oos_splits_config, get_project_root
from src.utils.logging_utils import setup_logging, get_logger
from src.analysis.oos_plateau_analysis import (
    analyze_plateau_stability,
    compare_single_best_vs_plateau
)

# Setup logging
setup_logging()
logger = get_logger(__name__)


def summarize_oos_for_symbol(
    symbol: str,
    sharpe_frac: float = 0.7
) -> dict:
    """
    Generate OOS summary for a single symbol
    
    Args:
        symbol: Symbol name
        sharpe_frac: Plateau threshold fraction
        
    Returns:
        Summary dictionary
    """
    logger.info(f"Summarizing OOS results for {symbol}...")
    
    project_root = get_project_root()
    oos_dir = project_root / "results" / "oos"
    
    train_file = oos_dir / f"score_oos_train_{symbol}_4H.csv"
    test_file = oos_dir / f"score_oos_test_{symbol}_4H.csv"
    
    if not train_file.exists() or not test_file.exists():
        logger.warning(f"Missing OOS files for {symbol}")
        return None
    
    # Load results
    train_df = pd.read_csv(train_file)
    test_df = pd.read_csv(test_file)
    
    # Run plateau analysis
    plateau_analysis = analyze_plateau_stability(
        train_df, test_df, sharpe_frac=sharpe_frac
    )
    
    if 'error' in plateau_analysis:
        logger.warning(f"Plateau analysis failed for {symbol}: {plateau_analysis['error']}")
        return None
    
    # Add symbol info
    plateau_analysis['symbol'] = symbol
    
    # Run comparison analysis
    comparison = compare_single_best_vs_plateau(train_df, test_df, sharpe_frac)
    plateau_analysis.update({
        'single_best_train_sharpe': comparison.get('best_train_sharpe'),
        'single_best_test_sharpe': comparison.get('best_test_sharpe'),
    })
    
    return plateau_analysis


def summarize_all_symbols(
    sharpe_frac: float = 0.7,
    symbols: List[str] = None
):
    """
    Generate comprehensive OOS summary for all symbols
    
    Args:
        sharpe_frac: Plateau threshold fraction
        symbols: List of symbols to process (None = all from config)
    """
    logger.info("=" * 80)
    logger.info("OOS RESULTS SUMMARY - PLATEAU ANALYSIS")
    logger.info("=" * 80)
    logger.info(f"Sharpe fraction for plateau: {sharpe_frac}")
    logger.info("=" * 80)
    
    # Load OOS config
    oos_config = load_oos_splits_config()
    
    # Get symbols
    if symbols is None:
        symbols = list(oos_config['symbols'].keys())
    
    logger.info(f"Processing {len(symbols)} symbols: {symbols}\n")
    
    # Collect summaries
    summaries = []
    
    for symbol in symbols:
        try:
            summary = summarize_oos_for_symbol(symbol, sharpe_frac)
            if summary is not None:
                summaries.append(summary)
        except Exception as e:
            logger.error(f"Failed to summarize {symbol}: {e}")
            import traceback
            traceback.print_exc()
    
    if not summaries:
        logger.warning("No valid summaries generated!")
        return
    
    # Create summary DataFrame
    summary_df = pd.DataFrame(summaries)
    
    # Reorder columns for readability
    col_order = [
        'symbol',
        'train_max_sharpe',
        'train_mean_sharpe',
        'plateau_size',
        'plateau_train_mean_sharpe',
        'plateau_test_mean_sharpe',
        'plateau_test_median_sharpe',
        'plateau_test_sharpe_gt0_ratio',
        'plateau_test_sharpe_gt0.3_ratio',
        'sharpe_degradation_mean',
        'single_best_train_sharpe',
        'single_best_test_sharpe',
    ]
    
    # Only include columns that exist
    col_order = [col for col in col_order if col in summary_df.columns]
    other_cols = [col for col in summary_df.columns if col not in col_order]
    summary_df = summary_df[col_order + other_cols]
    
    # Save detailed summary
    project_root = get_project_root()
    oos_dir = project_root / "results" / "oos"
    
    detailed_file = oos_dir / "score_oos_plateau_analysis_per_symbol.csv"
    summary_df.to_csv(detailed_file, index=False)
    logger.info(f"\nSaved detailed plateau analysis to: {detailed_file}")
    
    # Print summary table
    logger.info(f"\n{'='*80}")
    logger.info("PER-SYMBOL PLATEAU ANALYSIS")
    logger.info(f"{'='*80}\n")
    
    display_cols = [
        'symbol',
        'train_max_sharpe',
        'plateau_size',
        'plateau_test_mean_sharpe',
        'plateau_test_sharpe_gt0_ratio',
        'sharpe_degradation_mean'
    ]
    display_cols = [col for col in display_cols if col in summary_df.columns]
    
    logger.info(summary_df[display_cols].to_string(index=False))
    
    # Overall statistics
    logger.info(f"\n{'='*80}")
    logger.info("AGGREGATE STATISTICS")
    logger.info(f"{'='*80}")
    logger.info(f"Average train max Sharpe: {summary_df['train_max_sharpe'].mean():.3f}")
    logger.info(f"Average plateau test mean Sharpe: {summary_df['plateau_test_mean_sharpe'].mean():.3f}")
    logger.info(f"Average plateau Sharpe>0 ratio: {summary_df['plateau_test_sharpe_gt0_ratio'].mean():.1%}")
    logger.info(f"Average Sharpe degradation: {summary_df['sharpe_degradation_mean'].mean():.3f}")
    logger.info(f"Symbols with positive plateau test Sharpe: {(summary_df['plateau_test_mean_sharpe'] > 0).sum()}/{len(summary_df)}")
    
    # Save aggregate summary
    aggregate = {
        'total_symbols': len(summary_df),
        'avg_train_max_sharpe': summary_df['train_max_sharpe'].mean(),
        'avg_plateau_test_mean_sharpe': summary_df['plateau_test_mean_sharpe'].mean(),
        'avg_plateau_sharpe_gt0_ratio': summary_df['plateau_test_sharpe_gt0_ratio'].mean(),
        'avg_sharpe_degradation': summary_df['sharpe_degradation_mean'].mean(),
        'symbols_with_positive_plateau_sharpe': (summary_df['plateau_test_mean_sharpe'] > 0).sum(),
    }
    
    aggregate_df = pd.DataFrame([aggregate])
    aggregate_file = oos_dir / "score_oos_plateau_analysis_overall.csv"
    aggregate_df.to_csv(aggregate_file, index=False)
    logger.info(f"\nSaved aggregate summary to: {aggregate_file}")
    
    logger.info(f"\n{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description="Summarize OOS backtest results with plateau analysis")
    parser.add_argument('--sharpe_frac', type=float, default=0.7, help='Sharpe fraction for plateau threshold')
    parser.add_argument('--symbols', nargs='+', help='Specific symbols to process (default: all)')
    
    args = parser.parse_args()
    
    summarize_all_symbols(
        sharpe_frac=args.sharpe_frac,
        symbols=args.symbols
    )


if __name__ == '__main__':
    main()

