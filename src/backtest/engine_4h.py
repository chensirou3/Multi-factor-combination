"""
Simple 4H backtest engine for joint factor strategies
"""

from dataclasses import dataclass
from typing import Optional

import pandas as pd
import numpy as np

from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class BacktestResult:
    """Backtest result container"""
    equity_curve: pd.Series
    trades: pd.DataFrame
    stats: dict
    
    def summary(self) -> str:
        """Generate summary string"""
        lines = [
            "=" * 60,
            "Backtest Summary",
            "=" * 60,
            f"Total Return: {self.stats['total_return']*100:.2f}%",
            f"Sharpe Ratio: {self.stats['sharpe_ratio']:.2f}",
            f"Max Drawdown: {self.stats['max_drawdown']*100:.2f}%",
            f"Win Rate: {self.stats['win_rate']*100:.1f}%",
            f"Total Trades: {self.stats['n_trades']}",
            f"Avg Return per Trade: {self.stats['avg_return_per_trade']*100:.3f}%",
            "=" * 60,
        ]
        return "\n".join(lines)


def subset_df_by_date(
    df: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    time_col: str = 'time'
) -> pd.DataFrame:
    """
    Filter DataFrame by date range

    Args:
        df: Input DataFrame
        start_date: Start date (inclusive), format: 'YYYY-MM-DD'
        end_date: End date (inclusive), format: 'YYYY-MM-DD'
        time_col: Name of time column

    Returns:
        Filtered DataFrame
    """
    df_filtered = df.copy()

    # Ensure time column is datetime
    if time_col in df_filtered.columns:
        if not pd.api.types.is_datetime64_any_dtype(df_filtered[time_col]):
            df_filtered[time_col] = pd.to_datetime(df_filtered[time_col])
    elif df_filtered.index.name == time_col or time_col == 'index':
        # Time is in index
        if not pd.api.types.is_datetime64_any_dtype(df_filtered.index):
            df_filtered.index = pd.to_datetime(df_filtered.index)
    else:
        logger.warning(f"Time column '{time_col}' not found, skipping date filtering")
        return df_filtered

    # Apply filters
    if start_date is not None:
        start_dt = pd.to_datetime(start_date)
        if time_col in df_filtered.columns:
            df_filtered = df_filtered[df_filtered[time_col] >= start_dt]
        else:
            df_filtered = df_filtered[df_filtered.index >= start_dt]
        logger.info(f"Filtered data from {start_date}, rows: {len(df_filtered)}")

    if end_date is not None:
        end_dt = pd.to_datetime(end_date)
        if time_col in df_filtered.columns:
            df_filtered = df_filtered[df_filtered[time_col] <= end_dt]
        else:
            df_filtered = df_filtered[df_filtered.index <= end_dt]
        logger.info(f"Filtered data to {end_date}, rows: {len(df_filtered)}")

    return df_filtered


def run_simple_holding_backtest(
    df: pd.DataFrame,
    signal_col: str = 'signal',
    holding_bars: Optional[int] = None,
    cost_bps: float = 5.0,
    initial_capital: float = 10000.0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> BacktestResult:
    """
    Run simple holding period backtest

    Logic:
    1. Enter position when signal != 0
    2. Hold for specified number of bars
    3. Exit and compute return
    4. Apply transaction costs

    Args:
        df: DataFrame with signals and OHLC data
        signal_col: Column name for signals (+1, -1, 0)
        holding_bars: Number of bars to hold (if None, use df['holding_bars'])
        cost_bps: Transaction cost in basis points (one-way)
        initial_capital: Initial capital
        start_date: Optional start date for filtering (format: 'YYYY-MM-DD')
        end_date: Optional end date for filtering (format: 'YYYY-MM-DD')

    Returns:
        BacktestResult object
    """
    # Apply date filtering if specified
    if start_date is not None or end_date is not None:
        df = subset_df_by_date(df, start_date, end_date)
        if len(df) == 0:
            logger.warning("No data after date filtering!")
            return BacktestResult(
                equity_curve=pd.Series([initial_capital]),
                trades=pd.DataFrame(),
                stats={'n_trades': 0},
            )

    df = df.copy()
    
    # Get holding period
    if holding_bars is None:
        if 'holding_bars' in df.columns:
            holding_bars = df['holding_bars'].iloc[0]
        else:
            holding_bars = 3  # Default
    
    logger.info(f"Running backtest: holding_bars={holding_bars}, cost_bps={cost_bps}")
    
    # Initialize
    df['position'] = 0
    df['entry_price'] = np.nan
    df['exit_price'] = np.nan
    df['pnl'] = 0.0
    
    trades = []
    
    # Simulate trades
    i = 0
    while i < len(df):
        signal = df[signal_col].iloc[i]
        
        if signal != 0:
            # Entry
            entry_idx = i
            entry_price = df['close'].iloc[i]
            
            # Exit after holding_bars
            exit_idx = min(i + holding_bars, len(df) - 1)
            exit_price = df['close'].iloc[exit_idx]
            
            # Compute return
            if signal > 0:  # Long
                gross_return = (exit_price - entry_price) / entry_price
            else:  # Short
                gross_return = (entry_price - exit_price) / entry_price
            
            # Apply costs
            net_return = gross_return - 2 * (cost_bps / 10000)  # Round-trip cost
            
            # Record trade
            trades.append({
                'entry_time': df.index[entry_idx],
                'exit_time': df.index[exit_idx],
                'signal': signal,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'gross_return': gross_return,
                'net_return': net_return,
                'holding_bars': exit_idx - entry_idx,
            })
            
            df.loc[df.index[entry_idx], 'pnl'] = net_return
            
            # Skip to after exit
            i = exit_idx + 1
        else:
            i += 1
    
    # Convert trades to DataFrame
    trades_df = pd.DataFrame(trades)
    
    if len(trades_df) == 0:
        logger.warning("No trades generated!")
        return BacktestResult(
            equity_curve=pd.Series([initial_capital], index=[df.index[0]]),
            trades=trades_df,
            stats={'n_trades': 0},
        )
    
    # Compute equity curve
    equity = initial_capital * (1 + trades_df['net_return']).cumprod()
    equity_curve = pd.Series(equity.values, index=trades_df['entry_time'])
    
    # Compute statistics
    returns = trades_df['net_return']
    
    stats = {
        'n_trades': len(trades_df),
        'total_return': (equity.iloc[-1] / initial_capital) - 1,
        'avg_return_per_trade': returns.mean(),
        'std_return_per_trade': returns.std(),
        'sharpe_ratio': returns.mean() / returns.std() if returns.std() > 0 else 0,
        'win_rate': (returns > 0).sum() / len(returns),
        'max_drawdown': compute_max_drawdown(equity_curve),
        'avg_holding_bars': trades_df['holding_bars'].mean(),
    }
    
    result = BacktestResult(
        equity_curve=equity_curve,
        trades=trades_df,
        stats=stats,
    )
    
    logger.info(f"\n{result.summary()}")
    
    return result


def compute_max_drawdown(equity_curve: pd.Series) -> float:
    """Compute maximum drawdown"""
    running_max = equity_curve.expanding().max()
    drawdown = (equity_curve - running_max) / running_max
    return drawdown.min()

