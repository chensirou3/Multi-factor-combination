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

**Document Version**: 1.0  
**Last Updated**: 2025-11-19

