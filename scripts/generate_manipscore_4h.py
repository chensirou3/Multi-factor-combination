#!/usr/bin/env python3
"""
Generate ManipScore 4H data for all symbols from OFI project's OHLCV data.

This script:
1. Loads 4H OHLCV data from OFI project
2. Computes ManipScore from OHLCV features
3. Saves to results/{symbol}_4h_manipscore.csv

Usage:
    python scripts/generate_manipscore_4h.py --symbol XAUUSD
    python scripts/generate_manipscore_4h.py --all  # Process all symbols
"""

import sys
import os
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from utils.config_loader import load_symbols_config, load_paths_config
from utils.logging_utils import get_logger, setup_logging


def compute_manipscore_from_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute ManipScore from OHLCV data.

    ManipScore is based on:
    1. Price-volume divergence
    2. Wick ratio (manipulation candles)
    3. Volume spikes
    4. Price reversals

    Args:
        df: DataFrame with OHLCV columns

    Returns:
        pd.DataFrame: Input df with ManipScore and ManipScore_z columns added
    """
    df = df.copy()

    # Compute candlestick features
    df['body'] = abs(df['close'] - df['open'])
    df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
    df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
    df['total_wick'] = df['upper_wick'] + df['lower_wick']
    df['wick_ratio'] = df['total_wick'] / (df['body'] + 1e-8)

    # Compute returns
    df['ret'] = df['close'].pct_change()
    df['abs_ret'] = df['ret'].abs()

    # Compute volume features
    df['volume_ma'] = df['volume'].rolling(window=20, min_periods=5).mean()
    df['volume_ratio'] = df['volume'] / (df['volume_ma'] + 1e-8)

    # Component 1: Wick ratio anomaly (high wick ratio = manipulation)
    wick_score = df['wick_ratio'].clip(0, 10)  # Clip extreme values
    wick_score = (wick_score - wick_score.rolling(50, min_periods=10).mean()) / (wick_score.rolling(50, min_periods=10).std() + 1e-8)
    wick_score = wick_score.fillna(0).clip(-3, 3)

    # Component 2: Volume spike with small price move (wash trading indicator)
    volume_spike = df['volume_ratio'].clip(0, 10)
    price_move = df['abs_ret']
    wash_score = volume_spike * (1 / (price_move + 0.001))  # High volume, low price move
    wash_score = (wash_score - wash_score.rolling(50, min_periods=10).mean()) / (wash_score.rolling(50, min_periods=10).std() + 1e-8)
    wash_score = wash_score.fillna(0).clip(-3, 3)

    # Component 3: Price reversal after extreme move
    df['high_low_range'] = (df['high'] - df['low']) / (df['close'] + 1e-8)
    range_score = df['high_low_range'].clip(0, 0.1)
    range_score = (range_score - range_score.rolling(50, min_periods=10).mean()) / (range_score.rolling(50, min_periods=10).std() + 1e-8)
    range_score = range_score.fillna(0).clip(-3, 3)

    # Combine components into ManipScore
    df['ManipScore'] = (
        0.4 * wick_score +      # Manipulation candles
        0.4 * wash_score +      # Wash trading
        0.2 * range_score       # Extreme ranges
    )

    # Compute ManipScore z-score
    window = 200
    min_periods = 50

    rolling_mean = df['ManipScore'].rolling(window=window, min_periods=min_periods).mean()
    rolling_std = df['ManipScore'].rolling(window=window, min_periods=min_periods).std()

    df['ManipScore_z'] = (df['ManipScore'] - rolling_mean) / (rolling_std + 1e-8)
    df['ManipScore_z'] = df['ManipScore_z'].fillna(0)

    return df


def generate_manipscore_4h(symbol: str, output_dir: Path) -> pd.DataFrame:
    """
    Generate 4H ManipScore data for a symbol from OFI project data.

    Args:
        symbol: Trading symbol (e.g., 'XAUUSD', 'BTCUSD')
        output_dir: Output directory for results

    Returns:
        pd.DataFrame: 4H bars with ManipScore
    """
    logger = get_logger(f"generate_manipscore_{symbol}")
    logger.info(f"Generating ManipScore 4H data for {symbol}")

    try:
        # Step 1: Load 4H OHLCV data from OFI project
        paths_cfg = load_paths_config()
        ofi_project_root = paths_cfg['ofi_project_root']
        ofi_file = Path(ofi_project_root) / "results" / f"{symbol}_4H_merged_bars_with_ofi.csv"

        logger.info(f"Loading OHLCV data from {ofi_file}...")
        df = pd.read_csv(ofi_file)
        logger.info(f"Loaded {len(df):,} bars")

        # Step 2: Parse timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Step 3: Compute ManipScore
        logger.info("Computing ManipScore from OHLCV features...")
        df = compute_manipscore_from_ohlcv(df)
        logger.info("ManipScore computed successfully")

        # Step 4: Select output columns
        output_cols = [
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'ManipScore', 'ManipScore_z'
        ]

        df_output = df[output_cols].copy()

        # Step 5: Save to CSV
        output_file = output_dir / f"{symbol}_4h_manipscore.csv"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        df_output.to_csv(output_file, index=False)
        logger.info(f"Saved to {output_file}")
        logger.info(f"Output shape: {df_output.shape}")
        logger.info(f"Date range: {df_output['timestamp'].min()} to {df_output['timestamp'].max()}")
        logger.info(f"ManipScore range: [{df_output['ManipScore'].min():.3f}, {df_output['ManipScore'].max():.3f}]")
        logger.info(f"ManipScore_z range: [{df_output['ManipScore_z'].min():.3f}, {df_output['ManipScore_z'].max():.3f}]")

        return df_output

    except Exception as e:
        logger.error(f"Error generating ManipScore for {symbol}: {e}")
        raise


def main():
    # Setup logging
    setup_logging(log_to_file=False, log_to_console=True)

    parser = argparse.ArgumentParser(description="Generate ManipScore 4H data from OFI project OHLCV")
    parser.add_argument('--symbol', type=str, help='Symbol to process (e.g., XAUUSD)')
    parser.add_argument('--all', action='store_true', help='Process all symbols')
    parser.add_argument('--output-dir', type=str, help='Output directory (default: ManipScore project results/)')

    args = parser.parse_args()

    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        paths_cfg = load_paths_config()
        manip_project_root = paths_cfg.get('manip_project_root', '/home/ubuntu/market-manimpulation-analysis')
        output_dir = Path(manip_project_root) / "results"

    # Determine symbols to process
    if args.all:
        symbols_cfg = load_symbols_config()
        symbols = symbols_cfg.get('symbols', ['XAUUSD', 'BTCUSD', 'ETHUSD', 'EURUSD', 'XAGUSD'])
    elif args.symbol:
        symbols = [args.symbol]
    else:
        print("Error: Must specify --symbol or --all")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"ManipScore 4H Data Generation")
    print(f"{'='*60}")
    print(f"Output directory: {output_dir}")
    print(f"Symbols to process: {', '.join(symbols)}")
    print(f"{'='*60}\n")

    # Process each symbol
    success_count = 0
    for symbol in symbols:
        print(f"\n{'='*60}")
        print(f"Processing {symbol}")
        print(f"{'='*60}")

        try:
            df = generate_manipscore_4h(symbol, output_dir)
            print(f"✓ {symbol}: Generated {len(df):,} bars")
            success_count += 1
        except FileNotFoundError as e:
            print(f"✗ {symbol}: Data file not found - {e}")
            continue
        except Exception as e:
            print(f"✗ {symbol}: Failed - {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"\n{'='*60}")
    print(f"Generation complete!")
    print(f"Successfully processed: {success_count}/{len(symbols)} symbols")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

