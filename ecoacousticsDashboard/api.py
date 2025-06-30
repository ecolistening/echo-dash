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
    **filters: Any,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    dataset = DATASETS.get_dataset(dataset_name)
    logger.debug(f"Fetch acoustic feature data for dataset={dataset_name}")
    data = dataset.acoustic_features
    logger.debug(f"Applying filters {filters}")
    data = filter_data(data, **filters)

    # FIXME This is a bit of a hack. The dataset should be clean by the time it gets here.
    # DOUBLE FIXME: Moved across Lucas's hack from the front-end, this should be fixed in this sprint
    # the hack is in order to pivot, there should be no duplicates in the data, i.e. path / feature / value
    num_samples = data.shape[0]
    index = data.columns[~data.columns.isin(["feature", "value"])]

    logger.debug(f"Check for duplicates..")
    data = data.drop_duplicates(subset=[*index, "feature"], keep='first')
    if num_samples > (remaining := data.shape[0]):
        logger.debug(f"Removed {num_samples - remaining} duplicate samples.")

    data = data.pivot(columns='feature', index=index, values='value')

    num_samples = data.shape[0]
    data = data.loc[np.isfinite(data).all(axis=1), :]
    if num_samples > (remaining := data.shape[0]):
        logger.debug(f"Removed {num_samples - remaining} NaN samples.")
    # HACK /fin

    logger.debug(f"Running and caching UMAP for {dataset_name} with {remaining} samples")
    proj = umap_data(data)
    logger.debug(f"UMAP complete")
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
    for dataset in DATASETS:
        dates = (dataset.files.date.min(), dataset.files.date.max())
        locations = list2tuple(dataset.locations.site_name.unique().tolist())
        fetch_acoustic_features_umap(
            dataset.dataset_name,
            dates=dates,
            locations=locations,
            # sample_size=len(dataset.files)
        )

setup()

# NOTE:
# Please use the dispatch pattern mapping a string to a function
# instead of making the function call directly
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
FETCH_ACOUSTIC_FEATURES = "fetch_acoustic_features"
FETCH_ACOUSTIC_FEATURES_UMAP = "fetch_acoustic_features_umap"
FETCH_DATASET_CATEGORIES = "fetch_dataset_categories"
SEND_DATA_FOR_DOWNLOAD = "send_data_for_download"

API = {
    FETCH_DATASET: fetch_dataset,
    FETCH_DATASET_CONFIG: fetch_dataset_config,
    FETCH_DATASET_CATEGORIES: fetch_dataset_categories,
    FETCH_ACOUSTIC_FEATURES: fetch_acoustic_features,
    FETCH_ACOUSTIC_FEATURES_UMAP: fetch_acoustic_features_umap,
    SEND_DATA_FOR_DOWNLOAD: send_download_data,
}
