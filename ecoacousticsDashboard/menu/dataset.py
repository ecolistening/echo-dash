import dash_mantine_components as dmc
from dash_iconify import DashIconify

from config import root_dir

datasets = [d.name for d in root_dir.glob("*") if d.is_dir()]
ds = datasets[0]

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

settings_drawer = dmc.Drawer(
    title="Settings",
    id="settings-drawer",
    padding="md",
    size="55%",
    position='right',
    zIndex=10000,
    children=[
        dmc.Title(ds, order=2),
        dmc.Stack([
            dmc.ButtonGroup([
                dmc.Button(
                    'Save',
                    variant="filled",
                    leftIcon=DashIconify(icon='fluent:save-28-filled'),
                    # size="md",
                    compact=True,
                    id="dataset_settings_button",
                    n_clicks=0,
                    mb=10,
                ),
                dmc.Button(
                    'Cancel',
                    variant="filled",
                    leftIcon=DashIconify(icon='material-symbols:cancel'),
                    # size="md",
                    compact=True,
                    id="dataset_settings_button",
                    n_clicks=0,
                    mb=10,
                ),
            ])
        ]),
    ]
)

# @callback(
#     Output('settings-drawer', "opened"),
#     Input("dataset_settings_button", "n_clicks"),
#     prevent_initial_call=True,
# )
# def open_settings_drawer(n_clicks):
#     return True