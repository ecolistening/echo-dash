import attrs
import bigtree as bt
import functools
import numpy as np
import pandas as pd
import pickle

from configparser import ConfigParser
from pathlib import Path
from loguru import logger
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler
from typing import Any, Callable, Dict, List, Tuple, Iterable
from umap.parametric_umap import load_ParametricUMAP

@attrs.define
class Dataset:
    dataset_path: str

    dataset_id: str = attrs.field(init=False)
    dataset_name: str = attrs.field(init=False)
    audio_path: str = attrs.field(init=False)
    config: ConfigParser = attrs.field(init=False)

    @property
    def path(self):
        return Path.cwd().parent / "data" / self.dataset_path

    def __attrs_post_init__(self) -> None:
        self.config = self._read_or_build_config(self.path / "config.ini")
        self.dataset_name = self.config.get("Dataset", "name")
        self.dataset_id = self.config.get("Dataset", "id")
        self.audio_path = Path(self.config.get("Dataset", "audio_path"))

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
        files["local_file_path"] = (self.audio_path / files["file_path"]).astype(str)
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

    @staticmethod
    def append_columns(data: pd.DataFrame) -> pd.DataFrame:
        if "timestamp" in data.columns:
            data["minute"] = data["timestamp"].dt.minute
            data["hour"] = data["timestamp"].dt.hour
            data["weekday"] = data["timestamp"].dt.day_name()
            data["date"] = pd.to_datetime(data["timestamp"].dt.strftime('%Y-%m-%d'))
            data["month"] = data["timestamp"].dt.month_name()
            data["year"] = data["timestamp"].dt.year
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
