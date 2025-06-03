import attrs
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

from typing import Any, Dict, List, Tuple

@attrs.define
class Dataset:
    dataset_id: str
    dataset_name: str
    dataset_path: str
    audio_path: str

    def __attrs_post_init__(self) -> None:
        # cache files and site data
        self.files
        self.locations
        # cache solar data
        self.dates
        # cache acoustic features
        self.acoustic_features
        # cache species and birdet predictions
        self.species
        self.birdnet_species_probs

    @property
    def path(self):
        return pathlib.Path.cwd().parent / "data" / self.dataset_path

    @cached_property
    def config(self) -> ConfigParser:
        config_path = self.path / "config.ini"
        logger.debug(f"Load config from \"{config_path}\"..")
        return self._read_or_build_config(config_path)

    @cached_property
    def acoustic_features(self) -> pd.DataFrame:
        features_path = self.path / "indices.parquet"
        logger.debug(f"Loading & caching \"{features_path}\"..")
        data = pd.read_parquet(self.path / "indices.parquet")
        # TODO: my own hack to ensure temporal fields are on the acoustic indices (used in options / filters)
        # we will be able to do a simple table join once finished
        data = data.merge(
            self.files.join(self.locations, on="site_id"),
            left_on=["file", "site"],
            right_on=["file_name", "site_name"],
            how="left",
            suffixes=('', '_y'),
        )
        # TODO: Several hacks left by Lucas, persist to get this view working, can be removed when switching to better structured data
        # 1. remove duplicates
        num_samples = data.shape[0]
        data = data.drop_duplicates()
        if num_samples > data.shape[0]:
            logger.debug(f"Removed {num_samples - data.shape[0]} duplicate samples: {data.shape=}")
        # 2. strip
        striptext = None
        if self.dataset_name == "Cairngorms":
            striptext = "/mnt/lustre/projects/mfm/ecolistening/dashboard/audio/cairngorms/"
        elif self.dataset_name == "Sounding Out":
            striptext = "/mnt/lustre/projects/mfm/ecolistening/dac_audio/diurnal/dc_corrected/"
        if striptext is not None and 'path' in data.columns:
            logger.debug(f"Strip '{striptext}' from column path..")
            data['path'] = data['path'].map(lambda x: x.lstrip(striptext))
        # 3. adjust location names
        if self.dataset_name == "Sounding Out":
            data['location'] = data['habitat code']
            logger.debug("Updated location with habitat code")
        return data

    @cached_property
    def birdnet_species_probs(self) -> pd.DataFrame:
        birdnet_species_probs_path = self.path / "birdnet_species_probs_table.parquet"
        logger.debug(f"Loading & caching \"{birdnet_species_probs_path}\"..")
        return pd.read_parquet(birdnet_species_probs_path)

    @cached_property
    def species(self) -> pd.DataFrame:
        species_path = self.path / "species_table.parquet"
        logger.debug(f"Loading & caching \"{species_path}\"..")
        return pd.read_parquet(species_path)

    @property
    def species_predictions(self) -> pd.DataFrame:
        return (
            self.birdnet_species_probs
            .join(self.species, on="species_id")
            .join(self.files, on="file_id")
            .join(self.locations, on="site_id")
        )

    @cached_property
    def locations(self) -> pd.DataFrame:
        locations_path = self.path / "locations_table.parquet"
        logger.debug(f"Loading & caching \"{locations_path}\"..")
        locations = pd.read_parquet(locations_path)
        # TODO: hack to get working
        locations["site"] = locations["site_name"]
        # TODO: potential hack left by lucas, should be preserved?
        # Compute Site Hierarchy levels
        logger.debug(f"Compute site hierarchy levels..")
        locations = locations.assign(**{
            f'sitelevel_{k}': v
            for k,v in locations.site.str.split('/', expand=True).iloc[:,1:].to_dict(orient='list').items()
        })
        return locations

    @cached_property
    def files(self) -> pd.DataFrame:
        files_path = self.path / "files_table.parquet"
        logger.debug(f"Loading & caching \"{files_path}\"..")
        data = pd.read_parquet(files_path)
        logger.debug(f"Compute temporal splits..")
        data['hour'] = data.timestamp.dt.hour
        data['weekday'] = data.timestamp.dt.day_name()
        data['date'] = data.timestamp.dt.strftime('%Y-%m-%d')
        data['month'] = data.timestamp.dt.month_name()
        data['year'] = data.timestamp.dt.year
        return data

    @cached_property
    def dates(self) -> pd.DataFrame:
        try:
            dates_path = self.path / "dates_table.parquet"
            logger.debug(f"Loading & caching \"{dates_path}\"..")
            return pd.read_parquet(dates_path)
        except Exception as e:
            return pd.DataFrame()

    @staticmethod
    def _read_or_build_config(config_path) -> ConfigParser:
        config = ConfigParser()
        try:
            config.read(config_path)
        except (IOError, TypeError) as e:
            logger.error(e)
        else:
            if not config.has_section('Site Hierarchy'):
                config.add_section('Site Hierarchy')
        return config


