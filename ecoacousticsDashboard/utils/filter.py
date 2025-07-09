import pandas as pd

from loguru import logger
from datetime import date
from typing import List

from utils import list2tuple

def filter_data(
    data: pd.DataFrame,
    dates: List[str] | None = None,
    feature: str | None = None,
    locations: List[str] | None = None,
    sample: int | None = None
) -> pd.DataFrame:
    if dates is not None: dates = list2tuple(dates)
    if feature is not None: feature = str(feature)
    if locations is not None: locations = list2tuple(locations)

    logger.debug(
        f"Filter "
        f"dates:{len(dates) if dates is not None else None} "
        f"locations:{len(locations) if locations is not None else None} "
        f"{feature=}"
    )
    # FIXME remove until filter caching is sorted
    # data = filter_data_lru(data, dates, feature, locations)
    if dates is not None:
        dates = [date.fromisoformat(d) for d in dates]
        data = data[data.timestamp.dt.date.between(*dates)]
        logger.debug(f"Selected Dates: {data.shape=}")

    if feature is not None:
        data = data[data.feature == feature]
        logger.debug(f"Selected Features: {data.shape=}")

    if locations is not None and len(locations) > 0:
        # changed it from locations[-1] after unpacking nested list in list2tuple - Potential source for problems
        data = data[data['site'].isin([l.strip('/') for l in locations])]
        logger.debug(f"Seleted Locations: {data.shape=}")

    # Randomly sample
    if sample is not None:
        sample = int(sample)
        data = data.sample(n=sample, random_state=42)
        logger.debug(f"Selected {sample} random samples: {data.shape=}")

    return data
