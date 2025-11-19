# Quick Start Guide

This guide will help you get started with the multi-factor joint analysis framework.

## Prerequisites

1. **External Projects**: Ensure you have the two source projects available:
   ```bash
   # These should be in the same parent directory as manip-ofi-joint-analysis
   ../market-manimpulation-analysis/
   ../Order-Flow-Imbalance-analysis/
   ```

2. **Python Environment**: Python 3.10 or higher

## Step-by-Step Setup

### 1. Install Dependencies

```bash
cd manip-ofi-joint-analysis
pip install -r requirements.txt
```

This will install:
- pandas (data manipulation)
- numpy (numerical computing)
- pyarrow (parquet file support)
- pyyaml (configuration files)
- matplotlib, seaborn (visualization)

### 2. Configure Paths

Edit `config/paths.yaml` to match your setup:

```yaml
# External project locations
manip_project_root: "../market-manimpulation-analysis"
ofi_project_root: "../Order-Flow-Imbalance-analysis"

# Data file patterns (verify these match your actual files!)
ofi_4h_data_pattern: "${ofi_project_root}/results/{symbol}_4H_merged_bars_with_ofi.csv"
manip_4h_data_pattern: "${manip_project_root}/results/bars_4h_with_manipscore_full.csv"
```

**IMPORTANT**: Check that these paths and patterns match your actual data files!

### 3. Verify Data Availability

Check which symbols have data in both projects:

```bash
# Check OFI project
ls ../Order-Flow-Imbalance-analysis/results/*4H*.csv

# Check ManipScore project
ls ../market-manimpulation-analysis/results/*4h*.csv
```

Common symbols that should have both:
- BTCUSD
- ETHUSD
- XAUUSD

### 4. Build Merged Data

Run the data merging script:

```bash
# Build for all symbols
python scripts/build_merged_data.py

# Or build for a specific symbol
python scripts/build_merged_data.py --symbol BTCUSD
```

This will:
1. Load OFI 4H data
2. Load ManipScore 4H data
3. Normalize column names
4. Merge on timestamp
5. Validate data quality
6. Save to `data/intermediate/merged_4h/{SYMBOL}_4H_merged.parquet`

**Expected Output**:
```
Processing BTCUSD 4H
Loading OFI data...
Loading ManipScore data...
Normalizing columns...
Merging data...
Validating data quality...
✓ BTCUSD: 2500 rows
Saved to: data/intermediate/merged_4h/BTCUSD_4H_merged.parquet
```

### 5. Run Your First Backtest

#### Filter Mode (Recommended to start)

```bash
python scripts/run_joint_filter_grid.py --symbol BTCUSD
```

This will:
- Test multiple parameter combinations
- Use OFI to filter (only trade when |OFI_z| < threshold)
- Use ManipScore to generate signals
- Save results to `results/backtests/filter_grid_BTCUSD_4H.csv`

**Expected Output**:
```
Top 10 Configurations by Sharpe Ratio
============================================================
OFI_max=1.0, Manip=2.0, Hold=3: Sharpe=1.25, Return=15.3%, Trades=45
OFI_max=1.5, Manip=2.0, Hold=2: Sharpe=1.18, Return=12.8%, Trades=62
...
```

#### Score Mode

```bash
python scripts/run_joint_score_grid.py --symbol BTCUSD
```

This will:
- Test weighted combinations of ManipScore and OFI
- Save results to `results/backtests/score_grid_BTCUSD_4H.csv`

### 6. Analyze Results

View the backtest results:

```python
import pandas as pd

# Load filter mode results
df_filter = pd.read_csv('results/backtests/filter_grid_BTCUSD_4H.csv')

# Sort by Sharpe ratio
df_filter = df_filter.sort_values('sharpe_ratio', ascending=False)

# View top configurations
print(df_filter.head(10))

# Check win rate vs. Sharpe
import matplotlib.pyplot as plt
plt.scatter(df_filter['win_rate'], df_filter['sharpe_ratio'])
plt.xlabel('Win Rate')
plt.ylabel('Sharpe Ratio')
plt.show()
```

## Common Issues and Solutions

### Issue 1: "Merged data not found"

**Solution**: Run `python scripts/build_merged_data.py` first.

### Issue 2: "FileNotFoundError: OFI data not found"

**Solution**: 
1. Check `config/paths.yaml` - verify the `ofi_4h_data_pattern`
2. Check actual file names in `../Order-Flow-Imbalance-analysis/results/`
3. Update the pattern to match (e.g., `{symbol}_4H_*.csv` vs `{symbol}_4h_*.csv`)

### Issue 3: "FileNotFoundError: ManipScore data not found"

**Solution**:
1. Check `config/paths.yaml` - verify the `manip_4h_data_pattern`
2. ManipScore data may be in a single file for all symbols
3. Check `src/joint_data/loader.py` - may need to filter by symbol

### Issue 4: "No trades generated"

**Possible causes**:
1. Thresholds too strict (try lower values)
2. Data quality issues (check validation output)
3. Missing z-score columns (check merged data)

**Solution**: 
- Lower `manip_z_entry` from 2.0 to 1.5
- Lower `ofi_abs_z_max` from 1.0 to 1.5
- Check merged data: `pd.read_parquet('data/intermediate/merged_4h/BTCUSD_4H_merged.parquet')`

## Next Steps

1. **Analyze Factor Relationships**:
   - Compute correlation between ManipScore and OFI
   - Check factor autocorrelation
   - Analyze future return predictability

2. **Test Multiple Symbols**:
   ```bash
   for symbol in BTCUSD ETHUSD XAUUSD; do
       python scripts/run_joint_filter_grid.py --symbol $symbol
   done
   ```

3. **Optimize Parameters**:
   - Edit `config/joint_params.yaml` to add more parameter values
   - Focus on top-performing parameter ranges

4. **Add Factor 3**:
   - See `docs/PROJECT_PLAN.md` for extension guide
   - Update `config/factors.yaml`
   - Implement `src/joint_factors/factor3_view.py`

## Getting Help

- **Documentation**: See `docs/` directory
  - `PROJECT_PLAN.md` - Overall project design
  - `DATA_STANDARD.md` - Data format specification
  - `JOINT_METHOD.md` - Signal methodology

- **Code Comments**: All modules have detailed docstrings

- **Logs**: Check `results/logs/` for detailed execution logs

---

**Happy Researching!** 🚀

