import bigtree as bt
import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import datetime as dt
import numpy as np

from dash import callback, Output, Input, State, ALL, ctx
from loguru import logger
from typing import Any, Dict, List, Tuple

from api import (
    dispatch,
    FETCH_DATASETS,
    SET_CURRENT_DATASET,
    FETCH_DATASET_SITES_TREE,
    FETCH_DATASET_CONFIG,
    FETCH_ACOUSTIC_FEATURES,
    FETCH_FILES,
)

def path_name(node):
    return f'{node.sep}'.join(node.path_name.strip(node.sep).split(node.sep)[1:])

def ceil(a, precision=0):
    return np.round(a + 0.5 * 10**(-precision), precision)

def floor(a, precision=0):
    return np.round(a - 0.5 * 10**(-precision), precision)

@callback(
    Output("appshell", "navbar"),
    Input("burger", "opened"),
    State("appshell", "navbar"),
)
def navbar_is_open(opened, navbar):
    navbar["collapsed"] = {"desktop": not opened, "mobile": not opened }
    return navbar

@callback(
    Output("dataset-select", "data"),
    Input("load-datasets", "n_intervals"),
)
def fetch_datasets(_):
    trigger_id = ctx.triggered_id
    action = FETCH_DATASETS
    params = {}
    logger.debug(f"{trigger_id=} {action=} {params=}")
    # FIXME to dataset_id and dataset_name
    datasets = dispatch(action, default=[])
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
    Output("feature-dropdown", "value"),
    Output("feature-dropdown", "data"),
    Output("acoustic-feature-range-slider", "min"),
    Output("acoustic-feature-range-slider", "max"),
    Input("dataset-select", "value"),
)
def set_acoustic_feature(
    dataset_name: str
) -> Tuple[str, List[str], float, float]:
    trigger_id = ctx.triggered_id
    action = FETCH_ACOUSTIC_FEATURES
    params = dict(dataset_name=dataset_name)
    logger.debug(f"{trigger_id=} {action=} {params=}")
    acoustic_features = dispatch(action, **params)
    feature_names = acoustic_features["feature"].unique()
    selected_feature = feature_names[0]
    feature_min = floor(acoustic_features.loc[acoustic_features["feature"] == selected_feature, "value"].min(), precision=2)
    feature_max = ceil(acoustic_features.loc[acoustic_features["feature"] == selected_feature, "value"].max(), precision=2)
    return (
        selected_feature,
        feature_names,
        feature_min,
        feature_max,
    )

@callback(
    Output("acoustic-feature-range-slider", "value"),
    Output("acoustic-feature-range-slider", "marks"),
    Output("acoustic-feature-range-slider", "step"),
    Input("acoustic-feature-range-slider", "min"),
    Input("acoustic-feature-range-slider", "max"),
)
def update_acoustic_feature_range_slider(
    feature_min: float,
    feature_max: float,
) -> Tuple[Any, ...]:
    return (
        [feature_min, feature_max],
        slider_marks := {
            f"{floor(value, precision=2)}": f"{floor(value, precision=2)}"
            for value in np.linspace(feature_min, feature_max, 5)
        },
        step := (feature_max - feature_min) / 1e3,
    )

@callback(
    Output("acoustic-feature-range-bounds", "children"),
    Input("acoustic-feature-range-slider", "value"),
)
def update_acoustic_feature_range_bounds(
    value: List[float],
) -> str:
    selected_min, selected_max = value
    return f"{selected_min} - {selected_max}"

@callback(
    Output("date-picker", "minDate"),
    Output("date-picker", "maxDate"),
    Output("date-picker", "value"),
    Input("dataset-select", "value"),
)
def update_date_range(
    dataset_name: str
) -> Tuple[dt.date, dt.date, List[dt.date]]:
    trigger_id = ctx.triggered_id
    action = FETCH_FILES
    params = dict(dataset_name=dataset_name)
    logger.debug(f"{trigger_id=} {action=} {params=}")
    data = dispatch(FETCH_FILES, **params)
    min_date = data.timestamp.dt.date.min()
    max_date = data.timestamp.dt.date.max()
    return min_date, max_date, [min_date, max_date]

