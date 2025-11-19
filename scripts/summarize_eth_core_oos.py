"""
ETH Core Strategy: OOS Results Summary and Analysis

This script analyzes the OOS test results from run_eth_core_grid_oos.py and generates:
- Plateau stability analysis
- Train vs test performance comparison
- Core combo tracking analysis
- Summary statistics and recommendations
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
import yaml

from src.utils.logging_utils import get_logger
from src.utils.config_loader import get_project_root

logger = get_logger(__name__)


def load_results(config: dict) -> tuple:
    """
    Load OOS results from CSV files
    
    Returns:
        Tuple of (df_train, df_test, df_core_combo)
    """
    project_root = get_project_root()
    output_dir = project_root / config.get('output_dir', 'results/oos')
    
    train_file = output_dir / config['output_files']['train_grid']
    test_file = output_dir / config['output_files']['test_grid']
    core_file = output_dir / config['output_files']['core_combo_track']
    
    logger.info(f"Loading results from {output_dir}")
    
    df_train = pd.read_csv(train_file)
    df_test = pd.read_csv(test_file)
    df_core_combo = pd.read_csv(core_file)
    
    logger.info(f"Loaded train results: {len(df_train)} configs")
    logger.info(f"Loaded test results: {len(df_test)} configs")
    logger.info(f"Loaded core combo: {len(df_core_combo)} entries")
    
    return df_train, df_test, df_core_combo


def analyze_plateau_stability(
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    config: dict
) -> dict:
    """
    Analyze plateau stability between train and test sets
    
    Returns:
        Dictionary with plateau analysis results
    """
    logger.info("=" * 80)
    logger.info("PLATEAU STABILITY ANALYSIS")
    logger.info("=" * 80)
    
    min_trades_train = config.get('min_trades_train', 50)
    min_trades_test = config.get('min_trades_test', 20)
    plateau_frac = config.get('plateau_sharpe_frac', 0.7)
    
    # Filter valid configs
    valid_train = df_train[df_train['n_trades'] >= min_trades_train].copy()
    valid_test = df_test[df_test['n_trades'] >= min_trades_test].copy()
    
    # Train set plateau
    max_sharpe_train = valid_train['sharpe'].max()
    plateau_threshold = plateau_frac * max_sharpe_train
    plateau_train = valid_train[valid_train['sharpe'] >= plateau_threshold]
    
    logger.info(f"Train set:")
    logger.info(f"  Total configs: {len(df_train)}")
    logger.info(f"  Valid configs (>= {min_trades_train} trades): {len(valid_train)}")
    logger.info(f"  Max Sharpe: {max_sharpe_train:.3f}")
    logger.info(f"  Plateau threshold ({plateau_frac:.0%} × max): {plateau_threshold:.3f}")
    logger.info(f"  Plateau size: {len(plateau_train)} configs")
    logger.info(f"  Plateau Sharpe - mean: {plateau_train['sharpe'].mean():.3f}, median: {plateau_train['sharpe'].median():.3f}")
    
    # Test set statistics
    if len(valid_test) > 0:
        max_sharpe_test = valid_test['sharpe'].max()
        mean_sharpe_test = valid_test['sharpe'].mean()
        median_sharpe_test = valid_test['sharpe'].median()
        sharpe_gt0_ratio = (valid_test['sharpe'] > 0).sum() / len(valid_test)
        sharpe_gt03_ratio = (valid_test['sharpe'] > 0.3).sum() / len(valid_test)
        
        logger.info(f"\nTest set:")
        logger.info(f"  Total configs: {len(df_test)}")
        logger.info(f"  Valid configs (>= {min_trades_test} trades): {len(valid_test)}")
        logger.info(f"  Max Sharpe: {max_sharpe_test:.3f}")
        logger.info(f"  Mean Sharpe: {mean_sharpe_test:.3f}")
        logger.info(f"  Median Sharpe: {median_sharpe_test:.3f}")
        logger.info(f"  Sharpe > 0 ratio: {sharpe_gt0_ratio:.1%}")
        logger.info(f"  Sharpe > 0.3 ratio: {sharpe_gt03_ratio:.1%}")
        
        # Sharpe degradation
        sharpe_degradation = mean_sharpe_test - plateau_train['sharpe'].mean()
        sharpe_degradation_pct = (sharpe_degradation / plateau_train['sharpe'].mean()) * 100 if plateau_train['sharpe'].mean() != 0 else 0
        
        logger.info(f"\nPlateau Stability:")
        logger.info(f"  Train plateau mean Sharpe: {plateau_train['sharpe'].mean():.3f}")
        logger.info(f"  Test mean Sharpe: {mean_sharpe_test:.3f}")
        logger.info(f"  Sharpe degradation: {sharpe_degradation:.3f} ({sharpe_degradation_pct:.1f}%)")
    else:
        logger.warning("No valid test configs!")
        max_sharpe_test = 0
        mean_sharpe_test = 0
        median_sharpe_test = 0
        sharpe_gt0_ratio = 0
        sharpe_gt03_ratio = 0
        sharpe_degradation = 0
        sharpe_degradation_pct = 0
    
    return {
        'train_total_configs': len(df_train),
        'train_valid_configs': len(valid_train),
        'train_max_sharpe': max_sharpe_train,
        'train_plateau_size': len(plateau_train),
        'train_plateau_mean_sharpe': plateau_train['sharpe'].mean(),
        'train_plateau_median_sharpe': plateau_train['sharpe'].median(),
        'test_total_configs': len(df_test),
        'test_valid_configs': len(valid_test),
        'test_max_sharpe': max_sharpe_test,
        'test_mean_sharpe': mean_sharpe_test,
        'test_median_sharpe': median_sharpe_test,
        'test_sharpe_gt0_ratio': sharpe_gt0_ratio,
        'test_sharpe_gt03_ratio': sharpe_gt03_ratio,
        'sharpe_degradation': sharpe_degradation,
        'sharpe_degradation_pct': sharpe_degradation_pct,
    }


def analyze_core_combo(df_core_combo: pd.DataFrame) -> dict:
    """
    Analyze core combo performance
    
    Returns:
        Dictionary with core combo analysis
    """
    logger.info("=" * 80)
    logger.info("CORE COMBO ANALYSIS")
    logger.info("=" * 80)
    
    train_row = df_core_combo[df_core_combo['dataset'] == 'train']
    test_row = df_core_combo[df_core_combo['dataset'] == 'test']
    
    if len(train_row) == 0 or len(test_row) == 0:
        logger.warning("Core combo data incomplete!")
        return {}
    
    train_row = train_row.iloc[0]
    test_row = test_row.iloc[0]
    
    logger.info(f"Core combo params: z_threshold={train_row['z_threshold']}, hold_bars={train_row['hold_bars']}")
    logger.info(f"\nTrain set:")
    logger.info(f"  Sharpe: {train_row['sharpe']:.3f}")
    logger.info(f"  Total return: {train_row['total_return']:.2%}")
    logger.info(f"  Max drawdown: {train_row['max_drawdown']:.2%}")
    logger.info(f"  Win rate: {train_row['win_rate']:.2%}")
    logger.info(f"  Trades: {train_row['n_trades']}")
    
    logger.info(f"\nTest set:")
    logger.info(f"  Sharpe: {test_row['sharpe']:.3f}")
    logger.info(f"  Total return: {test_row['total_return']:.2%}")
    logger.info(f"  Max drawdown: {test_row['max_drawdown']:.2%}")
    logger.info(f"  Win rate: {test_row['win_rate']:.2%}")
    logger.info(f"  Trades: {test_row['n_trades']}")
    
    sharpe_change = test_row['sharpe'] - train_row['sharpe']
    sharpe_change_pct = (sharpe_change / train_row['sharpe']) * 100 if train_row['sharpe'] != 0 else 0
    
    logger.info(f"\nPerformance change:")
    logger.info(f"  Sharpe change: {sharpe_change:.3f} ({sharpe_change_pct:.1f}%)")
    
    return {
        'core_z_threshold': train_row['z_threshold'],
        'core_hold_bars': train_row['hold_bars'],
        'core_train_sharpe': train_row['sharpe'],
        'core_train_return': train_row['total_return'],
        'core_train_dd': train_row['max_drawdown'],
        'core_train_winrate': train_row['win_rate'],
        'core_train_trades': train_row['n_trades'],
        'core_test_sharpe': test_row['sharpe'],
        'core_test_return': test_row['total_return'],
        'core_test_dd': test_row['max_drawdown'],
        'core_test_winrate': test_row['win_rate'],
        'core_test_trades': test_row['n_trades'],
        'core_sharpe_change': sharpe_change,
        'core_sharpe_change_pct': sharpe_change_pct,
    }


def generate_recommendations(plateau_stats: dict, core_stats: dict, config: dict) -> list:
    """
    Generate recommendations based on OOS results

    Returns:
        List of recommendation strings
    """
    recommendations = []

    min_test_sharpe = config.get('min_test_sharpe', 0.2)
    max_test_dd = config.get('max_test_drawdown', 0.3)
    min_test_winrate = config.get('min_test_winrate', 0.4)

    # Check test set performance
    test_sharpe = plateau_stats.get('test_mean_sharpe', 0)
    test_sharpe_gt0 = plateau_stats.get('test_sharpe_gt0_ratio', 0)
    core_test_sharpe = core_stats.get('core_test_sharpe', 0)
    core_test_dd = core_stats.get('core_test_dd', 0)
    core_test_winrate = core_stats.get('core_test_winrate', 0)

    # Overall assessment
    if test_sharpe >= min_test_sharpe and test_sharpe_gt0 >= 0.6:
        recommendations.append("✅ PASS: Strategy shows positive OOS performance")
    elif test_sharpe >= 0 and test_sharpe_gt0 >= 0.5:
        recommendations.append("⚠️ MARGINAL: Strategy shows weak OOS performance")
    else:
        recommendations.append("❌ FAIL: Strategy fails OOS validation")

    # Core combo assessment
    if core_test_sharpe >= min_test_sharpe:
        recommendations.append(f"✅ Core combo passes (Sharpe {core_test_sharpe:.3f} >= {min_test_sharpe})")
    else:
        recommendations.append(f"❌ Core combo fails (Sharpe {core_test_sharpe:.3f} < {min_test_sharpe})")

    if core_test_dd <= max_test_dd:
        recommendations.append(f"✅ Drawdown acceptable ({core_test_dd:.1%} <= {max_test_dd:.1%})")
    else:
        recommendations.append(f"⚠️ Drawdown high ({core_test_dd:.1%} > {max_test_dd:.1%})")

    if core_test_winrate >= min_test_winrate:
        recommendations.append(f"✅ Win rate acceptable ({core_test_winrate:.1%} >= {min_test_winrate:.1%})")
    else:
        recommendations.append(f"⚠️ Win rate low ({core_test_winrate:.1%} < {min_test_winrate:.1%})")

    # Degradation assessment
    degradation_pct = plateau_stats.get('sharpe_degradation_pct', 0)
    if abs(degradation_pct) <= 30:
        recommendations.append(f"✅ Sharpe degradation acceptable ({degradation_pct:.1f}%)")
    elif abs(degradation_pct) <= 50:
        recommendations.append(f"⚠️ Sharpe degradation moderate ({degradation_pct:.1f}%)")
    else:
        recommendations.append(f"❌ Sharpe degradation severe ({degradation_pct:.1f}%)")

    # Sample size
    core_test_trades = core_stats.get('core_test_trades', 0)
    if core_test_trades >= 50:
        recommendations.append(f"✅ Sufficient test trades ({core_test_trades})")
    elif core_test_trades >= 20:
        recommendations.append(f"⚠️ Moderate test trades ({core_test_trades})")
    else:
        recommendations.append(f"❌ Insufficient test trades ({core_test_trades})")

    return recommendations


def main():
    """Main execution function"""
    logger.info("=" * 80)
    logger.info("ETH CORE STRATEGY: OOS RESULTS SUMMARY")
    logger.info("=" * 80)

    # Load configuration
    project_root = get_project_root()
    config_path = project_root / "config" / "eth_core_params.yaml"

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Load results
    df_train, df_test, df_core_combo = load_results(config)

    # Analyze plateau stability
    plateau_stats = analyze_plateau_stability(df_train, df_test, config)

    # Analyze core combo
    core_stats = analyze_core_combo(df_core_combo)

    # Combine all statistics
    summary_stats = {**plateau_stats, **core_stats}

    # Save summary
    output_dir = Path(config.get('output_dir', 'results/oos'))
    summary_file = output_dir / config['output_files']['oos_summary']

    df_summary = pd.DataFrame([summary_stats])
    df_summary.to_csv(summary_file, index=False)
    logger.info(f"\nSaved summary to {summary_file}")

    # Generate recommendations
    recommendations = generate_recommendations(plateau_stats, core_stats, config)

    logger.info("=" * 80)
    logger.info("RECOMMENDATIONS")
    logger.info("=" * 80)
    for rec in recommendations:
        logger.info(rec)

    # Final summary
    logger.info("=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Train plateau mean Sharpe: {plateau_stats.get('train_plateau_mean_sharpe', 0):.3f}")
    logger.info(f"Test mean Sharpe: {plateau_stats.get('test_mean_sharpe', 0):.3f}")
    logger.info(f"Core combo test Sharpe: {core_stats.get('core_test_sharpe', 0):.3f}")
    logger.info(f"Test Sharpe > 0 ratio: {plateau_stats.get('test_sharpe_gt0_ratio', 0):.1%}")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()

