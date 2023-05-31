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
from dash import Dash, Input, Output, dcc, html, callback, Patch
import pandas as pd

from config import filepath
from utils import is_docker

app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.LITERA, dbc.icons.BOOTSTRAP])


# df = pd.read_parquet(f, columns=['file','timestamp','recorder','feature','value']).drop_duplicates()
df = pd.read_parquet(filepath, columns=['timestamp','recorder','feature']).drop_duplicates()
df = df.assign(date=df.timestamp.dt.date)

pages = {m:m.split('.')[1:] for m in dash.page_registry}
children = {}
for p in pages:
    page = dash.page_registry[p]
    if len(pages[p]) == 1:
        children[pages[p][0]] = dbc.NavItem(dbc.NavLink(page['name'], href=page["relative_path"], active="exact"))
    else:
        if pages[p][0] not in children:
            children[pages[p][0]] = dbc.DropdownMenu(
                            children=[],
                            label=pages[p][0],
                            in_navbar=True,
                            nav=True,
                        )
        children[pages[p][0]].children.append(
            dbc.DropdownMenuItem(page['name'], href=page["relative_path"])
        )

navbar = dbc.NavbarSimple(
    children=list(children.values()),
    brand="Eyeballing Ecoacoustics",
    brand_href="#",
    color="primary",
    dark=True,
)

date_input = html.Div([
    dbc.Label("Dates", html_for="date-picker"),
    dbc.Button(html.I(className="bi p-2 lh-1"), className='btn btn-primary rounded-circle'),
    dcc.DatePickerRange(id='date-picker'),
], className="mb-3")



location_input = html.Div([
    dbc.Label("Locations", html_for=""),
    dbc.Checklist(
        options=[
            {"label": r, "value": r} for r in sorted(df.recorder.unique())
        ],
        value=[r for r in df.recorder.unique()],
        id="checklist-locations",
        inline=True,
        persistence=True
    ),
])

feature_input = html.Div([
    dbc.Label("Feature", html_for=""),
    dcc.Dropdown(
        id='feature-dropdown',
        options=df.feature.unique(), value=df.feature.unique()[0],
        # style={'min-width': '200px'},
        clearable=False, persistence=True),
])

filters = dbc.Form([
    html.H3("Filters"),
    date_input,
    location_input,
    feature_input
], id='filters')

body = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.Div([
                        filters,
                    ]), width=3),
                dbc.Col(dash.page_container),
            ]
        ),
    ]
)

app.layout = html.Div([dcc.Location(id="url"), navbar, body], id="page-content")


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)
    app.enable_dev_tools(dev_tools_ui=True, dev_tools_serve_dev_bundles=True)