"""
This app creates a simple sidebar layout using inline style arguments and the
dbc.Nav component.

dcc.Location is used to track the current location, and a callback uses the
current location to render the appropriate page content. The active prop of
each NavLink is set automatically according to the current pathname. To use
this feature you must install dash-bootstrap-components >= 0.11.0.

For more details on building multi-page Dash applications, check out the Dash
documentation: https://dash.plot.ly/urls
"""
import itertools
from datetime import date, datetime, timedelta

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import pandas as pd
from dash import Dash, callback, html, Output, Input, dcc, ALL, Patch, MATCH, ALLSMALLER, State
from dash_iconify import DashIconify
import bigtree as bt

from config import filepath, root_dir
from utils import load_and_filter_dataset, load_and_filter_sites

app = Dash(__name__, use_pages=True, external_stylesheets=[
    dbc.themes.LITERA, dbc.icons.BOOTSTRAP,
   "https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;900&display=swap"
])

header = dmc.Header(
    height=60,
    children=dmc.Center(dmc.Title("Eyeballing Ecoacoustics", order=1))
)

datasets = [d.name for d in root_dir.glob("*") if d.is_dir()]
ds = datasets[1]

dataset_input = dmc.Select(
    id='dataset-select',
    label='Dataset',
    description='Select a dataset to explore',
    data=datasets,
    searchable=True,
    nothingFound="No options found",
    clearable=False,
    value=ds,
    # style={"width": 200},
    persistence=True,
)

#TODO This is redundant with the filepath selection based on the menu. Remove.
# df = pd.read_parquet(f, columns=['file','timestamp','recorder','feature','value']).drop_duplicates()
# df = pd.read_parquet(filepath, columns=['timestamp', 'location', 'recorder', 'feature']).drop_duplicates()
# df = df.assign(date=df.timestamp.dt.date)#, habitat_code=df['habitat code'])

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

# location_top = html.Div([
#     dmc.Group([
#         dmc.Text("Locations"),
#         dmc.ButtonGroup([
#             dmc.Button('All', size='xs', compact=True),
#             dmc.Button('Clear', size='xs', compact=True),
#         ])
#     ]),
#     locations := dmc.ChipGroup(
#         [
#             dmc.Chip(r, value=r, variant='filled', size='xs') for r in sorted(df.location.unique())
#         ] + [],
#         value=[str(l) for l in df.location.unique()],
#         id="checklist-locations-top",
#         multiple=True,
#         persistence=True,
#     ),
# ])

# location_input = html.Div([
#     dmc.Group([
#         dmc.Text("Recorders"),
#         dmc.ButtonGroup([
#             dmc.Button('All', size='xs', compact=True),
#             dmc.Button('Clear', size='xs', compact=True),
#             dmc.Button('Per Site', size='xs', compact=True, variant='outline')
#         ])
#     ]),
#     recorders := dmc.ChipGroup(
#         [
#             dmc.Chip(str(r), value=str(r), variant='filled', size='xs', persistence=True) for r in sorted(df.recorder.unique())
#         ],
#         value=[str(l) for l in df.recorder.unique()],
#         id="checklist-locations",
#         multiple=True
#     ),
# ])

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
    # location_top,
    # location_input
])#, type='hover', offsetScrollbars=True, h='250')

def menu_from_page_registry():
    pages = {m: m.split('.')[1:] for m in dash.page_registry}
    children = {}

    for p in pages:
        page = dash.page_registry[p]

        if len(pages[p]) == 1:
            children[pages[p][0]] = dmc.NavLink(label=page['name'], href=page["relative_path"])
        else:
            if pages[p][0] not in children:
                children[pages[p][0]] = dmc.NavLink(label=pages[p][0], children=[])
            children[pages[p][0]].children.append(
                dmc.NavLink(label=page['name'], href=page["relative_path"])
            )

    return list(children.values())

navbar = dmc.Navbar(
    p="md",
    width={"base": 300},
    children=dmc.ScrollArea(
        dmc.Stack(children=[
            dmc.Title("Eyeballing Soundscapes", order=3),
        ] + menu_from_page_registry() + [
            dmc.Divider(),
            dmc.Title("Data", order=3),
            dataset_input,
            dmc.Title("Filters", order=3),
            filters,
            dataset_name := dcc.Store(id='dataset_name')
        ])
    )
)

