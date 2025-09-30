import attrs
import bigtree as bt
import functools
import numpy as np
import pandas as pd
import pyarrow as pa
import pickle
import os
import yaml

from configparser import ConfigParser
from pathlib import Path
from loguru import logger
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler
from typing import Any, Callable, Dict, List, Tuple, Iterable
from umap.parametric_umap import load_ParametricUMAP

from utils import floor, ceil

@attrs.define
class Dataset:
    path: str

    dataset_id: str = attrs.field(init=False)
    dataset_name: str = attrs.field(init=False)
    audio_path: str = attrs.field(init=False)
    config: ConfigParser = attrs.field(init=False)
    soundade_config: Dict[str, Any] = attrs.field(init=False)
    filters: Dict[str, Any] = attrs.field(init=False)

    def __attrs_post_init__(self) -> None:
        self.config = self._read_or_build_config(self.path / "config.ini")
        self.soundade_config = self._read_soundade_config(self.path / "config.yaml")
        self.dataset_name = self.config.get("Dataset", "name")
        self.dataset_id = self.config.get("Dataset", "id")
        self.audio_path = Path(self.config.get("Dataset", "audio_path"))
        self.filters = self._build_base_filters()

    @property
    def acoustic_feature_list(self):
        ignore_columns = ['sr', 'segment_id', 'segment_idx', 'file_id', 'duration', 'offset', 'frame_length', 'hop_length', 'n_fft', 'feature_length']
        file_path = list((self.path / "recording_acoustic_features_table.parquet").glob("*.parquet"))[0]
        if not file_path:
            raise Exception("Failed to read acoustic features table")
        columns = [s.name for s in pa.parquet.ParquetFile(file_path).schema]
        return [col for col in columns if col not in ignore_columns]

    @functools.cached_property
    def species(self):
        species = pd.read_parquet(self.path.parent / "species_table.parquet")
        species["common_name"] = species["common_name"].fillna("")
        species["species"] = species[["scientific_name", "common_name"]].agg("\n".join, axis=1)
        return species

    @functools.cached_property
    def locations(self):
        locations = pd.read_parquet(self.path / "locations_table.parquet")
        locations["site"] = self.dataset_name + "/" + locations["site_name"]
        for level, values in locations.site.str.split('/', expand=True).iloc[:, 1:].to_dict(orient='list').items():
            locations[f"sitelevel_{level}"] = values
        return locations

    @functools.cached_property
    def sites_tree(self):
        locations = self.locations
        return bt.dataframe_to_tree(locations, path_col="site")

    @functools.cached_property
    def solar(self):
        return pd.read_parquet(self.path / "solar_table.parquet")

    @functools.cached_property
    def weather(self):
        return pd.read_parquet(self.path / "weather_table.parquet")

    @functools.cached_property
    def files(self):
        files = pd.read_parquet(self.path / "files_table.parquet")
        return (
            self.append_columns(files)
            .merge(self.weather, left_on=["site_id", "nearest_hour"], right_on=["site_id", "timestamp"], suffixes=("", "_weather"))
            .merge(self.solar, on=["site_id", "date"], how="left")
            .merge(self.locations, on="site_id", how="left")
        )

    def save_config(self):
        with open(self.path / "config.ini", "w") as f:
            self.config.write(f)

    @functools.cached_property
    def umap(self) -> Callable:
        with open(self.path / "umap" / "config.yaml", "rb") as f:
            config = pickle.load(f)
        scaler = RobustScaler()
        for attr_name, attr_value in config.items():
            setattr(scaler, attr_name, attr_value)
        feature_column_names = config["feature_names_in_"]
        model = make_pipeline(scaler, load_ParametricUMAP(self.path / "umap"))

        def encode(data: pd.DataFrame) -> pd.DataFrame:
            xy = model.transform(data.loc[:, feature_column_names])
            data["x"], data["y"] = np.split(xy, indices_or_sections=2, axis=1)
            return data

        return encode

    def append_columns(self, data: pd.DataFrame) -> pd.DataFrame:
        if "timestamp" in data.columns:
            data["minute"] = data["timestamp"].dt.minute
            data["hour_categorical"] = data["timestamp"].dt.hour.astype(str)
            data["hour_continuous"] = data["timestamp"].dt.hour.astype(int)
            data["week_of_year_continuous"] = data["timestamp"].dt.isocalendar()["week"].astype(int)
            data["week_of_year_categorical"] = data["timestamp"].dt.isocalendar()["week"].astype(str)
            data["weekday"] = data["timestamp"].dt.day_name()
            data["date"] = pd.to_datetime(data["timestamp"].dt.strftime('%Y-%m-%d'))
            data["month"] = data["timestamp"].dt.month_name()
            data["year"] = data["timestamp"].dt.year.astype(str)
            data["time"] = data["timestamp"].dt.hour + data.timestamp.dt.minute / 60.0
            data["nearest_hour"] = data["timestamp"].dt.round("h")
        return data

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

    @staticmethod
    def _read_soundade_config(config_path) -> ConfigParser:
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f.read())
        except (IOError, TypeError) as e:
            logger.error(e)
            return {}

    def _build_base_filters(self):
        filters = {}
        # date filters
        data = pd.read_parquet(self.path / "files_table.parquet")
        min_date = data["timestamp"].dt.date.min().strftime("%Y-%m-%d")
        max_date = data["timestamp"].dt.date.max().strftime("%Y-%m-%d")
        filters["date_range_bounds"] = [min_date, max_date]
        # feature filters
        data = pd.read_parquet(self.path / "recording_acoustic_features_table.parquet")
        acoustic_features = {}
        for feature in self.acoustic_feature_list:
            df = data.loc[:, feature]
            acoustic_features[feature] = [floor(df.min(), precision=2), ceil(df.max(), precision=2)]
            filters["acoustic_features"] = acoustic_features
        # weather filters
        variables = [
            'temperature_2m', 'rain', 'snowfall',
            'wind_speed_10m', 'wind_speed_100m', 'wind_direction_10m',
            'wind_direction_100m', 'wind_gusts_10m'
        ]
        data = pd.read_parquet(self.path / "weather_table.parquet")
        weather_variables = {}
        for variable in variables:
            df = data.loc[:, variable]
            variable_ranges = {}
            min_val, max_val = floor(df.min()), ceil(df.max())
            # add a max val so pattern matchers don't break
            if (min_val == 0.0 and max_val == 0.0):
                max_val = 1.0
            variable_range = [min_val, max_val]
            variable_ranges["variable_range_bounds"] = variable_range
            weather_variables[variable] = variable_ranges
        filters["weather_variables"] = weather_variables
        # site filters
        data = pd.read_parquet(self.path / "locations_table.parquet")
        data["site"] = self.dataset_name + "/" + data["site_name"]
        tree = bt.dataframe_to_tree(data, path_col="site")
        sites = list(bt.tree_to_dict(tree).keys())[1:]
        filters["tree"] = sites
        filters["files"] = {}
        return filters
