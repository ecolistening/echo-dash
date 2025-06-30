import attrs
import numpy as np
import hashlib
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
from urllib.parse import quote, unquote

from configparser import ConfigParser
from config import root_dir
from utils import list2tuple
from utils import query as Q
from utils.umap import umap_data

from typing import Any, Callable, Dict, List, Tuple

def dedup(l: List[Any]) -> List[Any]:
    return list(dict.fromkeys(l))

@attrs.define
class Dataset:
    """
    Dataset class handles all data loading logic. A dataset, indexed by ID and file name
    contains many tables. Each is stored in a parquet file in the specified data directory.
    """
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
        # cache acoustic features and UMAP
        self.acoustic_features
        self.umap_acoustic_features
        # cache species and birdet predictions
        self.species
        self.birdnet_species_probs
        # load data views
        self.views

    @property
    def path(self):
        return pathlib.Path.cwd().parent / "data" / self.dataset_path

    @cached_property
    def views(self):
        return DatasetViews(self)

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
    def umap_acoustic_features(self) -> pd.DataFrame:
        data = self.acoustic_features
        # FIXME This is a bit of a hack. The dataset should be clean by the time it gets here.
        # DOUBLE FIXME: Moved across Lucas's hack from the front-end, this should be fixed in this sprint
        sample_no = data.shape[0]
        idx_cols = list(filter(lambda a: a not in ['feature', 'value'], data.columns))

        logger.debug(f"Check for duplicates..")
        data_nodup = data.drop_duplicates(subset=idx_cols + ['feature'], keep='first')
        if sample_no>data_nodup.shape[0]:
            logger.debug(f"Removed {sample_no-data_nodup.shape[0]} duplicate samples.")

        logger.debug(f"Select columns {idx_cols}")
        idx_data = data_nodup.pivot(columns='feature', index=idx_cols, values='value')

        sample_no = idx_data.shape[0]
        idx_data = idx_data.loc[np.isfinite(idx_data).all(axis=1), :]
        if sample_no>idx_data.shape[0]:
            logger.debug(f"Removed {sample_no-idx_data.shape[0]} NaN samples.")
        return umap_data(idx_data)

    # TODO: problem with caching 10M rows! so switched out the larger version...
    # a better way needs to be designed for this... our data files can get very large
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

    @cached_property
    def species_predictions(self) -> pd.DataFrame:
        return (
            self.birdnet_species_probs
            .join(self.species, on="species_id")
            .join(self.files, on="file_id")
            .join(self.locations, on="site_id")
            # HACK: site-level time data should really be separate
            # because its shared across birdnet and acoustic features
            .merge(
                self.acoustic_features[["file", "dddn"]].drop_duplicates(),
                left_on="file_name",
                right_on="file",
                how="left",
            )
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


# FIXME: there's no validation on the inputs before a query is executed
@attrs.define
class DatasetViews:
    """
    DatasetViews class loads persisted views, or creates, caches and persists new views
    """
    dataset: Dataset

    @cached_property
    def cache(self):
        return cachetools.LRUCache(maxsize=10)

    @property
    def path(self):
        return self.dataset.path / "views"

    @staticmethod
    def lookup_key(*args: Tuple[str]) -> str:
        key = "_".join([quote(arg, safe='') for arg in sorted(args)])
        h = hashlib.new("sha256")
        h.update(key.encode("utf-8"))
        return h.hexdigest()

    def species_richness(
        self,
        threshold: float,
        group_by: List[str],
        dates: List[str] = [],
        locations: List[str] = [],
    ) -> pd.DataFrame:
        return self._fetch_view(
            self.lookup_key(str(threshold), *group_by, *dates, *locations),
            DatasetViews.species_richness.__name__,
            lambda: Q.species_richness_query(self.dataset.species_predictions, threshold, group_by, dates, locations),
        )

    def species_abundance(
        self,
        threshold: float,
        group_by: List[str],
        dates: List[str] = [],
        locations: List[str] = [],
    ) -> pd.DataFrame:
        return self._fetch_view(
            self.lookup_key(str(threshold), *group_by, *dates, *locations),
            DatasetViews.species_abundance.__name__,
            lambda: Q.species_abundance_query(self.dataset.species_predictions, threshold, group_by, dates, locations),
        )

    def _fetch_view(
        self,
        lookup_id: str,
        query_name: str,
        query: Callable,
    ) -> pd.DataFrame:
        view_path = self.path / f"{query_name}_{lookup_id}.parquet"
        # if its not been cached and a persisted view exists, load it
        if lookup_id not in self.cache and view_path.exists():
            logger.debug(f"[LOAD] Query: {query_name}({lookup_id=})")
            self.cache[lookup_id] = pd.read_parquet(view_path)
            return self.cache[lookup_id]
        # if its not been cached, execute the query
        elif lookup_id not in self.cache:
            logger.debug(f"[CACHE] Query: {query_name}({lookup_id=})")
            view = query()
            view_path.parent.mkdir(exist_ok=True, parents=True)
            view.to_parquet(view_path)
            self.cache[lookup_id] = view
            return self.cache[lookup_id]
        # it has been cached, simply return it
        else:
            logger.debug(f"[FETCH] Query: {query_name}({lookup_id=})")
            return self.cache[lookup_id]


@attrs.define
class DatasetDecorator:
    dataset: Dataset

    def drop_down_select_options(self) -> Tuple[Dict[str, Any]]:
        logger.debug(f"Get options for dataset_name={self.dataset.dataset_name}")
        options = []
        # Add site hierarchies
        for level in self.site_levels:
            values = self.dataset.locations[level].unique()
            options += [{'value': level, 'label': self.dataset.config.get('Site Hierarchy', level, fallback=level), 'group': 'Site Level', 'type': 'categorical', 'order': tuple(sorted(values))}]
        # Add time of the day
        options += [{'value': 'dddn', 'label': 'Dawn/Day/Dusk/Night', 'group': 'Time of Day', 'type': 'categorical', 'order': ('dawn','day','dusk','night')}]
        # HACK -> will be fixed when solar data is present
        if len(self.dataset.dates):
            options += [{'value': f'hours after {c}', 'label': f'Hours after {c.capitalize()}', 'group': 'Time of Day', 'type': 'continuous'} for c in ('dawn', 'sunrise', 'noon', 'sunset', 'dusk')]
        # Add temporal columns with facet order
        options += [{'value': col, 'label': col.capitalize(), 'group': 'Temporal', 'type': 'categorical', 'order': order} for col, order in self.temporal_columns_with_order]
        # Add spatial columns with facet order
        options += [{'value': col, 'label': col.capitalize(), 'group': 'Spatial', 'type': 'categorical', 'order': tuple(sorted(self.dataset.locations[col].unique()))} for col in self.spatial_columns]
        # deprecated since they are already covered or offer no visualisation value
        #index = ['file', 'timestamp']
        #options += [{'value': i, 'label': i.capitalize(), 'group': 'Other Metadata', 'type': 'categorical', 'order': tuple(sorted(data[i].unique()))} for i in index]
        return tuple(options)

    def categorical_drop_down_select_options(self):
        return [opt for opt in self.drop_down_select_options() if opt['type'] in ('categorical')]

    @property
    def site_level_names(self) -> List[str]:
        return [self.dataset.config.get('Site Hierarchy', level, fallback=level) for level in self.site_levels]

    @property
    def site_levels(self) -> List[str]:
        return [col for col in self.dataset.locations.columns if col.startswith('sitelevel_')]

    @property
    def site_level_values(self) -> List[str]:
        columns = []
        for level in self.site_levels:
            columns.extend(self.dataset.locations[level].unique())
        return columns

    @property
    def temporal_columns(self) -> List[Tuple[str, List[Any]]]:
        return [key for key, _ in self.temporal_columns_with_order]

    @property
    def temporal_columns_with_order(self) -> List[Tuple[str, List[Any]]]:
        return (
            ('hour', list(range(24))),
            ('weekday', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']),
            # ('date', sorted(self.dataset.files['date'].unique())),
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
                logger.debug(f"Loading and caching {dataset['dataset_name']}")
                ds = Dataset(**dataset)
                datasets[ds.dataset_name] = ds
            except Exception as e:
                logger.error(f"Unable to load dataset {dataset['dataset_name']}")
                logger.error(e)
        return datasets
