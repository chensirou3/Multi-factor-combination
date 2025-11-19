#!/usr/bin/env python3
"""
Run fine-grained parameter grid search for all symbols.

This script runs both filter mode and score mode backtests for all symbols
using the fine-grained parameter grid defined in joint_params_fine.yaml.
"""

import sys
from pathlib import Path
import argparse
import time
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging_utils import setup_logging, get_logger
from src.utils.config_loader import load_symbols_config

logger = get_logger(__name__)


def run_filter_grid(symbol: str, timeframe: str = "4H", config_file: str = "joint_params_fine.yaml"):
    """Run filter mode grid search for a symbol."""
    import subprocess
    
    cmd = [
        "python3",
        str(project_root / "scripts" / "run_joint_filter_grid.py"),
        "--symbol", symbol,
        "--timeframe", timeframe,
        "--config", config_file
    ]
    
    logger.info(f"Running filter grid for {symbol} {timeframe}...")
    start_time = time.time()
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    elapsed = time.time() - start_time
    
    if result.returncode == 0:
        logger.info(f"✓ Filter grid completed for {symbol} in {elapsed:.1f}s")
        return True
    else:
        logger.error(f"✗ Filter grid failed for {symbol}")
        logger.error(result.stderr)
        return False


def run_score_grid(symbol: str, timeframe: str = "4H", config_file: str = "joint_params_fine.yaml"):
    """Run score mode grid search for a symbol."""
    import subprocess
    
    cmd = [
        "python3",
        str(project_root / "scripts" / "run_joint_score_grid.py"),
        "--symbol", symbol,
        "--timeframe", timeframe,
        "--config", config_file
    ]
    
    logger.info(f"Running score grid for {symbol} {timeframe}...")
    start_time = time.time()
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    elapsed = time.time() - start_time
    
    if result.returncode == 0:
        logger.info(f"✓ Score grid completed for {symbol} in {elapsed:.1f}s")
        return True
    else:
        logger.error(f"✗ Score grid failed for {symbol}")
        logger.error(result.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Run fine-grained grid search for all symbols")
    parser.add_argument('--mode', type=str, choices=['filter', 'score', 'both'], default='both',
                        help='Which mode to run (default: both)')
    parser.add_argument('--timeframe', type=str, default='4H',
                        help='Timeframe to analyze (default: 4H)')
    parser.add_argument('--config', type=str, default='joint_params_fine.yaml',
                        help='Config file to use (default: joint_params_fine.yaml)')
    parser.add_argument('--symbols', type=str, nargs='+',
                        help='Specific symbols to run (default: all from config)')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(log_to_file=True, log_to_console=True)
    
    # Load symbols from config
    symbols_config = load_symbols_config()
    all_symbols = symbols_config.get("symbols", [])
    
    # Use specified symbols or all symbols
    symbols_to_run = args.symbols if args.symbols else all_symbols
    
    logger.info("=" * 60)
    logger.info("Fine-Grained Grid Search - All Symbols")
    logger.info("=" * 60)
    logger.info(f"Symbols: {', '.join(symbols_to_run)}")
    logger.info(f"Timeframe: {args.timeframe}")
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Config: {args.config}")
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    results = {
        'filter': {},
        'score': {}
    }
    
    total_start = time.time()
    
    for symbol in symbols_to_run:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Processing {symbol}")
        logger.info(f"{'=' * 60}")
        
        # Run filter mode
        if args.mode in ['filter', 'both']:
            success = run_filter_grid(symbol, args.timeframe, args.config)
            results['filter'][symbol] = success
        
        # Run score mode
        if args.mode in ['score', 'both']:
            success = run_score_grid(symbol, args.timeframe, args.config)
            results['score'][symbol] = success
    
    total_elapsed = time.time() - total_start
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total time: {total_elapsed / 60:.1f} minutes")
    
    if args.mode in ['filter', 'both']:
        logger.info("\nFilter Mode Results:")
        for symbol, success in results['filter'].items():
            status = "✓" if success else "✗"
            logger.info(f"  {status} {symbol}")
    
    if args.mode in ['score', 'both']:
        logger.info("\nScore Mode Results:")
        for symbol, success in results['score'].items():
            status = "✓" if success else "✗"
            logger.info(f"  {status} {symbol}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

