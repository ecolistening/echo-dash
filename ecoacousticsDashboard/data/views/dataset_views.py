from __future__ import annotations

import attrs
import cachetools
import pandas as pd

from functools import cached_property
from loguru import logger
from typing import Callable, List, Tuple

from data.dataset import Dataset
from utils import dedup

# FIXME: there's no validation on the inputs before a query is executed
@attrs.define
class DatasetViews:
    """
    DatasetViews class loads persisted views, or creates, caches and persists new views
    """
    dataset: Dataset

    @cached_property
    def cache(self):
        return cachetools.LRUCache(maxsize=10)

    @property
    def path(self):
        return self.dataset.path / "views"

    @staticmethod
    def lookup_key(*args: Tuple[str]) -> str:
        return "_".join(args)

    def species_richness(
        self,
        threshold: float,
        group_by: List[str],
        dates: List[str] = [],
        locations: List[str] = [],
    ) -> pd.DataFrame:
        return self._fetch_view(
            self.lookup_key(str(threshold), *group_by, *dates, *locations),
            DatasetViews.species_richness.__name__,
            lambda: Q.species_richness_query(self.dataset.species_predictions, threshold, group_by, dates, locations),
        )

    def species_abundance(
        self,
        threshold: float,
        group_by: List[str],
        dates: List[str] = [],
        locations: List[str] = [],
    ) -> pd.DataFrame:
        return self._fetch_view(
            self.lookup_key(str(threshold), *group_by, *dates, *locations),
            DatasetViews.species_abundance.__name__,
            lambda: Q.species_abundance_query(self.dataset.species_predictions, threshold, group_by, dates, locations),
        )

    def _fetch_view(
        self,
        lookup_id: str,
        query_name: str,
        query: Callable,
    ) -> pd.DataFrame:
        view_path = self.path / "views" / f"{query_name}_{lookup_id}.parquet"
        # if its not been cached and a persisted view exists, load it
        if lookup_id not in self.cache and view_path.exists():
            logger.debug(f"[LOAD] Query: {query_name}({lookup_id=})")
            self.cache[lookup_id] = pd.read_parquet(view_path)
            return self.cache[lookup_id]
        # if its not been cached, execute the query
        elif lookup_id not in self.cache:
            logger.debug(f"[CACHE] Query: {query_name}({lookup_id=})")
            view = query()
            view_path.parent.mkdir(exist_ok=True, parents=True)
            view.to_parquet(view_path)
            self.cache[lookup_id] = view
            return self.cache[lookup_id]
        # it has been cached, simply return it
        else:
            logger.debug(f"[FETCH] Query: {query_name}({lookup_id=})")
            return self.cache[lookup_id]
