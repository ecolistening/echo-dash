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

def filter_dataset(df: pd.DataFrame, dates=None, feature: str=None, locations: List=None, recorders: List=None):
    data = df
    recorders = [int(r) for r in recorders]

    if dates is not None:
        pass

    if feature is not None:
        data = data[data.feature == feature]

    if locations is not None and len(locations) > 0:
        data = data[data['habitat code'].isin(locations)]

    if recorders is not None and len(recorders) > 0:
        data = data[data.recorder.isin(recorders)]

    return data