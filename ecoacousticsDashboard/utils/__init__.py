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

def list2tuple(arr):
    if isinstance(arr,tuple):
        return arr
    
    if not isinstance(arr,list):
        logger.error(f"Unknown type {type(arr)}")
        return arr
    
    # Iterate through nested lists to get all elements
    val = []
    rem = [arr]
    while len(rem)>0:
        obj = rem.pop(0)
        if isinstance(obj,list):
            for el in obj:
                rem.append(el)
        else:
            val.append(obj)
    return tuple(val)


# ~~~~~~~~~~~~~~~~~~~~~ #
#                       #
#         Cache         #
#                       #
# ~~~~~~~~~~~~~~~~~~~~~ #

@lru_cache(maxsize=10)
def load_and_filter_dataset_lru(dataset: str, dates: tuple=None, feature: str=None, locations: tuple=None, sample: int=None):
    datapath = os.path.join(root_dir,dataset,'indices.parquet')
    logger.debug(f"Load dataset from \"{datapath}\"..")
    data = pd.read_parquet(datapath)#.drop_duplicates()
    logger.debug(f"{data.shape=}")

    if dates is not None:
        logger.debug(f"Select dates..")
        dates = [date.fromisoformat(d) for d in dates]
        data = data[data.timestamp.dt.date.between(*dates)]
        logger.debug(f"{data.shape=}")

    if feature is not None:
        logger.debug(f"Select features..")
        data = data[data.feature == feature]
        logger.debug(f"{data.shape=}")

    if locations is not None and len(locations) > 0:
        logger.debug(f"Select locations..")
        # changed it from locations[-1] after unpacking nested list in list2tuple - Potential source for problems
        data = data[data['site'].isin([l.strip('/') for l in locations])]
        logger.debug(f"{data.shape=}")

    # Randomly sample
    if sample is not None:
        logger.debug(f"Select {sample} random samples..")
        data = data.sample(n=sample)
        logger.debug(f"{data.shape=}")

    # Compute Site Hierarchy levels
    logger.debug(f"Compute site hierarchy levels..")
    data = data.assign(**{f'sitelevel_{k}': v for k,v in data.site.str.split('/', expand=True).iloc[:,1:].to_dict(orient='list').items()})

    # Compute Temporal Splits
    logger.debug(f"Compute temporal splits..")
    data['hour'] = data.timestamp.dt.hour
    data['weekday'] = data.timestamp.dt.day_name()
    data['date'] = data.timestamp.dt.date
    data['month'] = data.timestamp.dt.month_name()
    data['year'] = data.timestamp.dt.year

    logger.debug(f"Return filtered data.")
    return data

@lru_cache(maxsize=10)
def load_and_filter_sites_lru(dataset: str):
    datapath = os.path.join(root_dir,dataset,'locations.parquet')
    logger.debug(f"Load site data from \"{datapath}\"..")
    data = pd.read_parquet(datapath)
    logger.debug(f"{data.shape=}")

    tree = bt.dataframe_to_tree(data.reset_index(drop=True), path_col='site')

    return tree

@lru_cache(maxsize=10)
def load_config_lru(dataset: str):
    # Initialise config parser
    config = configparser.ConfigParser()
    configpath = os.path.join(root_dir,dataset,'config.ini')
    logger.debug(f"Load config from \"{configpath}\"..")
    try:
        config.read(configpath)
    except (IOError, TypeError) as e:
        logger.warning(e)
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