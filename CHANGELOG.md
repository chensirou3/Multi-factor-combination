# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-11-19

### 🎉 Initial Release - Fine Grid Backtest Completed

#### Added
- **Project Architecture**
  - Modular multi-factor analysis framework
  - 4 configuration YAML files (paths, symbols, joint_params, factors)
  - 15+ Python source modules organized into 5 packages
  - 7 executable scripts for data generation, merging, and backtesting

- **Data Pipeline**
  - ManipScore generation from OHLCV data (3-component algorithm)
  - Automatic data merging between ManipScore and OFI factors
  - Support for 5 symbols: BTCUSD, ETHUSD, XAUUSD, XAGUSD, EURUSD
  - Data quality validation and normalization

- **Backtesting Engine**
  - Two signal generation modes:
    - Filter Mode: OFI filtering + ManipScore signals
    - Score Mode: Weighted combination of factor Z-scores
  - Grid search optimization framework
  - Performance metrics: Sharpe, Return, Win Rate, Max Drawdown

- **Analysis Tools**
  - Automated result analysis script
  - Best strategy extraction per symbol
  - Cross-symbol performance comparison

#### Results
- **Total Backtests**: 9,320 configurations
  - Filter Mode: 640 configs × 5 symbols = 3,200 backtests
  - Score Mode: 1,224 configs × 5 symbols = 6,120 backtests
- **Data Coverage**: 96,303 4H bars (2010-2025)
- **Execution Time**: 47.1 minutes

#### Key Findings
- **Best Strategy**: ETHUSD Score Mode
  - Parameters: w_manip=0.6, w_ofi=-0.3, z=3.0, hold=5
  - Performance: Sharpe=0.730, Return=9.67%, WinRate=75%
- **Hedge Strategy Discovery**: w_manip=0.6, w_ofi=-0.3 optimal for 4/5 symbols
- **Score Mode Superiority**: 2.4x higher Sharpe ratio vs Filter Mode
- **100% Positive Returns**: All 5 symbols profitable in both modes

#### Files
- Configuration: 4 YAML files
- Source Code: 20+ Python modules
- Scripts: 7 executable scripts
- Results: 12 CSV files (10 detailed + 2 summaries)
- Documentation: README.md, PROGRESS.md, CHANGELOG.md

---

## [1.1.0] - 2025-01-19

### 🎯 OOS & Robustness Analysis

#### Added
- **Out-of-Sample (OOS) Framework**
  - Time-based train/test splits for each symbol
  - Configuration file: `config/oos_splits.yaml`
  - Crypto: 4 years train (2017-2020), 5 years test (2021-2025)
  - Traditional: 9 years train (2010-2018), 7 years test (2019-2025)

- **Backtest Engine Enhancements**
  - Added `start_date` and `end_date` parameters to backtest engine
  - New `subset_df_by_date()` function for time filtering
  - Flexible time column handling (column-based or index-based)

- **OOS Scripts (Score Mode)**
  - `scripts/run_score_oos_per_symbol.py` - Single symbol OOS backtest
  - `scripts/run_score_oos_all.py` - Batch OOS for all symbols
  - `scripts/summarize_oos_results.py` - OOS summary with plateau analysis

- **Parameter Robustness Analysis**
  - `src/analysis/oos_plateau_analysis.py` - Plateau stability analysis
  - Top K parameter selection from train set
  - Plateau region identification (Sharpe ≥ threshold × max_sharpe)
  - Test set performance distribution metrics
  - Sharpe degradation tracking (train vs test)

- **Core Combo Tracking**
  - Special tracking for discovered optimal weights (0.6, -0.3)
  - Separate results file: `score_oos_core_combo_{SYMBOL}_4H.csv`
  - Performance comparison across all z-threshold and holding period combinations

- **Filter Mode OOS (Skeleton)**
  - `scripts/run_filter_oos_per_symbol.py` - Placeholder implementation
  - Reserved interfaces for future Filter mode OOS

#### Results Files
- `results/oos/score_oos_train_{SYMBOL}_4H.csv` - Train set results
- `results/oos/score_oos_test_{SYMBOL}_4H.csv` - Test set results
- `results/oos/score_oos_core_combo_{SYMBOL}_4H.csv` - Core combo tracking
- `results/oos/score_oos_plateau_analysis_per_symbol.csv` - Per-symbol plateau analysis
- `results/oos/score_oos_summary_overall.csv` - Overall summary

#### Documentation
- Updated README.md with OOS usage guide
- Added OOS methodology explanation
- Added plateau analysis rationale
- Updated project structure with new modules

#### Technical Details
- **Parameter Selection Methods**:
  - Top K: Select top K parameters by Sharpe ratio
  - Plateau: Select parameters with Sharpe ≥ sharpe_frac × max_sharpe
  - Default: Use plateau if size ≤ 2×K, otherwise use top K

- **Robustness Metrics**:
  - Test set Sharpe distribution (mean, median, std, min, max, percentiles)
  - Positive Sharpe ratio in test set
  - Sharpe degradation (train mean - test mean)
  - Threshold-based ratios (Sharpe > 0, > 0.3, > 0.5)

#### Configuration
- New config file: `config/oos_splits.yaml`
- Extended `src/utils/config_loader.py` with `load_oos_splits_config()`
- Date validation and ordering checks

---

## Future Releases

### [1.2.0] - Planned
- [ ] Visualization tools (equity curves, heatmaps)
- [ ] Paper trading simulation
- [ ] Complete Filter mode OOS implementation

### [1.2.0] - Planned
- [ ] Dynamic stop-loss/take-profit
- [ ] Position sizing (Kelly Criterion)
- [ ] Market regime filtering

### [2.0.0] - Planned
- [ ] Multi-timeframe analysis (1H, 8H, 1D)
- [ ] Additional symbols expansion
- [ ] Live trading deployment

---

**Version Format**: [Major.Minor.Patch]
- **Major**: Breaking changes or major feature additions
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes and minor improvements

