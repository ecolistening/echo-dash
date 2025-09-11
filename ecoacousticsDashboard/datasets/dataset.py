import attrs
import bigtree as bt
import functools
import numpy as np
import pandas as pd
import pathlib
import pickle

from configparser import ConfigParser
from loguru import logger
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler
from typing import Any, Callable, Dict, List, Tuple, Iterable
from umap.parametric_umap import load_ParametricUMAP

@attrs.define
class Dataset:
    dataset_id: str
    dataset_name: str
    dataset_path: str
    audio_path: str

    config: ConfigParser = attrs.field(init=False)
    sites_tree: bt.Node = attrs.field(init=False)

    files: pd.DataFrame = attrs.field(init=False)
    locations: pd.DataFrame = attrs.field(init=False)
    solar: pd.DataFrame = attrs.field(init=False)
    weather: pd.DataFrame = attrs.field(init=False)
    acoustic_features: pd.DataFrame = attrs.field(init=False)
    species: pd.DataFrame = attrs.field(init=False)
    species_predictions: pd.DataFrame = attrs.field(init=False)

    @property
    def path(self):
        return pathlib.Path.cwd().parent / "data" / self.dataset_path

    def __attrs_post_init__(self) -> None:
        self.config = self._read_or_build_config(self.path / "config.ini")
        logger.info({ "dataset_name": self.dataset_name, "message": "loaded config" })
        # cache species table
        self.species = pd.read_parquet(self.path.parent / "species_table.parquet")
        self._add_fields_to_species_table()
        logger.info({ "dataset_name": self.dataset_name, "message": "loaded species" })
        # cache locations table and site hierarchy
        self.locations = pd.read_parquet(self.path / "locations_table.parquet")
        self._add_fields_to_locations_table()
        self.sites_tree = bt.dataframe_to_tree(self.locations, path_col="site")
        logger.info({ "dataset_name": self.dataset_name, "message": "loaded locations" })
        # cache solar and weather data
        self.solar = pd.read_parquet(self.path / "solar_table.parquet").set_index(["site_id", "date"])
        self.weather = pd.read_parquet(self.path / "weather_table.parquet").set_index(["site_id", "timestamp"])
        logger.info({ "dataset_name": self.dataset_name, "message": "loaded solar / weather" })
        # cache file index, merge solar and weather data
        self.files = pd.read_parquet(self.path / "files_table.parquet")
        self._add_fields_to_files_table()
        self.files = (
            self.files
            .merge(self.weather, left_on=["site_id", "nearest_hour"], right_on=["site_id", "timestamp"], suffixes=("", "_weather"))
            .join(self.solar, on=["site_id", "date"])
            .join(self.locations, on="site_id")
        )
        logger.info({ "dataset_name": self.dataset_name, "message": "loaded files" })
        # cache acoustic features, merge file, solar, weather and location data
        self.acoustic_features = (
            pd.read_parquet(self.path / "recording_acoustic_features_table.parquet")
            .join(self.files.set_index("file_id"), on="file_id", rsuffix="_files")
        )
        logger.info({ "dataset_name": self.dataset_name, "message": "loaded acoustic features" })
        # cache birdnet predictions, merge file, solar, weather and location data
        # for every unique detection, pad with zeros for all other species
        # birdnet_probs = (
        #     pd.read_parquet(self.path / "birdnet_species_probs_table.parquet")
        #     .drop(["common_name", "label"], axis=1) # superfluous, exists on species table
        # )
        # indices = birdnet_probs.columns[~birdnet_probs.columns.isin(["scientific_name", "confidence"])]
        # self.species_predictions = (
        #     birdnet_probs[indices].drop_duplicates()
        #     .merge(self.species.reset_index(), how="cross")
        #     .merge(birdnet_probs, on=[*indices, "scientific_name"], how="left")
        #     .fillna(0.0)
        #     .join(self.files.set_index("file_id"), on="file_id", rsuffix="_files")
        # )
        self.species_predictions = (
            pd.read_parquet(self.path / "birdnet_species_probs_table.parquet")
            .drop(["common_name", "label"], axis=1) # superfluous, exists on species table
            .join(self.species.set_index("scientific_name"), on="scientific_name")
            .join(self.files.set_index("file_id"), on="file_id", rsuffix="_files")
        )
        logger.info({ "dataset_name": self.dataset_name, "message": "loaded species probs" })

    def save_config(self):
        with open(self.path / "config.ini", "w") as f:
            self.config.write(f)

    @functools.cached_property
    def acoustic_features_umap(self) -> pd.DataFrame:
        with open(self.path / "umap" / "config.yaml", "rb") as f:
            config = pickle.load(f)
        scaler = RobustScaler()
        for attr_name, attr_value in config.items():
            setattr(scaler, attr_name, attr_value)
        model = load_ParametricUMAP(self.path / "umap")
        feature_idx = self.acoustic_features.feature.isin(config["feature_names_in_"])
        index = self.acoustic_features.columns[~self.acoustic_features.columns.isin(["feature", "value"])]
        data = (
            self.acoustic_features[feature_idx]
            .pivot(index=index, columns="feature", values="value")
        )
        data["x"], data["y"] = np.split(
            make_pipeline(scaler, model).transform(data),
            indices_or_sections=2,
            axis=1,
        )
        return data.reset_index()

    def _add_fields_to_species_table(self) -> None:
        self.species["common_name"] = self.species["common_name"].fillna("")
        self.species["species"] = self.species[["scientific_name", "common_name"]].agg("\n".join, axis=1)
        # HACK: FIXME prevent nulls in the front-end by populating missing values
        self.species[self.species["habitat_type"].isna()] = "Unspecified"
        self.species[self.species["trophic_level"].isna()] = "Unspecified"
        self.species[self.species["trophic_niche"].isna()] = "Unspecified"
        self.species[self.species["primary_lifestyle"].isna()] = "Unspecified"

    def _add_fields_to_files_table(self):
        # TODO: this should be adjusted based on dataset? what about remote file path?
        self.files["file_path"] = self.files["local_file_path"]
        self.files["minute"] = self.files["timestamp"].dt.minute
        self.files["hour"] = self.files["timestamp"].dt.hour
        self.files["weekday"] = self.files["timestamp"].dt.day_name()
        self.files["date"] = pd.to_datetime(self.files["timestamp"].dt.strftime('%Y-%m-%d'))
        self.files["month"] = self.files["timestamp"].dt.month_name()
        self.files["year"] = self.files["timestamp"].dt.year
        self.files["time"] = self.files["timestamp"].dt.hour + self.files.timestamp.dt.minute / 60.0
        self.files["nearest_hour"] = self.files["timestamp"].dt.round("h")

    def _add_fields_to_locations_table(self) -> None:
        self.locations["site"] = self.dataset_name + "/" + self.locations["site_name"]
        for level, values in self.locations.site.str.split('/', expand=True).iloc[:, 1:].to_dict(orient='list').items():
            self.locations[f"site_level_{level}"] = values

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
