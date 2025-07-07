import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback
from dash import Output, Input, State, ALL
from dash_iconify import DashIconify
from loguru import logger
from typing import List

from api import (
    dispatch,
    FETCH_ACOUSTIC_FEATURES,
    FETCH_DATASET_CATEGORIES,
)
from components.top_bar import TopBar
from components.footer import Footer
from utils import list2tuple
from utils import sketch

PAGE_NAME = 'scatter-plot'
PAGE_TITLE = 'Acoustic Descriptor by Time of Day'

dash.register_page(
    __name__,
    title=PAGE_TITLE,
    name='Scatter Plot'
)

PLOT_HEIGHT = 800

# setup plot type selector
plot_types = {
    "Scatter": px.scatter,
    "Scatter Polar": sketch.scatter_polar,
}
plot_type_kwargs = {
    "Scatter": dict(
        x='hour',
        y='value',
        hover_name="file",
        hover_data=["timestamp", "path"], # Path last for sound sample modal
        # mode="markers",
        # marker=dict(size=6, opacity=1.0),
        # fill="toself",
    ),
    "Scatter Polar": dict(
        r='value',
        theta='hour',
        # # TODO: implement marker style and colour in custom polar facet grid plot
        mode="markers",
        marker=dict(size=6, opacity=1.0),
        # fill="toself",
    ),
}

plot_type_select_id = f"{PAGE_NAME}-plot-type-select"
# colour_select_id = f"{PAGE_NAME}-colour-select"
# symbol_select_id = f"{PAGE_NAME}-symbol-select"
# row_facet_select_id = f"{PAGE_NAME}-row-facet-select"
# col_facet_select_id = f"{PAGE_NAME}-col-facet-select"
size_slider_id = f'{PAGE_NAME}-plot-size'

layout = html.Div([
    TopBar(
        PAGE_NAME,
        children=[
            dmc.Select(
                id=plot_type_select_id,
                label="Select plot type",
                value="Scatter",
                data=[
                    dict(value=plot_type, label=plot_type)
                    for plot_type in plot_types.keys()
                ],
                searchable=True,
                clearable=False,
                style=dict(width=200),
                persistence=True,
            ),
            # components.ColourSelect(
            #     id=colour_select_id,
            #     default="month",
            # ),
            # components.SymbolSelect(
            #     id=symbol_select_id,
            #     default=None,
            # ),
            # components.RowFacetSelect(
            #     id=row_facet_select_id,
            #     default=None,
            # ),
            # components.ColumnFacetSelect(
            #     id=col_facet_select_id,
            #     default=None,
            # ),
        ],
    ),
    dmc.Grid([
        dmc.GridCol(
            span=4,
            children=[
                dmc.Text(
                    "Dot Size",
                    size="sm",
                    ta="left",
                ),
                dmc.Slider(
                    id=size_slider_id,
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
            ]
        ),
    ]),
    dmc.Divider(variant='dotted'),
    dcc.Loading(
        dcc.Graph(id=f"{PAGE_NAME}-graph"),
    ),
    dbc.Offcanvas(
        id="page-info",
        is_open=False,
        placement="bottom",
        children=Footer(PAGE_NAME),
    ),
    # FIXME
    # components.SoundSampleModal(
    #     PAGE_NAME,
    # ),
])

@callback(
    Output(f"{PAGE_NAME}-graph", "figure"),
    State("dataset-select", "value"),
    Input("date-picker", component_property='value'),
    Input({"type": "checklist-locations-hierarchy", "index": ALL}, "value"),
    Input("feature-dropdown", "value"),
    Input(plot_type_select_id, "value"),
    # Input(colour_select_id, "value"),
    # Input(symbol_select_id, "value"),
    # Input(row_facet_select_id, "value"),
    # Input(col_facet_select_id, "value"),
    Input(size_slider_id, "value"),
)
def update_figure(
    dataset_name: str,
    dates: List,
    locations: List[str],
    feature: str,
    plot_type: str,
    # colour_by: str,
    # symbol_by: str,
    # row_facet: str,
    # col_facet: str,
    dot_size: int,
) -> go.Figure:
    # logger.debug(
    #     f"Trigger ID={ctx.triggered_id}: {dataset_name=} "
    #     f"num_dates={len(dates)} num_locations={len(locations)} {feature=} "
    #     f"{plot_type=} {colour_by=} {symbol_by=} {row_facet=} {col_facet=} {dot_size=}"
    # )

    data = dispatch(
        FETCH_ACOUSTIC_FEATURES,
        dataset_name=dataset_name,
        dates=list2tuple(dates),
        locations=list2tuple(locations),
        feature=feature,
    )
    category_orders = dispatch(
        FETCH_DATASET_CATEGORIES,
        dataset_name=dataset_name,
    )

    plot = plot_types[plot_type]
    plot_kwargs = plot_type_kwargs[plot_type]
    fig = plot(
        data,
        **plot_kwargs,
        opacity=0.5,
        # color=colour_by,
        # symbol=symbol_by,
        # facet_row=row_facet,
        # facet_col=col_facet,
        category_orders=category_orders,
    )

    # Select sample for audio modal
    fig.update_layout(clickmode='event+select')

    # Add centered title
    fig.update_layout(
        height=PLOT_HEIGHT,
        title={
            'text':f"{PAGE_TITLE} ({feature})",
            'x':0.5,
            'y':0.97,
            'font':{'size':24}
        }
    )

    # Adjust size of scatter dots
    fig.update_traces(marker=dict(size=dot_size))

    return fig
