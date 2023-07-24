import itertools
from datetime import date

import bigtree as bt
import dash
import dash_mantine_components as dmc
import pandas as pd
from dash import html, callback, Output, Input, ALL

from app import path_name
from config import root_dir
from menu.dataset import ds, dataset_input
from utils import load_and_filter_dataset, load_and_filter_sites

# Initial load of dataset and tree
df = load_and_filter_dataset(ds)
tree = load_and_filter_sites(ds)

date_input = dmc.DateRangePicker(
        id="date-picker",
        label="Date Range",
        description="To include in plots",
        minDate=df.timestamp.dt.date.min(),
        maxDate=df.timestamp.dt.date.max(),
        value=[df.timestamp.dt.date.min(), df.timestamp.dt.date.max()],
        clearable=True,
        # style={"width": 330},
        persistence=True,
    )

location_hierarchy = html.Div([
    dmc.Group([
        dmc.Text(f"Sites (Lvl {1}/{tree.depth})"),
        dmc.ButtonGroup([
            dmc.Button('All', size='xs', compact=True),
            dmc.Button('Clear', size='xs', compact=True),
        ])
    ]),
    dmc.ChipGroup(
        #TODO Add a + button chip for those who can expand.
        [
            dmc.Chip(r.name, value=r.path_name, variant='filled', size='xs') for r in tree.children
        ] + [],
        value=[r.path_name for r in tree.children],
        # id={
        #     'type': 'checklist-locations-hierarchy',
        #     'index': 0
        # },
        multiple=True,
        persistence=True,
    ),
], id="checklist-locations-div")

feature_input = html.Div([
    dmc.Select(
        label="Acoustic Index",
        description='Select an acoustic index',
        id='feature-dropdown',
        data=sorted(df.feature.unique()), value=df.feature.unique()[0],
        searchable=True,
        dropdownPosition='bottom',
        # style={'min-width': '200px'},
        clearable=False,
        persistence=True),
])

filters = dmc.Stack([
    date_input,
    feature_input,
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

    try:
        flatvalues = list(itertools.chain(*values))
    except TypeError:
        pass

    for i in range(len(children) + 1, tree.max_depth):

        # Get a sorted list of nodes that match selected parents at the depth in question
        nodes = list(sorted(filter(
            lambda n: values is None or n.parent.path_name in flatvalues,
            bt.levelorder_iter(tree, filter_condition=lambda x: x.depth == i + 1)
        ), key=lambda n: n.path_name))

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
            acc = dmc.AccordionItem(
                [
                    dmc.AccordionControl(f"Level {i}/{tree.max_depth - 1}"),
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
    Output(location_hierarchy, component_property='children'),
    Input(dataset_input, component_property='value'),
    Input(date_input, component_property='value'),
)
def update_menu(dataset, value):
    value = [date.fromisoformat(v) for v in value]

    data = pd.read_parquet(root_dir / dataset / 'indices.parquet',
                           columns=['timestamp', 'location', 'recorder']).drop_duplicates()
    data = data.assign(date=data.timestamp.dt.date)
    min_date = data.timestamp.dt.date.min()
    max_date = data.timestamp.dt.date.max()

    if value[0] < min_date or value[0] > max_date:
        value[0] = min_date

    if value[1] < min_date or value[1] > max_date:
        value[1] = max_date

    locations = html.Div(dmc.Accordion(children=update_locations(dataset)), id="checklist-locations-div")

    return min_date, max_date, value, locations


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
