import pandas as pd
import pathlib
import pickle
import numpy as np

from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler
from umap.parametric_umap import load_ParametricUMAP

for dataset_path in [pathlib.Path("../data/cairngorms/"), pathlib.Path("../data/kilpisjarvi/"), pathlib.Path("../data/nature_sense/"), pathlib.Path("../data/sounding_out_chorus/")]:
    files = pd.read_parquet(dataset_path / "files_table.parquet").reset_index()
    features = (
        pd.read_parquet(dataset_path / "recording_acoustic_features_table.parquet")
        .merge(files[["file_id", "index"]], on="file_id", how="left")
        .drop(["file_id", "sr", "frame_length", "hop_length", "segment_id", "n_fft", "feature_length"], axis=1)
        .rename(columns={"index": "file_id", "segment_idx": "segment_id"})
        .pivot(index=['file_id', 'segment_id', 'duration', 'offset'], columns="feature", values="value")
        .reset_index()
        .rename_axis(None, axis=1)
    )
    features.to_parquet(dataset_path / "recording_acoustic_features.parquet")
    birdnet_probs = (
        pd.read_parquet(dataset_path / "birdnet_species_probs_table.parquet")
        .merge(files[["file_id", "index"]], how="left", on="file_id")
        .drop(["file_id", "model", "min_conf", "label", "common_name"], axis=1)
        .rename(columns={"index": "file_id"})
    )
    birdnet_probs.to_parquet(dataset_path / "birdnet_species_probs.parquet")
    files = (
        files
        .drop(["file_id", "duration"], axis=1)
        .rename(columns={"index": "file_id"})
        .assign(minute=lambda df: df["timestamp"].dt.minute)
        .assign(hour=lambda df: df["timestamp"].dt.hour)
        .assign(weekday=lambda df: df["timestamp"].dt.day_name())
        .assign(date=lambda df: pd.to_datetime(df["timestamp"].dt.strftime('%Y-%m-%d')))
        .assign(month=lambda df: df["timestamp"].dt.month_name())
        .assign(year=lambda df: df["timestamp"].dt.year)
        .assign(time=lambda df: df["timestamp"].dt.hour + df.timestamp.dt.minute / 60.0)
        .assign(nearest_hour=lambda df: df["timestamp"].dt.round("h"))
    )
    files.to_parquet(dataset_path / "files.parquet")

    # build union table for acoustic features
    locations = pd.read_parquet(dataset_path / "locations_table.parquet")
    weather = (
        pd.read_parquet(dataset_path / "weather_table.parquet")
        .assign(nearest_hour=lambda df: df["timestamp"])
        .drop("timestamp", axis=1)
    )
    file_site_weather = (
        files
        .merge(weather, on=["site_id", "nearest_hour"], how="left")
        .merge(locations, on="site_id", how="left")
    )
    indices = features.merge(file_site_weather, on="file_id", how="left")

    with open(dataset_path / "umap" / "config.yaml", "rb") as f:
        config = pickle.load(f)
    scaler = RobustScaler()
    for attr_name, attr_value in config.items():
        setattr(scaler, attr_name, attr_value)
    feature_column_names = config["feature_names_in_"]
    model = make_pipeline(scaler, load_ParametricUMAP(dataset_path / "umap"))

    def encode(data: pd.DataFrame) -> pd.DataFrame:
        xy = model.transform(data.loc[:, feature_column_names])
        data["x"], data["y"] = np.split(xy, indices_or_sections=2, axis=1)
        return data

    indices = encode(indices)
    indices.to_parquet(dataset_path / "indices.parquet")

    # build union table for birdnet probs
    species = (
        pd.read_parquet(dataset_path.parent / "species_table.parquet")
        .assign(species=lambda df: df[["scientific_name", "common_name"]].agg("\n".join, axis=1))
    )
    species_probs = (
        pd.read_parquet(dataset_path / "birdnet_species_probs.parquet", columns=["file_id", "scientific_name", "confidence"])
    )
    species_probs = species_probs.merge(species, on="scientific_name", how="left").merge(file_site_weather, on="file_id", how="left")
    species_probs.to_parquet(dataset_path / "species.parquet")
