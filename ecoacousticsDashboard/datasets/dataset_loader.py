import attrs
import pandas as pd
import pathlib

from loguru import logger
from typing import Any, Callable, Dict, List, Tuple, Iterable

from datasets.dataset import Dataset
from utils import query as Q

@attrs.define
class DatasetLoader(Iterable):
    root_dir: pathlib.Path
    datasets: List[Dataset] = attrs.field(init=False, default=list)

    def __attrs_post_init__(self):
        self.datasets = self._init_datasets([
            d for d in self.root_dir.iterdir() if d.is_dir()
        ])

    def __iter__(self):
        for each in self.datasets.values():
            yield each

    def get_dataset(self, dataset_name):
        return self.datasets[dataset_name]

    def get_dataset_names(self):
        return list(self.datasets.keys())

    @staticmethod
    def _init_datasets(datasets_dir: List[pathlib.Path]) -> Dict[str, Dataset]:
        datasets = {}
        for dataset_path in datasets_dir:
            try:
                ds = Dataset(path=dataset_path)
                datasets[ds.dataset_name] = ds
            except Exception as e:
                logger.error(f"Unable to load dataset at {dataset_path}")
                logger.error(e)
        if not len(datasets):
            raise Exception("No datasets available, shutting down")
        return datasets
