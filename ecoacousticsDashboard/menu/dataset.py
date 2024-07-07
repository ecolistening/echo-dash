import configparser

import dash_mantine_components as dmc
from dash import callback, Output, Input, ctx, ALL, State
from dash_iconify import DashIconify

from loguru import logger

from config import root_dir
from utils.data import get_dataset_names, load_and_filter_sites, load_config

datasets = get_dataset_names()
ds = datasets[0]

tree = load_and_filter_sites(ds)
config = load_config(ds)

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

dataset_settings_button = dmc.Button(
            "Settings",
            variant="filled",
            leftIcon=DashIconify(icon="fluent:settings-32-regular"),
            # size="md",
            compact=True,
            id="dataset_settings_button",
            n_clicks=0,
            mb=10,
        )

tree_label = []
if tree is not None:
    for i in range(1, tree.max_depth):
        tree_label.append(dmc.TextInput(label = f'Level {i}', value=config.get('Site Hierarchy', f'sitelevel_{i}', fallback=''),  id={
                            'type': 'sitelevel_label',
                            'index': i-1
                        }))
sites_form = dmc.Stack(tree_label, id='dataset-settings-sites-form')

settings_drawer = dmc.Drawer(
    title="Settings",
    id="settings-drawer",
    padding="md",
    size="55%",
    position='right',
    zIndex=10000,
    children=[
        dmc.Title(f'Settings for the {ds} dataset', order=2, id='dataset-settings-dataset-name'),
        dmc.Stack([
            dmc.Title('Stats', order=3),
            dmc.Text('Recordings: ', ),
            dmc.Title('Site Hierarchy', order=3),
            sites_form
        ]),
        dmc.Footer([
            dmc.ButtonGroup([
                dmc.Button(
                    'Save',
                    variant="filled",
                    leftIcon=DashIconify(icon='fluent:save-28-filled'),
                    id="dataset-settings-save-button",
                    n_clicks=0,
                    mb=10,
                ),
                dmc.Button(
                    'Cancel',
                    variant="filled",
                    leftIcon=DashIconify(icon='material-symbols:cancel'),
                    id="dataset-settings-cancel-button",
                    n_clicks=0,
                    mb=10,
                ),
            ])
        ], height=60),
    ]
)

@callback(
    Output('settings-drawer', "opened"),
    Input("dataset_settings_button", "n_clicks"),
    Input("dataset-settings-save-button", "n_clicks"),
    Input('dataset-settings-cancel-button', "n_clicks"),
    State('dataset-name', component_property='data'),
    State({'type': 'sitelevel_label', 'index': ALL}, 'value'),
    prevent_initial_call=True,
)
def handle_settings_drawer(settings_button, save_button, cancel_button, dataset, site_labels):
    if ctx.triggered_id == 'dataset_settings_button':
        return True
    elif ctx.triggered_id == 'dataset-settings-save-button':
        config = load_config(dataset)

        for i, label in enumerate(site_labels[1:]):
            config.set('Site Hierarchy', f'sitelevel_{i+1}', label)
        with open(root_dir / dataset / 'config.ini', 'w') as configfile:
            config.write(configfile)

    return False

@callback(
    Output('dataset-settings-sites-form', component_property='children'),
    Output('dataset-settings-dataset-name', component_property='value'),
    Input('dataset-name', component_property='data'),
    prevent_initial_call=True,
)
def update_sites_form(dataset):
    tr = load_and_filter_sites(dataset)
    config = load_config(dataset)
    children = [dmc.TextInput(label = f'Level {i}', value=config.get('Site Hierarchy', f'sitelevel_{i}', fallback=''),  id={
                            'type': 'sitelevel_label',
                            'index': i-1
                        }) for i in range(1, tr.max_depth)]
    title = f'Settings for the {dataset} dataset'

    return children, title