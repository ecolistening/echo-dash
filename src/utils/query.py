import pandas as pd
import datetime as dt
from loguru import logger
from typing import List
from utils import list2tuple

def species_abundance_query(
    data: pd.DataFrame,
    threshold: float,
    group_by: List[str],
    dates: List[str],
    locations: List[str],
) -> pd.DataFrame:
    """
    If two vocalizations from the same species overlap in time, assume they come from different individuals,
    therefore abundance is computed using the proxy of the maximum number of simultaneous detected vocalisations
    """
    return (
        data[
            (data['site'].isin([l.strip('/') for l in locations])) &
            (data.timestamp.dt.date.between(*list2tuple([dt.date.fromisoformat(d) for d in dates]), inclusive="both")) &
            (data["confidence"] > threshold)
        ]
        .groupby([*group_by, "species_id", "start_time", "end_time"])
        .size()
        .reset_index(name="count")
        .groupby([*group_by, "species_id"])["count"]
        .max()
        .reset_index(name="max_count")
        .groupby(group_by)
        .agg(abundance=("max_count", "sum"))
        .reset_index()
    )

def species_richness_query(
    data: pd.DataFrame,
    threshold: float,
    group_by: List[str],
    dates: List[str],
    locations: List[str],
) -> pd.DataFrame:
    """
    A count of unique species
    """
    return (
        data[
            (data['site'].isin([l.strip('/') for l in locations])) &
            (data.timestamp.dt.date.between(*list2tuple([dt.date.fromisoformat(d) for d in dates]), inclusive="both")) &
            (data["confidence"] > threshold)
        ]
        .groupby(group_by)["species_id"]
        .nunique()
        .reset_index(name="richness")
    )

def relative_species_abundance_query(
    threshold: str,
    group_by: List[str]
) -> pd.DataFrame:
    data = self.dataset.species_predictions
    filtered = data[data["confidence"] >= threshold]
    species_counts = filtered.groupby([*group_by, "species_id"]).size().reset_index(name="count")
    total_counts = species_counts.groupby(group_by)["count"].transform("sum")
    species_counts["relative_abundance"] = species_counts["count"] / total_counts
    return species_counts
