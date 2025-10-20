from __future__ import annotations

import attrs
import functools
import numpy as np

from loguru import logger
from typing import Any, Dict, Tuple, List

from datasets.dataset import Dataset
from utils import floor, ceil, capitalise_each

DEFAULT_OPTION_GROUPS = ("Site Level", "Time of Day", "Temporal")# "Spatial")
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
DDDN = ["dawn", "day", "dusk", "night"]

@attrs.define
class DatasetDecorator:
    dataset: Dataset

    def drop_down_select_option_groups(self, option_groups: Tuple[str] = ()):
        if not len(option_groups):
            option_groups = DEFAULT_OPTION_GROUPS
        opt_groups = []
        column_groups = zip(option_groups, [self.option_groups_mapping[s] for s in option_groups])
        for group_name, column_group in column_groups:
            opt_groups.append({
                "group": group_name,
                "items": [
                    { "value": value, **params }
                    for value, params in column_group.items()
                ],
            })
        return opt_groups

    @property
    def option_groups_mapping(self) -> Dict[str, List]:
        return {
            "File Level": self.file_level_columns,
            "Site Level": self.site_level_columns,
            "Time of Day": self.solar_columns,
            "Time": self.time_columns,
            "Temporal": self.temporal_columns,
            "Spatial": self.spatial_columns,
            "Temperature": self.temperature_columns,
            "Precipitation": self.precipitation_columns,
            "Wind": self.wind_columns,
            "Species Habitat": self.species_habitat_columns,
            "Functional Groups": self.species_functional_group_columns,
            "Acoustic Features": self.acoustic_feature_columns,
        }

    @property
    def options(self):
        return (
            self.site_level_columns |
            self.solar_columns |
            self.time_columns |
            self.temporal_columns |
            self.spatial_columns |
            self.temperature_columns |
            self.precipitation_columns |
            self.wind_columns |
            self.species_habitat_columns |
            self.species_functional_group_columns |
            self.acoustic_feature_columns
        )

    @property
    def category_orders(self):
        return {
            column: order
            for column, params in self.options.items()
            if (order := params.get("order", None)) is not None
        }

    @property
    def file_level_columns(self) -> Dict[str, List[Any]]:
        return {
            "valid": {
                "label": "Valid",
            }
        }

    @functools.cached_property
    def acoustic_feature_columns(self) -> Dict[str, List[Any]]:
        return {
            feature: {
                "label": capitalise_each(feature),
            }
            for feature in self.dataset.acoustic_feature_list
        }

    @functools.cached_property
    def site_level_columns(self) -> Dict[str, List[Any]]:
        columns = {}
        for column in self.dataset.locations.columns:
            if column.startswith("sitelevel_"):
                label = self.dataset.config.get('Site Hierarchy', column, fallback=column)
                values = self.dataset.files[column].unique()
                try:
                    order = list(map(str, sorted(map(int, values))))
                except ValueError:
                    order = list(sorted(values))
                columns[column] = {"label": label, "order": order}
        return columns

    @functools.cached_property
    def solar_columns(self) -> Dict[str, List[Any]]:
        return {
            "dddn": {
                "order": sorted(self.dataset.files["dddn"].unique(), key=lambda x: DDDN.index(x)),
                "label": "Dawn/Day/Dusk/Night",
            },
        }

    @functools.cached_property
    def time_columns(self) -> Dict[str, List[Any]]:
        return {
            "time": {
                "label": "Hours After Midnight",
                "min": self.dataset.files["time"].min(),
                "max": self.dataset.files["time"].max(),
            },
            **{
                # FIXME: change these in soundade to snake case for application-wide consistency
                f"hours after {c}": {
                    "label": f"Hours After {c.capitalize()}",
                    "min": self.dataset.files[f"hours after {c}"].min(),
                    "max": self.dataset.files[f"hours after {c}"].max(),
                }
                for c in ["dawn", "sunrise", "noon", "sunset", "dusk"]
            }
        }

    @functools.cached_property
    def temporal_columns(self) -> Dict[str, List[Any]]:
        return {
            "hour_continuous": {
                "order": list(range(24)),
                "label": "Hour (Continuous)",
            },
            "hour_categorical": {
                "order": list(map(str, range(24))),
                "label": "Hour (Categorical)",
            },
            "week_of_year_continuous": {
                "order": list(range(53)),
                "label": "Week of Year (Continuous)",
            },
            "week_of_year_categorical": {
                "order": list(map(str, range(53))),
                "label": "Week of Year (Categorical)",
            },
            "weekday": {
                "order": sorted(self.dataset.files["weekday"].unique(), key=lambda x: WEEKDAYS.index(x)),
                "label": "Week Day",
            },
            "month": {
                "order": sorted(self.dataset.files["month"].unique(), key=lambda x: MONTHS.index(x)),
                "label": "Month",
            },
            "year": {
                "order": sorted(self.dataset.files['year'].unique()),
                "label": "Year",
            },
        }

    @functools.cached_property
    def spatial_columns(self) -> Dict[str, List[Any]]:
        return {
            "location": {
                "order": sorted(self.dataset.locations["location"].unique()),
                "label": "Location"
            },
            "site": {
                "order": sorted(self.dataset.locations["site"].unique()),
                "label": "Site"
            },
            "recorder": {
                # "order": self.dataset.locations["recorder"].unique(),
                "label": "Recorder"
            },
        }

    @functools.cached_property
    def weather_columns(self) -> Dict[str, List[Any]]:
        return (
            self.temperature_columns |
            self.precipitation_columns |
            self.wind_columns
        )

    @functools.cached_property
    def temperature_columns(self) -> Dict[str, List[Any]]:
        return {
            "temperature_2m": {
                "label": "Temperature at 2m elevation (°C)",
                "min": floor(self.dataset.weather["temperature_2m"].min() / 10) * 10,
                "max": ceil(self.dataset.weather["temperature_2m"].max() / 10) * 10,
            },
        }

    @functools.cached_property
    def precipitation_columns(self) -> Dict[str, List[Any]]:
        labels = ["Rain (cm)", "Snowfall (cm)"]
        column_names = ["rain", "snowfall"]
        columns = {}
        for variable, label in zip(column_names, labels):
            min_val, max_val = 0.0, ceil(max(self.dataset.weather[variable].max(), 1.0) / 10) * 10
            # add a max val so pattern matchers don't break
            if (min_val == 0.0 and max_val == 0.0):
                max_val = 1.0
            columns[variable] = {
                "label": label,
                "min": min_val,
                "max": max_val,
            }
        return columns

    @functools.cached_property
    def wind_columns(self) -> Dict[str, List[Any]]:
        columns = {}
        labels = [
            "Wind Speed at 10m elevation (kph)",
            "Wind Speed at 100m elevation (kph)",
            "Wind Direction at 10m elevation (°)",
            "Wind Direction at 100m elevation (°)",
            "Wind Gusts at 10m elevation (kph)",
        ]
        column_names = [
            "wind_speed_10m",
            "wind_speed_100m",
            "wind_direction_10m",
            "wind_direction_100m",
            "wind_gusts_10m",
        ]
        for variable, label in zip(column_names, labels):
            min_val, max_val = 0.0, ceil(max(self.dataset.weather[variable].max(), 1.0) / 10) * 10
            # add a max val so pattern matchers don't break
            if (min_val == 0.0 and max_val == 0.0):
                max_val = 1.0
            columns[variable] = {
                "label": label,
                "min": min_val,
                "max": max_val,
            }
        return columns

    @functools.cached_property
    def species_habitat_columns(self) -> Dict[str, List[Any]]:
        return {
            "habitat_type": {
                "label": "Habitat Type",
                "order": list(filter(None, self.dataset.species["habitat_type"].unique())),
            },
            "habitat_density": {
                "label": "Habitat Density",
                "order": list(filter(lambda x: not np.isnan(x), self.dataset.species["habitat_density"].unique())),
            },
        }

    @functools.cached_property
    def species_functional_group_columns(self) -> Dict[str, List[Any]]:
        return {
            "trophic_niche": {
                "label": "Trophic Niche",
                "order": list(filter(None, self.dataset.species["trophic_niche"].unique())),
            },
            "trophic_level": {
                "label": "Trophic Level",
                "order": list(filter(None, self.dataset.species["trophic_level"].unique())),
            },
            "primary_lifestyle": {
                "label": "Primary Lifestyle",
                "order": list(filter(None, self.dataset.species["primary_lifestyle"].unique())),
            },
        }

