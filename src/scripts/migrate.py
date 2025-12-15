import pathlib
import pandas as pd
import pickle
import numpy as np
import rootutils

from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler
from umap.parametric_umap import load_ParametricUMAP

rootutils.setup_root(__file__, indicator=".project-root", pythonpath=True)

# data migration into single tables, massive data duplication but may be faster at runtime
for dataset_name in ["cairngorms", "kilpisjarvi", "nature_sense", "sounding_out", "sounding_out_chorus"]:
    root = rootutils.find_root() / ".." / "data" / dataset_name

    files = pd.read_parquet(root / "files_table.parquet")
    weather = pd.read_parquet(root / "weather_table.parquet")
    solar = pd.read_parquet(root / "solar_table.parquet")
    features = pd.read_parquet(root / "recording_acoustic_features_table.parquet")
    species_probs = pd.read_parquet(root / "birdnet_species_probs_table.parquet")
    locs = pd.read_parquet(root / "locations_table.parquet")
    species = pd.read_parquet(root / ".." / "species_table.parquet")
    species["species"] = species[["scientific_name", "common_name"]].agg("\n".join, axis=1)

    locs["site"] = dataset_name + "/" + locs["site_name"]
    for level, values in locs.site.str.split('/', expand=True).iloc[:, 1:].to_dict(orient='list').items():
        try:
            locs[f"sitelevel_{level}"] = list(map(int, values))
        except ValueError:
            locs[f"sitelevel_{level}"] = values

    files["minute"] = files["timestamp"].dt.minute
    files["hour_categorical"] = files["timestamp"].dt.hour.astype(str)
    files["hour_continuous"] = files["timestamp"].dt.hour.astype(float)
    files["week_of_year_continuous"] = files["timestamp"].dt.isocalendar()["week"] / 53
    files["week_of_year_categorical"] = files["timestamp"].dt.isocalendar()["week"].astype(str)
    files["weekday"] = files["timestamp"].dt.day_name().str[:3]
    files["date"] = pd.to_datetime(files["timestamp"].dt.strftime('%Y-%m-%d'))
    files["month"] = files["timestamp"].dt.month_name().str[:3]
    files["year"] = files["timestamp"].dt.year.astype(str)
    files["time"] = files["timestamp"].dt.hour + files.timestamp.dt.minute / 60.0
    files["nearest_hour"] = files["timestamp"].dt.round("h")

    files["hour_after_sunrise"] = files["hours after sunrise"].round(0).astype("Int64")
    files["hour_after_dawn"] = files["hours after dawn"].round(0).astype("Int64")
    files["hour_after_noon"] = files["hours after noon"].round(0).astype("Int64")
    files["hour_after_dusk"] = files["hours after dusk"].round(0).astype("Int64")
    files["hour_after_sunset"] = files["hours after sunset"].round(0).astype("Int64")

    files["sr_original"] = files["sr"]
    files["file_duration"] = files["duration"]
    files.drop(["sr", "duration"], axis=1, inplace=True)

    weather.rename(columns={"timestamp": "nearest_hour"}, inplace=True)

    file_site_weather = files.merge(weather, on=["site_id", "nearest_hour"], how="left").merge(locs, on="site_id", how="left")

    with open(root / "umap" / "config.yaml", "rb") as f:
        config = pickle.load(f)

    scaler = RobustScaler()
    for attr_name, attr_value in config.items():
        setattr(scaler, attr_name, attr_value)

    feature_column_names = config["feature_names_in_"]
    umap_model = load_ParametricUMAP(root / "umap")
    model = make_pipeline(scaler, umap_model)

    xy = model.transform(features.loc[:, feature_column_names])
    features["x"], features["y"] = np.split(xy, indices_or_sections=2, axis=1)

    file_site_weather.to_parquet(root / "files.parquet")
    df = features.merge(file_site_weather, on="file_id", how="left")
    df.to_parquet(root / "features.parquet")
    df1 = species_probs.merge(species, on=["scientific_name", "common_name"], how="left").merge(file_site_weather, on="file_id", how="left")
    df1.to_parquet(root / "species.parquet")
