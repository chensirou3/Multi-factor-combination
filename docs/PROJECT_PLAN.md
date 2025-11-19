# Multi-Factor Joint Analysis - Project Plan

## Overview

This project implements a modular multi-factor research framework for combining:
- **Factor 1**: ManipScore (market manipulation detection)
- **Factor 2**: OFI (order flow imbalance)
- **Factor 3**: TBD (future expansion)

## Design Principles

1. **Modularity**: Each factor is independent and can be added/removed easily
2. **Extensibility**: Framework designed to accommodate factor3, factor4, etc.
3. **No Duplication**: Reuse existing factor calculations from source projects
4. **Data-Driven**: All parameters configurable via YAML files
5. **Reproducibility**: Clear data lineage and version control

## Data Flow

```
External Projects
├── market-manimpulation-analysis/
│   └── results/bars_4h_with_manipscore_full.csv
└── Order-Flow-Imbalance-analysis/
    └── results/{symbol}_4H_merged_bars_with_ofi.csv

↓ (loader.py)

Normalized DataFrames
├── ManipScore: [time, open, high, low, close, ManipScore, ManipScore_z]
└── OFI: [time, open, high, low, close, volume, OFI_raw, OFI_z, OFI_abs_z]

↓ (merger.py)

Merged DataFrame
[time, symbol, timeframe, OHLCV, ManipScore_z, OFI_z, OFI_abs_z, ret_fwd_*]

↓ (joint_signals.py)

Signal DataFrame
[..., signal, composite_z, holding_bars]

↓ (engine_4h.py)

Backtest Results
[equity_curve, trades, stats]
```

## Module Responsibilities

### src/utils/
- **config_loader.py**: Load and parse YAML configs with variable substitution
- **logging_utils.py**: Centralized logging setup
- **io_utils.py**: File I/O with parquet/CSV support

### src/joint_data/
- **loader.py**: Load 4H data from external projects, normalize columns
- **merger.py**: Merge ManipScore + OFI on time, handle duplicates
- **validators.py**: Data quality checks (missing rate, continuity, etc.)

### src/joint_factors/
- **factor_registry.py**: Central registry for all factors (extensible)
- **manip_view.py**: ManipScore feature extraction
- **ofi_view.py**: OFI feature extraction
- **joint_signals.py**: ★ Core logic for combining factors

### src/analysis/
- **factor_stats.py**: Single factor analysis (distribution, autocorr, IC)
- **cross_factor_analysis.py**: Factor correlations, double-sort

### src/backtest/
- **engine_4h.py**: Simple holding period backtest engine

## Joint Signal Strategies

### 1. Filter Mode

**Hypothesis**: Manipulation signals work better when order flow is balanced.

**Logic**:
```python
# Step 1: Filter
if |OFI_z| < threshold:  # Balanced order flow
    # Step 2: Signal
    if ManipScore_z > entry_threshold:
        signal = -1  # Expect reversal → SHORT
    elif ManipScore_z < -entry_threshold:
        signal = +1  # Expect reversal → LONG
```

**Parameters**:
- `ofi_abs_z_max`: Filter threshold (0.5, 1.0, 1.5, 2.0)
- `manip_z_entry`: Signal threshold (1.5, 2.0, 2.5, 3.0)
- `holding_bars`: Holding period (1, 2, 3, 5)

### 2. Score Mode

**Hypothesis**: Weighted combination captures complementary information.

**Logic**:
```python
# Step 1: Compute composite score
composite_z = w1 * ManipScore_z + w2 * OFI_z

# Step 2: Generate signal
if composite_z > threshold:
    signal = -1  # Reversal logic
elif composite_z < -threshold:
    signal = +1
```

**Weight Interpretations**:
- `w1=1.0, w2=0.0`: ManipScore only (baseline)
- `w1=0.7, w2=0.3`: ManipScore dominant, OFI supporting
- `w1=1.0, w2=-0.5`: ManipScore signal, OFI hedge
  - High Manip + Low OFI → strong signal
  - High Manip + High OFI → weaker signal

## Parameter Grid Search

All parameter combinations are tested to find optimal settings:

**Filter Mode**: 4 × 4 × 4 = 64 combinations
**Score Mode**: 7 × 3 × 4 = 84 combinations

Results ranked by Sharpe ratio, with robustness checks across symbols.

## Future Extensions

### Adding Factor 3

1. **Update config/factors.yaml**:
```yaml
factor3:
  name: "LiquidityStress"
  enabled: true
  columns:
    z_score: "liquidity_stress_z"
```

2. **Create src/joint_factors/factor3_view.py**:
```python
def get_factor3_features(df):
    # Extract factor3 features
    pass
```

3. **Update joint_signals.py**:
```python
composite_z = (
    w1 * ManipScore_z +
    w2 * OFI_z +
    w3 * factor3_z  # Add factor3
)
```

4. **No changes needed** to backtest engine or scripts!

## Development Phases

### Phase 1: Foundation ✅
- [x] Project structure
- [x] Configuration system
- [x] Utility modules
- [x] Data loader with column normalization

### Phase 2: Data Integration (Current)
- [ ] Verify data paths in external projects
- [ ] Test data loading for all symbols
- [ ] Build merged datasets
- [ ] Validate data quality

### Phase 3: Analysis
- [ ] Single factor statistics
- [ ] Factor correlation analysis
- [ ] Double-sort analysis
- [ ] Future return predictability

### Phase 4: Backtesting
- [ ] Filter mode grid search
- [ ] Score mode grid search
- [ ] Robustness testing across symbols
- [ ] Performance visualization

### Phase 5: Optimization
- [ ] Parameter sensitivity analysis
- [ ] Transaction cost impact
- [ ] Regime-dependent performance
- [ ] Factor3 integration

## Success Criteria

1. **Data Integration**: Successfully merge ManipScore + OFI for ≥3 symbols
2. **Signal Generation**: Generate valid signals with reasonable frequency (1-10% of bars)
3. **Backtest**: Positive Sharpe ratio on at least one symbol/parameter combination
4. **Extensibility**: Easy to add factor3 without major refactoring
5. **Documentation**: Clear README and docs for future use

## Risk Mitigation

1. **Data Availability**: Start with BTCUSD, ETHUSD, XAUUSD (most likely to have both factors)
2. **Column Mismatch**: Flexible column detection with fallbacks
3. **Look-Ahead Bias**: All signals shifted by 1 bar before backtest
4. **Overfitting**: Test on multiple symbols, use simple strategies first

## Timeline Estimate

- **Phase 1**: ✅ Complete
- **Phase 2**: 1-2 days (data integration and validation)
- **Phase 3**: 1 day (analysis)
- **Phase 4**: 1 day (backtesting)
- **Phase 5**: 1-2 days (optimization and factor3)

**Total**: ~5-7 days for full implementation

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-19

