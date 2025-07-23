import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash import dcc
from dash_iconify import DashIconify

from callbacks.pages import index_scatter_callbacks

from components.dataset_options_select import DatasetOptionsSelect
from components.data_download_widget import DataDownloadWidget
from components.controls_panel import ControlsPanel
from components.filter_panel import FilterPanel
from components.date_range_filter import DateRangeFilter
from components.site_level_filter import SiteLevelFilter
from components.environmental_filter import EnvironmentalFilter
from components.acoustic_feature_filter import AcousticFeatureFilter
from components.figure_download_widget import FigureDownloadWidget
from components.footer import Footer

PAGE_NAME = 'index-scatter'
PAGE_TITLE = 'Acoustic Descriptor by Time of Day'

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name='Scatter Plot'
)

PLOT_HEIGHT = 800

layout = dmc.Box([
    dcc.Store(id="index-scatter-graph-data"),
    FilterPanel([
        dmc.Group(
            align="start",
            grow=True,
            children=[
                SiteLevelFilter(),
                DateRangeFilter(),
                EnvironmentalFilter(),
            ]
        ),
        dmc.Space(h=10),
        dmc.Group(
            align="start",
            grow=True,
            children=[
                AcousticFeatureFilter(),
            ]
        ),
    ]),
    dmc.Space(h="sm"),
    ControlsPanel([
        dmc.Group(
            grow=True,
            children=[
                DatasetOptionsSelect(
                    id="index-scatter-colour-select",
                    label="Colour by",
                ),
                DatasetOptionsSelect(
                    id="index-scatter-symbol-select",
                    label="Symbol by"
                ),
                DatasetOptionsSelect(
                    id="index-scatter-facet-row-select",
                    label="Facet rows by"
                ),
                DatasetOptionsSelect(
                    id="index-scatter-facet-column-select",
                    label="Facet columns by"
                ),
                dmc.Flex(
                    p="1rem",
                    align="center",
                    justify="right",
                    direction="row",
                    children=[
                        dmc.Group(
                            grow=True,
                            children=[
                                DataDownloadWidget(
                                    graph_data="index-scatter-graph-data",
                                ),
                                FigureDownloadWidget(
                                    plot_name="index-scatter-graph",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        dmc.Group(
            grow=True,
            children=dmc.Stack([
                dmc.Text(
                    "Dot Size",
                    size="sm",
                    ta="left",
                ),
                dmc.Slider(
                    id="index-scatter-size-slider",
                    min=1,
                    max=20,
                    step=1,
                    value=6,
                    marks=[
                        {"value": i, "label": f"{i}"}
                        for i in (1, 10, 20)
                    ],
                    persistence=True
                )
            ]),
        ),
    ]),
    dcc.Loading(
        dcc.Graph(id=f"index-scatter-graph"),
    ),
    dbc.Offcanvas(
        id="index-scatter-page-info",
        is_open=False,
        placement="bottom",
        children=Footer("index-scatter"),
    ),
])
