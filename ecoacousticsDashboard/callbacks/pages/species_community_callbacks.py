import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import functools
import itertools
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots

from dash import html, dcc, callback, ctx, no_update
from dash import Output, Input, State, ALL, MATCH
from io import StringIO
from typing import Any, Dict, List, Tuple

from api import dispatch, FETCH_BIRDNET_SPECIES
from utils import list2tuple
from utils import sketch

MAX_WIDTH = 1600
CELL_WIDTH = 50
CELL_HEIGHT = 25

@callback(
    Output("species-community-page-info", "is_open"),
    Input("info-icon", "n_clicks"),
    State("species-community-page-info", "is_open"),
    prevent_initial_call=True,
)
def toggle_page_info(n_clicks: int, is_open: bool) -> bool:
    return not is_open

@callback(
    Output("species-community-graph", "figure"),
    State("dataset-select", "value"),
    Input("filter-store", "data"),
    # Input("umap-filter-store", "data"),
    Input("species-community-threshold-slider", "value"),
    Input("species-community-axis-select", "value"),
    Input("species-community-facet-column-select", "value"),
    Input("species-community-facet-row-select", "value"),
    Input("dataset-category-orders", "data"),
    Input("dataset-options", "data"),
)
def draw_figure(
    dataset_name: str,
    filters: Dict[str, Any],
    # file_filter_groups: Dict[str, List],
    threshold: float,
    axis_group: str,
    facet_col: str,
    facet_row: str,
    category_orders: Dict[str, List[str]],
    options: Dict[str, List[str]],
) -> go.Figure:
    data = dispatch(
        FETCH_BIRDNET_SPECIES,
        dataset_name=dataset_name,
        dates=list2tuple(filters["date_range"]),
        locations=list2tuple(filters["current_sites"]),
        # file_ids=frozenset(itertools.chain(*list(file_filter_groups.values()))),
    )
    data["detected"] = (data["confidence"] > threshold).astype(int)
    counts = (
        data.groupby([*list(filter(None, [axis_group, facet_col, facet_row])), "species"])["detected"]
        .sum()
        .reset_index()
        .sort_values(by="detected", ascending=True)
    )
    z_min = 0
    z_max = max(counts["detected"].max(), 1)

    if facet_row is None:
        counts["_row_facet"] = "All"
        facet_row = "_row_facet"
    if facet_col is None:
        counts["_col_facet"] = "All"
        facet_col = "_col_facet"

    row_categories = counts[facet_row].unique()
    col_categories = counts[facet_col].unique()
    categories = list(itertools.product(row_categories, col_categories))
    subplot_titles = [
        f"{r if r != 'All' else ''} {c if c != 'All' else ''}"
        for r in row_categories
        for c in col_categories
    ]

    all_x = counts[axis_group].unique().tolist()
    all_y = counts["species"].unique().tolist()

    num_rows = len(row_categories)
    num_cols = len(col_categories)
    fig = make_subplots(
        rows=num_rows,
        cols=num_cols,
        subplot_titles=subplot_titles,
        shared_yaxes=True,
        horizontal_spacing=0.01,
        vertical_spacing=0.01,
    )

    for i, (row_cat, col_cat) in enumerate(categories):
        row = i // num_cols + 1
        col = i % num_cols + 1
        subset = counts[(counts[facet_row] == row_cat) & (counts[facet_col] == col_cat)]
        if subset.empty:
            subset = pd.DataFrame(0, index=all_y, columns=all_x)
        else:
            subset = subset.pivot_table(
                index="species",
                columns=axis_group,
                values="detected",
                aggfunc="sum",
                fill_value=0,
            ).reindex(
                index=all_y,
                columns=all_x,
                fill_value=0,
            )
        fig.add_trace(
            go.Heatmap(
                z=subset.values,
                x=subset.columns,
                y=subset.index,
                colorscale="Greys",
                text=subset.values,
                texttemplate="%{text}",
                textfont={"size": 10, "color": "black"},
                showscale=(row == 1 and col == len(col_categories)),
                zmin=z_min,
                zmax=z_max,
            ),
            row=row, col=col,
        )
    fig.update_yaxes(categoryorder="array", categoryarray=all_y)
    fig.update_layout(
        # margin=dict(l=0, r=0, t=80, b=80),
        barmode='stack',
        height=CELL_HEIGHT * len(all_y) * len(row_categories),
        width=max(MAX_WIDTH, CELL_WIDTH * len(all_x) * len(col_categories)),
        title=dict(
            text=f"Species by Site",
            automargin=True,
            x=0.5,
            y=1.00,
            xanchor="center",
            yanchor="top",
            font=dict(size=24),
        ),
    )
    return fig
