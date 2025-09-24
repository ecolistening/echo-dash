from __future__ import annotations

import bigtree as bt
import functools
import pandas as pd
import numpy as np
import itertools
import datetime as dt

from io import StringIO
from dash import ctx
from loguru import logger
from typing import Any, Dict, List, Tuple

from config import root_dir
from datasets.dataset_loader import DatasetLoader
from datasets.dataset import Dataset
from datasets.decorator import DatasetDecorator
from utils import list2tuple, hashify
from utils.filter import filter_data

DATASETS = DatasetLoader(root_dir)

def filter_sites_query(sites, filters):
    sites = sites[sites['site'].isin([l.strip('/') for l in filters["current_sites"]])].reset_index()
    site_ids = ", ".join([f"'{site_id}'" for site_id in sites.site_id])
    return f"site_id in ({site_ids})"

def filter_files_query(filters):
    file_ids = ", ".join([f"{file_id}" for file_id in itertools.chain(*filters["files"].values())])
    return f"file_id not in ({file_ids})"

def filter_dates_query(filters):
    return f"timestamp >= '{filters['date_range'][0]}' and timestamp <= '{filters['date_range'][1]}'"

def filter_weather_query(filters):
    return " and ".join([
        f"(({variable_name} >= {params['variable_range'][0]} and {variable_name} <= {params['variable_range'][1]}) or {variable_name}.isnull())"
        for variable_name, params in filters["weather_variables"].items()
    ])

def filter_feature_query(filters):
    return f"`{filters['current_feature']}` >= {filters['current_feature_range'][0]} and `{filters['current_feature']}` <= {filters['current_feature_range'][1]}"

@functools.lru_cache(maxsize=1)
def fetch_datasets():
    return [dataset.dataset_name for dataset in DATASETS]

@functools.lru_cache(maxsize=3)
def fetch_dataset(
    dataset_name: str
) -> Dataset:
    dataset = DATASETS.get_dataset(dataset_name)
    return dataset

def set_current_dataset(
    dataset_name: str,
) -> str:
    return dataset_name

@functools.lru_cache(maxsize=3)
def fetch_dataset_config(
    dataset_name: str
) -> Dict[str, Any]:
    dataset = fetch_dataset(dataset_name)
    return {
        section: dict(dataset.config.items(section))
        for section in dataset.config.sections()
    }

@functools.lru_cache(maxsize=3)
def fetch_sites_tree(
    dataset_name: str,
):
    dataset = DATASETS.get_dataset(dataset_name)
    return dataset.sites_tree

def set_dataset_config(
    dataset_name: str,
    site_labels: List[str] = [],
) -> Dict[str, Any]:
    dataset = DATASETS.get_dataset(dataset_name)
    for i, label in enumerate(site_labels):
        dataset.config.set("Site Hierarchy", f"sitelevel_{i + 1}", label)
    dataset.save_config()
    fetch_dataset_config.cache_clear()
    fetch_sites_tree.cache_clear()
    return {
        section: dict(dataset.config.items(section))
        for section in dataset.config.sections()
    }

# @functools.lru_cache(maxsize=3)
def fetch_dataset_options(
    dataset_name: str
) -> Dict[str, Any]:
    dataset = DATASETS.get_dataset(dataset_name)
    return DatasetDecorator(dataset).options

# @functools.lru_cache(maxsize=3)
def fetch_dataset_dropdown_option_groups(
    dataset_name: str,
    options: Tuple[str] = (),
) -> Dict[str, Any]:
    dataset = DATASETS.get_dataset(dataset_name)
    decorator = DatasetDecorator(dataset)
    return decorator.drop_down_select_option_groups(options)

# @functools.lru_cache(maxsize=3)
def fetch_dataset_category_orders(
    dataset_name: str
) -> Dict[str, Any]:
    dataset = DATASETS.get_dataset(dataset_name)
    return DatasetDecorator(dataset).category_orders

# @functools.lru_cache(maxsize=3)
def fetch_files(
    dataset_name: str,
    filters: Dict[str, Any] = {},
    valid_only: bool = True,
) -> pd.DataFrame:
    dataset = DATASETS.get_dataset(dataset_name)
    if not len(filters):
        return (
            pd.read_parquet(dataset.path / "files.parquet", columns=["file_id", "file_path", "file_name", "valid", "site_id", "dddn", "timestamp"])
            .merge(dataset.locations, on="site_id", how="left")
        )

    file_query = filter_files_query(filters)
    site_query = filter_sites_query(dataset.locations, filters)
    date_query = filter_dates_query(filters)
    weather_query = filter_weather_query(filters)

    files = (
        pd.read_parquet(dataset.path / "files.parquet", columns=["file_id", "valid", "site_id", "file_name", "dddn", "timestamp"])
        .query(f"valid == True and {file_query} and {date_query} and {site_query}")
        .assign(nearest_hour=lambda df: df["timestamp"].dt.round("h"))
    )
    weather = (
        pd.read_parquet(dataset.path / "weather_table.parquet")
        .rename(columns=dict(timestamp="nearest_hour"))
    )
    return dataset.append_columns(
        files.merge(weather, on=["site_id", "nearest_hour"], how="left")
        .query(weather_query)
        .drop([col for col in weather.columns if col not in ["site_id", "nearest_hour"]], axis=1)
        .merge(dataset.locations, on="site_id", how="left")
    )

