import configparser
import itertools
from datetime import date
from typing import List
import pandas as pd
import bigtree as bt

from config import root_dir


def load_and_filter_dataset(dataset: str, dates=None, feature: str=None, locations: List=None, sample=None):
    data = pd.read_parquet(root_dir / dataset / 'indices.parquet')#.drop_duplicates()

    if dates is not None:
        dates = [date.fromisoformat(d) for d in dates]
        data = data[data.timestamp.dt.date.between(*dates)]

    if feature is not None:
        data = data[data.feature == feature]

    if locations is not None and len(locations) > 0:
        data = data[data['site'].isin([l.strip('/') for l in locations[-1]])]

    # Randomly sample
    if sample is not None:
        data = data.sample(n=sample)

    # Compute Site Hierarchy levels
    data = data.assign(**{f'sitelevel_{k}': v for k,v in data.site.str.split('/', expand=True).iloc[:,1:].to_dict(orient='list').items()})

    # Compute Temporal Splits
    data['hour'] = data.timestamp.dt.hour
    data['weekday'] = data.timestamp.dt.day_name()
    data['date'] = data.timestamp.dt.date
    data['month'] = data.timestamp.dt.month_name()
    data['year'] = data.timestamp.dt.year

    return data

def load_and_filter_sites(dataset: str, dates=None, feature: str=None, locations: List=None, recorders: List=None):
    data = pd.read_parquet(root_dir / dataset / 'locations.parquet')

    tree = bt.dataframe_to_tree(data.reset_index(drop=True), path_col='site')

    return tree

def load_config(dataset: str):
    # Initialise config parser
    config = configparser.ConfigParser()
    try:
        config.read(root_dir / dataset / 'config.ini')
    except (IOError, TypeError) as e:
        pass
    if not config.has_section('Site Hierarchy'):
        config.add_section('Site Hierarchy')

    return config