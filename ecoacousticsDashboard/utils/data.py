import configparser
from datetime import date
import itertools
from functools import lru_cache
import os
from typing import List

import bigtree as bt
from loguru import logger
import pandas as pd

from config import root_dir
from utils import list2tuple

# ~~~~~~~~~~~~~~~~~~~~~ #
#                       #
#     Data Reading      #
#                       #
# ~~~~~~~~~~~~~~~~~~~~~ #

def read_dataset(dataset: str, columns: list = None):
    datapath = os.path.join(root_dir,dataset,'indices.parquet')
    logger.debug(f"Read dataset from \"{datapath}\"..")
    try:
        data = pd.read_parquet(datapath, columns=columns).drop_duplicates()
    except Exception as e:
        data = None
        logger.error(e)
    else:
        logger.debug(f"{data.shape=}")
    return data

def read_sites(dataset: str):
    datapath = os.path.join(root_dir,dataset,'locations.parquet')
    logger.debug(f"Read site data from \"{datapath}\"..")
    try:
        data = pd.read_parquet(datapath)
    except Exception as e:
        data = None
        logger.error(e)
    else:
        logger.debug(f"{data.shape=}")
    return data

def read_config(dataset: str):
    # Initialise config parser
    config = configparser.ConfigParser()
    configpath = os.path.join(root_dir,dataset,'config.ini')
    logger.debug(f"Load config from \"{configpath}\"..")
    try:
        config.read(configpath)
    except (IOError, TypeError) as e:
        logger.error(e)
    return config


def get_dataset_names():
    return [d.name for d in root_dir.glob("*") if d.is_dir()]

# ~~~~~~~~~~~~~~~~~~~~~ #
#                       #
#         Cache         #
#                       #
# ~~~~~~~~~~~~~~~~~~~~~ #

@lru_cache(maxsize=10)
def load_and_filter_dataset_lru(dataset: str, dates: tuple=None, feature: str=None, locations: tuple=None, sample: int=None):
     
    if any((dates,feature,locations,sample)):
        logger.debug(f"Use preloaded dataset..")
        data = load_and_filter_dataset(dataset)
    else:
        data = read_dataset(dataset)

        sample_no = data.shape[0]
        data = data.drop_duplicates()
        if sample_no>data.shape[0]:
            logger.debug(f"Removed {sample_no-data.shape[0]} duplicate samples: {data.shape=}")

        # Compute Site Hierarchy levels
        data = data.assign(**{f'sitelevel_{k}': v for k,v in data.site.str.split('/', expand=True).iloc[:,1:].to_dict(orient='list').items()})
        logger.debug(f"Computed site hierarchy levels")

        # Compute Temporal Splits
        data['hour'] = data.timestamp.dt.hour
        data['weekday'] = data.timestamp.dt.day_name()
        data['date'] = data.timestamp.dt.date
        data['month'] = data.timestamp.dt.month_name()
        data['year'] = data.timestamp.dt.year
        logger.debug(f"Computed temporal splits")

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
        data = data.sample(n=sample)
        logger.debug(f"Selected {sample} random samples: {data.shape=}")

    return data

@lru_cache(maxsize=10)
def load_and_filter_sites_lru(dataset: str):
    data = read_sites(dataset)

    tree = bt.dataframe_to_tree(data.reset_index(drop=True), path_col='site')

    return tree

@lru_cache(maxsize=10)
def load_config_lru(dataset: str):
    '''
        Storing result in cache brings the risk that changes in the config will not be effective until reset or cache is filled.
    '''
    config = read_config(dataset)
    if not config.has_section('Site Hierarchy'):
        config.add_section('Site Hierarchy')

    return config

@lru_cache(maxsize=10)
def get_path_from_config_lru(dataset: str, section: str, option:str):
    '''
        Gets a path stored as 'option' in the 'section' of the config of a given 'dataset'.

        Storing result in cache brings the risk that changes in the config will not be effective until reset or cache is filled.
    '''
    logger.debug(f"Extract path \'{option}\' from config section \'{section}\' for dataset \'{dataset}\'..")
    config = load_config(dataset)
    if config.has_option(section, option):
        extract_path = config.get(section, option)
        logger.debug(f"Extracted path \'{extract_path}\'")
        if not os.path.isabs(extract_path):
            extract_path = os.path.join(root_dir,dataset,extract_path)
            logger.debug(f"Transformed path: \'{extract_path}\'")
    else:
        extract_path = None
        logger.debug(f"Could not find path.")
    return extract_path

# ~~~~~~~~~~~~~~~~~~~~~ #
#                       #
#          API          #
#                       #
# ~~~~~~~~~~~~~~~~~~~~~ #

## In order to cache the data, input types need to be hashable - all lists need to be converted to tuples
def load_and_filter_dataset(dataset: str, dates: list=None, feature: str=None, locations: list=None, sample: int=None):

    dataset = str(dataset)
    if dates is not None: dates = list2tuple(dates)
    if feature is not None: feature = str(feature)
    if locations is not None: locations = list2tuple(locations)
    if sample is not None: sample = int(sample)
    
    logger.debug(f"Load {dataset=} {dates=} {feature=} {locations=} {sample=}")
    return load_and_filter_dataset_lru(dataset, dates, feature, locations, sample)

def load_and_filter_sites(dataset: str, dates=None, feature: str=None, locations: List=None, recorders: List=None):
    logger.debug(f"Load site data for {dataset=}")
    return load_and_filter_sites_lru(str(dataset))

def load_config(dataset: str):
    logger.debug(f"Load config for {dataset=}")
    return load_config_lru(str(dataset))

def get_path_from_config(dataset: str, section: str, option:str):
    logger.debug(f"Get path for {dataset=} {section=} {option=}")
    return get_path_from_config_lru(str(dataset), str(section), str(option))