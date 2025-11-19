"""
Test OOS setup - Check if data and configurations are ready
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config_loader import (
    load_oos_splits_config,
    load_symbols_config,
    get_project_root
)
from src.utils.logging_utils import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


def test_oos_config():
    """Test OOS configuration loading"""
    logger.info("=" * 80)
    logger.info("Testing OOS Configuration")
    logger.info("=" * 80)
    
    try:
        oos_config = load_oos_splits_config()
        logger.info("✅ OOS config loaded successfully")
        
        symbols = list(oos_config['symbols'].keys())
        logger.info(f"Configured symbols: {symbols}")
        
        for symbol in symbols:
            splits = oos_config['symbols'][symbol]
            logger.info(f"\n{symbol}:")
            logger.info(f"  Train: {splits['train_start']} to {splits['train_end']}")
            logger.info(f"  Test:  {splits['test_start']} to {splits['test_end']}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to load OOS config: {e}")
        return False


def test_data_availability():
    """Test if merged data files exist"""
    logger.info("\n" + "=" * 80)
    logger.info("Testing Data Availability")
    logger.info("=" * 80)
    
    try:
        symbols_config = load_symbols_config()
        symbols = symbols_config.get('symbols', [])
        
        project_root = get_project_root()
        merged_dir = project_root / "data" / "intermediate" / "merged_4h"
        
        logger.info(f"Looking for merged data in: {merged_dir}")
        
        if not merged_dir.exists():
            logger.warning(f"❌ Merged data directory does not exist: {merged_dir}")
            logger.info("\nTo create merged data, run:")
            logger.info("  python scripts/generate_manipscore_4h.py")
            logger.info("  python scripts/build_merged_data.py")
            return False
        
        found_data = []
        missing_data = []
        
        for symbol in symbols:
            # Try different possible file names
            possible_files = [
                merged_dir / f"{symbol}_4H_merged.parquet",
                merged_dir / f"{symbol}_4h_merged.parquet",
                merged_dir / f"{symbol}_merged.parquet",
            ]
            
            found = False
            for file_path in possible_files:
                if file_path.exists():
                    found_data.append(symbol)
                    logger.info(f"✅ {symbol}: Found at {file_path.name}")
                    found = True
                    break
            
            if not found:
                missing_data.append(symbol)
                logger.warning(f"❌ {symbol}: Not found")
        
        logger.info(f"\nSummary:")
        logger.info(f"  Found: {len(found_data)}/{len(symbols)} symbols")
        logger.info(f"  Missing: {missing_data}")
        
        return len(found_data) > 0
        
    except Exception as e:
        logger.error(f"❌ Failed to check data availability: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backtest_results():
    """Test if previous backtest results exist"""
    logger.info("\n" + "=" * 80)
    logger.info("Testing Previous Backtest Results")
    logger.info("=" * 80)
    
    try:
        project_root = get_project_root()
        backtests_dir = project_root / "results" / "backtests"
        
        if not backtests_dir.exists():
            logger.warning(f"❌ Backtests directory does not exist: {backtests_dir}")
            return False
        
        score_files = list(backtests_dir.glob("score_grid_*_4H_fine.csv"))
        filter_files = list(backtests_dir.glob("filter_grid_*_4H_fine.csv"))
        
        logger.info(f"Found {len(score_files)} Score mode backtest files")
        logger.info(f"Found {len(filter_files)} Filter mode backtest files")
        
        for file in score_files:
            logger.info(f"  ✅ {file.name}")
        
        return len(score_files) > 0
        
    except Exception as e:
        logger.error(f"❌ Failed to check backtest results: {e}")
        return False


def main():
    logger.info("🔍 OOS Setup Test\n")
    
    results = {
        'OOS Config': test_oos_config(),
        'Data Availability': test_data_availability(),
        'Backtest Results': test_backtest_results(),
    }
    
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n🎉 All tests passed! Ready to run OOS backtest.")
        logger.info("\nNext steps:")
        logger.info("  python scripts/run_score_oos_per_symbol.py --symbol BTCUSD")
        logger.info("  python scripts/run_score_oos_all.py")
    else:
        logger.warning("\n⚠️ Some tests failed. Please fix the issues before running OOS backtest.")
    
    return all_passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

