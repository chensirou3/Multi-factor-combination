"""
Data loader for OFI and ManipScore factors

This module loads 4H factor data from external projects and normalizes column names.

IMPORTANT: The data paths and column mappings are based on inspection of:
- Order-Flow-Imbalance-analysis GitHub repo
- market-manimpulation-analysis GitHub repo

You MUST verify and adjust these mappings based on actual data structure.
"""

from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

from ..utils.config_loader import load_paths_config, load_factors_config
from ..utils.logging_utils import get_logger
from ..utils.io_utils import read_csv, read_parquet

logger = get_logger(__name__)


def _detect_time_column(df: pd.DataFrame, candidates: list[str]) -> str:
    """
    Detect which time column exists in DataFrame
    
    Args:
        df: DataFrame to check
        candidates: List of candidate column names
        
    Returns:
        Name of detected time column
        
    Raises:
        ValueError: If no time column found
    """
    # Check index first
    if df.index.name in candidates or isinstance(df.index, pd.DatetimeIndex):
        return df.index.name or 'index'
    
    # Check columns
    for col in candidates:
        if col in df.columns:
            return col
    
    raise ValueError(f"No time column found. Tried: {candidates}")


def load_ofi_4h(symbol: str, timeframe: str = "4H") -> pd.DataFrame:
    """
    Load OFI 4H factor data for a symbol
    
    Expected file location (based on OFI project structure):
        results/{symbol}_{timeframe}_merged_bars_with_ofi.csv
    
    Expected columns:
        - timestamp/time/datetime (time column)
        - open, high, low, close, volume (OHLCV)
        - OFI (raw OFI)
        - OFI_z (standardized OFI)
        - fut_ret_2, fut_ret_5, fut_ret_10 (future returns)
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSD")
        timeframe: Timeframe (default: "4H")
        
    Returns:
        DataFrame with OFI factor data
        
    Raises:
        FileNotFoundError: If data file not found
    """
    cfg = load_paths_config()
    
    # Construct file path
    # TODO: Verify this pattern matches actual OFI project output
    pattern = cfg['ofi_4h_data_pattern']
    file_path = pattern.format(symbol=symbol, timeframe=timeframe)
    
    file_path = Path(file_path)
    
    if not file_path.exists():
        # Try alternative patterns
        alt_patterns = [
            f"{cfg['ofi_project_root']}/results/{symbol}_{timeframe}_merged_bars_with_ofi.csv",
            f"{cfg['ofi_project_root']}/data/bars/{symbol}_{timeframe}.parquet",
            f"{cfg['ofi_project_root']}/data/bars/{symbol}/{timeframe}/merged.parquet",
        ]
        
        for alt_path in alt_patterns:
            alt_path = Path(alt_path)
            if alt_path.exists():
                file_path = alt_path
                logger.info(f"Found OFI data at alternative path: {file_path}")
                break
        else:
            raise FileNotFoundError(
                f"OFI data not found for {symbol} {timeframe}.\n"
                f"Tried: {file_path}\n"
                f"Also tried: {alt_patterns}\n\n"
                f"TODO: You may need to:\n"
                f"  1. Run OFI factor calculation in Order-Flow-Imbalance-analysis project\n"
                f"  2. Update paths.yaml with correct data location\n"
                f"  3. Check if symbol/timeframe data exists"
            )
    
    # Load data
    logger.info(f"Loading OFI data: {file_path}")
    
    if file_path.suffix == '.parquet':
        df = read_parquet(file_path)
    else:
        df = read_csv(file_path, index_col=None)
    
    logger.info(f"Loaded OFI data: {len(df)} rows, {len(df.columns)} columns")
    
    return df


