from __future__ import annotations

import bigtree as bt
import functools
import pandas as pd
import numpy as np

from io import StringIO
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

def fetch_datasets():
    return [dataset.dataset_name for dataset in DATASETS]

def fetch_dataset(
    dataset_name: str
) -> Dataset:
    dataset = DATASETS.get_dataset(dataset_name)
    return dataset

def set_current_dataset(
    dataset_name: str,
) -> str:
    return dataset_name

def fetch_dataset_config(
    dataset_name: str
) -> Dict[str, Any]:
    dataset = fetch_dataset(dataset_name)
    return {
        section: dict(dataset.config.items(section))
        for section in dataset.config.sections()
    }

def set_dataset_config(
    dataset_name: str,
    site_labels: List[str] = [],
) -> Dict[str, Any]:
    dataset = DATASETS.get_dataset(dataset_name)
    for i, label in enumerate(site_labels):
        dataset.config.set("Site Hierarchy", f"sitelevel_{i + 1}", label)
    dataset.save_config()
    return {
        section: dict(dataset.config.items(section))
        for section in dataset.config.sections()
    }

def fetch_sites_tree(
    dataset_name: str,
):
    dataset = DATASETS.get_dataset(dataset_name)
    return dataset.sites_tree

def fetch_dataset_categories(
    dataset_name: str
) -> Dict[str, Any]:
    dataset = DATASETS.get_dataset(dataset_name)
    return DatasetDecorator(dataset).category_orders()

def fetch_dataset_dropdown_options(
    dataset_name: str
) -> Dict[str, Any]:
    dataset = DATASETS.get_dataset(dataset_name)
    return DatasetDecorator(dataset).drop_down_select_options()

def fetch_dataset_categorical_dropdown_options(
    dataset_name: str
) -> Dict[str, Any]:
    dataset = DATASETS.get_dataset(dataset_name)
    return DatasetDecorator(dataset).categorical_drop_down_select_options()

def fetch_files(
    dataset_name: str,
    file_ids: List[str] | None = None,
    **filters: Any,
) -> pd.DataFrame:
    logger.debug(f"Fetch acoustic feature data for dataset={dataset_name}")
    dataset = DATASETS.get_dataset(dataset_name)
    # FIXME: another hack, we should just be able to get the files table
    # but we have two sources of truth at the moment
    file_ids = file_ids or dataset.files.index
    data = dataset.files.loc[file_ids].join(
        dataset.locations,
        on="site_id",
    ).reset_index().merge(
        dataset.acoustic_features[["file", "site"]],
        left_on=["file_name", "site_name"],
        right_on=["file", "site"],
        how="inner",
        suffixes=('', '_IGNORE'),
    ).drop_duplicates()
    logger.debug(f"Applying filters {filters}")
    return filter_data(data, **filters)

def fetch_locations(
    dataset_name: str,
) -> pd.DataFrame:
    dataset = DATASETS.get_dataset(dataset_name)
    logger.debug(f"Fetch acoustic feature data for dataset={dataset_name}")
    return dataset.locations

@functools.lru_cache(maxsize=10)
def fetch_acoustic_features(
    dataset_name: str,
    **filters: Any,
) -> pd.DataFrame:
    dataset = DATASETS.get_dataset(dataset_name)
    logger.debug(f"Fetch acoustic feature data for dataset={dataset_name}")
    data = dataset.acoustic_features
    logger.debug(f"Applying filters {filters}")
    return filter_data(data, **filters)

@functools.lru_cache(maxsize=4)
def fetch_acoustic_features_umap(
    dataset_name: str,
    sample_size: int,
    **filters: Any,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    logger.debug(f"Fetch acoustic features for dataset={dataset_name}")
    dataset = DATASETS.get_dataset(dataset_name)
    # ensure umap directory exists
    (dataset.path / "umap").mkdir(exist_ok=True, parents=True)
    # hash to get the umap id
    umap_id = hashify(str(tuple([dataset_name] + list(filters.items()))))
    # load from disk if its present
    if (umap_path := (dataset.path / "umap" / f"{umap_id}.parquet")).exists():
        logger.debug(f"Loading UMAP from {umap_path}")
        return pd.read_parquet(umap_path)
    data = dataset.acoustic_features
    logger.debug(f"Applying filters {filters}")
    data = filter_data(data, **filters)
    logger.debug(f"Pivoting features")
    data = data.pivot(
        index=data.columns[~data.columns.isin(["feature", "value"])],
        columns='feature',
        values='value',
    )
    sample = data.sample(min(sample_size, len(data)))
    logger.debug(f"Running UMAP on subsample {sample_size}/{len(data)} ")
    proj = umap_data(sample)
    logger.debug(f"UMAP complete")
    logger.debug(f"Persisting UMAP to {umap_path}")
    # persist so we don't need to recompute
    proj.to_parquet(umap_path)
    return proj

def setup():
    """
    Sets up the LRU cache for UMAP
    Not a great solution
    """
    for dataset in DATASETS:
        dates = (dataset.files.date.min(), dataset.files.date.max())
        locations = list2tuple(dataset.locations.site_name.unique().tolist())
        fetch_acoustic_features_umap(
            dataset.dataset_name,
            dates=dates,
            locations=locations,
            sample_size=len(fetch_files(
                dataset.dataset_name,
                dates=dates,
                locations=locations,
            ))
        )

setup()

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

def dispatch(
    end_point: str,
    default: Any | None = None,
    **payload: Dict[str, Any],
) -> Any:
    try:
        func = API[end_point]
        logger.debug(f"Sending {end_point}")
        return func(**payload)
    except Exception as e:
        logger.warning(f"{end_point} failed")
        logger.error(e)
        return default

FETCH_DATASETS = "fetch_datasets"
FETCH_DATASET = "fetch_dataset"
SET_CURRENT_DATASET = "set_current_dataset"
FETCH_DATASET_CONFIG = "fetch_dataset_config"
SET_DATASET_CONFIG = "set_dataset_config"
FETCH_DATASET_SITES_TREE = "fetch_dataset_sites_tree"
FETCH_DATASET_DROPDOWN_OPTIONS = "fetch_dataset_dropdown_options"
FETCH_DATASET_CATEGORICAL_DROPDOWN_OPTIONS = "fetch_dataset_categorical_dropdown_options"
FETCH_FILES = "fetch_files"
FETCH_LOCATIONS = "fetch_locations"
FETCH_ACOUSTIC_FEATURES = "fetch_acoustic_features"
FETCH_ACOUSTIC_FEATURES_UMAP = "fetch_acoustic_features_umap"
FETCH_DATASET_CATEGORIES = "fetch_dataset_categories"

API = {
    FETCH_DATASETS: fetch_datasets,
    FETCH_DATASET: fetch_dataset,
    SET_CURRENT_DATASET: set_current_dataset,
    FETCH_DATASET_CONFIG: fetch_dataset_config,
    SET_DATASET_CONFIG: set_dataset_config,
    FETCH_DATASET_SITES_TREE: fetch_sites_tree,
    FETCH_DATASET_CATEGORIES: fetch_dataset_categories,
    FETCH_DATASET_DROPDOWN_OPTIONS: fetch_dataset_dropdown_options,
    FETCH_DATASET_CATEGORICAL_DROPDOWN_OPTIONS: fetch_dataset_categorical_dropdown_options,
    FETCH_FILES: fetch_files,
    FETCH_LOCATIONS: fetch_locations,
    FETCH_ACOUSTIC_FEATURES: fetch_acoustic_features,
    FETCH_ACOUSTIC_FEATURES_UMAP: fetch_acoustic_features_umap,
}
