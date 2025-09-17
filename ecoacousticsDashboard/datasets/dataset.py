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
        return pd.read_parquet(self.path / "solar_table.parquet").set_index(["site_id", "date"])

    @functools.cached_property
    def weather(self):
        return pd.read_parquet(self.path / "weather_table.parquet").set_index(["site_id", "timestamp"])

    @functools.cached_property
    def files(self):
        files = pd.read_parquet(self.path / "files_table.parquet")
        files["local_file_path"] = (self.audio_path / files["file_path"]).astype(str)
        files["minute"] = files["timestamp"].dt.minute
        files["hour"] = files["timestamp"].dt.hour
        files["weekday"] = files["timestamp"].dt.day_name()
        files["date"] = pd.to_datetime(files["timestamp"].dt.strftime('%Y-%m-%d'))
        files["month"] = files["timestamp"].dt.month_name()
        files["year"] = files["timestamp"].dt.year
        files["time"] = files["timestamp"].dt.hour + files.timestamp.dt.minute / 60.0
        files["nearest_hour"] = files["timestamp"].dt.round("h")
        weather = self.weather
        solar = self.solar
        locations = self.locations
        return (
            files
            .merge(weather, left_on=["site_id", "nearest_hour"], right_on=["site_id", "timestamp"], suffixes=("", "_weather"))
            .join(solar, on=["site_id", "date"])
            .join(locations, on="site_id")
        )

    @functools.cached_property
    def species_predictions(self):
        species = self.species
        files = self.files
        return (
            pd.read_parquet(self.path / "birdnet_species_probs_table.parquet")
            .drop(["common_name", "label"], axis=1) # superfluous, exists on species table
            .join(species.set_index("scientific_name"), on="scientific_name")
            .join(files.set_index("file_id"), on="file_id", rsuffix="_files")
        )

    def save_config(self):
        with open(self.path / "config.ini", "w") as f:
            self.config.write(f)

    @functools.cached_property
    def acoustic_features(self) -> pd.DataFrame:
        files = self.files
        return (
            pd.read_parquet(self.path / "recording_acoustic_features_table.parquet")
            .join(files.set_index("file_id"), on="file_id", rsuffix="_files")
        )

    @functools.cached_property
    def acoustic_features_umap(self) -> pd.DataFrame:
        with open(self.path / "umap" / "config.yaml", "rb") as f:
            config = pickle.load(f)
        scaler = RobustScaler()
        for attr_name, attr_value in config.items():
            setattr(scaler, attr_name, attr_value)
        model = load_ParametricUMAP(self.path / "umap")
        acoustic_features = self.acoustic_features
        feature_idx = acoustic_features.feature.isin(config["feature_names_in_"])
        index = acoustic_features.columns[~acoustic_features.columns.isin(["feature", "value"])]
        data = (
            acoustic_features[feature_idx]
            .pivot(index=index, columns="feature", values="value")
        )
        data["x"], data["y"] = np.split(
            make_pipeline(scaler, model).transform(data),
            indices_or_sections=2,
            axis=1,
        )
        return data.reset_index()

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
