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
from datetime import date, datetime, timedelta

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import pandas as pd
from dash import Dash, callback, html, Output, Input, dcc

from config import filepath, root_dir

app = Dash(__name__, use_pages=True, external_stylesheets=[
    dbc.themes.LITERA, dbc.icons.BOOTSTRAP,
   "https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;900&display=swap"
])

#TODO This is redundant with the filepath selection based on the menu. Remove.
# df = pd.read_parquet(f, columns=['file','timestamp','recorder','feature','value']).drop_duplicates()
df = pd.read_parquet(filepath, columns=['timestamp', 'location', 'recorder', 'feature']).drop_duplicates()
df = df.assign(date=df.timestamp.dt.date)#, habitat_code=df['habitat code'])

header = dmc.Header(
    height=60,
    children=dmc.Center(dmc.Title("Eyeballing Ecoacoustics", order=1))
)

datasets = [d.name for d in root_dir.glob("*") if d.is_dir()]
dataset_input = dmc.Select(
    id='dataset-select',
    label='Dataset',
    description='Select a dataset to explore',
    data=datasets,
    searchable=True,
    nothingFound="No options found",
    clearable=False,
    value=datasets[0],
    # style={"width": 200},
    persistence=True,
)

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
        dmc.Text("Locations"),
        dmc.ButtonGroup([
            dmc.Button('All', size='xs', compact=True),
            dmc.Button('Clear', size='xs', compact=True),
        ])
    ]),
    locations := dmc.ChipGroup(
        [
            dmc.Chip(r, value=r, variant='filled', size='xs') for r in sorted(df.location.unique())
        ] + [],
        value=[str(l) for l in df.location.unique()],
        id="checklist-locations-hierarchy",
        multiple=True,
        persistence=True,
    ),
])

location_input = html.Div([
    dmc.Group([
        dmc.Text("Recorders"),
        dmc.ButtonGroup([
            dmc.Button('All', size='xs', compact=True),
            dmc.Button('Clear', size='xs', compact=True),
            dmc.Button('Per Site', size='xs', compact=True, variant='outline')
        ])
    ]),
    recorders := dmc.ChipGroup(
        [
            dmc.Chip(str(r), value=str(r), variant='filled', size='xs', persistence=True) for r in sorted(df.recorder.unique())
        ],
        value=[str(l) for l in df.recorder.unique()],
        id="checklist-locations",
        multiple=True
    ),
])

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
    location_input
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
    children=dmc.Stack(children=[
        dmc.Title("Eyeballing Soundscapes", order=3),
    ] + menu_from_page_registry() + [
        dmc.Divider(),
        dmc.Title("Data", order=3),
        dataset_input,
        dmc.Title("Filters", order=3),
        filters,
        dataset_name := dcc.Store(id='dataset_name')
    ]),
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

@callback(
    Output(date_input, component_property='minDate'),
    Output(date_input, component_property='maxDate'),
    Output(date_input, component_property='value'),
    Output(locations, component_property='children'),
    Output(locations, component_property='value'),
    Output(recorders, component_property='children'),
    Output(recorders, component_property='value'),
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

    location_values = sorted(df.location.unique())
    location_options = [dmc.Chip(r, value=r, variant='filled', size='xs') for r in location_values]

    recorder_values = sorted(df.recorder.unique())
    recorder_options = [dmc.Chip(r, value=r, variant='filled', size='xs') for r in recorder_values]

    return (minDate, maxDate, value, location_options, location_values, recorder_options, recorder_values)

@callback(
    Output(dataset_name, component_property='data'),
    Input(dataset_input, component_property='value'),
)
def update_dataset(dataset):
    return dataset

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)
    app.enable_dev_tools(dev_tools_ui=True, dev_tools_serve_dev_bundles=True)
