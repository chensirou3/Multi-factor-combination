"""
Backtest module for joint factor strategies
"""

from .engine_4h import run_simple_holding_backtest, BacktestResult

__all__ = [
    "run_simple_holding_backtest",
    "BacktestResult",
]

