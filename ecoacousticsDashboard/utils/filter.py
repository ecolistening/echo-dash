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
    file_ids: List[str] | None = None,
    temperature_2m: Tuple[float, float] | None = None,
    precipitation: Tuple[float, float] | None = None,
    snowfall: Tuple[float, float] | None = None,
    rain: Tuple[float, float] | None = None,
    wind_speed_10m: Tuple[float, float] | None = None,
    wind_speed_100m: Tuple[float, float] | None = None,
    wind_direction_10m: Tuple[float, float] | None = None,
    wind_direction_100m: Tuple[float, float] | None = None,
    wind_gusts_10m: Tuple[float, float] | None = None,
) -> pd.DataFrame:
    if file_ids is not None:
        data = data[~data["file_id"].isin(file_ids)]

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

    # FIXME: not a particularly dynamic or intelligent solution but its good enough
    # this should really be data-driven, not hard coded
    if temperature_2m is not None:
        data = data[(data["temperature_2m"] >= min(temperature_2m)) & (data["temperature_2m"] <= max(temperature_2m))]
    if precipitation is not None:
        data = data[(data["precipitation"] >= min(precipitation)) & (data["precipitation"] <= max(precipitation))]
    if snowfall is not None:
        data = data[(data["snowfall"] >= min(snowfall)) & (data["snowfall"] <= max(snowfall))]
    if rain is not None:
        data = data[(data["rain"] >= min(rain)) & (data["rain"] <= max(rain))]
    if wind_speed_10m is not None:
        data = data[(data["wind_speed_10m"] >= min(wind_speed_10m)) & (data["wind_speed_10m"] <= max(wind_speed_10m))]
    if wind_speed_100m is not None:
        data = data[(data["wind_speed_100m"] >= min(wind_speed_100m)) & (data["wind_speed_100m"] <= max(wind_speed_100m))]
    if wind_direction_10m is not None:
        data = data[(data["wind_direction_10m"] >= min(wind_direction_10m)) & (data["wind_direction_10m"] <= max(wind_direction_10m))]
    if wind_direction_100m is not None:
        data = data[(data["wind_direction_100m"] >= min(wind_direction_100m)) & (data["wind_direction_100m"] <= max(wind_direction_100m))]
    if wind_gusts_10m is not None:
        data = data[(data["wind_gusts_10m"] >= min(wind_gusts_10m)) & (data["wind_gusts_10m"] <= max(wind_gusts_10m))]

    if sample_size is not None and len(data) > sample_size:
        data = data.sample(n=int(sample_size), random_state=42)

    return data
