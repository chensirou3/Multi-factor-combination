# Joint Signal Methodology

This document explains the mathematical and intuitive logic behind combining ManipScore and OFI.

## Factor Characteristics

### ManipScore (Factor 1)

**Definition**: Detects market manipulation patterns using microstructure anomalies.

**Properties**:
- **Direction**: Reversal
- **Interpretation**: 
  - High ManipScore → manipulation detected → expect reversal → **SHORT**
  - Low ManipScore → manipulation detected (opposite) → expect reversal → **LONG**
- **Z-score**: `ManipScore_z` (standardized using rolling window)

**Hypothesis**: Manipulated prices tend to revert to fair value.

### OFI (Order Flow Imbalance, Factor 2)

**Definition**: Measures buy vs. sell pressure in the order book.

**Properties**:
- **Direction**: Can be used for momentum OR filtering
- **Interpretation**:
  - Positive OFI → buying pressure
  - Negative OFI → selling pressure
  - Extreme |OFI| → one-sided order flow
- **Z-score**: `OFI_z` (standardized)
- **Absolute Z-score**: `OFI_abs_z = |OFI_z|` (for filtering)

**Hypothesis**: Extreme order flow imbalance may indicate:
1. Strong momentum (continuation)
2. Overbought/oversold (reversal)
3. Noisy market conditions (filter out)

## Joint Signal Approaches

### Approach 1: Filter Mode

**Core Idea**: Use OFI to filter market conditions, ManipScore to generate signals.

#### Mathematical Definition

```
Signal(t) = {
    -1  if |OFI_z(t)| < θ_ofi AND ManipScore_z(t) > θ_manip
    +1  if |OFI_z(t)| < θ_ofi AND ManipScore_z(t) < -θ_manip
     0  otherwise
}
```

Where:
- `θ_ofi`: OFI filter threshold (e.g., 1.0)
- `θ_manip`: ManipScore entry threshold (e.g., 2.0)

#### Intuition

**Why filter with OFI?**

1. **Balanced Market Hypothesis**: Manipulation signals may work better when order flow is balanced.
   - Extreme one-sided flow → strong momentum or liquidity crisis
   - Balanced flow → more "normal" market conditions
   - Manipulation patterns easier to detect in balanced markets

2. **Noise Reduction**: Extreme OFI may indicate:
   - News events (high volatility)
   - Liquidity shocks
   - Flash crashes
   - These are noisy conditions where reversal signals may fail

**Why signal with ManipScore?**

- ManipScore specifically designed to detect manipulation
- Reversal logic: high manipulation → expect correction
- Filter ensures we only trade in favorable conditions

#### Parameter Interpretation

| `θ_ofi` | Interpretation |
|---------|----------------|
| 0.5 | Very strict filter (only very balanced markets) |
| 1.0 | Moderate filter (exclude extreme order flow) |
| 2.0 | Loose filter (only exclude very extreme cases) |

| `θ_manip` | Interpretation |
|-----------|----------------|
| 1.5 | More signals, lower quality |
| 2.0 | Balanced (2 std dev) |
| 3.0 | Fewer signals, higher quality |

#### Example

```python
from src.joint_factors import generate_filter_signal, FilterSignalConfig

config = FilterSignalConfig(
    ofi_abs_z_max=1.0,      # Only trade when |OFI_z| < 1.0
    manip_z_entry=2.0,      # Enter when |ManipScore_z| > 2.0
    direction='reversal',   # Reversal logic
    holding_bars=3,         # Hold for 3 bars (12 hours)
)

df_signals = generate_filter_signal(df, config)
```

### Approach 2: Score Mode

**Core Idea**: Combine factors into a weighted composite score.

#### Mathematical Definition

```
CompositeScore(t) = w₁ · ManipScore_z(t) + w₂ · OFI_z(t)

Signal(t) = {
    -1  if CompositeScore(t) > θ_composite
    +1  if CompositeScore(t) < -θ_composite
     0  otherwise
}
```

Where:
- `w₁, w₂`: Factor weights
- `θ_composite`: Composite score threshold (e.g., 2.0)

#### Weight Interpretations

**Case 1: Both Positive (Reinforcement)**

```
w₁ = 0.7, w₂ = 0.3
```

- Both factors contribute in same direction
- High Manip + High OFI → strong composite signal
- Assumes OFI has some reversal information

**Case 2: Opposite Signs (Hedging)**

```
w₁ = 1.0, w₂ = -0.5
```

- ManipScore signals reversal
- OFI hedges against extreme order flow
- High Manip + Low OFI → strong signal (composite = 1.0 - (-0.5) = 1.5)
- High Manip + High OFI → weak signal (composite = 1.0 + (-0.5) = 0.5)

**Case 3: Baseline (ManipScore Only)**

```
w₁ = 1.0, w₂ = 0.0
```

- Pure ManipScore strategy
- Useful for comparison

#### Intuition

**Why weighted combination?**

