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
    datasets_table: pd.DataFrame = attrs.field(init=False, default=list)

    def __attrs_post_init__(self):
        self.datasets_table = pd.read_parquet(self.root_dir / "datasets_table.parquet")
        self.datasets = self._init_datasets(self.datasets_table)

    def __iter__(self):
        for each in self.datasets.values():
            yield each

    def get_dataset(self, dataset_name):
        return self.datasets[dataset_name]

    def get_dataset_names(self):
        return list(self.datasets.keys())

    @staticmethod
    def _init_datasets(datasets_table: pd.DataFrame) -> Dict[str, Dataset]:
        datasets = {}
        for dataset in datasets_table.reset_index().to_dict(orient="records"):
            try:
                logger.debug(f"Loading {dataset['dataset_name']}")
                ds = Dataset(**dataset)
                datasets[ds.dataset_name] = ds
            except Exception as e:
                logger.error(f"Unable to load dataset {dataset['dataset_name']}")
                logger.error(e)
        return datasets
