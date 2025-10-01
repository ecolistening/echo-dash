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
from utils.filter import (
    filter_sites_query,
    filter_files_query,
    filter_dates_query,
    filter_weather_query,
    filter_feature_query,
)

DATASETS = DatasetLoader(root_dir)

def filter_dict_to_tuples(filters):
    filters_args = {
        "current_sites": list2tuple(filters["current_sites"]),
        "current_date_range": list2tuple(filters["date_range"]),
        "current_feature": (filters["current_feature"], list2tuple(filters["current_feature_range"])),
        "current_file_ids": list2tuple(list(itertools.chain(*filters["files"].values()))),
        "current_weather": list2tuple([(variable_name, list2tuple(params["variable_range"])) for variable_name, params in filters["weather_variables"].items()]),
        "current_species": list2tuple(filters["species"]),
    }
    return filters_args

@functools.lru_cache(maxsize=1)
def fetch_datasets():
    return [dataset.dataset_name for dataset in DATASETS]

@functools.lru_cache(maxsize=3)
def fetch_dataset(
    dataset_name: str
) -> Dataset:
    dataset = DATASETS.get_dataset(dataset_name)
    return dataset

def fetch_base_filters(
    dataset_name: str
) -> Dataset:
    dataset = DATASETS.get_dataset(dataset_name)
    return dataset.filters

def set_current_dataset(
    dataset_name: str,
) -> str:
    return dataset_name