1. **Complementary Information**: Each factor captures different aspects
   - ManipScore: Manipulation patterns
   - OFI: Order flow dynamics

2. **Noise Reduction**: Combining factors can reduce false signals
   - Require both factors to agree (if same sign)
   - Use one to hedge the other (if opposite signs)

3. **Flexibility**: Weights can be optimized for different regimes

#### Example

```python
from src.joint_factors import generate_score_signal, ScoreSignalConfig

config = ScoreSignalConfig(
    weight_manip=0.7,
    weight_ofi=0.3,
    composite_z_entry=2.0,
    direction='reversal',
    holding_bars=3,
)

df_signals = generate_score_signal(df, config)
```

## Comparison: Filter vs. Score

| Aspect | Filter Mode | Score Mode |
|--------|-------------|------------|
| **Complexity** | Simple (two-step) | Moderate (weighted sum) |
| **Interpretability** | High (clear filter + signal) | Medium (composite score) |
| **Signal Frequency** | Lower (strict filter) | Higher (more combinations) |
| **Flexibility** | Less (binary filter) | More (continuous weights) |
| **Best For** | Clear regime separation | Smooth factor combination |

## Avoiding Look-Ahead Bias

**Critical**: All signals are shifted by 1 bar before backtesting.

```python
# In joint_signals.py
df['raw_signal'] = compute_signal(df)  # Signal at time t
df['signal'] = df['raw_signal'].shift(1)  # Trade at time t+1
```

This ensures we only use information available at time t to trade at t+1.

## Future Extensions

### Adding Factor 3

**Score Mode Extension**:

```
CompositeScore(t) = w₁ · ManipScore_z(t) + w₂ · OFI_z(t) + w₃ · Factor3_z(t)
```

**Filter Mode Extension**:

Option 1: Multi-stage filter
```
if |OFI_z| < θ_ofi AND |Factor3_z| < θ_factor3:
    signal = f(ManipScore_z)
```

Option 2: Use Factor3 as signal
```
if |OFI_z| < θ_ofi:
    signal = f(ManipScore_z, Factor3_z)  # Combine for signal
```

## References

- **ManipScore**: See `market-manimpulation-analysis` repository
- **OFI**: See `Order-Flow-Imbalance-analysis` repository
- **Multi-factor Models**: Fama-French, Carhart momentum, etc.

---

## Phase OOS & Robustness

### Out-of-Sample (OOS) Validation

**Why OOS Matters**:

In quantitative trading, the biggest risk is **overfitting** - finding patterns that work perfectly on historical data but fail in live trading. OOS validation addresses this by:

1. **Time-based splits**: Train on early data, test on recent data
2. **Parameter selection**: Choose parameters from train set only
3. **Validation**: Evaluate on unseen test set data
4. **Reality check**: Test set performance approximates future live performance

**OOS Framework**:

```
Full Dataset: 2010-2025 (15 years)
    ↓
Split by time
    ↓
Train Set (early period)     Test Set (recent period)
    ↓                              ↓
Run all parameter combos      Run selected params only
    ↓                              ↓
Select top K or plateau       Evaluate performance
    ↓                              ↓
Train Sharpe: 0.8            Test Sharpe: 0.5 (realistic)
```

**Time Splits** (configured in `config/oos_splits.yaml`):

- **Crypto (BTC, ETH)**:
  - Train: 2017-2020 (4 years)
  - Test: 2021-2025 (5 years)
  - Rationale: Crypto markets mature quickly, recent data more relevant

- **Traditional (XAU, XAG, EUR)**:
  - Train: 2010-2018 (9 years)
  - Test: 2019-2025 (7 years)
  - Rationale: Longer history for stable markets

**Implementation**:

```python
# Load OOS configuration
oos_config = load_oos_splits_config()
splits = oos_config['symbols']['BTCUSD']

# Train set backtest
train_results = []
for params in param_grid:
    result = run_backtest(df, params,
                         start_date=splits['train_start'],
                         end_date=splits['train_end'])
    train_results.append(result)

# Select top parameters
top_params = select_top_k(train_results, k=20)

# Test set validation
test_results = []
for params in top_params:
    result = run_backtest(df, params,
                         start_date=splits['test_start'],
                         end_date=splits['test_end'])
    test_results.append(result)
```

### Parameter Plateau Analysis

**Why Plateau Matters**:

A single "best" parameter may be:
- **Overfit**: Works perfectly on train data by chance
- **Unstable**: Small changes in parameters cause large performance swings
- **Unreliable**: Unlikely to maintain performance out-of-sample

A **parameter plateau** indicates:
- **Robustness**: Multiple similar parameters perform well
- **Stability**: Performance is smooth across parameter space
- **True edge**: Signal is real, not data mining artifact

**Plateau Definition**:

```
Plateau = {params | Sharpe(params) ≥ sharpe_frac × Sharpe_max}

where:
- Sharpe_max = maximum Sharpe ratio in train set
- sharpe_frac = threshold fraction (default: 0.7)
```

