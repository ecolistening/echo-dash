import attrs
import cachetools
from dataclasses import dataclass
from datetime import date
import pathlib
import itertools
from functools import lru_cache, cached_property
import os
from typing import List

import bigtree as bt
from loguru import logger
import pandas as pd

from configparser import ConfigParser
from config import root_dir
from utils import list2tuple
from utils import query as Q

from typing import Any, Callable, Dict, List, Tuple

def filter_data(
    data: str,
    dates: List[str] | None = None,
    feature: str | None = None,
    locations: List[str] | None = None,
    sample: int | None = None
):
    # TODO double check this
    # Prevent double caching of unfiltered datasets
    # if not any((dates,feature,locations)):
    #     logger.debug(f"No filters selected, redirect")
    #     data = load_dataset(dataset)

    # else:
    if dates is not None: dates = list2tuple(dates)
    if feature is not None: feature = str(feature)
    if locations is not None: locations = list2tuple(locations)

    logger.debug(f"Filter "
                 f"dates:{len(dates) if dates is not None else None} "
                 f"locations:{len(locations) if locations is not None else None} "
                 f"{feature=}")
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

@lru_cache(maxsize=5)
def filter_data_lru(dataset, dates: Tuple | None = None, feature: str | None = None, locations: Tuple | None = None):
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

    return data

@lru_cache(maxsize=10)
def load_and_filter_sites_lru(dataset: str):
    dataset = dataset_loader.get_dataset(dataset)
    data = dataset.locations

    if data is None:
        logger.warning(f"Can't filter tree for dataset {dataset}")
        return None

    tree = bt.dataframe_to_tree(data.reset_index(drop=True), path_col='site')

    return tree

#@lru_cache(maxsize=3)
def load_config_lru(dataset_name: str):
    '''
        Storing result in cache brings the risk that changes in the config will not be effective until reset or cache is filled.
    '''
    return dataset_loader.get_dataset(dataset_name).config

@lru_cache(maxsize=3)
def get_path_from_config_lru(dataset: str, section: str, option:str):
    '''
        Gets a path stored as 'option' in the 'section' of the config of a given 'dataset'.

        Storing result in cache brings the risk that changes in the config will not be effective until reset or cache is filled.
    '''
    logger.debug(f"Extract path \'{option}\' from config section \'{section}\' for dataset \'{dataset}\'..")
    
    extract_path = None
    config = load_config(dataset)
    if config.has_option(section, option):
        extract_path = config.get(section, option)
        logger.debug(f"Extracted path \'{extract_path}\'")
        if not os.path.isabs(extract_path):
            extract_path = os.path.join(root_dir,dataset,extract_path)
            logger.debug(f"Transformed path: \'{extract_path}\'")
    else:
        logger.debug(f"Could not find path in config.")
        if option=='sound_file_path':
            path_ = os.path.join(root_dir,dataset,'soundfiles')
            if os.path.isdir(path_):
                extract_path = path_
                logger.debug(f"Found default path \'{extract_path}\'")
        if option=='gdrive_sound_file_path':
            extract_path = os.path.join("DASHBOARD_MP3",dataset,'soundfiles')

    return extract_path


# ~~~~~~~~~~~~~~~~~~~~~ #
#                       #
#          API          #
#                       #
# ~~~~~~~~~~~~~~~~~~~~~ #

def load_and_filter_sites(dataset: str):
    logger.debug(f"Load site data for {dataset=}")
    return load_and_filter_sites_lru(str(dataset))

def load_config(dataset: str):
    logger.debug(f"Load config for {dataset=}")
    return load_config_lru(str(dataset))

def get_path_from_config(dataset: str, section: str, option:str):
    logger.debug(f"Get path for {dataset=} {section=} {option=}")
    # return get_path_from_config_lru(str(dataset), str(section), str(option))