@callback(
    Output("site-level-filter-group", "children"),
    Input("dataset-select", "value"),
)
def update_site_level_filters(
    dataset_name: str,
) -> dmc.Accordion:
    trigger_id = ctx.triggered_id
    params = dict(dataset_name=dataset_name)
    logger.debug(f"{trigger_id=} {params=}")
    site_hierarchy_tree = dispatch(FETCH_DATASET_SITES_TREE, **params)
    config = dispatch(FETCH_DATASET_CONFIG, **params)
    children = []
    for depth in range(1, site_hierarchy_tree.max_depth):
        nodes = bt.levelorder_iter(site_hierarchy_tree, filter_condition=lambda x: x.depth == depth + 1)
        nodes = list(sorted(nodes, key=lambda m: m.path_name))
        site_level_name = (
            config
            .get("Site Hierarchy", {})
            .get(f"sitelevel_{depth}", f"Level {depth}/{site_hierarchy_tree.max_depth - 1}")
        )
        child = dmc.AccordionItem(
            value=f"level_{depth}",
            children=[
                dmc.AccordionControl(site_level_name),
                dmc.AccordionPanel(
                    children=dmc.Group(
                        justify="flex-start",
                        children=dmc.ChipGroup(
                            id={ 'type': 'checklist-locations-hierarchy', 'index': depth },
                            multiple=True,
                            persistence=True,
                            value=[node.path_name for node in nodes],
                            children=[
                                dmc.Chip(
                                    path_name(node),
                                    value=node.path_name,
                                    variant='filled',
                                    size='xs'
                                )
                                for node in nodes
                            ],
                        ),
                    ),
                ),
            ],
        )
        children.append(child)
    return dmc.Accordion(
        chevronPosition="right",
        variant="separated",
        radius="sm",
        children=children,
    )

# @callback(
#     Output({"type": "checklist-locations-hierarchy", "index": ALL}, "children"),
#     Output({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
#     Input("dataset-select", "value"),
#     Input({"type": "checklist-locations-hierarchy", "index": ALL}, "children"),
#     Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
# )
# def update_location_hierarchy(
#     dataset_name,
#     current_children,
#     value
# ):  # , all_values, previous_values
#     # TODO:
#     for i in range(len(children) + 1, tree.max_depth):

#         # Get a sorted list of nodes that match selected parents at the depth in question
#         nodes = list(sorted(filter(
#             lambda n: values is None or n.parent.path_name in flatvalues,
#             bt.levelorder_iter(tree, filter_condition=lambda x: x.depth == i + 1)
#         ), key=lambda m: m.path_name))

#         # Create children
#         kids = [
#                    dmc.Chip(
#                        path_name(r),
#                        value=r.path_name,
#                        variant='filled',
#                        size='xs'
#                    ) for r in nodes
#                    # bt.levelorder_iter(tree, filter_condition=lambda x: x.depth == i + 1) if (values is None or r.parent.path_name in flatvalues)
#                ] + []

#         if values is not None:
#             values[i - 1] = [r.path_name for r in nodes]
#             flatvalues = list(itertools.chain(*values))

#         if wrap_in_accordian:
#             config = load_config(dataset)

#             acc = dmc.AccordionItem(
#                 [
#                     dmc.AccordionControl(config.get('Site Hierarchy', f'sitelevel_{i}', fallback=f"Level {i}/{tree.max_depth - 1}")),
#                     dmc.AccordionPanel(children=dmc.ChipGroup(
#                         kids,
#                         value=[r.path_name for r in nodes],
#                         id={
#                             'type': 'checklist-locations-hierarchy',
#                             'index': i
#                         },
#                         multiple=True,
#                         persistence=True,
#                     )),
#                 ],
#                 value=f"level_{i}",
#             )
#             children.append(acc)
#         else:
#             children.append(kids)

#     # print('Children: ', children)

#     if values is not None:
#         return children, values

#     return children
#     try:
#         level = dash.callback_context.triggered_id['index']
#         current_children, value = update_locations(dataset, children=current_children[:level], values=value)
#     except TypeError as e:
#         pass

#         return current_children, value