**Example**:

```
Train set results:
- Max Sharpe: 1.0
- Plateau threshold: 0.7 × 1.0 = 0.7
- Plateau size: 50 parameter sets with Sharpe ≥ 0.7

Test set results (plateau params):
- Mean Sharpe: 0.5
- Median Sharpe: 0.48
- Sharpe > 0 ratio: 85%
- Sharpe degradation: 1.0 - 0.5 = 0.5

Interpretation:
✅ Robust: 85% of plateau params still profitable OOS
✅ Stable: Median close to mean (low variance)
⚠️ Degradation: 50% Sharpe loss (typical for OOS)
```

**Single Best vs Plateau Comparison**:

| Metric | Single Best | Plateau (50 params) |
|--------|-------------|---------------------|
| Train Sharpe | 1.0 | 0.85 (mean) |
| Test Sharpe | 0.3 | 0.5 (mean) |
| Test Sharpe > 0 | 100% (1/1) | 85% (42/50) |
| Interpretation | Likely overfit | More robust |

**Implementation**:

```python
from src.analysis.oos_plateau_analysis import analyze_plateau_stability

# Analyze plateau stability
analysis = analyze_plateau_stability(
    train_df=train_results,
    test_df=test_results,
    sharpe_frac=0.7
)

print(f"Plateau size: {analysis['plateau_size']}")
print(f"Test mean Sharpe: {analysis['plateau_test_mean_sharpe']:.3f}")
print(f"Sharpe > 0 ratio: {analysis['plateau_test_sharpe_gt0_ratio']:.1%}")
```

### Core Combo Tracking

**Discovered Pattern**:

From fine grid backtest (v1.0), we discovered an optimal weight pattern:
- `w_manip = 0.6`
- `w_ofi = -0.3`

This "hedge strategy" (positive ManipScore weight, negative OFI weight) performed best on 4/5 symbols.

**OOS Validation**:

To validate this discovery, we track this specific weight combination across all z-thresholds and holding periods:

```python
# Core combo parameters
core_weights = (0.6, -0.3)

# Test across all z and holding combinations
for z in [1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
    for hold in [1, 2, 3, 4, 5, 6, 8, 10]:
        params = {
            'w_manip': 0.6,
            'w_ofi': -0.3,
            'composite_z_entry': z,
            'holding_bars': hold
        }

        # Train and test
        train_result = run_backtest(df, params, train_period)
        test_result = run_backtest(df, params, test_period)

        # Save to core_combo results
```

**Output**: `results/oos/score_oos_core_combo_{SYMBOL}_4H.csv`

This allows us to answer:
- Is the (0.6, -0.3) pattern robust OOS?
- Which z-threshold and holding period work best with these weights?
- Does the pattern generalize across symbols?

### Robustness Metrics

**Key Metrics** (computed by `summarize_oos_results.py`):

1. **Test Set Sharpe Distribution**:
   - Mean, median, std, min, max
   - Percentiles (25th, 75th)
   - Indicates stability and variance

2. **Positive Sharpe Ratios**:
   - Sharpe > 0 ratio
   - Sharpe > 0.3 ratio
   - Sharpe > 0.5 ratio
   - Indicates reliability

3. **Sharpe Degradation**:
   - Train mean - Test mean
   - Train median - Test median
   - Indicates overfitting degree

4. **Plateau Stability**:
   - Plateau size (train)
   - Plateau test performance
   - Plateau Sharpe > 0 ratio
   - Indicates parameter robustness

**Interpretation Guidelines**:

| Metric | Good | Acceptable | Poor |
|--------|------|------------|------|
| Test mean Sharpe | > 0.5 | > 0.3 | < 0.3 |
| Sharpe > 0 ratio | > 80% | > 60% | < 60% |
| Sharpe degradation | < 0.3 | < 0.5 | > 0.5 |
| Plateau size | > 30 | > 15 | < 15 |

### OOS Workflow

**Complete OOS Process**:

```bash
# Step 1: Run OOS backtest for all symbols
python scripts/run_score_oos_all.py

# Step 2: Summarize results with plateau analysis
python scripts/summarize_oos_results.py

# Step 3: Review results
# - results/oos/score_oos_train_{SYMBOL}_4H.csv
# - results/oos/score_oos_test_{SYMBOL}_4H.csv
# - results/oos/score_oos_core_combo_{SYMBOL}_4H.csv
# - results/oos/score_oos_plateau_analysis_per_symbol.csv
# - results/oos/score_oos_summary_overall.csv
```

**Decision Making**:

Based on OOS results, decide:
1. **Deploy**: If test Sharpe > 0.3 and Sharpe > 0 ratio > 70%
2. **Refine**: If degradation > 0.5, consider simpler model
3. **Reject**: If test Sharpe < 0 or Sharpe > 0 ratio < 50%

---

**Document Version**: 1.1
**Last Updated**: 2025-01-19

