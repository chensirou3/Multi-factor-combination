"""
Check time range of merged data files
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from src.utils.config_loader import get_project_root, load_symbols_config

def check_data_range():
    """Check time range for all symbols"""
    project_root = get_project_root()
    merged_dir = project_root / "data" / "intermediate" / "merged_4h"
    
    symbols_config = load_symbols_config()
    symbols = symbols_config.get('symbols', [])
    
    print("=" * 80)
    print("Data Time Range Check")
    print("=" * 80)
    
    for symbol in symbols:
        file_path = merged_dir / f"{symbol}_4H_merged.parquet"
        
        if not file_path.exists():
            print(f"\n{symbol}: FILE NOT FOUND")
            continue
        
        try:
            df = pd.read_parquet(file_path)
            
            # Get time column
            if 'time' in df.columns:
                time_col = df['time']
            elif isinstance(df.index, pd.DatetimeIndex):
                time_col = df.index
            else:
                print(f"\n{symbol}: NO TIME COLUMN FOUND")
                continue
            
            # Get time range
            start_time = time_col.min()
            end_time = time_col.max()
            total_rows = len(df)
            
            # Check timezone
            if hasattr(time_col, 'dt'):
                tz = time_col.dt.tz
            else:
                tz = time_col.tz
            
            print(f"\n{symbol}:")
            print(f"  Start: {start_time}")
            print(f"  End:   {end_time}")
            print(f"  Rows:  {total_rows:,}")
            print(f"  TZ:    {tz}")
            
            # Check if data covers train/test periods
            train_start = pd.to_datetime('2017-01-01')
            train_end = pd.to_datetime('2020-12-31')
            test_start = pd.to_datetime('2021-01-01')
            test_end = pd.to_datetime('2025-12-31')
            
            if tz is not None:
                train_start = train_start.tz_localize(tz)
                train_end = train_end.tz_localize(tz)
                test_start = test_start.tz_localize(tz)
                test_end = test_end.tz_localize(tz)
            
            has_train = (start_time <= train_start) and (end_time >= train_end)
            has_test = (start_time <= test_start) and (end_time >= test_end)
            
            print(f"  Train period (2017-2020): {'✅' if has_train else '❌'}")
            print(f"  Test period (2021-2025):  {'✅' if has_test else '❌'}")
            
        except Exception as e:
            print(f"\n{symbol}: ERROR - {e}")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    check_data_range()

