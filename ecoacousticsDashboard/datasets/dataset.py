import attrs
import bigtree as bt
import functools
import numpy as np
import pandas as pd
import pathlib

from configparser import ConfigParser
from loguru import logger
from typing import Any, Callable, Dict, List, Tuple, Iterable

from datasets.dataset_views import DatasetViews

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
        self.weather
        # cache acoustic features and UMAP
        self.acoustic_features
        # cache species and birdet predictions
        self.species
        self.birdnet_species_probs
        # load data views
        self.views

    @property
    def path(self):
        return pathlib.Path.cwd().parent / "data" / self.dataset_path

    @functools.cached_property
    def views(self):
        return DatasetViews(self)

    @functools.cached_property
    def config(self) -> ConfigParser:
        config_path = self.path / "config.ini"
        logger.debug(f"Load config from \"{config_path}\"..")
        return self._read_or_build_config(config_path)

    def save_config(self):
        with open(self.path / "config.ini", "w") as f:
            self.config.write(f)

    @functools.cached_property
    def sites_tree(self):
        return bt.dataframe_to_tree(
            self.locations.reset_index(drop=True),
            path_col="site",
        )

    @functools.cached_property
    def acoustic_features(self) -> pd.DataFrame:
        features_path = self.path / "indices.parquet"
        logger.debug(f"Loading & caching \"{features_path}\"..")
        data = pd.read_parquet(self.path / "indices.parquet")
        # TODO: my own hack to ensure temporal fields are on the acoustic indices (used in options / filters)
        # we will be able to do a simple table join once finished
        data = data.merge(
            self.files.join(self.locations, on="site_id").reset_index(),
            left_on=["file", "site"],
            right_on=["file_name", "site_name"],
            how="left",
            suffixes=('', '_y'),
        )
        # FIXME This is a bit of a hack. The dataset should be clean by the time it gets here.
        # DOUBLE FIXME: Moved across Lucas's hack from the front-end, this should be fixed in this sprint
        # the hack is in order to pivot, there should be no duplicates in the data, i.e. path / feature / value
        # UPDATE: I believe the duplicates are not actually duplicates, but features corresponding to windows of
        # the spectrogram, these should either be treated independently and given a unique identifier in soundade
        # or shown as aggregate statistics (as in soundade's summary stats)
        def dedup_acoustic_features(data):
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

            return data.reset_index().melt(
                id_vars=index,
                value_vars=data.columns,
                var_name="feature"
            )

        # TODO: Several hacks left by Lucas, persist to get this view working, can be removed when switching to better structured data
        # 1. remove duplicates
        data = dedup_acoustic_features(data)
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

    # TODO: problem with caching 10M rows! so switched out the larger version...
    # a better way needs to be designed for this... our data files can get very large
    @functools.cached_property
    def birdnet_species_probs(self) -> pd.DataFrame:
        birdnet_species_probs_path = self.path / "birdnet_species_probs_table.parquet"
        logger.debug(f"Loading & caching \"{birdnet_species_probs_path}\"..")
        return pd.read_parquet(birdnet_species_probs_path)

    @functools.cached_property
    def species(self) -> pd.DataFrame:
        species_path = self.path / "species_table.parquet"
        logger.debug(f"Loading & caching \"{species_path}\"..")
        return pd.read_parquet(species_path)

    @functools.cached_property
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

    @functools.cached_property
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

    @functools.cached_property
    def files(self) -> pd.DataFrame:
        files_path = self.path / "files_table.parquet"
        logger.debug(f"Loading & caching \"{files_path}\"..")
        data = pd.read_parquet(files_path)
        logger.debug(f"Compute temporal splits..")
        data['minute'] = data["timestamp"].dt.minute
        data['hour'] = data["timestamp"].dt.hour
        data['weekday'] = data["timestamp"].dt.day_name()
        data['date'] = data["timestamp"].dt.strftime('%Y-%m-%d')
        data['month'] = data["timestamp"].dt.month_name()
        data['year'] = data["timestamp"].dt.year
        data["time"] = data["timestamp"].dt.hour + data.timestamp.dt.minute / 60.0
        return data

    @functools.cached_property
    def dates(self) -> pd.DataFrame:
        try:
            dates_path = self.path / "dates_table.parquet"
            logger.debug(f"Loading & caching \"{dates_path}\"..")
            return pd.read_parquet(dates_path)
        except Exception as e:
            return pd.DataFrame()

    @functools.cached_property
    def weather(self) -> pd.DataFrame:
        try:
            weather_path = self.path / "weather_table.parquet"
            logger.debug(f"Loading & caching \"{weather_path}\"..")
            return pd.read_parquet(weather_path).set_index(["site_id", "timestamp"])
        except Exception as e:
            return pd.DataFrame()

    @functools.cached_property
    def file_weather(self) -> pd.DataFrame:
        """
        if we want to look at the weather for specific files,
        we need to duplicate weather data for each file reference
        Weather data is by the hour, but files can be snapshots at any temporal resolution
        we round the file timestamp to the nearest hour, left join with weather on the timestamp
        by preserving the weather timestamp, we throw away everything other than file_id
        resulting df is same length as files table with weather data from the nearest hour
        """
        try:
            files = self.files
            files["nearest_hour"] = files["timestamp"].dt.round("h")
            id_vars = ["file_id", "site_id", "timestamp_weather", "timestamp"]
            return files.reset_index().merge(
                self.weather.reset_index(),
                left_on=["nearest_hour", "site_id"],
                right_on=["timestamp", "site_id"],
                suffixes=("", "_weather"),
            ).filter(
                items=[*id_vars, *self.weather.columns],
            )
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
