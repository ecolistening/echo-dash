import pandas as pd

from loguru import logger
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler
from typing import Any
from umap import UMAP

def umap_data(
    data: pd.DataFrame,
    **kwargs: Any,
) -> pd.DataFrame:
    pipe = make_pipeline(RobustScaler(), UMAP(**kwargs))
    proj = pipe.fit_transform(data)
    return (
        pd.DataFrame(proj, index=data.index)
        .rename(columns={0: "x", 1: "y"})
        .reset_index()
    )
