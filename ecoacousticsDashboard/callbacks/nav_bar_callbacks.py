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

from api import dispatch, FETCH_DATASETS, FETCH_FILES, FETCH_ACOUSTIC_FEATURES
from constants import AcousticFeatureStore, DateStore
from utils import ceil, floor

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
    Output("acoustic-feature-store", "data"),
    Output("acoustic-feature-current-bounds", "data"),
    Input("dataset-select", "value"),
)
def set_acoustic_feature_store(
    dataset_name: str,
) -> Tuple[AcousticFeatureStore, List[Any]]:
    data = dispatch(FETCH_ACOUSTIC_FEATURES, dataset_name=dataset_name)
    features = data["feature"].unique()
    store = {}
    for feature in features:
        df = data.loc[data["feature"] == feature, "value"]
        store[feature] = {
            "min": floor(df.min(), precision=2),
            "max": ceil(df.max(), precision=2),
        }
    current_feature = features[0]
    state = {
        "feature": current_feature,
        "start_value": store[current_feature]["min"],
        "end_value": store[current_feature]["max"]
    }
    return store, state

@callback(
    Output("date-range-store", "data"),
    Output("date-range-current-bounds", "data"),
    Input("dataset-select", "value"),
)
def set_date_store(
    dataset_name: str
) -> Tuple[DateStore, List[dt.date]]:
    data = dispatch(FETCH_FILES, dataset_name=dataset_name)
    min_date = data.timestamp.dt.date.min()
    max_date = data.timestamp.dt.date.max()
    store = {"min": min_date, "max": max_date}
    return store, [store["min"], store["max"]]

@callback(
    Output("filter-state", "children"),
    Input("date-range-current-bounds", "data"),
    Input("acoustic-feature-current-bounds", "data"),
    Input("umap-filter-store", "data"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
)
def update_active_filters(
    date_range: List[str],
    feature_range: List[float],
    discluded_file_ids: str,
    locations: List[str],
) -> dmc.AccordionItem:
    no_active_filters = (
        (date_range is None or not len(date_range)) and
        (feature_range is None or not len(feature_range)) and
        (discluded_file_ids is None or not len(discluded_file_ids)) and
        (locations is None or not len(locations))
    )
    if no_active_filters:
        return "No filters currently active"
    return ""

@callback(
    Output("site-filter-chips", "children"),
    State("dataset-config", "data"),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def update_active_site_filters(
    config: Dict[str, str],
    locations: List[str],
) -> dmc.Accordion:
    if not len(config):
        return []
    sites = [
        f"{config.get('Site Hierarchy', {}).get(f'sitelevel_{i+1}', f'sitelevel_{i+1}')}={value}"
        for i, group in enumerate(locations)
        for value in group
    ]
    return dmc.Accordion(
        id="site-filters-accordion",
        chevronPosition="right",
        variant="separated",
        radius="sm",
        value=["site-filter"],
        children=[
            dmc.AccordionItem(
                value="sites-filter",
                children=[
                    dmc.AccordionControl("Site Level"),
                    dmc.AccordionPanel(
                        pb="1rem",
                        children=dmc.ChipGroup(
                            id={"type": "active-filter-chip-group", "index": "site-level"},
                            value=sites,
                            multiple=True,
                            children=[
                                dmc.Chip(
                                    variant="outline",
                                    icon=DashIconify(icon="bi-x-circle"),
                                    value=value,
                                    mt="xs",
                                    children=value,
                                )
                                for value in sites
                            ]
                        )
                    )
                ]
            )
        ]
    )


@callback(
    Output("date-range-filter-chips", "children"),
    Input("date-range-current-bounds", "data"),
    prevent_initial_call=True,
)
def update_active_date_filters(
    selected_dates: List[str],
) -> dmc.Accordion:
    if not len(selected_dates):
        return []
    date_range = [
        f"{key}={selected_dates[i]}"
        for i, key in enumerate(["start_date", "end_date"])
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
    Output("acoustic-feature-range-filter-chips", "children"),
    Input("acoustic-feature-current-bounds", "data"),
    prevent_initial_call=True,
)
def update_active_acoustic_range_filters(
    state: Dict[str, Any],
) -> dmc.Accordion:
    feature_range = [
        f"{key}={floor(state[key], precision=2)}"
        for key in ["start_value", "end_value"]
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
                                children=state["feature"],
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

@callback(
    Output("date-range-current-bounds", "data", allow_duplicate=True),
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
    return [
        selected_dates.get("start_date", dt.datetime.strptime(current_date_store["min"], "%Y-%m-%d").date()),
        selected_dates.get("end_date", dt.datetime.strptime(current_date_store["max"], "%Y-%m-%d").date()),
    ]

@callback(
    Output("acoustic-feature-current-bounds", "data", allow_duplicate=True),
    State("acoustic-feature-store", "data"),
    State("acoustic-feature-current-bounds", "data"),
    Input({"type": "active-filter-chip-group", "index": "acoustic-feature"}, "value"),
    prevent_initial_call=True,
)
def reset_acoustic_feature_range_selection(
    store: Dict[str, Any],
    state: Dict[str, Any],
    values: List[str],
) -> Dict[str, Any]:
    selected_values = {}
    for value in values:
        prefix, value = value.split("=")
        selected_values[prefix] = float(value)
    feature = state["feature"]
    return {
        "feature": feature,
        "start_value": selected_values.get("start_value", store[feature]["min"]),
        "end_value": selected_values.get("end_value", store[feature]["max"]),
    }
