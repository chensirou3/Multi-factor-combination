#!/usr/bin/env python3
"""Analyze fine grid search results across all symbols"""

import pandas as pd
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging_utils import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def analyze_results():
    """Analyze fine grid search results"""
    
    results_dir = project_root / "results" / "backtests"
    symbols = ["BTCUSD", "ETHUSD", "XAUUSD", "XAGUSD", "EURUSD"]
    
    logger.info("="*80)
    logger.info("Fine Grid Search Results Analysis")
    logger.info("="*80)
    
    # Analyze Filter Mode
    logger.info("\n" + "="*80)
    logger.info("FILTER MODE - Top 5 Strategies per Symbol")
    logger.info("="*80)
    
    filter_summary = []
    
    for symbol in symbols:
        file_path = results_dir / f"filter_grid_{symbol}_4H_fine.csv"
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            continue
        
        df = pd.read_csv(file_path)
        df = df.sort_values('sharpe_ratio', ascending=False)
        
        logger.info(f"\n{symbol} - Top 5 Configurations:")
        logger.info("-" * 80)
        
        for idx, row in df.head(5).iterrows():
            logger.info(
                f"  OFI_max={row['ofi_abs_z_max']:.2f}, Manip={row['manip_z_entry']:.2f}, "
                f"Hold={int(row['holding_bars'])}: "
                f"Sharpe={row['sharpe_ratio']:.3f}, Return={row['total_return']*100:.2f}%, "
                f"WinRate={row['win_rate']*100:.1f}%, Trades={int(row['n_trades'])}, "
                f"MaxDD={row['max_drawdown']*100:.2f}%"
            )
        
        # Add best config to summary
        best = df.iloc[0]
        filter_summary.append({
            'symbol': symbol,
            'ofi_max': best['ofi_abs_z_max'],
            'manip_entry': best['manip_z_entry'],
            'holding_bars': int(best['holding_bars']),
            'sharpe': best['sharpe_ratio'],
            'return': best['total_return'] * 100,
            'win_rate': best['win_rate'] * 100,
            'n_trades': int(best['n_trades']),
            'max_dd': best['max_drawdown'] * 100
        })
    
    # Analyze Score Mode
    logger.info("\n" + "="*80)
    logger.info("SCORE MODE - Top 5 Strategies per Symbol")
    logger.info("="*80)
    
    score_summary = []
    
    for symbol in symbols:
        file_path = results_dir / f"score_grid_{symbol}_4H_fine.csv"
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            continue
        
        df = pd.read_csv(file_path)
        df = df.sort_values('sharpe_ratio', ascending=False)
        
        logger.info(f"\n{symbol} - Top 5 Configurations:")
        logger.info("-" * 80)
        
        for idx, row in df.head(5).iterrows():
            logger.info(
                f"  w_manip={row['weight_manip']:.2f}, w_ofi={row['weight_ofi']:.2f}, "
                f"z={row['composite_z_entry']:.2f}, hold={int(row['holding_bars'])}: "
                f"Sharpe={row['sharpe_ratio']:.3f}, Return={row['total_return']*100:.2f}%, "
                f"WinRate={row['win_rate']*100:.1f}%, Trades={int(row['n_trades'])}, "
                f"MaxDD={row['max_drawdown']*100:.2f}%"
            )
        
        # Add best config to summary
        best = df.iloc[0]
        score_summary.append({
            'symbol': symbol,
            'w_manip': best['weight_manip'],
            'w_ofi': best['weight_ofi'],
            'z_entry': best['composite_z_entry'],
            'holding_bars': int(best['holding_bars']),
            'sharpe': best['sharpe_ratio'],
            'return': best['total_return'] * 100,
            'win_rate': best['win_rate'] * 100,
            'n_trades': int(best['n_trades']),
            'max_dd': best['max_drawdown'] * 100
        })
    
    # Save summaries
    filter_df = pd.DataFrame(filter_summary)
    score_df = pd.DataFrame(score_summary)
    
    filter_df.to_csv(results_dir / "filter_best_per_symbol.csv", index=False)
    score_df.to_csv(results_dir / "score_best_per_symbol.csv", index=False)
    
    logger.info("\n" + "="*80)
    logger.info("SUMMARY - Best Strategy per Symbol")
    logger.info("="*80)
    logger.info(f"\nFilter Mode Summary saved to: filter_best_per_symbol.csv")
    logger.info(f"Score Mode Summary saved to: score_best_per_symbol.csv")
    
    # Overall statistics
    logger.info("\n" + "="*80)
    logger.info("OVERALL STATISTICS")
    logger.info("="*80)
    logger.info(f"\nFilter Mode:")
    logger.info(f"  Avg Sharpe: {filter_df['sharpe'].mean():.3f}")
    logger.info(f"  Avg Return: {filter_df['return'].mean():.2f}%")
    logger.info(f"  Positive Returns: {(filter_df['return'] > 0).sum()}/{len(filter_df)}")
    
    logger.info(f"\nScore Mode:")
    logger.info(f"  Avg Sharpe: {score_df['sharpe'].mean():.3f}")
    logger.info(f"  Avg Return: {score_df['return'].mean():.2f}%")
    logger.info(f"  Positive Returns: {(score_df['return'] > 0).sum()}/{len(score_df)}")


if __name__ == '__main__':
    analyze_results()

