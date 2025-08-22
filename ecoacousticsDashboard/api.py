from __future__ import annotations

import bigtree as bt
import functools
import pandas as pd
import numpy as np

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
from utils.umap import umap_data

DATASETS = DatasetLoader(root_dir)

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

@functools.lru_cache(maxsize=3)
def fetch_dataset_options(
    dataset_name: str
) -> Dict[str, Any]:
    dataset = DATASETS.get_dataset(dataset_name)
    return DatasetDecorator(dataset).options

@functools.lru_cache(maxsize=3)
def fetch_dataset_dropdown_option_groups(
    dataset_name: str,
    options: Tuple[str] = (),
) -> Dict[str, Any]:
    dataset = DATASETS.get_dataset(dataset_name)
    return DatasetDecorator(dataset).drop_down_select_option_groups(options)

@functools.lru_cache(maxsize=3)
def fetch_dataset_category_orders(
    dataset_name: str
) -> Dict[str, Any]:
    dataset = DATASETS.get_dataset(dataset_name)
    return DatasetDecorator(dataset).category_orders

@functools.lru_cache(maxsize=3)
def fetch_files(
    dataset_name: str,
    file_ids: List[str] | None = None,
    **filters: Any,
) -> pd.DataFrame:
    dataset = DATASETS.get_dataset(dataset_name)
    file_ids = file_ids or dataset.files.index
    return filter_data(dataset.files.loc[file_ids], **filters)

@functools.lru_cache(maxsize=3)
def fetch_locations(
    dataset_name: str,
) -> pd.DataFrame:
    dataset = DATASETS.get_dataset(dataset_name)
    return dataset.locations

@functools.lru_cache(maxsize=3)
def fetch_weather(
    dataset_name: str,
    **filters: Any,
) -> pd.DataFrame:
    dataset = DATASETS.get_dataset(dataset_name)
    return dataset.weather

@functools.lru_cache(maxsize=10)
def fetch_file_weather(
    dataset_name: str,
    variable: str,
    **filters: Any,
) -> pd.DataFrame:
    dataset = DATASETS.get_dataset(dataset_name)
    id_vars = ["file_id", "site_id", "timestamp_weather", "timestamp"]
    return filter_data((
        dataset.files
        .filter(items=[*id_vars, variable])
        .melt(id_vars=id_vars, var_name="variable", value_name="value")
        .join(dataset.locations, on="site_id", how="left")
    ), **filters)

@functools.lru_cache(maxsize=10)
def fetch_acoustic_features(
    dataset_name: str,
    **filters: Any,
) -> pd.DataFrame:
    dataset = DATASETS.get_dataset(dataset_name)
    data = filter_data(dataset.acoustic_features, **filters)
    return data

@functools.lru_cache(maxsize=10)
def fetch_birdnet_species(
    dataset_name: str,
    **filters: Any,
) -> pd.DataFrame:
    dataset = DATASETS.get_dataset(dataset_name)
    return filter_data(dataset.species_predictions, **filters)

@functools.lru_cache(maxsize=10)
def fetch_birdnet_species_richness(
    dataset_name: str,
    threshold: float,
    group_by: List[str],
    **filters: Any,
) -> pd.DataFrame:
    dataset = DATASETS.get_dataset(dataset_name)
    data = filter_data(dataset.species_predictions, **filters)
    return (
        data[data["confidence"] >= threshold]
        .groupby(list(group_by))["species_id"]
        .nunique()
        .reset_index(name="richness")
    )

@functools.lru_cache(maxsize=4)
def fetch_acoustic_features_umap(
    dataset_name: str,
    file_ids: frozenset = frozenset(),
    **filters: Any,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    dataset = DATASETS.get_dataset(dataset_name)
    data = dataset.acoustic_features_umap
    return filter_data(data, file_ids=file_ids, **filters)

# NOTE:
# Please use the dispatch pattern mapping a string to a function
# instead of making an API function call directly in UI components
#
# Example: dispatch(FETCH_DATASET_CONFIG, dataset_name=dataset_name)
# Returns: { config }
#
# This unifies the API into a single file, making it:
#
# (1) simpler to understand where everything is
# (2) less messy when rendering components in the front-end
# (3) easier to switch to a service-based architecture at a later date

from dash import exceptions

def dispatch(
    action: str,
    default: Any | None = None,
    **payload: Dict[str, Any],
) -> Any:
    try:
        triggered_id = ctx.triggered_id
    except exceptions.MissingCallbackContextException as e:
        triggered_id = "preload"

    logger.debug(f"{triggered_id=} {action=} {payload=}")

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
FETCH_BIRDNET_SPECIES_RICHNESS = "fetch_birdnet_species_richness"
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
    FETCH_BIRDNET_SPECIES_RICHNESS: fetch_birdnet_species_richness,
    FETCH_WEATHER: fetch_weather,
    FETCH_FILE_WEATHER: fetch_file_weather,
}

# TODO: switch to parametric UMAP so we simply load the model in the dataset class, no need to pre-cache
def setup():
    for dataset in DATASETS:
        dispatch(
            FETCH_ACOUSTIC_FEATURES_UMAP,
            dataset_name=dataset.dataset_name,
            dates=(dataset.files.date.min(), dataset.files.date.max()),
            locations=list2tuple(dataset.locations.site_name.unique().tolist()),
            sample_size=len(dispatch(FETCH_FILES, dataset_name=dataset.dataset_name)),
            file_ids=frozenset(),
        )

setup()
