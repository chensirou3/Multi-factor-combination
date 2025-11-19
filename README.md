# ManipScore-OFI Joint Analysis Framework

A comprehensive quantitative trading research framework combining market manipulation detection (ManipScore) with order flow imbalance (OFI) for multi-factor strategy development.

## 📊 Project Overview

This project implements a sophisticated multi-factor analysis system that combines:

- **ManipScore**: Market manipulation detection factor (reversal logic)
- **OFI (Order Flow Imbalance)**: Order flow imbalance factor (momentum/filtering logic)

### Key Features

- ✅ **Dual-mode strategy**: Filter mode and Score mode
- ✅ **Fine-grained grid search**: 9,320+ configurations tested
- ✅ **Out-of-sample validation**: Train/test split with robustness analysis
- ✅ **Parameter plateau analysis**: Identify robust parameter regions
- ✅ **Multi-asset coverage**: Crypto (BTC, ETH) and traditional assets (XAU, XAG, EUR)
- ✅ **Comprehensive backtesting**: 15 years of 4H data (2010-2025)

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone git@github.com:chensirou3/Multi-factor-combination.git
cd Multi-factor-combination/manip-ofi-joint-analysis

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

#### 1. Build Merged Data

```bash
# Generate ManipScore for 4H timeframe
python scripts/generate_manipscore_4h.py

# Merge ManipScore with OFI data
python scripts/build_merged_data.py
```

#### 2. Run Grid Search Backtest

```bash
# Score mode (all symbols, fine grid)
python scripts/run_all_symbols_fine_grid.py --mode score

# Filter mode (all symbols, fine grid)
python scripts/run_all_symbols_fine_grid.py --mode filter

# Analyze results
python scripts/analyze_fine_grid_results.py
```

#### 3. Run Out-of-Sample (OOS) Backtest

```bash
# Run OOS for all symbols (Score mode)
python scripts/run_score_oos_all.py

# Or run for a single symbol
python scripts/run_score_oos_per_symbol.py --symbol BTCUSD

# Summarize OOS results with plateau analysis
python scripts/summarize_oos_results.py
```

#### 4. Run ETH Core Strategy (Simplified & Optimized)

**New in v1.2**: Based on OOS results, we developed a simplified strategy focused on ETHUSD with fixed optimal weights.

```bash
# Run ETH core strategy grid search + OOS validation
python scripts/run_eth_core_grid_oos.py

# Analyze ETH core strategy results
python scripts/summarize_eth_core_oos.py
```

**Key improvements**:
- ✅ Fixed weights: `w_manip=0.6, w_ofi=-0.3` (best from OOS)
- ✅ Reduced parameter space: 30 configs (vs 1,224)
- ✅ Focus on ETHUSD only (best performing symbol)
- ✅ Minimum trade filters for statistical significance
- ✅ Plateau-based parameter selection

See [docs/ETH_CORE_STRATEGY.md](docs/ETH_CORE_STRATEGY.md) for details.

## 📁 Project Structure

```
manip-ofi-joint-analysis/
├── config/                      # Configuration files
│   ├── paths.yaml              # Data paths
│   ├── symbols.yaml            # Symbol definitions
│   ├── joint_params.yaml       # Strategy parameters (coarse)
│   ├── joint_params_fine.yaml  # Strategy parameters (fine grid)
│   ├── oos_splits.yaml         # Out-of-sample time splits
│   └── eth_core_params.yaml    # ETH core strategy parameters (v1.2)
│
├── src/                        # Source code
│   ├── utils/                  # Utility modules
│   │   ├── config_loader.py   # Configuration loading
│   │   ├── logging_utils.py   # Logging utilities
│   │   └── io_utils.py        # I/O utilities
│   ├── joint_data/            # Data loading
│   │   └── loader.py          # Merged data loader
│   ├── joint_factors/         # Factor computation
│   │   └── joint_signals.py   # Signal generation (Filter, Score, ETH Core)
│   ├── analysis/              # Analysis modules
│   │   ├── performance.py     # Performance metrics
│   │   └── oos_plateau_analysis.py  # OOS plateau analysis
│   └── backtest/              # Backtest engine
│       └── engine_4h.py       # 4H backtest engine with OOS support
│
├── scripts/                    # Executable scripts
│   ├── generate_manipscore_4h.py      # Generate ManipScore
│   ├── build_merged_data.py           # Build merged datasets
│   ├── run_joint_filter_grid.py       # Filter mode grid search
│   ├── run_joint_score_grid.py        # Score mode grid search
│   ├── run_all_symbols_fine_grid.py   # Fine grid for all symbols
│   ├── analyze_fine_grid_results.py   # Analyze grid results
│   ├── run_score_oos_per_symbol.py    # OOS for single symbol (Score)
│   ├── run_score_oos_all.py           # OOS for all symbols (Score)
│   ├── summarize_oos_results.py       # OOS summary with plateau analysis
│   ├── run_filter_oos_per_symbol.py   # OOS skeleton (Filter mode)
│   ├── run_eth_core_grid_oos.py       # ETH core strategy OOS (v1.2)
│   └── summarize_eth_core_oos.py      # ETH core strategy summary (v1.2)
│
├── results/                    # Results directory
│   ├── backtests/             # Grid search results
│   ├── oos/                   # Out-of-sample results
│   └── logs/                  # Log files
│
├── docs/                       # Documentation
│   ├── JOINT_METHOD.md        # Methodology documentation
│   └── ETH_CORE_STRATEGY.md   # ETH core strategy documentation (v1.2)
│
├── PROGRESS.md                 # Project progress report
├── CHANGELOG.md                # Version changelog
└── README.md                   # This file
```

