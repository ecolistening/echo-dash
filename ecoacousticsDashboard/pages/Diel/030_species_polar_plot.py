import dash
import dash_mantine_components as dmc
import itertools
import plotly.express as px
import plotly.graph_objects as go

from dash import html, ctx, dcc, callback, Output, State, Input, ALL
from loguru import logger
from plotly.subplots import make_subplots

from menu.dataset import ds
from utils.data import dataset_loader, filter_data, DatasetDecorator
from utils.plot_filter_menu import get_filter_drop_down

PAGE_NAME = 'species-polar-plot'
PAGE_TITLE = 'Polar Plot of Species Occurrence by Time of Day'
PLOT_HEIGHT = 800
dash.register_page(__name__, title=PAGE_TITLE, name='Species Occurrence Polar Plot')

dataset = dataset_loader.get_dataset(ds)
# TODO: use species_id
species_list = dataset.species_predictions.common_name.unique()
species_default = species_list[0]

colour_select, row_facet_select, col_facet_select = get_filter_drop_down(
    PAGE_NAME,
    colour_by_cat=True,
    include_symbol=False,
    colour_default='hour',
    row_facet_default='location',
    col_facet_default='weekday',
)

species_select = dmc.Select(
    id=f'{PAGE_NAME}-species-select',
    label="Select species",
    value=species_default,
    searchable=True,
    clearable=False,
    style={"width": 200},
    persistence=True,
    data=[
        {"value": common_name, "label": common_name }
        for common_name in species_list
    ],
)

filter_group = dmc.Group(children=[colour_select, row_facet_select, col_facet_select, species_select])

graph = dcc.Graph(id=f'{PAGE_NAME}-graph')

layout = html.Div([
    html.Div([html.H1(PAGE_TITLE)]),
    html.Hr(),
    dmc.Divider(variant='dotted'),
    filter_group,
    graph,
])

@callback(
    Output(f'{PAGE_NAME}-graph', component_property='figure'),
    Input('dataset-select', component_property='value'),
    Input({'type': 'checklist-locations-hierarchy', 'index': ALL}, 'value'),
    Input(colour_select, component_property='value'),
    Input(row_facet_select, component_property='value'),
    Input(col_facet_select, component_property='value'),
    Input(species_select, component_property='value'),
)
def update_figure(dataset_name, locations, colour_by, row_facet, col_facet, species_name):
    logger.debug(f"Trigger ID={ctx.triggered_id}: {dataset_name=} {colour_by=} {row_facet=} {col_facet=} {species_name=}")

    dataset = dataset_loader.get_dataset(dataset_name)
    species_data = dataset.species_predictions[dataset.species_predictions.common_name == species_name]
    data = filter_data(species_data, locations=locations)

    row_categories = data[row_facet].unique()
    col_categories = data[col_facet].unique()
    num_rows = len(row_categories)
    num_cols = len(col_categories)
    categories = list(itertools.product(row_categories, col_categories))
    subplot_titles = [str(col_cat) for col_cat in col_categories] + [""] * ((num_rows - 1) * num_cols)

    fig = make_subplots(
        rows=num_rows, cols=num_cols,
        specs=[[dict(type="polar")]*num_cols for _ in range(num_rows)],
        subplot_titles=subplot_titles,
        horizontal_spacing=0.05,
        vertical_spacing=0.05,
    )

    for i, (row_category, col_category) in enumerate(categories):
        row = i // num_cols + 1
        col = i % num_cols + 1
        show_colourbar = (row == 1 and col == 1)
        subset = data[(data[row_facet] == row_category) & (data[col_facet] == col_category)].sort_values(by="hour")
        fig.add_trace(go.Barpolar(
            r=subset.groupby("hour")["confidence"].mean(),
            theta=subset["hour"].unique() * 360 / 24,
            # width=1,
            marker_line_color="black",
            marker_line_width=2,
            opacity=0.8,
            # TODO determine categorical or continuous
            # marker=dict(
            #     color=subset[colour_by],
            #     colorscale="Viridis",
            #     cmin=0, cmax=1,
            #     colorbar=dict(
            #         title=colour_by,
            #         len=0.75,
            #         lenmode="fraction",
            #     ) if show_colourbar else None,
            # ),
            showlegend=False,
        ), row=row, col=col)

    for i, row_category in enumerate(row_categories):
        fig.add_annotation(
            dict(
                text=str(row_category),
                x=0.05,
                y=1 - (i + 0.5) / num_rows,
                xref="paper",
                yref="paper",
                align="right",
                xanchor="right",
                yanchor="middle",
                showarrow=False,
                font=dict(size=14),
            )
        )

    for row_i in range(num_rows):
        for col_i in range(num_cols):
            subplot_i = row_i * num_cols + col_i + 1
            polar_key = 'polar' if subplot_i == 1 else f'polar{subplot_i}'
            domain = fig.layout[polar_key].domain
            x0, x1 = domain.x[0], domain.x[1]
            y0, y1 = domain.y[0], domain.y[1]
            x = x1 - 0.01
            y = y1 - 0.01
            fig.add_annotation(
                dict(
                    text="Hour of Day",
                    x=x,
                    y=y,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(size=14),
                    align="center"
                )
            )

    fig.update_layout(
        height=PLOT_HEIGHT,
        title=dict(
            text=PAGE_TITLE,
            x=0.5,
            y=0.97,
            font=dict(size=24)
        ),
        **{
            f"polar{i if i > 1 else ''}": dict(
                radialaxis=dict(
                    range=[0, 1],
                    showticklabels=True,
                    ticks="",
                    title="Confidence"

                ),
                angularaxis=dict(
                    tickmode="array",
                    tickvals=[0, 90, 180, 270],
                    ticktext=["00:00", "06:00", "12:00", "18:00"],
                    direction="clockwise",
                    rotation=90,
                    ticks=""
                )
            )
            for i in range(1, num_rows * num_cols + 1)
        }
    )

    return fig

