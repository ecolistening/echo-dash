import itertools
from datetime import date

import bigtree as bt
import dash
import dash_mantine_components as dmc
import pandas as pd

from dash import html, callback, Output, Input, State, ALL, ctx, no_update
from loguru import logger

from menu.dataset import ds, dataset_input
from utils.data import dataset_loader, load_and_filter_sites, load_config

def path_name(node):
    return f'{node.sep}'.join(node.path_name.strip(node.sep).split(node.sep)[1:])

# Initial load of dataset and tree
df = dataset_loader.get_acoustic_features(ds)
tree = load_and_filter_sites(ds)

if df is None or 'feature' not in df.columns:
    logger.warning("Features not found.")

    feature_list = ["no_feature"]
else:
    feature_list = df.feature.unique()

if df is None or 'timestamp' not in df.columns:
    logger.warning("Timestamps not found.")

    date_min = date(1970,1,1)
    date_max = date.today()
else:
    date_min = df.timestamp.dt.date.min()
    date_max = df.timestamp.dt.date.max()

feature_input = dmc.Select(
        label="Acoustic Descriptor",
        description='Select an acoustic desscriptor',
        id='feature-dropdown',
        data=sorted(feature_list), 
        value=feature_list[0],
        searchable=True,
        dropdownPosition='bottom',
        # style={'min-width': '200px'},
        clearable=False,
        persistence=True)

date_input = dmc.DateRangePicker(
        id="date-picker",
        label="Date Range",
        description="To include in plots",
        minDate=date_min,
        maxDate=date_max,
        value=[date_min, date_max],
        clearable=True,
        # style={"width": 330},
        persistence=True,
    )

if tree is None:
    logger.warning("Tree not found.")
    loc_group = [dmc.Chip("no_name", value="no_path", variant='filled', size='xs')]
    loc_value = ["no_path"]
else:
    loc_group = [dmc.Chip(r.name, value=path_name(r), variant='filled', size='xs') for r in tree.children]
    loc_value = [path_name(r) for r in tree.children]

location_hierarchy = html.Div([
    dmc.Group([
        dmc.Text('Loading...'),
        dmc.ButtonGroup([
            dmc.Button('All', size='xs', compact=True),
            dmc.Button('Clear', size='xs', compact=True),
        ])
    ]),
    dmc.ChipGroup(
        loc_group + [],
        value=loc_value,
        multiple=True,
        persistence=True,
    ),
], id="checklist-locations-div")


filters = dmc.Stack([
    feature_input,
    date_input,
    location_hierarchy,
])

def update_locations(dataset, children=None, values=None):
    '''Update the locations options.

    This function provides either the initial location options or updates it when selections are made.
    Children and values are passed when the options are already instantiated and being updated.
    Children are a list of child objects to keep, so everything below the last passed-in level is replaced.
    '''
    wrap_in_accordian = children is None
    children = children if children is not None else []
    tree = load_and_filter_sites(dataset)

    if tree is None:
        logger.warning("Tree not found.")
        return children

    try:
        flatvalues = list(itertools.chain(*values))
    except TypeError:
        pass

    for i in range(len(children) + 1, tree.max_depth):

        # Get a sorted list of nodes that match selected parents at the depth in question
        nodes = list(sorted(filter(
            lambda n: values is None or n.parent.path_name in flatvalues,
            bt.levelorder_iter(tree, filter_condition=lambda x: x.depth == i + 1)
        ), key=lambda m: m.path_name))

        # Create children
        kids = [
                   dmc.Chip(
                       path_name(r),
                       value=r.path_name,
                       variant='filled',
                       size='xs'
                   ) for r in nodes
                   # bt.levelorder_iter(tree, filter_condition=lambda x: x.depth == i + 1) if (values is None or r.parent.path_name in flatvalues)
               ] + []

        if values is not None:
            values[i - 1] = [r.path_name for r in nodes]
            flatvalues = list(itertools.chain(*values))

        if wrap_in_accordian:
            config = load_config(dataset)

            acc = dmc.AccordionItem(
                [
                    dmc.AccordionControl(config.get('Site Hierarchy', f'sitelevel_{i}', fallback=f"Level {i}/{tree.max_depth - 1}")),
                    dmc.AccordionPanel(children=dmc.ChipGroup(
                        kids,
                        value=[r.path_name for r in nodes],
                        id={
                            'type': 'checklist-locations-hierarchy',
                            'index': i
                        },
                        multiple=True,
                        persistence=True,
                    )),
                ],
                value=f"level_{i}",
            )
            children.append(acc)
        else:
            children.append(kids)

    # print('Children: ', children)

    if values is not None:
        return children, values

    return children


@callback(
    Output(date_input, component_property='minDate'),
    Output(date_input, component_property='maxDate'),
    Output(date_input, component_property='value'),
    Output(feature_input, component_property='data'),
    Output(feature_input, component_property='value'),
    Output(location_hierarchy, component_property='children'),
    Input(dataset_input, component_property='value'),
    Input(date_input, component_property='value'),
    State(feature_input, component_property='value'),
)
def update_menu(dataset, date_value, feature_value):
    logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset=} {date_value=} {feature_value=}")

    date_value = [date.fromisoformat(v) for v in date_value]

    data = dataset_loader.get_acoustic_features(dataset)

    if data is None:
        logger.warning("data not found.")
        feature_value = "no_feature"
        feature_data = ["no_feature"]

        min_date = date(1970,1,1)
        max_date = date.today()
    else:
        feature_data = sorted(data.feature.unique())
        if feature_value not in feature_data:
            feature_value = feature_data[0]
        else:
            feature_value = no_update

        data = data.assign(date=data.timestamp.dt.date)
        min_date = data.timestamp.dt.date.min()
        max_date = data.timestamp.dt.date.max()

    # Reset date selection for new datasets
    if ctx.triggered_id is None or ctx.triggered_id == 'dataset-select':
        date_value[0] = min_date
        date_value[1] = max_date
        locations = html.Div(dmc.Accordion(children=update_locations(dataset)), id="checklist-locations-div")

    elif ctx.triggered_id == 'date-picker':
        if date_value[0] < min_date or date_value[0] > max_date:
            date_value[0] = min_date

        if date_value[1] < min_date or date_value[1] > max_date:
            date_value[1] = max_date
        
        locations = no_update

    return  min_date, max_date, date_value, \
            feature_data, feature_value, \
            locations


@callback(
    Output({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'children'),
    Output({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'value'),
    Input(dataset_input, component_property='value'),
    Input({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'children'),
    Input({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'value'),
)
def update_location_hierarchy(dataset, current_children, value):  # , all_values, previous_values):
    try:
        level = dash.callback_context.triggered_id['index']
        current_children, value = update_locations(dataset, children=current_children[:level], values=value)
    except TypeError as e:
        pass

    return current_children, value