## 🎯 Strategy Modes

### Filter Mode

**Logic**: Use OFI to filter market conditions, ManipScore to generate signals

```python
# Only trade when |OFI_z| < threshold (balanced order flow)
# Enter when |ManipScore_z| > threshold (manipulation detected)
# Direction: Reversal (high ManipScore → expect reversal → SHORT)
```

**Parameters**:
- `ofi_abs_z_max`: OFI filter threshold (0.3 - 2.0)
- `manip_z_entry`: ManipScore entry threshold (1.0 - 3.5)
- `holding_bars`: Holding period (1 - 10 bars)

### Score Mode

**Logic**: Weighted combination of factors

```python
# CompositeScore = w_manip * ManipScore_z + w_ofi * OFI_z
# Enter when |CompositeScore| > threshold
# Direction: Reversal logic
```

**Parameters**:
- `w_manip`, `w_ofi`: Factor weights (e.g., 0.6, -0.3)
- `composite_z_entry`: Composite score threshold (1.5 - 4.0)
- `holding_bars`: Holding period (1 - 10 bars)

## 📈 Key Findings

### Fine Grid Backtest Results (Full Sample)

| Symbol | Mode | Best Sharpe | Return | Win Rate | Best Params |
|--------|------|-------------|--------|----------|-------------|
| ETHUSD | Score | 0.730 | 9.67% | 75% | w=(0.6,-0.3), z=3.0, hold=5 |
| BTCUSD | Score | 0.484 | 3.20% | 67% | w=(0.6,-0.3), z=2.5, hold=3 |
| XAUUSD | Score | 0.467 | 2.89% | 64% | w=(0.6,-0.3), z=2.5, hold=4 |
| XAGUSD | Score | 0.459 | 2.85% | 63% | w=(0.6,-0.3), z=2.5, hold=4 |
| EURUSD | Score | 0.280 | 1.84% | 58% | w=(0.6,-0.3), z=2.0, hold=3 |

**Key Insights**:
- Score mode consistently outperforms Filter mode
- Optimal weight pattern: `w_manip ≈ 0.6, w_ofi ≈ -0.3` (hedge strategy)
- All 5 symbols achieved positive returns
- Average Sharpe ratio: 0.484 (Score mode)

### Out-of-Sample (OOS) Validation

The OOS framework validates strategy robustness by:

1. **Time-based splits**: Train on early data, test on recent data
2. **Parameter selection**: Top K or plateau region from train set
3. **Stability metrics**: Test set Sharpe distribution, degradation analysis
4. **Core combo tracking**: Special tracking for discovered optimal weights (0.6, -0.3)

**Why OOS Matters**:
- Prevents overfitting to historical data
- Validates parameter stability across different market regimes
- Identifies robust "plateau regions" vs. single best parameters

**Why Plateau Analysis**:
- Single "best" parameter may be overfit
- Robust strategies have a plateau of good parameters
- Plateau stability indicates true edge vs. data mining

## 🔧 Configuration

### OOS Time Splits (`config/oos_splits.yaml`)

```yaml
symbols:
  BTCUSD:
    train_start: "2017-01-01"
    train_end: "2020-12-31"
    test_start: "2021-01-01"
    test_end: "2025-12-31"
  # ... similar for other symbols
```

### Parameter Grids (`config/joint_params_fine.yaml`)

- **Score mode**: 1,224 configs per symbol (17 weights × 9 z-thresholds × 8 holding periods)
- **Filter mode**: 640 configs per symbol (8 OFI × 10 ManipScore × 8 holding periods)

## 📊 Results Files

### Grid Search Results

- `results/backtests/score_grid_{SYMBOL}_4H_fine.csv` - Score mode results
- `results/backtests/filter_grid_{SYMBOL}_4H_fine.csv` - Filter mode results

### OOS Results

- `results/oos/score_oos_train_{SYMBOL}_4H.csv` - Train set results
- `results/oos/score_oos_test_{SYMBOL}_4H.csv` - Test set results
- `results/oos/score_oos_core_combo_{SYMBOL}_4H.csv` - Core combo (0.6, -0.3) tracking
- `results/oos/score_oos_plateau_analysis_per_symbol.csv` - Plateau analysis per symbol
- `results/oos/score_oos_summary_overall.csv` - Overall summary

## 🛠️ Development

### Running Tests

```bash
# Run OOS for a single symbol (for testing)
python scripts/run_score_oos_per_symbol.py --symbol ETHUSD --top_k 10

# Run with custom plateau threshold
python scripts/summarize_oos_results.py --sharpe_frac 0.8
```

### Adding New Symbols

1. Add symbol to `config/symbols.yaml`
2. Add OOS splits to `config/oos_splits.yaml`
3. Ensure data files exist in `data/merged/`

## 📚 Documentation

- **PROGRESS.md**: Detailed progress report and findings
- **CHANGELOG.md**: Version history and updates
- **docs/JOINT_METHOD.md**: Methodology and technical details

## 🤝 Contributing

This is a research project. For questions or suggestions, please open an issue.

## 📄 License

This project is for research purposes only.

---

**Last Updated**: 2025-01-19
**Version**: 1.1.0 (OOS & Robustness Analysis)