@attrs.define
class DatasetDecorator:
    dataset: Dataset

    def drop_down_select_options(self) -> Tuple[Dict[str, Any]]:
        logger.debug(f"Get options for dataset_name={self.dataset.dataset_name}")
        options = []
        # Add site hierarchies
        for level in self.site_level_columns:
            values = self.dataset.locations[level].unique()
            options += [{'value': level, 'label': self.dataset.config.get('Site Hierarchy', level, fallback=level), 'group': 'Site Level', 'type': 'categorical', 'order': tuple(sorted(values))}]
        # Add time of the day
        options += [{'value': 'dddn', 'label': 'Dawn/Day/Dusk/Night', 'group': 'Time of Day', 'type': 'categorical', 'order': ('dawn','day','dusk','night')}]
        # HACK -> will be fixed when solar data is present
        if len(self.dataset.dates):
            options += [{'value': f'hours after {c}', 'label': f'Hours after {c.capitalize()}', 'group': 'Time of Day', 'type': 'continuous'} for c in ('dawn', 'sunrise', 'noon', 'sunset', 'dusk')]
        # Add temporal columns with facet order
        options += [{'value': col, 'label': col.capitalize(), 'group': 'Temporal', 'type': 'categorical', 'order': order} for col, order in self.temporal_columns]
        # Add spatial columns with facet order
        options += [{'value': col, 'label': col.capitalize(), 'group': 'Spatial', 'type': 'categorical', 'order': tuple(sorted(self.dataset.locations[col].unique()))} for col in self.spatial_columns]
        # deprecated since they are already covered or offer no visualisation value
        #index = ['file', 'timestamp']
        #options += [{'value': i, 'label': i.capitalize(), 'group': 'Other Metadata', 'type': 'categorical', 'order': tuple(sorted(data[i].unique()))} for i in index]
        return tuple(options)

    def categorical_drop_down_select_options(self):
        return [opt for opt in self.drop_down_select_options() if opt['type'] in ('categorical')]

    @property
    def site_level_columns(self) -> List[str]:
        return list(filter(lambda a: a.startswith('sitelevel_'), self.dataset.locations.columns))

    @property
    def temporal_columns(self) -> List[Tuple[str, List[Any]]]:
        return (
            ('hour', list(range(24))),
            ('weekday', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']),
            ('date', sorted(self.dataset.files['date'].unique())),
            ('month', ['January','February','March','April','May','June','July','August','September','October','November','December']),
            ('year', sorted(self.dataset.files['year'].unique())),
        )

    @property
    def spatial_columns(self) -> List[str]:
        return ['location', 'site', 'recorder']

    def category_orders(self):
        categorical_orders = {}
        for opt in self.drop_down_select_options():
            name = opt['value']
            order = opt.get('order',None)
            if order is None:
                logger.debug(f"Option {name}: No order provided")
            else:
                logger.debug(f"Option {name}: {order}")
                categorical_orders[name] = order
        return categorical_orders


# a simple collection of datasets
@attrs.define
class DatasetLoader:
    root_dir: pathlib.Path

    @cached_property
    def datasets(self) -> Dict[str, Dataset]:
        return self._init_datasets(self.datasets_table)

    @cached_property
    def datasets_table(self):
        return pd.read_parquet(self.root_dir / "datasets_table.parquet")

    def get_dataset(self, dataset_name):
        return self.datasets[dataset_name]

    def get_dataset_names(self):
        return list(self.datasets.keys())

    @staticmethod
    def _init_datasets(datasets_table: pd.DataFrame) -> Dict[str, Dataset]:
        datasets = {}
        for dataset in datasets_table.reset_index().to_dict(orient="records"):
            try:
                logger.debug(f"Loading and caching {dataset["dataset_name"]}")
                ds = Dataset(**dataset)
                datasets[ds.dataset_name] = ds
            except Exception as e:
                logger.error(f"Unable to load dataset {dataset["dataset_name"]}")
                logger.error(e)
        return datasets


dataset_loader = DatasetLoader(root_dir)

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
