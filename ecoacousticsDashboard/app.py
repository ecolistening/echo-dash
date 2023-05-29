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
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, dcc, html
import pandas as pd

from utils import is_docker

app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.LITERA])


# Incorporate data
f = Path('/data/features.23D17.dashboard_subset_mini.parquet')
if not is_docker():
    f = Path('/Users/ca492/Documents/sussex/projects/ecoacoustics-dashboard/features.23D17.dashboard_subset_mini.parquet')

# df = pd.read_parquet(f, columns=['file','timestamp','recorder','feature','value']).drop_duplicates()
df = pd.read_parquet(f, columns=['file_timestamp','recorder']).drop_duplicates()
df = df.assign(date=df.file_timestamp.dt.date)

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavLink(page['name'], href=page["relative_path"], active="exact")
        for page in dash.page_registry.values()
    ],
    brand="Eyeballing Ecoacoustics",
    brand_href="#",
    color="primary",
    dark=True,
)

date_input = html.Div([
    dbc.Label("Dates", html_for="date-picker"),
    dcc.DatePickerRange(id='date-picker'),
], className="mb-3")

location_input = html.Div([
    dbc.Label("Locations", html_for=""),
    dbc.Checklist(
        options=[
            {"label": r, "value": r} for r in df.recorder.unique()
        ],
        value=[r for r in df.recorder.unique()],
        id="checklist-locations",
        inline=True,
        persistence=True
    ),
])

filters = dbc.Form([
    html.H3("Filters"),
    date_input,
    location_input,
], id='filters')

body = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(filters, width="auto"),
                dbc.Col(dash.page_container),
            ]
        ),
    ]
)

app.layout = html.Div([dcc.Location(id="url"), navbar, body], id="page-content")

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)
    app.enable_dev_tools(dev_tools_ui=True, dev_tools_serve_dev_bundles=True)