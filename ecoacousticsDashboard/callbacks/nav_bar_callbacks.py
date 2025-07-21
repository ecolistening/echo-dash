import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt

from dash import callback, ctx, no_update
from dash import Output, Input, State
from dash import ALL, MATCH
from dash_iconify import DashIconify
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
    Output("dataset-select", "value"),
    Output("dataset-select", "data"),
    State("dataset-select", "value"),
    Input("load-datasets", "n_intervals"),
)
def fetch_datasets(current_dataset, _) -> List[Dict[str, str]]:
    # FIXME switch to dataset_id and dataset_name
    datasets = dispatch(FETCH_DATASETS, default=[])
    dataset_options = [
        dict(label=dataset, value=dataset)
        for dataset in datasets
    ]
    if current_dataset is None or not len(current_dataset):
        current_dataset = dataset_options[0]["value"]
    return current_dataset, dataset_options

@callback(
    Output("filter-state", "children"),
    Input("date-range-store", "data"),
    Input("acoustic-feature-store", "data"),
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
    date_store: List[str],
) -> dmc.Accordion:
    if not len(date_store):
        return []
    date_range = [
        f"{key}={date_store[key]}"
        for key in ["start_date", "end_date"]
    ]
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
                    dmc.AccordionControl("Date Range"),
                    dmc.AccordionPanel(
                        pb="1rem",
                        children=dmc.ChipGroup(
                            id={"type": "active-filter-chip-group", "index": "date-range"},
                            value=date_range,
                            multiple=True,
                            children=[
                                dmc.Chip(
                                    variant="outline",
                                    icon=DashIconify(icon="bi-x-circle"),
                                    value=value,
                                    mt="xs",
                                    children=value,
                                )
                                for value in date_range
                            ]
                        )
                    )
                ]
            )
        ]
    )

@callback(
    Output("date-range-store", "data", allow_duplicate=True),
    Output("date-picker", "value", allow_duplicate=True),
    State("date-range-store", "data"),
    Input({"type": "active-filter-chip-group", "index": "date-range"}, "value"),
    prevent_initial_call=True,
)
def reset_date_range_selection(
    current_date_store: Dict[str, dt.date],
    values: List[str],
) -> Dict[str, dt.date]:
    selected_dates = {}
    for value in values:
        prefix, date_str = value.split("=")
        selected_dates[prefix] = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
    current_date_store["start_date"] = selected_dates.get("start_date", dt.datetime.strptime(current_date_store["min"], "%Y-%m-%d").date())
    current_date_store["end_date"] = selected_dates.get("end_date", dt.datetime.strptime(current_date_store["max"], "%Y-%m-%d").date())
    return current_date_store, [current_date_store["start_date"], current_date_store["end_date"]]

@callback(
    Output("acoustic-feature-range-filter-chips", "children"),
    Input("acoustic-feature-store", "data"),
    prevent_initial_call=True,
)
def update_active_acoustic_range_filters(
    store: List[float],
) -> dmc.Accordion:
    feature_range = [
        f"{key}={floor(store[key], precision=2)}"
        for key in ["feature_min", "feature_max"]
    ]
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
                        pb="1rem",
                        children=[
                            dmc.Text(
                                children=store["feature"],
                                size="sm",
                            ),
                            dmc.Space(h="sm"),
                            dmc.ChipGroup(
                                id={"type": "active-filter-chip-group", "index": "acoustic-feature"},
                                value=feature_range,
                                multiple=True,
                                children=[
                                    dmc.Chip(
                                        variant="outline",
                                        icon=DashIconify(icon="bi-x-circle"),
                                        value=value,
                                        mt="xs",
                                        children=value,
                                    )
                                    for value in feature_range
                                ]
                            ),
                        ]
                    )
                ]
            )
        ]
    )

@callback(
    Output("acoustic-feature-store", "data", allow_duplicate=True),
    Output("acoustic-feature-range-slider", "value", allow_duplicate=True),
    State("acoustic-feature-store", "data"),
    Input({"type": "active-filter-chip-group", "index": "acoustic-feature"}, "value"),
    prevent_initial_call=True,
)
def reset_acoustic_feature_range_selection(
    store: Dict[str, Any],
    values: List[str],
) -> Dict[str, Any]:
    selected_values = {}
    for value in values:
        prefix, feature_value = value.split("=")
        selected_values[prefix] = float(feature_value)
    store["feature_min"] = selected_values.get("feature_min", store["min"])
    store["feature_max"] = selected_values.get("feature_max", store["max"])
    return store, [store["feature_min"], store["feature_max"]]

@callback(
    Output("file-filter-chips", "children"),
    Input("umap-filter-store", "data"),
    prevent_initial_call=True,
)
def update_active_file_filters(
    file_filter_groups: Dict[int, List[str]],
) -> dmc.Accordion:
    if not len(file_filter_groups):
        return []

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
                        pb="1rem",
                        children=dmc.ChipGroup(
                            id={"type": "active-filter-chip-group", "index": "file"},
                            value=list(file_filter_groups.keys()),
                            multiple=True,
                            children=[
                                dmc.Chip(
                                    variant="outline",
                                    icon=DashIconify(icon="bi-x-circle"),
                                    value=selection_id,
                                    mt="xs",
                                    children=f"UMAP Selection {selection_id}",
                                )
                                for selection_id in file_filter_groups.keys()
                            ]
                        )
                    )
                ]
            )
        ]
    )

@callback(
    Output("umap-filter-store", "data"),
    State("umap-filter-store", "data"),
    Input({"type": "active-filter-chip-group", "index": "file"}, "value"),
    prevent_initial_call=True,
)
def remove_umap_selection(
    file_filter_groups: Dict[str, List[str]],
    values: bool,
) -> Dict[str, List[str]]:
    return { value: file_filter_groups[value] for value in values }