# @functools.lru_cache(maxsize=3)
def fetch_locations(
    dataset_name: str,
) -> pd.DataFrame:
    dataset = DATASETS.get_dataset(dataset_name)
    return dataset.locations

# @functools.lru_cache(maxsize=3)
def fetch_weather(
    dataset_name: str,
) -> pd.DataFrame:
    dataset = DATASETS.get_dataset(dataset_name)
    return pd.read_parquet(dataset.path / "weather_table.parquet")

# @functools.lru_cache(maxsize=10)
def fetch_file_weather(
    dataset_name: str,
    filters: Dict[str, Any] = {},
) -> pd.DataFrame:
    dataset = DATASETS.get_dataset(dataset_name)
    if not len(filters):
        return pd.read_parquet(dataset.path / "weather_table.parquet")

    file_query = filter_files_query(filters)
    site_query = filter_sites_query(dataset.locations, filters)
    date_query = filter_dates_query(filters)
    weather_query = filter_weather_query(filters)

    files = (
        pd.read_parquet(dataset.path / "files.parquet", columns=["file_id", "valid", "site_id", "file_name", "dddn", "timestamp"])
        .assign(nearest_hour=lambda df: df["timestamp"].dt.round("h"))
        .query(f"valid == True and {file_query} and {date_query} and {site_query}")
    )
    weather = (
        pd.read_parquet(dataset.path / "weather_table.parquet")
        .rename(columns=dict(timestamp="nearest_hour"))
    )
    return dataset.append_columns(
        files.merge(weather, on=["site_id", "nearest_hour"], how="left")
        .query(weather_query)
        .melt(id_vars=["file_id", "site_id", "nearest_hour", "timestamp"], var_name="variable", value_name="value")
        .merge(dataset.locations, on="site_id", how="left")
    )

# @functools.lru_cache(maxsize=10)
def fetch_acoustic_features(
    dataset_name: str,
    filters: Dict[str, Any] = {},
) -> pd.DataFrame:
    dataset = DATASETS.get_dataset(dataset_name)
    if not len(filters):
        return pd.read_parquet(dataset.path / "recording_acoustic_features.parquet")

    file_query = filter_files_query(filters)
    site_query = filter_sites_query(dataset.locations, filters)
    date_query = filter_dates_query(filters)
    weather_query = filter_weather_query(filters)
    feature_query = filter_feature_query(filters)

    files = (
        pd.read_parquet(dataset.path / "files.parquet", columns=["file_id", "valid", "site_id", "file_name", "dddn", "timestamp"])
        .query(f"valid == True and {file_query} and {date_query} and {site_query}")
        .assign(nearest_hour=lambda df: df["timestamp"].dt.round("h"))
    )
    weather = (
        pd.read_parquet(dataset.path / "weather_table.parquet")
        .rename(columns=dict(timestamp="nearest_hour"))
    )
    file_site_weather = (
        files.merge(weather, on=["site_id", "nearest_hour"], how="left")
        .query(weather_query)
        .drop([col for col in weather.columns if col not in ["site_id", "nearest_hour"]], axis=1)
        .merge(dataset.locations, on="site_id", how="left")
    )
    features = (
        pd.read_parquet(dataset.path / "recording_acoustic_features.parquet", columns=["file_id", "segment_id", "duration", "offset", filters["current_feature"]])
        .query(f"file_id in ({', '.join([f'{file_id}' for file_id in files.file_id])}) and {feature_query}")
        .assign(feature=lambda df: filters["current_feature"])
        .rename(columns={filters["current_feature"]: "value"})
    )
    return dataset.append_columns(features.merge(file_site_weather, on="file_id", how="left"))

# @functools.lru_cache(maxsize=10)
def fetch_birdnet_species(
    dataset_name: str,
    threshold: float,
    filters: Dict[str, Any] = {},
) -> pd.DataFrame:
    dataset = DATASETS.get_dataset(dataset_name)
    decorator = DatasetDecorator(dataset)
    sites = dataset.locations

    file_query = filter_files_query(filters)
    site_query = filter_sites_query(dataset.locations, filters)
    date_query = filter_dates_query(filters)
    weather_query = filter_weather_query(filters)

    files = (
        pd.read_parquet(dataset.path / "files.parquet", columns=["file_id", "valid", "site_id", "file_name", "dddn", "timestamp"])
        .query(f"valid == True and {file_query} and {date_query} and {site_query}")
        .assign(nearest_hour=lambda df: df["timestamp"].dt.round("h"))
    )
    weather = (
        pd.read_parquet(dataset.path / "weather_table.parquet")
        .rename(columns=dict(timestamp="nearest_hour"))
    )
    file_site_weather = (
        files.merge(weather, on=["site_id", "nearest_hour"], how="left")
        .query(weather_query)
        .drop([col for col in weather.columns if col not in ["site_id", "nearest_hour"]], axis=1)
        .merge(dataset.locations, on="site_id", how="left")
    )
    species = (
        pd.read_parquet(
            dataset.path.parent / "species_table.parquet",
            columns=["scientific_name", "common_name", *decorator.species_habitat_columns, *decorator.species_functional_group_columns],
        )
        .assign(species=lambda df: df[["scientific_name", "common_name"]].agg("\n".join, axis=1))
    )
    species_probs = (
        pd.read_parquet(dataset.path / "birdnet_species_probs.parquet", columns=["file_id", "scientific_name", "confidence"])
        .query(f"confidence >= {threshold} and file_id in ({', '.join([f'{file_id}' for file_id in file_site_weather.file_id])})")
        .assign(detected=lambda df: [1] * len(df))
    )
    return dataset.append_columns(
        species_probs
        .merge(species, on="scientific_name", how="left")
        .merge(file_site_weather, on="file_id", how="left")
    )

