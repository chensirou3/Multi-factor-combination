"""
Data merger for combining ManipScore and OFI factors
"""

from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

from ..utils.config_loader import load_paths_config
from ..utils.logging_utils import get_logger
from ..utils.io_utils import write_parquet, ensure_dir
from .loader import load_ofi_4h, load_manip_4h, normalize_ofi_columns, normalize_manip_columns
from .validators import validate_data_quality

logger = get_logger(__name__)


def merge_manip_ofi(
    manip_df: pd.DataFrame,
    ofi_df: pd.DataFrame,
    on: str | list[str] = 'time',
    how: str = 'inner',
    suffixes: tuple[str, str] = ('_manip', '_ofi'),
) -> pd.DataFrame:
    """
    Merge ManipScore and OFI DataFrames
    
    Args:
        manip_df: ManipScore DataFrame (normalized)
        ofi_df: OFI DataFrame (normalized)
        on: Column(s) to merge on (default: 'time' index)
        how: Merge method ('inner', 'outer', 'left', 'right')
        suffixes: Suffixes for overlapping columns
        
    Returns:
        Merged DataFrame
    """
    logger.info(f"Merging ManipScore ({len(manip_df)} rows) and OFI ({len(ofi_df)} rows)")
    
    # Reset index if merging on time
    if on == 'time' or (isinstance(on, list) and 'time' in on):
        manip_df = manip_df.reset_index()
        ofi_df = ofi_df.reset_index()
    
    # Merge
    merged = pd.merge(
        manip_df,
        ofi_df,
        on=on,
        how=how,
        suffixes=suffixes,
    )
    
    # Handle duplicate OHLC columns
    # Keep OFI version as it has volume
    ohlc_cols = ['open', 'high', 'low', 'close']
    for col in ohlc_cols:
        col_manip = f'{col}_manip'
        col_ofi = f'{col}_ofi'
        
        if col_manip in merged.columns and col_ofi in merged.columns:
            # Check if they're consistent
            diff = (merged[col_manip] - merged[col_ofi]).abs()
            max_diff = diff.max()
            
            if max_diff > 1e-6:
                logger.warning(
                    f"OHLC mismatch detected for {col}: max_diff={max_diff:.6f}. "
                    f"Keeping OFI version."
                )
            
            # Keep OFI version, drop ManipScore version
            merged[col] = merged[col_ofi]
            merged = merged.drop(columns=[col_manip, col_ofi])
        elif col_manip in merged.columns:
            merged = merged.rename(columns={col_manip: col})
        elif col_ofi in merged.columns:
            merged = merged.rename(columns={col_ofi: col})
    
    # Handle volume column (only in OFI)
    if 'volume_ofi' in merged.columns:
        merged = merged.rename(columns={'volume_ofi': 'volume'})
    
    # Set time index
    if 'time' in merged.columns:
        merged = merged.set_index('time')
    
    # Sort by time
    merged = merged.sort_index()
    
    logger.info(f"Merged result: {len(merged)} rows, {len(merged.columns)} columns")
    logger.info(f"Date range: {merged.index.min()} to {merged.index.max()}")
    
    return merged


def build_merged_for_symbol(
    symbol: str,
    timeframe: str = "4H",
    output_dir: Optional[str | Path] = None,
    validate: bool = True,
) -> pd.DataFrame:
    """
    Build merged factor data for a single symbol
    
    This function:
    1. Loads OFI data
    2. Loads ManipScore data
    3. Normalizes column names
    4. Merges on time
    5. Validates data quality
    6. Saves to output directory
    
    Args:
        symbol: Trading symbol
        timeframe: Timeframe (default: "4H")
        output_dir: Output directory (default: from config)
        validate: Whether to validate data quality
        
    Returns:
        Merged DataFrame
    """
    logger.info(f"Building merged data for {symbol} {timeframe}")
    
    # Load data
    try:
        ofi_df = load_ofi_4h(symbol, timeframe)
        ofi_df = normalize_ofi_columns(ofi_df)
    except FileNotFoundError as e:
        logger.error(f"Failed to load OFI data: {e}")
        raise
    
    try:
        manip_df = load_manip_4h(symbol, timeframe)
        manip_df = normalize_manip_columns(manip_df)
    except FileNotFoundError as e:
        logger.error(f"Failed to load ManipScore data: {e}")
        raise
    
    # Merge
    merged = merge_manip_ofi(manip_df, ofi_df)
    
    # Add metadata columns
    merged['symbol'] = symbol
    merged['timeframe'] = timeframe
    
    # Validate
    if validate:
        logger.info("Validating merged data quality...")
        validation_results = validate_data_quality(merged)
        
        for check, result in validation_results.items():
            if result['status'] == 'PASS':
                logger.info(f"✓ {check}: {result['message']}")
            elif result['status'] == 'WARNING':
                logger.warning(f"⚠ {check}: {result['message']}")
            else:
                logger.error(f"✗ {check}: {result['message']}")
    
    # Save
    if output_dir is None:
        cfg = load_paths_config()
        output_dir = cfg.get('merged_4h_dir', 'data/intermediate/merged_4h')
    
    output_dir = Path(output_dir)
    ensure_dir(output_dir)
    
    output_file = output_dir / f"{symbol}_{timeframe}_merged.parquet"
    write_parquet(merged, output_file)
    
    logger.info(f"Saved merged data to {output_file}")
    
    return merged

