from __future__ import annotations

import attrs

from loguru import logger
from typing import Any, Dict, Tuple, List

from datasets.dataset import Dataset

@attrs.define
class DatasetDecorator:
    dataset: Dataset

    def drop_down_select_options(self) -> Tuple[Dict[str, Any]]:
        logger.debug(f"Get options for dataset_name={self.dataset.dataset_name}")
        options = []
        # Add site hierarchies
        for level in self.site_levels:
            values = self.dataset.locations[level].unique()
            options += [{'value': level, 'label': self.dataset.config.get('Site Hierarchy', level, fallback=level), 'group': 'Site Level', 'type': 'categorical', 'order': tuple(sorted(values))}]
        # Add time of the day
        options += [{'value': 'dddn', 'label': 'Dawn/Day/Dusk/Night', 'group': 'Time of Day', 'type': 'categorical', 'order': ('dawn','day','dusk','night')}]
        # HACK -> will be fixed when solar data is present
        if len(self.dataset.dates):
            options += [{'value': f'hours after {c}', 'label': f'Hours after {c.capitalize()}', 'group': 'Time of Day', 'type': 'continuous'} for c in ('dawn', 'sunrise', 'noon', 'sunset', 'dusk')]
        # Add temporal columns with facet order
        options += [{'value': col, 'label': col.capitalize(), 'group': 'Temporal', 'type': 'categorical', 'order': order} for col, order in self.temporal_columns_with_order]
        # Add spatial columns with facet order
        options += [{'value': col, 'label': col.capitalize(), 'group': 'Spatial', 'type': 'categorical', 'order': tuple(sorted(self.dataset.locations[col].unique()))} for col in self.spatial_columns]
        # deprecated since they are already covered or offer no visualisation value
        #index = ['file', 'timestamp']
        #options += [{'value': i, 'label': i.capitalize(), 'group': 'Other Metadata', 'type': 'categorical', 'order': tuple(sorted(data[i].unique()))} for i in index]
        return tuple(options)

    def categorical_drop_down_select_options(self):
        return [opt for opt in self.drop_down_select_options() if opt['type'] in ('categorical')]

    @property
    def site_level_names(self) -> List[str]:
        return [self.dataset.config.get('Site Hierarchy', level, fallback=level) for level in self.site_levels]

    @property
    def site_levels(self) -> List[str]:
        return [col for col in self.dataset.locations.columns if col.startswith('sitelevel_')]

    @property
    def site_level_values(self) -> List[str]:
        columns = []
        for level in self.site_levels:
            columns.extend(self.dataset.locations[level].unique())
        return columns

    @property
    def temporal_columns(self) -> List[Tuple[str, List[Any]]]:
        return [key for key, _ in self.temporal_columns_with_order]

    @property
    def temporal_columns_with_order(self) -> List[Tuple[str, List[Any]]]:
        return (
            ('hour', list(range(24))),
            ('weekday', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']),
            # ('date', sorted(self.dataset.files['date'].unique())),
            ('month', ['January','February','March','April','May','June','July','August','September','October','November','December']),
            ('year', sorted(self.dataset.files['year'].unique())),
        )

    @property
    def spatial_columns(self) -> List[str]:
        return ['location', 'site', 'recorder']

    def category_orders(self):
        categorical_orders = {}
        for opt in self.drop_down_select_options():
            name = opt['value']
            order = opt.get('order',None)
            if order is None:
                logger.debug(f"Option {name}: No order provided")
            else:
                logger.debug(f"Option {name}: {order}")
                categorical_orders[name] = order
        return categorical_orders


