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
    else:
        if not config.has_section('Site Hierarchy'):
            config.add_section('Site Hierarchy')

    return config


def get_dataset_names():
    return [d.name for d in root_dir.glob("*") if d.is_dir()]

# ~~~~~~~~~~~~~~~~~~~~~ #
#                       #
#         Cache         #
#                       #
# ~~~~~~~~~~~~~~~~~~~~~ #

@lru_cache(maxsize=10)
def load_dataset_lru(dataset: str):
    data = read_dataset(dataset)

    sample_no = data.shape[0]
    data = data.drop_duplicates()
    if sample_no>data.shape[0]:
        logger.debug(f"Removed {sample_no-data.shape[0]} duplicate samples: {data.shape=}")


    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # Dirty fixes that need to be sorted in the Dataset! #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    # Adjust file path
    striptext = None
    if dataset == "cairngorms":
        striptext = "/mnt/lustre/projects/mfm/ecolistening/dashboard/audio/cairngorms/"
    elif dataset == "sounding out":
        striptext = "/mnt/lustre/projects/mfm/ecolistening/dac_audio/diurnal/dc_corrected/"

    if striptext is not None and 'path' in data.columns:
        logger.debug(f"Strip '{striptext}' from column path..")
        data['path'] = data['path'].map(lambda x: x.lstrip(striptext))


    # Adjust location names
    if dataset == "sounding out":
        # for location in data['location'].unique():
        #     print(data.loc[data['location'] == location].iloc[0])

        data['location'] = data['habitat code']
        logger.debug("Updated location with habitat code")

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #



    # Compute Site Hierarchy levels
    logger.debug(f"Compute site hierarchy levels..")
    data = data.assign(**{f'sitelevel_{k}': v for k,v in data.site.str.split('/', expand=True).iloc[:,1:].to_dict(orient='list').items()})
    
    # Compute Temporal Splits
    logger.debug(f"Compute temporal splits..")
    data['hour'] = data.timestamp.dt.hour
    data['weekday'] = data.timestamp.dt.day_name()
    #data['date'] = data.timestamp.dt.date
    data['date'] = data.timestamp.dt.strftime('%Y-%m-%d')
    data['month'] = data.timestamp.dt.month_name()
    data['year'] = data.timestamp.dt.year
    
    logger.debug(f"Finished loading dataset {dataset}")
    return data

@lru_cache(maxsize=5)
def load_and_filter_dataset_lru(dataset: str, dates: tuple=None, feature: str=None, locations: tuple=None):
     
    data = load_dataset(dataset)

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
    data = read_sites(dataset)

    tree = bt.dataframe_to_tree(data.reset_index(drop=True), path_col='site')

    return tree

#@lru_cache(maxsize=3)
def load_config_lru(dataset: str):
    '''
        Storing result in cache brings the risk that changes in the config will not be effective until reset or cache is filled.
    '''
    config = read_config(dataset)
    
    return config

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

    return extract_path

