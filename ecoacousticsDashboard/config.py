from pathlib import Path

import pandas as pd

from utils import is_docker

# Incorporate data
filepath = Path('/data/features.23D17.dashboard_single_values.parquet')
if not is_docker():
    filepath = Path('/Users/ca492/Documents/sussex/projects/ecoacoustics-dashboard/features.23D17.dashboard_single_values.parquet')