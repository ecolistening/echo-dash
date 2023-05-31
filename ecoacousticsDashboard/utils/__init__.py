from pathlib import Path
import os
from typing import List

import pandas as pd


def is_docker():
    cgroup = Path('/proc/self/cgroup')
    return (
            os.path.exists('/.dockerenv') or
            os.path.isfile(cgroup) and any('docker' in line for line in open(cgroup))
    )

def filter_dataset(df: pd.DataFrame, dates=None, feature: str=None, locations: List=None):
    data = df

    if dates is not None:
        pass

    if feature is not None:
        data = data[data.feature == feature]

    if locations is not None and locations != []:
        data = data[data.recorder.isin(locations)]

    return data