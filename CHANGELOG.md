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

## Future Releases

### [1.1.0] - Planned
- [ ] Out-of-sample testing (train/test split)
- [ ] Visualization tools (equity curves, heatmaps)
- [ ] Paper trading simulation

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

