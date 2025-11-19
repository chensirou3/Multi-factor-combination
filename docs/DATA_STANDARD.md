# Data Format Standard

This document defines the standard data format for merged factor tables.

## Merged 4H Factor Table

### File Location
```
data/intermediate/merged_4h/{SYMBOL}_{TIMEFRAME}_merged.parquet
```

Example: `data/intermediate/merged_4h/BTCUSD_4H_merged.parquet`

### Index
- **Name**: `time`
- **Type**: `datetime64[ns]`
- **Timezone**: UTC (recommended)
- **Frequency**: 4H (4-hour bars)

### Required Columns

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| `symbol` | str | Trading symbol (e.g., "BTCUSD") | Metadata |
| `timeframe` | str | Timeframe (e.g., "4H") | Metadata |
| `open` | float64 | Open price | OFI project |
| `high` | float64 | High price | OFI project |
| `low` | float64 | Low price | OFI project |
| `close` | float64 | Close price | OFI project |
| `volume` | float64 | Volume | OFI project |
| `OFI_raw` | float64 | Raw order flow imbalance | OFI project |
| `OFI_z` | float64 | Standardized OFI (z-score) | OFI project |
| `OFI_abs_z` | float64 | Absolute value of OFI_z | Computed |
| `ManipScore` | float64 | Raw manipulation score | ManipScore project |
| `ManipScore_z` | float64 | Standardized ManipScore | ManipScore project or computed |

### Optional Columns

| Column | Type | Description |
|--------|------|-------------|
| `ret_fwd_1` | float64 | 1-bar forward return |
| `ret_fwd_2` | float64 | 2-bar forward return |
| `ret_fwd_5` | float64 | 5-bar forward return |
| `ret_fwd_10` | float64 | 10-bar forward return |

### Data Quality Requirements

1. **Missing Values**: ≤ 20% for key columns (OFI_z, ManipScore_z, close)
2. **Time Continuity**: Gaps should be < 10% of total bars
3. **No Duplicates**: No duplicate timestamps
4. **Valid Range**: 
   - Prices > 0
   - |z-scores| typically < 5 (outliers may exist)

### Example Data

```python
import pandas as pd

# Load merged data
df = pd.read_parquet('data/intermediate/merged_4h/BTCUSD_4H_merged.parquet')

print(df.head())
```

Output:
```
                     symbol timeframe     open     high      low    close  volume  OFI_raw   OFI_z  OFI_abs_z  ManipScore  ManipScore_z  ret_fwd_1
time                                                                                                                                                
2020-01-01 00:00:00  BTCUSD        4H  7200.5  7250.0  7180.0  7230.0   150.2    125.3   0.85       0.85        0.023          1.25       0.0015
2020-01-01 04:00:00  BTCUSD        4H  7230.0  7280.0  7220.0  7265.0   180.5   -85.2  -0.58       0.58       -0.015         -0.95       0.0025
...
```

## Source Data Formats

### OFI Project Output

**File**: `results/{SYMBOL}_{TIMEFRAME}_merged_bars_with_ofi.csv`

**Columns**:
- `timestamp` or `time`: datetime
- `open`, `high`, `low`, `close`, `volume`: OHLCV
- `OFI`: raw OFI
- `OFI_z`: standardized OFI
- `fut_ret_2`, `fut_ret_5`, `fut_ret_10`: future returns

### ManipScore Project Output

**File**: `results/bars_4h_with_manipscore_full.csv`

**Columns**:
- `timestamp` or index: datetime
- `open`, `high`, `low`, `close`: OHLC
- `ManipScore`: raw manipulation score
- `ManipScore_z`: may or may not be present (computed if missing)

## Column Normalization Rules

### Time Column
Try in order:
1. `timestamp`
2. `time`
3. `datetime`
4. `date`
5. Index (if DatetimeIndex)

### OFI Columns
- `OFI` → `OFI_raw`
- `OFI_z` → `OFI_z` (keep as is)
- Compute `OFI_abs_z = abs(OFI_z)` if not present

### ManipScore Columns
- `ManipScore` → `ManipScore` (keep as is)
- `ManipScore_z` → compute if not present using rolling z-score (window=200)

### Future Return Columns
- `fut_ret_2` → `ret_fwd_2`
- `fut_ret_5` → `ret_fwd_5`
- etc.

### OHLCV Columns
- Keep as is: `open`, `high`, `low`, `close`, `volume`
- If conflict between ManipScore and OFI versions, prefer OFI (has volume)

## Validation Checks

The `validators.py` module performs these checks:

1. **Required Columns**: Verify all required columns exist
2. **Missing Rate**: Check missing value rate for each column
3. **Time Continuity**: Check for gaps in time series
4. **Duplicates**: Check for duplicate timestamps
5. **Value Range**: Check for invalid values (e.g., negative prices)

## Usage Example

```python
from src.joint_data import build_merged_for_symbol

# Build merged data for BTCUSD 4H
df = build_merged_for_symbol(
    symbol='BTCUSD',
    timeframe='4H',
    validate=True,  # Run validation checks
)

# Data is automatically saved to:
# data/intermediate/merged_4h/BTCUSD_4H_merged.parquet

print(f"Loaded {len(df)} rows")
print(f"Columns: {list(df.columns)}")
print(f"Date range: {df.index.min()} to {df.index.max()}")
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-19

