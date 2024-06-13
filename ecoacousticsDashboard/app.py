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

# Setup Logging
import os
import sys
from loguru import logger
os.makedirs('log',exist_ok=True)
logger.add("log/{time}.log", rotation="00:00", retention="90 days")

logger.info("Setup server..")
logger.debug(f"Python Version: {sys.version}")

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import Dash, dcc, Output, Input, callback

from menu.dataset import dataset_input, dataset_settings_button, settings_drawer
from menu.filter import filters

app = Dash(__name__, use_pages=True, external_stylesheets=[
    dbc.themes.LITERA, dbc.icons.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;900&display=swap"
])

server = app.server

header = dmc.Header(
    height=60,
    children=dmc.Center(dmc.Title("EchoDash", order=1))
)


def menu_from_page_registry():
    pages = {m: m.split('.')[1:] for m in dash.page_registry}
    children = {}
    for p in pages:
        page = dash.page_registry[p]
        if len(pages[p]) == 0:
            logger.warning(f"Can't find page {p}")
            continue
        elif len(pages[p]) == 1:
            children[pages[p][0]] = dmc.NavLink(label=page['name'], href=page["relative_path"])
        else:
            if pages[p][0] not in children:
                children[pages[p][0]] = dmc.NavLink(label=pages[p][0], children=[])
            children[pages[p][0]].children.append(
                dmc.NavLink(label=page['name'], href=page["relative_path"])
            )

    return_list = []

    # Put groups in desired order. Adjust file name to sort individual pages within groups alphabetically
    for group in ('home','Metadata','Overview','Diel','Seasonal'):
        return_list.append(children[group])

    return return_list


navbar = dmc.Navbar(
    p="md",
    width={"base": 300},
    children=dmc.ScrollArea(
        dmc.Stack(children=[
                               dmc.Title("EchoDash", order=3),
                           ] + menu_from_page_registry() + [
                               dmc.Divider(),
                               dmc.Title("Data", order=3),
                               dataset_input,
                               dataset_settings_button,
                               dmc.Title("Filters", order=3),
                               filters,
                               dataset_name := dcc.Store(id='dataset-name'),
                               settings_drawer
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
    # withNormalizeCSS=True,
    children=dmc.AppShell(children=[dash.page_container, settings_drawer], navbar=navbar),
    # children=dmc.AppShell(children=dash.page_container, navbar=navbar),
)

@callback(
    Output('dataset-name', component_property='data'),
    Input('dataset-select', component_property='value'),
    prevent_initial_call=True,
)
def update_dataset_name(dataset):
    return dataset


if __name__ == '__main__':
    logger.info("Start server..")
    app.run_server(host='0.0.0.0', debug=True)
    app.enable_dev_tools(dev_tools_ui=True, dev_tools_serve_dev_bundles=True)
    logger.info("Server shutdown.")