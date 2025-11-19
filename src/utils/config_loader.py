"""
Configuration loader with variable substitution support
"""

import os
import re
from pathlib import Path
from typing import Any, Dict

import yaml


def load_yaml(path: str | Path) -> Dict[str, Any]:
    """
    Load YAML configuration file
    
    Args:
        path: Path to YAML file
        
    Returns:
        Dictionary containing configuration
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config if config is not None else {}


def substitute_variables(config: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Recursively substitute ${var} style variables in config
    
    Args:
        config: Configuration dictionary
        context: Variable context for substitution
        
    Returns:
        Config with variables substituted
    """
    if context is None:
        context = {}
    
    # Add config itself to context for self-referencing
    context.update(config)
    
    def _substitute(obj):
        if isinstance(obj, str):
            # Find all ${var} patterns
            pattern = r'\$\{([^}]+)\}'
            matches = re.findall(pattern, obj)
            
            result = obj
            for var_name in matches:
                if var_name in context:
                    var_value = str(context[var_name])
                    result = result.replace(f'${{{var_name}}}', var_value)
            
            return result
        
        elif isinstance(obj, dict):
            return {k: _substitute(v) for k, v in obj.items()}
        
        elif isinstance(obj, list):
            return [_substitute(item) for item in obj]
        
        else:
            return obj
    
    return _substitute(config)


def get_project_root() -> Path:
    """Get project root directory"""
    # Assume this file is in src/utils/
    return Path(__file__).parent.parent.parent


def load_paths_config() -> Dict[str, Any]:
    """
    Load paths configuration with variable substitution
    
    Returns:
        Paths configuration dictionary
    """
    project_root = get_project_root()
    config_path = project_root / "config" / "paths.yaml"
    
    config = load_yaml(config_path)
    
    # Substitute variables
    config = substitute_variables(config)
    
    # Convert relative paths to absolute
    for key in ['manip_project_root', 'ofi_project_root']:
        if key in config:
            path = Path(config[key])
            if not path.is_absolute():
                config[key] = str((project_root / path).resolve())
    
    return config


def load_symbols_config() -> Dict[str, Any]:
    """
    Load symbols configuration
    
    Returns:
        Symbols configuration dictionary
    """
    project_root = get_project_root()
    config_path = project_root / "config" / "symbols.yaml"
    
    return load_yaml(config_path)


def load_joint_params_config(config_file: str = "joint_params.yaml") -> Dict[str, Any]:
    """
    Load joint parameters configuration

    Args:
        config_file: Name of the config file (default: joint_params.yaml)

    Returns:
        Joint parameters configuration dictionary
    """
    project_root = get_project_root()
    config_path = project_root / "config" / config_file

    return load_yaml(config_path)


def load_factors_config() -> Dict[str, Any]:
    """
    Load factors configuration
    
    Returns:
        Factors configuration dictionary
    """
    project_root = get_project_root()
    config_path = project_root / "config" / "factors.yaml"
    
    return load_yaml(config_path)


def get_enabled_factors() -> list[str]:
    """
    Get list of enabled factor names

    Returns:
        List of enabled factor names
    """
    config = load_factors_config()
    factors = config.get('factors', {})

    return [
        name for name, spec in factors.items()
        if spec.get('enabled', False)
    ]


def load_oos_splits_config() -> Dict[str, Any]:
    """
    Load out-of-sample (OOS) time splits configuration

    Returns:
        OOS splits configuration dictionary

    Raises:
        FileNotFoundError: If config file not found
        ValueError: If date validation fails
    """
    import pandas as pd

    project_root = get_project_root()
    config_path = project_root / "config" / "oos_splits.yaml"

    config = load_yaml(config_path)

    # Validate each symbol's time splits
    symbols = config.get('symbols', {})
    for symbol, splits in symbols.items():
        # Check required fields
        required_fields = ['timeframe', 'train_start', 'train_end', 'test_start', 'test_end']
        for field in required_fields:
            if field not in splits:
                raise ValueError(f"Missing required field '{field}' for symbol {symbol}")

        # Validate date format and ordering
        try:
            train_start = pd.to_datetime(splits['train_start'])
            train_end = pd.to_datetime(splits['train_end'])
            test_start = pd.to_datetime(splits['test_start'])
            test_end = pd.to_datetime(splits['test_end'])

            # Check ordering
            if train_start >= train_end:
                raise ValueError(f"{symbol}: train_start must be before train_end")
            if test_start >= test_end:
                raise ValueError(f"{symbol}: test_start must be before test_end")
            if train_end >= test_start:
                raise ValueError(f"{symbol}: train_end must be before test_start (no overlap)")

        except Exception as e:
            raise ValueError(f"Invalid date format for symbol {symbol}: {e}")

    return config

