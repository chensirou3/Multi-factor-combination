"""
Build merged 4H factor data for all symbols

This script:
1. Loads OFI and ManipScore data from external projects
2. Normalizes column names
3. Merges on time
4. Validates data quality
5. Saves to data/intermediate/merged_4h/

Usage:
    python scripts/build_merged_data.py
    python scripts/build_merged_data.py --symbol BTCUSD
    python scripts/build_merged_data.py --timeframe 4H
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config_loader import load_symbols_config, load_paths_config
from src.utils.logging_utils import setup_logging, get_logger
from src.joint_data import build_merged_for_symbol

# Setup logging
setup_logging()
logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Build merged factor data")
    parser.add_argument(
        '--symbol',
        type=str,
        default=None,
        help='Symbol to process (default: all symbols from config)'
    )
    parser.add_argument(
        '--timeframe',
        type=str,
        default='4H',
        help='Timeframe (default: 4H)'
    )
    
    args = parser.parse_args()
    
    # Load config
    symbols_cfg = load_symbols_config()
    
    # Determine symbols to process
    if args.symbol:
        symbols = [args.symbol]
    else:
        symbols = symbols_cfg.get('symbols', [])
    
    logger.info(f"Processing {len(symbols)} symbols: {symbols}")
    logger.info(f"Timeframe: {args.timeframe}")
    
    # Process each symbol
    results = {}
    
    for symbol in symbols:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {symbol} {args.timeframe}")
        logger.info(f"{'='*60}")
        
        try:
            merged_df = build_merged_for_symbol(
                symbol=symbol,
                timeframe=args.timeframe,
                validate=True,
            )
            
            results[symbol] = {
                'status': 'SUCCESS',
                'n_rows': len(merged_df),
                'date_range': (merged_df.index.min(), merged_df.index.max()),
            }
            
            logger.info(f"✓ {symbol}: {len(merged_df)} rows")
            
        except FileNotFoundError as e:
            logger.error(f"✗ {symbol}: Data not found - {e}")
            results[symbol] = {
                'status': 'FAILED',
                'error': str(e),
            }
        
        except Exception as e:
            logger.error(f"✗ {symbol}: Error - {e}", exc_info=True)
            results[symbol] = {
                'status': 'ERROR',
                'error': str(e),
            }
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("Summary")
    logger.info(f"{'='*60}")
    
    n_success = sum(1 for r in results.values() if r['status'] == 'SUCCESS')
    n_failed = len(results) - n_success
    
    logger.info(f"Total symbols: {len(results)}")
    logger.info(f"Success: {n_success}")
    logger.info(f"Failed: {n_failed}")
    
    for symbol, result in results.items():
        if result['status'] == 'SUCCESS':
            logger.info(
                f"  ✓ {symbol}: {result['n_rows']} rows, "
                f"{result['date_range'][0]} to {result['date_range'][1]}"
            )
        else:
            logger.error(f"  ✗ {symbol}: {result.get('error', 'Unknown error')}")
    
    logger.info(f"\nMerged data saved to: {load_paths_config()['merged_4h_dir']}")
    
    return 0 if n_failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

