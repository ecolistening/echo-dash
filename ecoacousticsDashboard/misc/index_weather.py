import argparse
import datetime as dt
import numpy as np
import pandas as pd
import pyarrow as pa
import time
import itertools
import openmeteo_requests
import requests_cache

from pathlib import Path
from loguru import logger
from typing import Any, Dict, Tuple, List
from retry_requests import retry

OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

_client = None

def init_client(**kwargs):
    global _client
    if _client is None:
        _client = OpenMeteoClient(**kwargs)
    return _client

def OpenMeteoClient(
    retries: int = 5,
    expire_after: int = -1,
    backoff_factor: float = 0.2,
) -> openmeteo_requests.Client:
    cache_session = requests_cache.CachedSession('.cache', expire_after=expire_after)
    retry_session = retry(cache_session, retries=retries, backoff_factor=backoff_factor)
    return openmeteo_requests.Client(session=retry_session)

DEFAULT_WEATHER_COLUMNS = [
    "temperature_2m",
    "rain",
    "precipitation",
    "snowfall",
    "wind_speed_10m",
    "wind_speed_100m",
    "wind_direction_10m",
    "wind_direction_100m",
    "wind_gusts_10m",
]

def find_weather_hourly(
    d: Dict[str, Any],
    columns: List[str] = DEFAULT_WEATHER_COLUMNS,
) -> Dict[str, Any]:
    client = init_client()
    params = {
        "latitude": d["latitude"],
        "longitude": d["longitude"],
        "start_date": d["start_date"],
        "end_date": d["end_date"],
        "hourly": columns,
    }
    # Probably need to try/catch?
    responses = client.weather_api(OPEN_METEO_ARCHIVE_URL, params=params)
    hourly = responses[0].Hourly()
    data = {
        column: hourly.Variables(i).ValuesAsNumpy()
        for i, column in enumerate(columns)
    }
    df = pd.DataFrame({
        "timestamp": pd.date_range(
            pd.to_datetime(hourly.Time(), unit="s", utc=True),
            pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        ),
        **data,
    })
    df["site_id"] = d["site_id"]
    return df.to_dict(orient="records")

def index_weather(
    files_df: pd.DataFrame,
    sites_df: pd.DataFrame,
    save_dir: str | Path | None = None,
) -> None:
    start_time = time.time()
    logger.info("Fetching weather data from open meteo")
    df = (
        files_df[["site_id", "timestamp"]]
        .groupby("site_id")
        .agg(start_date=("timestamp", lambda x: x.dt.date.min()), end_date=("timestamp", lambda x: x.dt.date.max()))
        .join(sites_df[["latitude", "longitude", "site_name"]], how="left")
        .reset_index()
    )
    weather_df = pd.DataFrame(list(itertools.chain(*list(map(find_weather_hourly, df.to_dict(orient="records"))))))
    if save_dir is not None:
        weather_df.to_parquet(save_dir / "weather_table.parquet")
    print(weather_df)

def main(
    files_path: str | Path,
    sites_path: str | Path,
    save_dir: str | Path,
) -> None:
    index_weather(
        files_df=pd.read_parquet(files_path),
        sites_df=pd.read_parquet(sites_path),
        save_dir=save_dir,
    )

def get_base_parser():
    parser = argparse.ArgumentParser(
        description='Fetch and persist weather data for audio files',
        add_help=False,
    )
    parser.add_argument(
        "--files-path",
        required=True,
        type=lambda p: Path(p),
        help="Parquet file containing site information."
    )
    parser.add_argument(
        "--sites-path",
        required=True,
        type=lambda p: Path(p),
        help="Parquet file containing site information."
    )
    parser.add_argument(
        "--save-dir",
        default=None,
        type=lambda p: Path(p),
        help="Parquet file containing site information."
    )
    return parser

if __name__ == '__main__':
    parser = get_base_parser()
    args = parser.parse_args()
    main(**vars(args))
