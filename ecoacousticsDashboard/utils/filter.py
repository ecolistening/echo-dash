import pandas as pd

from loguru import logger
from datetime import date
from typing import Tuple, List

def filter_data(
    data: pd.DataFrame,
    dates: List[str] | None = None,
    feature: str | None = None,
    feature_range: Tuple[float, float] | None = None,
    locations: List[str] | None = None,
    sample_size: int | None = None,
) -> pd.DataFrame:
    if dates is not None:
        dates = [date.fromisoformat(d) for d in dates]
        data = data[data.timestamp.dt.date.between(*dates)]

    if feature is not None:
        data = data[data.feature == feature]

    if feature_range is not None:
        feature_min, feature_max = feature_range
        data = data[(feature_min <= data.value) & (data.value <= feature_max)]

    if locations is not None and len(locations) > 0:
        # changed it from locations[-1] after unpacking nested list in list2tuple - Potential source for problems
        data = data[data['site'].isin([l.strip('/') for l in locations])]

    if sample_size is not None:
        sample_size = int(sample_size)
        data = data.sample(n=sample_size, random_state=42)

    return data
