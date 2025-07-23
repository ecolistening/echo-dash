from __future__ import annotations

import attrs

from loguru import logger
from typing import Any, Dict, Tuple, List

from datasets.dataset import Dataset

@attrs.define
class DatasetDecorator:
    dataset: Dataset

    def category_orders(self):
        category_orders = {}
        for group in [self.site_level_columns, self.solar_columns, self.temporal_columns, self.spatial_columns]:
            for column, params in group.items():
                category_orders[column] = params["order"]
        return category_orders

    def categorical_drop_down_select_options(self):
        return [
            opt_group
            for opt_group in self.drop_down_select_options()
            if opt_group["type"] in ("categorical")
        ]

    # TODO: refactor so the dropdown is parametrised at the component level
    def drop_down_select_options(self) -> Tuple[Dict[str, Any]]:
        opt_groups = []
        column_groups = zip(
            ["Site Level", "Time of Day", "Temporal", "Spatial"],
            [self.site_level_columns, self.solar_columns, self.temporal_columns, self.spatial_columns]
        )
        for group_name, column_group in column_groups:
            opt_groups.append({
                "group": group_name,
                "type": "categorical",
                "items": [
                    { "value": value, "label": params["label"] }
                    for value, params in column_group.items()
                ],
            })
        return opt_groups

    def spatial_drop_down_select_options(self) -> Tuple[Dict[str, Any]]:
        opt_groups = []
        column_groups = zip(
            ["Spatial"],
            [self.spatial_columns]
        )
        for group_name, column_group in column_groups:
            opt_groups.append({
                "group": group_name,
                "type": "categorical",
                "items": [
                    { "value": value, "label": params["label"] }
                    for value, params in column_group.items()
                ],
            })
        return opt_groups

    @property
    def site_level_columns(self) -> Dict[str, List[Any]]:
        return {
            column: {
                "order": self.dataset.locations[column].unique(),
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
                "order": self.dataset.locations["location"].unique(),
                "label": "Location"
            },
            "site": {
                "order": self.dataset.locations["site"].unique(),
                "label": "Site"
            },
            "recorder": {
                "order": self.dataset.locations["recorder"].unique(),
                "label": "Recorder"
            },
        }