@functools.lru_cache(maxsize=3)
def fetch_dataset_config(
    dataset_name: str
) -> Dict[str, Any]:
    dataset = fetch_dataset(dataset_name)
    return { "SoundADE": dataset.soundade_config } | {
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
    return { "SoundADE": dataset.soundade_config } | {
        section: dict(dataset.config.items(section))
        for section in dataset.config.sections()
    }

def fetch_dataset_options(
    dataset_name: str
) -> Dict[str, Any]:
    dataset = DATASETS.get_dataset(dataset_name)
    return DatasetDecorator(dataset).options

def fetch_dataset_dropdown_option_groups(
    dataset_name: str,
    options: Tuple[str] = (),
) -> Dict[str, Any]:
    dataset = DATASETS.get_dataset(dataset_name)
    decorator = DatasetDecorator(dataset)
    return decorator.drop_down_select_option_groups(options)

def fetch_dataset_category_orders(
    dataset_name: str
) -> Dict[str, Any]:
    dataset = DATASETS.get_dataset(dataset_name)
    return DatasetDecorator(dataset).category_orders

def fetch_species_list(
    dataset_name: str,
) -> None:
    dataset = DATASETS.get_dataset(dataset_name)
    species_list = dataset.species_list()
    logger.info(f"{species_list=}")
    return species_list

def set_species_list(
    dataset_name: str,
    species_list: Tuple[str, ...]
) -> None:
    dataset = DATASETS.get_dataset(dataset_name)
    dataset.save_species_list(species_list)
    return True

@functools.lru_cache(maxsize=3)
def fetch_files(
    dataset_name: str,
    current_sites: Tuple[str, ...] = tuple(),
    current_date_range: Tuple[str, ...] = tuple(),
    current_feature: Tuple[str, Tuple[float, ...]] = tuple(),
    current_file_ids: Tuple[str, ...] = tuple(),
    current_weather: Tuple[str, Tuple[float, ...]] = tuple(),
    valid_only: bool = True,
    **kwargs: Any,
) -> pd.DataFrame:
    dataset = DATASETS.get_dataset(dataset_name)
    files = (
        pd.read_parquet(dataset.path / "files_table.parquet", columns=["file_id", "valid", "site_id", "file_name", "file_path", "dddn", "timestamp", "hours after sunrise", "hours after dawn", "hours after noon", "hours after dusk", "hours after sunset"])
        .query(f"{'valid == True and ' if valid_only else ''}{filter_files_query(current_file_ids)} and {filter_sites_query(dataset.locations, current_sites)} and {filter_dates_query(current_date_range)}")
        .assign(nearest_hour=lambda df: df["timestamp"].dt.round("h"))
    )
    weather = (
        pd.read_parquet(dataset.path / "weather_table.parquet")
        .rename(columns=dict(timestamp="nearest_hour"))
    )
    file_site_weather = (
        files.merge(weather, on=["site_id", "nearest_hour"], how="left")
        .query(filter_weather_query(current_weather))
        # .drop([col for col in weather.columns if col not in ["site_id", "nearest_hour"]], axis=1)
        .merge(dataset.locations, on="site_id", how="left")
    )
    return dataset.append_columns(file_site_weather)

@functools.lru_cache(maxsize=3)
def fetch_locations(
    dataset_name: str,
) -> pd.DataFrame:
    dataset = DATASETS.get_dataset(dataset_name)
    return dataset.locations

@functools.lru_cache(maxsize=3)
def fetch_species(
    dataset_name: str,
) -> pd.DataFrame:
    dataset = DATASETS.get_dataset(dataset_name)
    return dataset.species

@functools.lru_cache(maxsize=3)
def fetch_weather(
    dataset_name: str,
) -> pd.DataFrame:
    dataset = DATASETS.get_dataset(dataset_name)
    return pd.read_parquet(dataset.path / "weather_table.parquet")

@functools.lru_cache(maxsize=10)
def fetch_file_weather(
    dataset_name: str,
    current_sites: Tuple[str, ...],
    current_date_range: Tuple[str, ...],
    current_feature: Tuple[str, Tuple[float, ...]],
    current_file_ids: Tuple[str, ...],
    current_weather: Tuple[str, Tuple[float, ...]],
    **kwargs: Any,
) -> pd.DataFrame:
    dataset = DATASETS.get_dataset(dataset_name)
    files = (
        pd.read_parquet(dataset.path / "files_table.parquet", columns=["file_id", "valid", "site_id", "file_name", "file_path", "dddn", "timestamp", "hours after sunrise", "hours after dawn", "hours after noon", "hours after dusk", "hours after sunset"])
        .assign(nearest_hour=lambda df: df["timestamp"].dt.round("h"))
        .query(f"valid == True and {filter_files_query(current_file_ids)} and {filter_sites_query(dataset.locations, current_sites)} and {filter_dates_query(current_date_range)}")
    )
    weather = (
        pd.read_parquet(dataset.path / "weather_table.parquet")
        .rename(columns=dict(timestamp="nearest_hour"))
    )
    return dataset.append_columns(
        files.merge(weather, on=["site_id", "nearest_hour"], how="left")
        .query(filter_weather_query(current_weather))
        .merge(dataset.locations, on="site_id", how="left")
        .melt(id_vars=["file_id", "site_id", "nearest_hour", "timestamp", *dataset.locations.columns], var_name="variable", value_name="value")
    )

@functools.lru_cache(maxsize=10)
def fetch_acoustic_features(
    dataset_name: str,
    current_sites: Tuple[str, ...],
    current_date_range: Tuple[str, ...],
    current_feature: Tuple[str, Tuple[float, ...]],
    current_file_ids: Tuple[str, ...],
    current_weather: Tuple[str, Tuple[float, ...]],
    **kwargs: Any,
) -> pd.DataFrame:
    dataset = DATASETS.get_dataset(dataset_name)
    files = (
        pd.read_parquet(dataset.path / "files_table.parquet", columns=["file_id", "valid", "site_id", "file_name", "file_path", "dddn", "timestamp", "hours after sunrise", "hours after dawn", "hours after noon", "hours after dusk", "hours after sunset"])
        .query(f"valid == True and {filter_files_query(current_file_ids)} and {filter_sites_query(dataset.locations, current_sites)} and {filter_dates_query(current_date_range)}")
        .assign(nearest_hour=lambda df: df["timestamp"].dt.round("h"))
    )
    weather = (
        pd.read_parquet(dataset.path / "weather_table.parquet")
        .rename(columns=dict(timestamp="nearest_hour"))
    )
    file_site_weather = (
        files.merge(weather, on=["site_id", "nearest_hour"], how="left")
        .query(filter_weather_query(current_weather))
        # .drop([col for col in weather.columns if col not in ["site_id", "nearest_hour"]], axis=1)
        .merge(dataset.locations, on="site_id", how="left")
    )
    file_ids = ", ".join([f"'{file_id}'" for file_id in file_site_weather.file_id])
    features = (
        pd.read_parquet(dataset.path / "recording_acoustic_features_table.parquet", columns=["file_id", "segment_id", "duration", "offset", current_feature[0]])
        .query(f"file_id in ({file_ids}) and {filter_feature_query(current_feature)}")
        .assign(feature=lambda df: current_feature[0])
        .rename(columns={current_feature[0]: "value"})
    )
    return dataset.append_columns(features.merge(file_site_weather, on="file_id", how="left"))

@functools.lru_cache(maxsize=10)
def fetch_birdnet_species(
    dataset_name: str,
    threshold: float,
    current_sites: Tuple[str, ...],
    current_date_range: Tuple[str, ...],
    current_feature: Tuple[str, Tuple[float, ...]],
    current_file_ids: Tuple[str, ...],
    current_weather: Tuple[str, Tuple[float, ...]],
    current_species: Tuple[str, ...],
    **kwargs: Any,
) -> pd.DataFrame:
    dataset = DATASETS.get_dataset(dataset_name)
    decorator = DatasetDecorator(dataset)

    files = (
        pd.read_parquet(dataset.path / "files_table.parquet", columns=["file_id", "valid", "site_id", "file_name", "file_path", "dddn", "timestamp", "hours after sunrise", "hours after dawn", "hours after noon", "hours after dusk", "hours after sunset"])
        .query(f"valid == True and {filter_files_query(current_file_ids)} and {filter_sites_query(dataset.locations, current_sites)} and {filter_dates_query(current_date_range)}")
        .assign(nearest_hour=lambda df: df["timestamp"].dt.round("h"))
    )
    weather = (
        pd.read_parquet(dataset.path / "weather_table.parquet")
        .rename(columns=dict(timestamp="nearest_hour"))
    )
    file_site_weather = (
        files.merge(weather, on=["site_id", "nearest_hour"], how="left")
        .query(filter_weather_query(current_weather))
        # .drop([col for col in weather.columns if col not in ["site_id", "nearest_hour"]], axis=1)
        .merge(dataset.locations, on="site_id", how="left")
    )
    species = (
        pd.read_parquet(
            dataset.path.parent / "species_table.parquet",
            columns=["scientific_name", "common_name", *decorator.species_habitat_columns, *decorator.species_functional_group_columns],
        )
        .assign(species=lambda df: df[["scientific_name", "common_name"]].agg("\n".join, axis=1))
    )
    if len(current_species):
        species = species[species["scientific_name"].isin(current_species)]
    file_ids = ", ".join([f"'{file_id}'" for file_id in file_site_weather.file_id])
    species_probs = (
        pd.read_parquet(dataset.path / "birdnet_species_probs_table.parquet", columns=["file_id", "scientific_name", "confidence"])
        .query(f"confidence >= {threshold} and file_id in ({file_ids})")
        .assign(detected=lambda df: [1] * len(df))
    )
    return dataset.append_columns(
        species_probs
        .merge(species, on="scientific_name", how="left")
        .merge(file_site_weather, on="file_id", how="left")
    )

@functools.lru_cache(maxsize=4)
def fetch_acoustic_features_umap(
    dataset_name: str,
    current_sites: Tuple[str, ...],
    current_date_range: Tuple[str, ...],
    current_feature: Tuple[str, Tuple[float, ...]],
    current_file_ids: Tuple[str, ...],
    current_weather: Tuple[str, Tuple[float, ...]],
    **kwargs: Any,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    dataset = DATASETS.get_dataset(dataset_name)

    files = (
        pd.read_parquet(dataset.path / "files_table.parquet", columns=["file_id", "valid", "site_id", "file_name", "dddn", "timestamp"])
        .query(f"valid == True and {filter_files_query(current_file_ids)} and {filter_sites_query(dataset.locations, current_sites)} and {filter_dates_query(current_date_range)}")
        .assign(nearest_hour=lambda df: df["timestamp"].dt.round("h"))
    )
    weather = (
        pd.read_parquet(dataset.path / "weather_table.parquet")
        .rename(columns=dict(timestamp="nearest_hour"))
    )
    file_site_weather = (
        files.merge(weather, on=["site_id", "nearest_hour"], how="left")
        .query(filter_weather_query(current_weather))
        # .drop([col for col in weather.columns if col not in ["site_id", "nearest_hour"]], axis=1)
        .merge(dataset.locations, on="site_id", how="left")
    )
    file_ids = ", ".join([f"'{file_id}'" for file_id in file_site_weather.file_id])
    xy = dataset.umap(
        pd.read_parquet(dataset.path / "recording_acoustic_features_table.parquet")
        .query(f"file_id in ({file_ids})")
    )
    return dataset.append_columns(
        file_site_weather
        .merge(xy, on="file_id", how="left")
    )

from dash import exceptions

def dispatch(
    action: str,
    default: Any | None = None,
    **payload: Dict[str, Any],
) -> Any:
    func = API[action]
    return func(**payload)

FETCH_DATASETS = "fetch_datasets"
FETCH_DATASET = "fetch_dataset"
SET_CURRENT_DATASET = "set_current_dataset"
FETCH_DATASET_CONFIG = "fetch_dataset_config"
SET_DATASET_CONFIG = "set_dataset_config"
FETCH_DATASET_SITES_TREE = "fetch_dataset_sites_tree"
FETCH_BASE_FILTERS = "fetch_base_filters"
FETCH_SPECIES_LIST = "fetch_species_list"
SET_SPECIES_LIST = "set_species_list"

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
FETCH_SPECIES = "fetch_species"

API = {
    FETCH_DATASETS: fetch_datasets,
    FETCH_DATASET: fetch_dataset,
    SET_CURRENT_DATASET: set_current_dataset,
    FETCH_DATASET_CONFIG: fetch_dataset_config,
    SET_DATASET_CONFIG: set_dataset_config,
    FETCH_DATASET_SITES_TREE: fetch_sites_tree,
    FETCH_BASE_FILTERS: fetch_base_filters,
    FETCH_SPECIES_LIST: fetch_species_list,
    SET_SPECIES_LIST: set_species_list,

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
    FETCH_SPECIES: fetch_species,
}
