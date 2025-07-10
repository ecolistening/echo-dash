import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash import dcc
from dash_iconify import DashIconify

from callbacks.pages import index_box_callbacks

from components.dataset_options_select import DatasetOptionsSelect
from components.controls_panel import ControlsPanel
from components.filter_panel import FilterPanel
from components.date_range_filter import DateRangeFilter
from components.site_level_filter import SiteLevelFilter
from components.environmental_filter import EnvironmentalFilter
from components.acoustic_feature_filter import AcousticFeatureFilter
from components.figure_download_widget import FigureDownloadWidget
from components.footer import Footer

PAGE_NAME = "index-box-plot"
PAGE_TITLE = "Box Plot of Acoustic Descriptor by Time of Day"

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name="Box Plot"
)

PLOT_HEIGHT = 800

layout = dmc.Box([
    dcc.Store(id="index-box-graph-data"),
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
                    id="index-box-colour-select",
                    label="Colour by"
                ),
                DatasetOptionsSelect(
                    id="index-box-facet-row-select",
                    label="Facet rows by"
                ),
                DatasetOptionsSelect(
                    id="index-box-facet-column-select",
                    label="Facet columns by"
                ),
                dmc.Box(
                    style={
                        "padding": "1rem",
                        "display": "flex",
                        "align-content": "center",
                        "justify-content": "right",
                    },
                    children=[
                        FigureDownloadWidget(
                            plot_name="index-box-graph",
                        ),
                    ],
                ),
            ],
        ),
        dmc.Group(
            children=[
                dmc.Stack([
                    dmc.Text(
                        "Group by Time",
                        size="sm",
                        ta="left",
                    ),
                    dmc.SegmentedControl(
                        id="index-box-time-aggregation",
                        data=[
                            {"value": "time", "label": "15 minutes"},
                            {"value": "hour", "label": "1 hour"},
                            {"value": "dddn", "label": "Dawn-Day-Dusk-Night"}
                        ],
                        value="dddn",
                        persistence=True
                    ),
                ]),
                dmc.Stack([
                    dmc.Chip(
                        "Outliers",
                        id="index-box-outliers-tickbox",
                        value="outlier",
                        checked=True,
                        persistence=True,
                    ),
                ]),
            ],
        ),
    ]),
    dcc.Loading(
        dcc.Graph(id="index-box-graph"),
    ),
    dbc.Offcanvas(
        id="index-box-page-info",
        is_open=False,
        placement="bottom",
        children=Footer("index-box"),
    ),
])

