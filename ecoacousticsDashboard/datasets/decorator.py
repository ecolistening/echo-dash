from __future__ import annotations

import attrs

from loguru import logger
from typing import Any, Dict, Tuple, List

from datasets.dataset import Dataset
from utils import floor, ceil

DEFAULT_OPTION_GROUPS = ("Site Level", "Time of Day", "Temporal")# "Spatial")

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
            "Temporal": self.temporal_columns,
            "Spatial": self.spatial_columns,
            "Temperature": self.temperature_columns,
            "Precipitation": self.precipitation_columns,
            "Wind": self.wind_columns,
            "Species Habitat": self.species_habitat_columns,
            "Functional Groups": self.species_functional_group_columns,
        }

    @property
    def options(self):
        return (
            self.site_level_columns |
            self.solar_columns |
            self.temporal_columns |
            self.spatial_columns |
            self.temperature_columns |
            self.precipitation_columns |
            self.wind_columns |
            self.species_habitat_columns |
            self.species_functional_group_columns
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

    @property
    def site_level_columns(self) -> Dict[str, List[Any]]:
        return {
            column: {
                "order": sorted(self.dataset.locations[column].unique()),
                "label": self.dataset.config.get('Site Hierarchy', column, fallback=column),
            }
            for column in self.dataset.locations.columns
            if column.startswith("sitelevel_")
        }

    @property
    def solar_columns(self) -> Dict[str, List[Any]]:
        # # FIXME -> will be fixed when solar data is present
        # if len(self.dataset.dates):
        #     opt_groups += [{'value': f'hours after {c}', 'label': f'Hours after {c.capitalize()}', 'group': 'Time of Day', 'type': 'continuous'} for c in ('dawn', 'sunrise', 'noon', 'sunset', 'dusk')]
        return {
            "dddn": {
                "order": ["dawn", "day", "dusk", "night"],
                "label": "Dawn/Day/Dusk/Night",
            },
        }

    @property
    def temporal_columns(self) -> Dict[str, List[Any]]:
        return {
            "hour": {
                "order": list(range(24)),
                "label": "Hour",
            },
            "weekday": {
                "order": ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                "label": "Week Day",
            },
            "month": {
                "order": ['January','February','March','April','May','June','July','August','September','October','November','December'],
                "label": "Month",
            },
            "year": {
                "order": sorted(self.dataset.files['year'].unique()),
                "label": "Year",
            },
        }

    @property
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

    @property
    def weather_columns(self) -> Dict[str, List[Any]]:
        return (
            self.temperature_columns |
            self.precipitation_columns |
            self.wind_columns
        )

    @property
    def temperature_columns(self) -> Dict[str, List[Any]]:
        return {
            "temperature_2m": {
                "label": "Temperature at 2m elevation (°C)",
                "min": floor(self.dataset.weather["temperature_2m"].min()),
                "max": ceil(self.dataset.weather["temperature_2m"].max()),
            },
        }

    @property
    def precipitation_columns(self) -> Dict[str, List[Any]]:
        return {
            "precipitation": {
                "label": "Total Precipitation (cm)",
                "min": 0, # floor(self.dataset.weather["precipitation"].min()),
                "max": ceil(self.dataset.weather["precipitation"].max()),
            },
            "rain": {
                "label": "Rain (cm)",
                "min": 0, # floor(self.dataset.weather["rain"].min()),
                "max": ceil(self.dataset.weather["rain"].max()),
            },
            "snowfall": {
                "label": "Snowfall (cm)",
                "min": 0, # floor(self.dataset.weather["snowfall"].min()),
                "max": ceil(self.dataset.weather["snowfall"].max()),
            },
        }

    @property
    def wind_columns(self) -> Dict[str, List[Any]]:
        return {
            "wind_speed_10m": {
                "label": "Wind Speed at 10m elevation (kph)",
                "min": 0, # floor(self.dataset.weather["wind_speed_10m"].min()),
                "max": ceil(self.dataset.weather["wind_speed_10m"].max()),
            },
            "wind_speed_100m": {
                "label": "Wind Speed at 100m elevation (kph)",
                "min": 0, # floor(self.dataset.weather["wind_speed_100m"].min()),
                "max": ceil(self.dataset.weather["wind_speed_100m"].max()),
            },
            "wind_direction_10m": {
                "label": "Wind Direction at 10m elevation (°)",
                "min": 0, # floor(self.dataset.weather["wind_direction_10m"].min()),
                "max": ceil(self.dataset.weather["wind_direction_10m"].max()),
            },
            "wind_direction_100m": {
                "label": "Wind Direction at 100m elevation (°)",
                "min": 0, # floor(self.dataset.weather["wind_direction_100m"].min()),
                "max": ceil(self.dataset.weather["wind_direction_100m"].max()),
            },
            "wind_gusts_10m": {
                "label": "Wind Gusts at 10m elevation (kph)",
                "min": 0, # floor(self.dataset.weather["wind_gusts_10m"].min()),
                "max": ceil(self.dataset.weather["wind_gusts_10m"].max()),
            },
        }

    @property
    def species_habitat_columns(self) -> Dict[str, List[Any]]:
        return {
            "habitat_type": {
                "label": "Habitat Type",
                "order": list(self.dataset.species["habitat_type"].unique()),
            },
            "habitat_density": {
                "label": "Habitat Density",
                "order": list(self.dataset.species["habitat_density"].unique()),
            },
        }

    @property
    def species_functional_group_columns(self) -> Dict[str, List[Any]]:
        return {
            "trophic_niche": {
                "label": "Trophic Niche",
                "order": list(self.dataset.species["trophic_niche"].unique()),
            },
            "trophic_level": {
                "label": "Trophic Level",
                "order": list(self.dataset.species["trophic_level"].unique()),
            },
            "primary_lifestyle": {
                "label": "Primary Lifestyle",
                "order": list(self.dataset.species["primary_lifestyle"].unique()),
            },
        }

