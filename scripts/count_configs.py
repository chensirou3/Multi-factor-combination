#!/usr/bin/env python3
"""Count configurations in parameter grid"""

import yaml
from pathlib import Path

config_file = Path(__file__).parent.parent / "config" / "joint_params_fine.yaml"

with open(config_file) as f:
    cfg = yaml.safe_load(f)

filter_params = cfg['filter_mode']
score_params = cfg['score_mode']

filter_count = len(filter_params['ofi_abs_z_max']) * len(filter_params['manip_z_entry']) * len(filter_params['holding_bars'])
score_count = len(score_params['weights']) * len(score_params['composite_z_entry']) * len(score_params['holding_bars'])

print(f'Filter mode: {filter_count} configurations')
print(f'  - OFI thresholds: {len(filter_params["ofi_abs_z_max"])}')
print(f'  - ManipScore thresholds: {len(filter_params["manip_z_entry"])}')
print(f'  - Holding periods: {len(filter_params["holding_bars"])}')
print(f'')
print(f'Score mode: {score_count} configurations')
print(f'  - Weight combinations: {len(score_params["weights"])}')
print(f'  - Z-score thresholds: {len(score_params["composite_z_entry"])}')
print(f'  - Holding periods: {len(score_params["holding_bars"])}')
print(f'')
print(f'Total per symbol: {filter_count + score_count} configurations')
print(f'Total for 5 symbols: {(filter_count + score_count) * 5} configurations')

