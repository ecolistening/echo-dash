import os
from pathlib import Path

def is_docker():
    cgroup = Path('/proc/self/cgroup')
    return (
            os.path.exists('/.dockerenv') or
            os.path.isfile(cgroup) and any('docker' in line for line in open(cgroup))
    )

root_dir = Path('/data/')
if not is_docker():
    root_dir = Path('/Users/ca492/Documents/sussex/projects/ecoacoustics-dashboard/data')

#TODO this is redundant with filepath selection based on the menu. Remove.
# Incorporate data
filepath = Path('/data/features.23D17.dashboard_single_values.parquet')
if not is_docker():
    filepath = Path('/Users/ca492/Documents/sussex/projects/ecoacoustics-dashboard/features.23D17.dashboard_single_values.parquet')