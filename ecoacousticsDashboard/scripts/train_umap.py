import argparse
import datetime as dt
import numpy as np
import pandas as pd
import pyarrow as pa
import itertools
import pickle

from pathlib import Path
from loguru import logger
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler
from typing import Any, Dict, Tuple, List
from umap.parametric_umap import ParametricUMAP

FEATURES = [
    'zero crossing rate', 'spectral centroid', 'root mean square',
    'spectral flux', 'acoustic evenness index', 'bioacoustic index',
    'acoustic complexity index', 'spectral entropy', 'temporal entropy',
]

def train_umap(
    data: pd.DataFrame,
    save_dir: str | Path | None = None,
    **kwargs: Any,
) -> None:
    data = data[["file_id", *FEATURES]].set_index("file_id")
    num_samples = data.shape[0]
    data = data.loc[np.isfinite(data).all(axis=1), :]
    if num_samples > (remaining := data.shape[0]):
        logger.debug(f"Removed {num_samples - remaining} NaN samples.")
    # scale features using outlier-robust scaler
    scaler = RobustScaler()
    # a parametric model we can save and use to encode later
    # FIXME: there appears to be a bug where if you don't specify a decoder, you cannot
    # reload the pickled model. This fixes it, but a decoder is trained concurrently and separately
    model = ParametricUMAP(parametric_reconstruction=True, **kwargs)
    # fit the graph and embedding function
    pipe = make_pipeline(scaler, model)
    logger.debug(f"Fitting...")
    pipe.fit(data)
    # persist scaling parameters and feature list
    save_dir.mkdir(exist_ok=True, parents=True)
    with open(save_dir / "config.yaml", "wb") as f:
        config = dict(
            center_=scaler.center_,
            scale_=scaler.scale_,
            n_features_in_=scaler.n_features_in_,
            feature_names_in_=scaler.feature_names_in_,
        )
        pickle.dump(config, f)
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
    start_time = time.time()

    train_umap(
        data=pd.read_parquet(acoustic_features_path),
        save_dir=save_dir,
        n_neighbors=n_neighbours,
        min_dist=min_dist,
        n_components=n_components,
        metric=metric,
    )

    log.info(f"UMAP complete")
    log.info(f"Time taken: {str(dt.timedelta(seconds=time.time() - start_time))}")

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