@lru_cache(maxsize=10)
def get_options_for_dataset_lru(dataset: str):
    data = load_dataset(dataset)
    config = load_config(dataset)
    options = []

    # Add site hierarchies
    sitelevel_cols = list(filter(lambda a: a.startswith('sitelevel_'), data.columns))
    for feat in sitelevel_cols:
        values = data[feat].unique()

        try:
            values_int = map(int,values)
            order = tuple(str(i) for i in sorted(values_int))
        except:
            order = tuple(sorted(values))
        else:
            logger.debug(f"Convert sitelevel {feat} to string.")
            data[feat] = data[feat].astype(str)


        options += [{'value': feat, 'label': config.get( 'Site Hierarchy', feat, fallback=feat), 'group': 'Site Level', 'type': 'categorical', 'order': order}]

    # Add time of the day
    options += [{'value': 'dddn', 'label': 'Dawn/Day/Dusk/Night', 'group': 'Time of Day', 'type': 'categorical', 'order': ('dawn','day','dusk','night')}]
    options += [{'value': f'hours after {c}', 'label': f'Hours after {c.capitalize()}', 'group': 'Time of Day', 'type': 'continuous'} for c in ('dawn', 'sunrise', 'noon', 'sunset', 'dusk')]

    # Add temporal columns with facet order
    temporal_cols = (   
                        ('hour', list(range(24))),
                        ('weekday', ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')),
                        ('date', sorted(data['date'].unique())),
                        ('month', ('January','February','March','April','May','June','July','August','September','October','November','December')),
                        ('year', sorted(data['year'].unique())),
                    )
    options += [{'value': feat, 'label': feat.capitalize(), 'group': 'Temporal', 'type': 'categorical', 'order': order} for feat,order in temporal_cols]

    spatial_cols = ['location', 'site', 'recorder']
    options += [{'value': i, 'label': i.capitalize(), 'group': 'Spatial', 'type': 'categorical', 'order': tuple(sorted(data[i].unique()))} for i in spatial_cols]

    # deprecated since they are already covered or offer no visualisation value
    #index = ['file', 'timestamp']
    #options += [{'value': i, 'label': i.capitalize(), 'group': 'Other Metadata', 'type': 'categorical', 'order': tuple(sorted(data[i].unique()))} for i in index]

    # Filter options to ensure they are present in the dataset
    options = [opt for opt in options if opt['value'] in data.columns]

    return tuple(options)

@lru_cache(maxsize=10)
def get_cat_options_for_dataset_lru(dataset: str):
    options = get_options_for_dataset(dataset)
    return [opt for opt in options if opt['type'] in ('categorical')]

@lru_cache(maxsize=10)
def get_categorical_orders_for_dataset_lru(dataset: str):
    #{opt['value']: opt.get('order') for opt in options if opt.get('order',None) is not None}

    options = get_options_for_dataset(dataset)
    categorical_orders = {}
    for opt in options:
        name = opt['value']
        order = opt.get('order',None)
        if order is None:
            logger.debug(f"Option {name}: No order provided")
        else:
            logger.debug(f"Option {name}: {order}")
            categorical_orders[name] = order

    return categorical_orders

# ~~~~~~~~~~~~~~~~~~~~~ #
#                       #
#          API          #
#                       #
# ~~~~~~~~~~~~~~~~~~~~~ #

def load_dataset(dataset: str):
    logger.debug(f"Load {dataset=}")
    return load_dataset_lru(str(dataset))

## In order to cache the data, input types need to be hashable - all lists need to be converted to tuples
def load_and_filter_dataset(dataset: str, dates: list=None, feature: str=None, locations: list=None, sample: int=None):

    # Prevent double caching of unfiltered datasets
    if not any((dates,feature,locations)):
        logger.debug(f"No filters selected, redirect")
        data = load_dataset(dataset)

    else:
        dataset = str(dataset)
        if dates is not None: dates = list2tuple(dates)
        if feature is not None: feature = str(feature)
        if locations is not None: locations = list2tuple(locations)

        logger.debug(f"Load {dataset=} and filter dates:{len(dates)} locations:{len(locations)} {feature=}")
        data = load_and_filter_dataset_lru(dataset, dates, feature, locations)

    # Randomly sample
    if sample is not None:
        sample = int(sample)
        data = data.sample(n=sample, random_state=42)
        logger.debug(f"Selected {sample} random samples: {data.shape=}")

    return data

def load_and_filter_sites(dataset: str):
    logger.debug(f"Load site data for {dataset=}")
    return load_and_filter_sites_lru(str(dataset))

def load_config(dataset: str):
    logger.debug(f"Load config for {dataset=}")
    return load_config_lru(str(dataset))

def get_path_from_config(dataset: str, section: str, option:str):
    logger.debug(f"Get path for {dataset=} {section=} {option=}")
    return get_path_from_config_lru(str(dataset), str(section), str(option))

def get_options_for_dataset(dataset: str):
    logger.debug(f"Get options for {dataset=}")
    return get_options_for_dataset_lru(str(dataset))

def get_cat_options_for_dataset(dataset: str):
    logger.debug(f"Get categorical options for {dataset=}")
    return get_cat_options_for_dataset_lru(str(dataset))

def get_categorical_orders_for_dataset(dataset: str):
    logger.debug(f"Get categorical_orders for {dataset=}")
    return get_categorical_orders_for_dataset_lru(str(dataset))