app.layout = dmc.MantineProvider(
    theme={
        "fontFamily": "'Inter', sans-serif",
        "primaryColor": "indigo",
        "components": {
            "Button": {"styles": {"root": {"fontWeight": 400}}},
            "Alert": {"styles": {"title": {"fontWeight": 500}}},
            "AvatarGroup": {"styles": {"truncated": {"fontWeight": 500}}},
        },
    },
    inherit=True,
    withGlobalStyles=True,
    withNormalizeCSS=True,
    children=dmc.AppShell(children=dash.page_container, navbar=navbar),#, header=header),
)

def path_name(node):
    return f'{node.sep}'.join(node.path_name.strip(node.sep).split(node.sep)[1:])


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

    for i in range(len(children)+1, tree.max_depth):

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
                ) for r in nodes #bt.levelorder_iter(tree, filter_condition=lambda x: x.depth == i + 1) if (values is None or r.parent.path_name in flatvalues)
            ] + []

        if values is not None:
            values[i-1] = [r.path_name for r in nodes]
            flatvalues = list(itertools.chain(*values))

        if wrap_in_accordian:
            acc = dmc.AccordionItem(
                [
                    dmc.AccordionControl(f"Level {i}/{tree.max_depth - 1}"),
                    dmc.AccordionPanel(children=dmc.ChipGroup(
                        kids,
                        value=[r.path_name for r in nodes
                               # bt.levelorder_iter(tree, filter_condition=lambda x: x.depth == i + 1)
                        ],
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
    # Output(locations, component_property='children'),
    # Output(locations, component_property='value'),
    # Output(recorders, component_property='children'),
    # Output(recorders, component_property='value'),
    Input(dataset_input, component_property='value'),
    Input(date_input, component_property='value'),
)
def update_menu(dataset, value):
    value = [date.fromisoformat(v) for v in value]

    df = pd.read_parquet(root_dir / dataset / 'indices.parquet', columns=['timestamp', 'location', 'recorder']).drop_duplicates()
    df = df.assign(date=df.timestamp.dt.date)
    minDate = df.timestamp.dt.date.min()
    maxDate = df.timestamp.dt.date.max()

    if value[0] < minDate or value[0] > maxDate:
        value[0] = minDate

    if value[1] < minDate or value[1] > maxDate:
        value[1] = maxDate

    # print(tree.max_depth)
    # bt.print_tree(tree, all_attrs=True)
    location_hierarchy = html.Div(dmc.Accordion(children=update_locations(dataset)), id="checklist-locations-div")

    location_values = sorted(df.location.unique())
    location_options = [dmc.Chip(r, value=r, variant='filled', size='xs') for r in location_values]

    recorder_values = sorted(df.recorder.unique())
    recorder_options = [dmc.Chip(r, value=r, variant='filled', size='xs') for r in recorder_values]

    # patched_children = Patch()
    # print(values)

    return (minDate, maxDate, value,
            location_hierarchy)
            # ,
            # location_options, location_values, recorder_options, recorder_values) #, patched_children)

# @callback(
#     Output(dataset_name, component_property='data'),
#     Input(dataset_input, component_property='value'),
# )
# def update_dataset(dataset):
#     return dataset


@callback(
    Output({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'children'),
    Output({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'value'),
    Input(dataset_input, component_property='value'),
    Input({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'children'),
    Input({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'value'),
)
def display_output(dataset, current_children, value):#, all_values, previous_values):
    # print(value)
    # print(current_children)
    #
    # # print(children)
    # print('Prop IDs: ', dash.callback_context.triggered_prop_ids)
    # try:
    #     print('Trig IDs: ', dash.callback_context.triggered_id['index'])
    # except TypeError as e:
    #     pass
    # print('Args Grouping: ', dash.callback_context.args_grouping[0])

    try:
        level = dash.callback_context.triggered_id['index']
        # print(f'Current Children Level {level}: ', current_children[:level])
        current_children, value = update_locations(dataset, children=current_children[:level], values=value)
    except TypeError as e:
        pass

    return current_children, value

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)
    app.enable_dev_tools(dev_tools_ui=True, dev_tools_serve_dev_bundles=True)
