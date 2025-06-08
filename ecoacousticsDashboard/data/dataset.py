from __future__ import annotations

import attrs
import bigtree as bt
import pandas as pd
import pathlib

from configparser import ConfigParser
from loguru import logger

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

    def as_dict(self):
        return dict(
            dataset_id=dataset_id,
            dataset_name=dataset_name,
        )

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

    @cached_property
    def sites_tree(self):
        return bt.dataframe_to_tree(
            self.locations.reset_index(drop=True),
            path_col="site",
        )

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