def load_manip_4h(symbol: str, timeframe: str = "4h") -> pd.DataFrame:
    """
    Load ManipScore 4H factor data for a symbol
    
    Expected file location (based on ManipScore project structure):
        results/bars_4h_with_manipscore_full.csv (for XAUUSD)
    
    NOTE: ManipScore project may only have XAUUSD data.
    For other symbols, you may need to run ManipScore calculation first.
    
    Expected columns:
        - timestamp/time/datetime (time column)
        - open, high, low, close (OHLC)
        - ManipScore (raw manipulation score)
        - ManipScore_z (may need to compute if not present)
    
    Args:
        symbol: Trading symbol (e.g., "XAUUSD")
        timeframe: Timeframe (default: "4h")
        
    Returns:
        DataFrame with ManipScore factor data
        
    Raises:
        FileNotFoundError: If data file not found
    """
    cfg = load_paths_config()
    
    # Construct file path
    # TODO: Verify this pattern matches actual ManipScore project output
    pattern = cfg['manip_4h_data_pattern']
    
    # ManipScore project uses lowercase "4h"
    timeframe_lower = timeframe.lower()
    
    file_path = pattern.format(symbol=symbol, timeframe=timeframe_lower)
    file_path = Path(file_path)
    
    if not file_path.exists():
        # Try alternative patterns
        alt_patterns = [
            f"{cfg['manip_project_root']}/results/bars_{timeframe_lower}_with_manipscore_full.csv",
            f"{cfg['manip_project_root']}/results/{symbol}_{timeframe_lower}_manipscore.csv",
            f"{cfg['manip_project_root']}/data/{symbol}_{timeframe_lower}.parquet",
        ]
        
        for alt_path in alt_patterns:
            alt_path = Path(alt_path)
            if alt_path.exists():
                file_path = alt_path
                logger.info(f"Found ManipScore data at alternative path: {file_path}")
                break
        else:
            raise FileNotFoundError(
                f"ManipScore data not found for {symbol} {timeframe}.\n"
                f"Tried: {file_path}\n"
                f"Also tried: {alt_patterns}\n\n"
                f"TODO: You may need to:\n"
                f"  1. Run ManipScore calculation in market-manimpulation-analysis project\n"
                f"  2. Update paths.yaml with correct data location\n"
                f"  3. Note: ManipScore project may only have XAUUSD data"
            )
    
    # Load data
    logger.info(f"Loading ManipScore data: {file_path}")
    
    if file_path.suffix == '.parquet':
        df = read_parquet(file_path)
    else:
        df = read_csv(file_path, index_col=None)
    
    logger.info(f"Loaded ManipScore data: {len(df)} rows, {len(df.columns)} columns")

    return df


def normalize_ofi_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize OFI DataFrame column names to standard format

    Standard columns:
        - time: datetime index
        - symbol: trading symbol
        - timeframe: timeframe string
        - open, high, low, close, volume: OHLCV
        - OFI_raw: raw OFI value
        - OFI_z: standardized OFI
        - OFI_abs_z: absolute value of OFI_z
        - ret_fwd_1, ret_fwd_2, ret_fwd_5, ret_fwd_10: future returns

    Args:
        df: Raw OFI DataFrame

    Returns:
        DataFrame with normalized columns
    """
    df = df.copy()

    cfg = load_paths_config()
    time_candidates = cfg.get('time_column_candidates', ['timestamp', 'time', 'datetime'])

    # Detect and set time index
    time_col = _detect_time_column(df, time_candidates)

    if time_col == 'index':
        df.index = pd.to_datetime(df.index)
        df.index.name = 'time'
    else:
        df['time'] = pd.to_datetime(df[time_col])
        df = df.set_index('time')
        if time_col != 'time':
            df = df.drop(columns=[time_col], errors='ignore')

    # Rename OFI columns
    rename_map = {}

    if 'OFI' in df.columns and 'OFI_raw' not in df.columns:
        rename_map['OFI'] = 'OFI_raw'

    if rename_map:
        df = df.rename(columns=rename_map)

    # Compute OFI_abs_z if not present
    if 'OFI_z' in df.columns and 'OFI_abs_z' not in df.columns:
        df['OFI_abs_z'] = df['OFI_z'].abs()
        logger.debug("Computed OFI_abs_z from OFI_z")

    # Rename future return columns to standard format
    fut_ret_cols = [col for col in df.columns if col.startswith('fut_ret_')]
    for col in fut_ret_cols:
        # fut_ret_2 → ret_fwd_2
        horizon = col.split('_')[-1]
        new_name = f'ret_fwd_{horizon}'
        if new_name != col:
            rename_map[col] = new_name

    if rename_map:
        df = df.rename(columns=rename_map)

    logger.debug(f"Normalized OFI columns: {list(df.columns)}")

    return df


def normalize_manip_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize ManipScore DataFrame column names to standard format

    Standard columns:
        - time: datetime index
        - symbol: trading symbol
        - timeframe: timeframe string
        - open, high, low, close: OHLC
        - ManipScore: raw manipulation score
        - ManipScore_z: standardized ManipScore

    Args:
        df: Raw ManipScore DataFrame

    Returns:
        DataFrame with normalized columns
    """
    df = df.copy()

    cfg = load_paths_config()
    factors_cfg = load_factors_config()

    time_candidates = cfg.get('time_column_candidates', ['timestamp', 'time', 'datetime'])

    # Detect and set time index
    time_col = _detect_time_column(df, time_candidates)

    if time_col == 'index':
        df.index = pd.to_datetime(df.index)
        df.index.name = 'time'
    else:
        df['time'] = pd.to_datetime(df[time_col])
        df = df.set_index('time')
        if time_col != 'time':
            df = df.drop(columns=[time_col], errors='ignore')

    # Compute ManipScore_z if not present
    if 'ManipScore' in df.columns and 'ManipScore_z' not in df.columns:
        # Get normalization settings from factors config
        manip_cfg = factors_cfg.get('factors', {}).get('manip', {})
        norm_cfg = manip_cfg.get('normalization', {})
        window = norm_cfg.get('window', 200)
        min_periods = norm_cfg.get('min_periods', 50)

        # Compute rolling z-score
        rolling_mean = df['ManipScore'].rolling(window=window, min_periods=min_periods).mean()
        rolling_std = df['ManipScore'].rolling(window=window, min_periods=min_periods).std()

        df['ManipScore_z'] = (df['ManipScore'] - rolling_mean) / rolling_std

        logger.info(f"Computed ManipScore_z using rolling window={window}")

    logger.debug(f"Normalized ManipScore columns: {list(df.columns)}")

    return df


