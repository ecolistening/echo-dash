from __future__ import annotations

import attrs
import pandas as pd
import pathlib

from functools import cached_property
from loguru import logger
from typing import Dict, List

from config import root_dir
from data.dataset import Dataset

@attrs.define
class DatasetLoader:
    root_dir: pathlib.Path
    datasets: List[str] = attrs.field(factory=list)

    def __attrs_post_init__(self) -> None:
        self._init_datasets(self.datasets_table)

    @cached_property
    def datasets_table(self):
        return pd.read_parquet(self.root_dir / "datasets_table.parquet")

    def get_dataset(self, dataset_name):
        return self.datasets[dataset_name]

    def get_dataset_names(self):
        return list(self.datasets.keys())

    def get_sites(self, dataset_name: str):
        dataset = self.datasets[dataset_name]
        return dataset.locations

    def _init_datasets(self, datasets_table: pd.DataFrame) -> Dict[str, Dataset]:
        self.datasets = {}
        for dataset in datasets_table.reset_index().to_dict(orient="records"):
            try:
                logger.debug(f"Loading and caching {dataset['dataset_name']}")
                dataset = Dataset(**dataset)
                self.datasets[dataset.dataset_name] = dataset
            except Exception as e:
                logger.error(f"Unable to load dataset {dataset['dataset_name']}")
                logger.error(e)