# @functools.lru_cache(maxsize=4)
def fetch_acoustic_features_umap(
    dataset_name: str,
    filters: Dict[str, Any],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    dataset = DATASETS.get_dataset(dataset_name)

    file_query = filter_files_query(filters)
    site_query = filter_sites_query(dataset.locations, filters)
    date_query = filter_dates_query(filters)
    weather_query = filter_weather_query(filters)

    files = (
        pd.read_parquet(dataset.path / "files.parquet", columns=["file_id", "valid", "site_id", "file_name", "dddn", "timestamp"])
        .query(f"valid == True and {file_query} and {date_query} and {site_query}")
        .assign(nearest_hour=lambda df: df["timestamp"].dt.round("h"))
    )
    weather = (
        pd.read_parquet(dataset.path / "weather_table.parquet")
        .rename(columns=dict(timestamp="nearest_hour"))
    )
    file_site_weather = (
        files.merge(weather, on=["site_id", "nearest_hour"], how="left")
        .query(weather_query)
        .drop([col for col in weather.columns if col not in ["site_id", "nearest_hour"]], axis=1)
        .merge(dataset.locations, on="site_id", how="left")
    )
    features = dataset.umap(
        pd.read_parquet(dataset.path / "recording_acoustic_features.parquet")
        .query(f"file_id in ({', '.join([f'{file_id}' for file_id in files.file_id])})")
    )
    return dataset.append_columns(
        file_site_weather
        .merge(features, on="file_id", how="left")
    )

from dash import exceptions

def dispatch(
    action: str,
    default: Any | None = None,
    **payload: Dict[str, Any],
) -> Any:
    try:
        func = API[action]
        return func(**payload)
    except Exception as e:
        logger.error(e)
        return default

FETCH_DATASETS = "fetch_datasets"
FETCH_DATASET = "fetch_dataset"
SET_CURRENT_DATASET = "set_current_dataset"
FETCH_DATASET_CONFIG = "fetch_dataset_config"
SET_DATASET_CONFIG = "set_dataset_config"
FETCH_DATASET_SITES_TREE = "fetch_dataset_sites_tree"

FETCH_DATASET_OPTIONS = "fetch_dataset_options"
FETCH_DATASET_CATEGORY_ORDERS = "fetch_dataset_category_orders"
FETCH_DATASET_DROPDOWN_OPTION_GROUPS = "fetch_dataset_dropdown_option_groups"

FETCH_FILES = "fetch_files"
FETCH_LOCATIONS = "fetch_locations"
FETCH_ACOUSTIC_FEATURES = "fetch_acoustic_features"
FETCH_ACOUSTIC_FEATURES_UMAP = "fetch_acoustic_features_umap"
FETCH_BIRDNET_SPECIES = "fetch_birdnet_species"
FETCH_WEATHER = "fetch_weather"
FETCH_FILE_WEATHER = "fetch_file_weather"

API = {
    FETCH_DATASETS: fetch_datasets,
    FETCH_DATASET: fetch_dataset,
    SET_CURRENT_DATASET: set_current_dataset,
    FETCH_DATASET_CONFIG: fetch_dataset_config,
    SET_DATASET_CONFIG: set_dataset_config,
    FETCH_DATASET_SITES_TREE: fetch_sites_tree,

    FETCH_DATASET_OPTIONS: fetch_dataset_options,
    FETCH_DATASET_CATEGORY_ORDERS: fetch_dataset_category_orders,
    FETCH_DATASET_DROPDOWN_OPTION_GROUPS: fetch_dataset_dropdown_option_groups,

    FETCH_FILES: fetch_files,
    FETCH_LOCATIONS: fetch_locations,
    FETCH_ACOUSTIC_FEATURES: fetch_acoustic_features,
    FETCH_ACOUSTIC_FEATURES_UMAP: fetch_acoustic_features_umap,
    FETCH_BIRDNET_SPECIES: fetch_birdnet_species,
    FETCH_WEATHER: fetch_weather,
    FETCH_FILE_WEATHER: fetch_file_weather,
}
