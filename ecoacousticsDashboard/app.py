import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import flask
import os

from dash import dcc, Output, Input, callback
from loguru import logger

from menu.dataset import dataset_input, dataset_settings_button, settings_drawer
from menu.filter import filters

def create_dash_app(requests_pathname_prefix: str = None) -> dash.Dash:
    logger.info("Starting Dash server...")
    server = flask.Flask(__name__)
    server.secret_key = os.environ.get("secret_key", "secret")

    app = dash.Dash(
        __name__,
        server=server,
        requests_pathname_prefix=requests_pathname_prefix,
        use_pages=True,
        external_stylesheets=[
            dbc.themes.LITERA, dbc.icons.BOOTSTRAP,
            "https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;900&display=swap"
        ]
    )

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

    return app