def load_merged_4h_data(symbol: str, timeframe: str = "4H") -> pd.DataFrame:
    """
    Load merged 4H data (OFI + ManipScore) for a symbol

    This function loads the pre-merged data file created by build_merged_data.py

    Args:
        symbol: Trading symbol (e.g., 'BTCUSD', 'ETHUSD')
        timeframe: Timeframe string (default: '4H')

    Returns:
        DataFrame with merged factor data

    Raises:
        FileNotFoundError: If merged data file not found

    Example:
        >>> df = load_merged_4h_data('BTCUSD')
        >>> print(df.columns)
        Index(['time', 'open', 'high', 'low', 'close', 'volume',
               'OFI', 'OFI_z', 'ManipScore', 'ManipScore_z'])
    """
    from ..utils.config_loader import get_project_root

    logger.info(f"Loading merged 4H data for {symbol}")

    # Get project root
    project_root = get_project_root()

    # Construct file path
    merged_dir = project_root / "data" / "intermediate" / "merged_4h"

    # Try different possible file names
    possible_files = [
        merged_dir / f"{symbol}_{timeframe}_merged.parquet",
        merged_dir / f"{symbol}_{timeframe.lower()}_merged.parquet",
        merged_dir / f"{symbol}_merged.parquet",
    ]

    file_path = None
    for path in possible_files:
        if path.exists():
            file_path = path
            break

    if file_path is None:
        raise FileNotFoundError(
            f"Merged data file not found for {symbol}. Tried:\n" +
            "\n".join(f"  - {p}" for p in possible_files) +
            f"\n\nPlease run: python scripts/build_merged_data.py"
        )

    logger.info(f"Loading from: {file_path}")

    # Load data
    df = read_parquet(file_path)

    # Ensure time column is datetime
    if 'time' in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df['time']):
            df['time'] = pd.to_datetime(df['time'])
    elif df.index.name == 'time' or isinstance(df.index, pd.DatetimeIndex):
        if not pd.api.types.is_datetime64_any_dtype(df.index):
            df.index = pd.to_datetime(df.index)

    logger.info(f"Loaded merged data: {len(df)} rows, {len(df.columns)} columns")
    logger.debug(f"Columns: {list(df.columns)}")

    # Validate required columns
    required_cols = ['OFI', 'OFI_z', 'ManipScore', 'ManipScore_z']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        logger.warning(f"Missing expected columns: {missing_cols}")

    return df

