import functools
import pandas as pd
import numpy as np

from io import StringIO
from loguru import logger
from typing import Any, Dict, List, Tuple

from utils import list2tuple
from utils.umap import umap_data
from utils.data import dataset_loader as DATASETS
from utils.data import Dataset, DatasetDecorator
from utils.data import filter_data

# DATASETS = DatasetLoader(root_dir)

def fetch_dataset(
    dataset_name: str
) -> Dataset:
    dataset = DATASETS.get_dataset(dataset_name)
    return dataset

def fetch_dataset_config(
    dataset_name: str
) -> Dict[str, Any]:
    dataset = fetch_dataset(dataset_name)
    return dataset.config

def fetch_dataset_categories(
    dataset_name: str
) -> Dict[str, Any]:
    dataset = DATASETS.get_dataset(dataset_name)
    return DatasetDecorator(dataset).category_orders()

def fetch_dataset_dropdown_options(
    dataset_name: str
) -> Dict[str, Any]:
    dataset = DATASETS.get_dataset(dataset_name)
    return DatasetDecorator(dataset).category_orders()

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
    if (umap_path := (dataset.path / "umap.parquet")).exists():
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
    proj.to_parquet(umap_path)
    return proj

def send_download_data(
    dataset_name,
    json_data: str,
    dl_type: str
) -> Dict[str, Any]:
    data = pd.read_json(StringIO(json_data), orient='table')
    if dl_type == 'dl_csv':
        return dcc.send_data_frame(
            data.to_csv,
            f'{dataset_name}.csv'
        )
    elif dl_type == 'dl_xls':
        return dcc.send_data_frame(
            data.to_excel,
            f'{dataset_name}.xlsx',
            sheet_name="Sheet_name_1"
        )
    elif dl_type == 'dl_json':
        return dcc.send_data_frame(
            data.to_json,
            f'{dataset_name}.json'
        )
    elif dl_type == 'dl_parquet':
        return dcc.send_data_frame(
            data.to_parquet,
            f'{dataset_name}.parquet'
        )
    else:
        raise KeyError(f"Unsupported output data type: '{dl_type}'")

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
        logger.debug(f"Sending {end_point}")
        func = API[end_point]
        return func(**payload)
    except Exception as e:
        logger.warning(f"{end_point} failed")
        logger.error(e)
        return default

FETCH_DATASET = "fetch_dataset"
FETCH_DATASET_CONFIG = "fetch_dataset_config"
FETCH_FILES = "fetch_files"
FETCH_ACOUSTIC_FEATURES = "fetch_acoustic_features"
FETCH_ACOUSTIC_FEATURES_UMAP = "fetch_acoustic_features_umap"
FETCH_DATASET_CATEGORIES = "fetch_dataset_categories"
SEND_DATA_FOR_DOWNLOAD = "send_data_for_download"

API = {
    FETCH_DATASET: fetch_dataset,
    FETCH_DATASET_CONFIG: fetch_dataset_config,
    FETCH_DATASET_CATEGORIES: fetch_dataset_categories,
    FETCH_FILES: fetch_files,
    FETCH_ACOUSTIC_FEATURES: fetch_acoustic_features,
    FETCH_ACOUSTIC_FEATURES_UMAP: fetch_acoustic_features_umap,
    SEND_DATA_FOR_DOWNLOAD: send_download_data,
}
