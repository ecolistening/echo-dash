import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash import callback, Output, Input, State, ALL, ctx, no_update
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_DATASETS
from utils import floor

@callback(
    Output("appshell", "navbar"),
    Input("burger", "opened"),
    State("appshell", "navbar"),
)
def navbar_is_open(
    opened: bool,
    navbar: Dict[str, str],
) -> Dict[str, str]:
    navbar["collapsed"] = {"desktop": not opened, "mobile": not opened }
    return navbar

@callback(
    Output("dataset-select", "data"),
    Input("load-datasets", "n_intervals"),
)
def fetch_datasets(_) -> List[Dict[str, str]]:
    # FIXME to dataset_id and dataset_name
    datasets = dispatch(FETCH_DATASETS, default=[])
    return [
        dict(label=dataset, value=dataset)
        for dataset in datasets
    ]

@callback(
    Output("dataset-select", "value"),
    Input("dataset-select", "data"),
    prevent_initial_call=True
)
def set_default_dataset(dataset_options: List[str]):
    return dataset_options[0]["value"]

@callback(
    Output("filter-state", "children"),
    Input("date-range-store", "data"),
    Input("acoustic-feature-range-store", "data"),
    Input("umap-filter-store", "data"),
)
def update_active_filters(
    date_range: List[str],
    feature_range: List[float],
    discluded_file_ids: str,
) -> dmc.AccordionItem:
    no_active_filters = (
        (date_range is None or not len(date_range)) and
        (feature_range is None or not len(feature_range)) and
        (discluded_file_ids is None or not len(discluded_file_ids))
    )
    if no_active_filters:
        return "No filters currently active"
    return ""

# @callback(
#     Output("date-range-store", "data"),
#     Input("date-range-filter-chip-group","value")
# )
# def update_date_range(
#     chip_value: List[str],
# ) -> List[str]:
#     import code; code.interact(local=locals())

@callback(
    Output("date-range-filter-chips", "children"),
    Input("date-range-store", "data"),
    prevent_initial_call=True,
)
def update_active_date_filters(
    date_range: List[str],
) -> dmc.AccordionItem:
    if date_range is None or len(date_range) == 0:
        return ""
    date_range = dict(zip(["start_date", "end_date"], date_range))
    return dmc.Accordion(
        id="date-range-filters-accordion",
        chevronPosition="right",
        variant="separated",
        radius="sm",
        value=["dates-filter"],
        children=[
            dmc.AccordionItem(
                value="dates-filter",
                children=[
                    dmc.AccordionControl("Dates"),
                    dmc.AccordionPanel(
                        children=dmc.ChipGroup(
                            id="date-range-filter-chip-group",
                            value=list(date_range.values()),
                            deselectable=True,
                            children=[
                                dmc.Chip(
                                    f"{prefix}={date}",
                                    value=date,
                                    mt="xs",
                                )
                                for prefix, date in date_range.items()
                                if date is not None
                            ]
                        )
                    )
                ]
            )
        ]
    )

@callback(
    Output("acoustic-feature-range-filter-chips", "children"),
    Input("acoustic-feature-range-store", "data"),
    prevent_initial_call=True,
)
def update_active_acoustic_range_filters(
    feature_range: List[float],
) -> dmc.AccordionItem:
    feature_range = dict(zip(["feature_min", "feature_max"], feature_range))
    return dmc.Accordion(
        id="active-acoustic-range-filters-accordion",
        chevronPosition="right",
        variant="separated",
        value=["acoustic-range-filter"],
        radius="sm",
        children=[
            dmc.AccordionItem(
                value="acoustic-range-filter",
                children=[
                    dmc.AccordionControl("Acoustic Feature Range"),
                    dmc.AccordionPanel(
                        style={"padding": "0 0 1rem 0"},
                        children=dmc.ChipGroup(
                            id="acoustic-feature-range-filter-chip-group",
                            value=list(feature_range.values()),
                            deselectable=True,
                            children=[
                                dmc.Chip(
                                    f"{prefix}={floor(value, precision=2)}",
                                    value=value,
                                    mt="xs",
                                )
                                for prefix, value in feature_range.items()
                            ]
                        )
                    )
                ]
            )
        ]
    )

@callback(
    Output("file-filter-chips", "children"),
    Input("umap-filter-store", "data"),
    prevent_initial_call=True,
)
def update_active_file_filters(
    discluded_file_ids: List[str],
) -> dmc.AccordionItem:
    return dmc.Accordion(
        id="active-file-filters-accordion",
        chevronPosition="right",
        variant="separated",
        radius="sm",
        children=[
            dmc.AccordionItem(
                value="files-filter",
                children=[
                    dmc.AccordionControl("Files"),
                    dmc.AccordionPanel(
                        style={"padding": "0 0 1rem 0"},
                        children=dmc.ChipGroup(
                            id="filters-filter-chip-group",
                            value=discluded_file_ids,
                            deselectable=True,
                            children=[
                                dmc.Chip(
                                    file_id,
                                    value=file_id,
                                )
                                for file_id in discluded_file_ids
                            ]
                        )
                    )
                ]
            )
        ]
    )
