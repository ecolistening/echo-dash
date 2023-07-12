from datetime import date
from typing import List
import pandas as pd

from config import root_dir


def load_and_filter_dataset(dataset: str, dates=None, feature: str=None, locations: List=None, recorders: List=None):
    data = pd.read_parquet(root_dir / dataset / 'indices.parquet')#.drop_duplicates()
    recorders = [int(r) for r in recorders]

    dates = [date.fromisoformat(d) for d in dates]
    if dates is not None:
        data = data[data.timestamp.dt.date.between(*dates)]

    if feature is not None:
        data = data[data.feature == feature]

    if locations is not None and len(locations) > 0:
        data = data[data['location'].isin(locations)]

    if recorders is not None and len(recorders) > 0:
        data = data[data.recorder.isin(recorders)]

    return data

