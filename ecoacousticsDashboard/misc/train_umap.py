import argparse
import numpy as np
import pandas as pd
import pyarrow as pa
import itertools
import yaml

from pathlib import Path
from loguru import logger
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler
from typing import Any, Dict, Tuple, List
from umap.parametric_umap import ParametricUMAP

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

def train_umap(
    data: pd.DataFrame,
    save_dir: str | Path | None = None,
    **kwargs: Any,
) -> None:
    data = dedup_acoustic_features(data)
    data = data.pivot(
        index=data.columns[~data.columns.isin(["feature", "value"])],
        columns='feature',
        values='value',
    )
    # scale features using outlier-robust scaler
    scaler = RobustScaler()
    # a parametric model we can save and use to encode later
    model = ParametricUMAP(**kwargs)
    # fit the graph and embedding function
    pipe = make_pipeline(scaler, model)
    logger.debug(f"Fitting..")
    pipe.fit(data)
    # persist training scaler parameters for inference
    save_dir.mkdir(exist_ok=True, parents=True)
    with open(save_dir / "config.yaml", "w+"):
        yaml.dump(dict(
            center_=scaler.center_,
            scale_=scaler.scale_,
            n_features_in_=scaler.n_features_in_,
            feature_names_in_=scaler.features_names_in_,
        ))
        logger.debug(f"Scaler parameters saved to {save_dir / 'config.yaml'}")
    # persist the model
    model.save(save_dir)
    logger.debug(f"Model saved to {save_dir}")

def main(
    acoustic_features_path: str | Path,
    save_dir: str | Path,
    n_neighbours: int,
    min_dist: float,
    n_components: int,
    metric: str,
) -> None:
    train_umap(
        data=pd.read_parquet(acoustic_features_path),
        save_dir=save_dir,
        n_neighbors=n_neighbours,
        min_dist=min_dist,
        n_components=n_components,
        metric=metric,
    )

def get_base_parser():
    parser = argparse.ArgumentParser(
        description='Fetch and persist weather data for audio files',
        add_help=False,
    )
    parser.add_argument(
        "--acoustic-features-path",
        required=True,
        type=lambda p: Path(p),
        help="Parquet file containing site information."
    )
    parser.add_argument(
        "--save-dir",
        default=None,
        type=lambda p: Path(p),
        help="Parquet file containing site information."
    )
    parser.add_argument(
        "--n-neighbours",
        default=15,
        type=int,
        help="Balances local vs global structure by constraining the inferred graph's neighbourhood"
    )
    parser.add_argument(
        "--min-dist",
        default=0.1,
        type=float,
        help="Controls how tightly UMAP packs points together"
    )
    parser.add_argument(
        "--n-components",
        default=2,
        type=float,
        help="The number of dimensions in the output embedding"
    )
    parser.add_argument(
        "--metric",
        default='euclidean',
        type=str,
        help="Distance metric in feature space"
    )
    return parser

if __name__ == '__main__':
    parser = get_base_parser()
    args = parser.parse_args()
    main(**vars(args))

