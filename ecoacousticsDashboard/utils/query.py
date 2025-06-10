import pandas as pd
from typing import List

def species_abundance_query(
    df: pd.DataFrame,
    species_name: str,
    threshold: float,
    group_by: List[str]
) -> pd.DataFrame:
    """
    If two vocalizations from the same species overlap in time, assume they come from different individuals,
    therefore abundance is computed using the proxy of the maximum number of simultaneous detected vocalisations
    """
    return (
        df[(df["confidence"] > threshold) & (df["common_name"] == species_name)]
        .groupby([*group_by, "species_id", "start_time", "end_time"])
        .size()
        .reset_index(name="count")
        .groupby([*group_by, "species_id"])["count"]
        .max()
        .reset_index(name="abundance")
    )

def species_richness_query(
    df: pd.DataFrame,
    threshold: float,
    group_by: List[str]
) -> pd.DataFrame:
    """
    A count of unique species
    """
    return (
        df[df["confidence"] > threshold]
        .groupby(group_by)["species_id"]
        .nunique()
        .reset_index(name="richness")
    )

def relative_species_abundance_query(
    threshold: str,
    group_by: List[str]
) -> pd.DataFrame:
    df = self.dataset.species_predictions
    filtered = df[df["confidence"] >= threshold]
    species_counts = filtered.groupby([*group_by, "species_id"]).size().reset_index(name="count")
    total_counts = species_counts.groupby(group_by)["count"].transform("sum")
    species_counts["relative_abundance"] = species_counts["count"] / total_counts
    return species_counts
