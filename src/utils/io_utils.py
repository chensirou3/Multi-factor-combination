"""
I/O utilities for reading and writing data files
"""

import glob
from pathlib import Path
from typing import List, Optional

import pandas as pd

from .logging_utils import get_logger

logger = get_logger(__name__)


def ensure_dir(path: str | Path) -> Path:
    """
    Ensure directory exists, create if not
    
    Args:
        path: Directory path
        
    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_parquet(
    path: str | Path,
    columns: Optional[List[str]] = None,
    **kwargs
) -> pd.DataFrame:
    """
    Read parquet file
    
    Args:
        path: Path to parquet file
        columns: Optional list of columns to read
        **kwargs: Additional arguments for pd.read_parquet
        
    Returns:
        DataFrame
    """
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    logger.debug(f"Reading parquet: {path}")
    
    df = pd.read_parquet(path, columns=columns, **kwargs)
    
    logger.debug(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    
    return df


def write_parquet(
    df: pd.DataFrame,
    path: str | Path,
    **kwargs
) -> None:
    """
    Write DataFrame to parquet file
    
    Args:
        df: DataFrame to write
        path: Output path
        **kwargs: Additional arguments for pd.to_parquet
    """
    path = Path(path)
    ensure_dir(path.parent)
    
    logger.debug(f"Writing parquet: {path} ({len(df)} rows)")
    
    df.to_parquet(path, **kwargs)
    
    logger.info(f"Saved to {path}")


def read_csv(
    path: str | Path,
    parse_dates: bool = True,
    index_col: Optional[int | str] = 0,
    **kwargs
) -> pd.DataFrame:
    """
    Read CSV file
    
    Args:
        path: Path to CSV file
        parse_dates: Whether to parse dates
        index_col: Column to use as index
        **kwargs: Additional arguments for pd.read_csv
        
    Returns:
        DataFrame
    """
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    logger.debug(f"Reading CSV: {path}")
    
    df = pd.read_csv(path, parse_dates=parse_dates, index_col=index_col, **kwargs)
    
    logger.debug(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    
    return df


def write_csv(
    df: pd.DataFrame,
    path: str | Path,
    **kwargs
) -> None:
    """
    Write DataFrame to CSV file
    
    Args:
        df: DataFrame to write
        path: Output path
        **kwargs: Additional arguments for pd.to_csv
    """
    path = Path(path)
    ensure_dir(path.parent)
    
    logger.debug(f"Writing CSV: {path} ({len(df)} rows)")
    
    df.to_csv(path, **kwargs)
    
    logger.info(f"Saved to {path}")


def read_glob_parquet(
    pattern: str,
    concat: bool = True,
    **kwargs
) -> pd.DataFrame | List[pd.DataFrame]:
    """
    Read multiple parquet files matching a glob pattern
    
    Args:
        pattern: Glob pattern (e.g., "data/*.parquet")
        concat: Whether to concatenate into single DataFrame
        **kwargs: Additional arguments for pd.read_parquet
        
    Returns:
        Single DataFrame if concat=True, else list of DataFrames
    """
    files = sorted(glob.glob(pattern))
    
    if not files:
        raise FileNotFoundError(f"No files found matching pattern: {pattern}")
    
    logger.info(f"Found {len(files)} files matching pattern: {pattern}")
    
    dfs = [read_parquet(f, **kwargs) for f in files]
    
    if concat:
        logger.info(f"Concatenating {len(dfs)} DataFrames")
        return pd.concat(dfs, ignore_index=True)
    else:
        return dfs


def read_glob_csv(
    pattern: str,
    concat: bool = True,
    **kwargs
) -> pd.DataFrame | List[pd.DataFrame]:
    """
    Read multiple CSV files matching a glob pattern
    
    Args:
        pattern: Glob pattern (e.g., "data/*.csv")
        concat: Whether to concatenate into single DataFrame
        **kwargs: Additional arguments for pd.read_csv
        
    Returns:
        Single DataFrame if concat=True, else list of DataFrames
    """
    files = sorted(glob.glob(pattern))
    
    if not files:
        raise FileNotFoundError(f"No files found matching pattern: {pattern}")
    
    logger.info(f"Found {len(files)} files matching pattern: {pattern}")
    
    dfs = [read_csv(f, **kwargs) for f in files]
    
    if concat:
        logger.info(f"Concatenating {len(dfs)} DataFrames")
        return pd.concat(dfs, ignore_index=True)
    else:
        return dfs

