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
from utils import list2tuple, send_download

MAX_WIDTH = 1600
CELL_HEIGHT = 40

def fetch_data(dataset_name, filters):
    return dispatch(
        FETCH_BIRDNET_SPECIES,
        dataset_name=dataset_name,
        dates=list2tuple(filters["date_range"]),
        locations=list2tuple(filters["current_sites"]),
        file_ids=frozenset(itertools.chain(*list(filters["files"].values()))),
    )

def plot(
    df: pd.DataFrame,
    axis_group: str,
    facet_col: str | None = None,
    facet_row: str | None = None,
    category_orders: Dict[str, Any] | None = None,
) -> go.Figure:
    counts = (
        df.groupby([*list(filter(None, [axis_group, facet_col, facet_row])), "species"])["detected"]
        .sum()
        .reset_index()
        .sort_values(by="detected", ascending=True)
    )
    # ensure faceting works regardless of whether specified
    if axis_group is None:
        counts["_axis_group"] = "All"
        axis_group = "_axis_group"
    if facet_row is None:
        counts["_row_facet"] = "All"
        facet_row = "_row_facet"
    if facet_col is None:
        counts["_col_facet"] = "All"
        facet_col = "_col_facet"

    z_min = 0
    z_max = max(counts["detected"].max(), 1)
    all_x = counts[axis_group].unique().tolist()

    # calculate plot heights proportional to the number of species detected
    row_categories = []
    row_heights = []
    for row_cat in category_orders.get(facet_row, counts[facet_row].unique()):
        species_count = counts.loc[counts[facet_row] == row_cat, "species"].count()
        if species_count > 0:
            row_categories.append(row_cat)
            row_heights.append(species_count)
    row_heights = np.array(row_heights)
    height = CELL_HEIGHT * row_heights.sum()
    row_heights = list(row_heights / row_heights.sum())

    # col categories remain consistent width
    col_categories = category_orders.get(facet_col, counts[facet_col].unique())

    fig = make_subplots(
        rows=len(row_categories),
        cols=len(col_categories),
        row_heights=None if len(row_heights) == 1 else list(row_heights),
        subplot_titles=[
            "<br>".join(list(filter(None, [
                str(r) if r != 'All' else None,
                str(c) if c != 'All' else None
            ])))
            for r in row_categories
            for c in col_categories
        ],
        horizontal_spacing=0.01,
        vertical_spacing=0.075,
    )

    for i, row_cat in enumerate(row_categories):
        row = i + 1
        row_species = counts.loc[counts[facet_row] == row_cat, "species"]
        for j, col_cat in enumerate(col_categories):
            col = j + 1
            subset = counts[(counts[facet_row] == row_cat) & (counts[facet_col] == col_cat)]
            if subset.empty:
                subset = pd.DataFrame(0, index=row_species, columns=all_x)
            else:
                subset = subset.pivot_table(
                    index="species",
                    columns=axis_group,
                    values="detected",
                    aggfunc="sum",
                    fill_value=0,
                ).reindex(
                    index=row_species,
                    columns=all_x,
                    fill_value=0,
                )
            fig.add_trace(
                go.Heatmap(
                    z=subset.values,
                    x=subset.columns,
                    y=row_species,
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

    updates = {}
    for i in range(len(row_categories)):
        for j in range(2, len(col_categories) + 1):
            axis_num = i * len(col_categories) + j
            updates[f"yaxis{axis_num}"] = dict(showticklabels=False)
    # for i in range(len(row_categories)):
    #     base_axis_num = i * len(col_categories) + 1  # first col in row i
    #     base_axis = "y" + (str(base_axis_num) if base_axis_num > 1 else "")  # y, y2, y3...
    #     for j in range(2, len(col_categories)+1):  # rest of cols in the row
    #         axis_num = i * len(col_categories) + j
    #         axis_name = "yaxis" + str(axis_num)  # this is the layout property
    #         match_name = "y" + (str(base_axis_num) if base_axis_num > 1 else "")  # this is the value for 'matches'
    #         updates[axis_name] = {"matches": match_name}
    # fig.update_yaxes(
    #     categoryorder="array",
    #     categoryarray=all_y,
    # )
    fig.update_layout(
        barmode='stack',
        height=height,
        width=MAX_WIDTH,
        **updates,
        title=dict(
            automargin=True,
            x=0.5,
            y=1.00,
            xanchor="center",
            yanchor="top",
            font=dict(size=24),
        ),
    )
    return fig

def register_callbacks():
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
        Input("species-community-threshold-slider", "value"),
        Input("species-community-axis-select", "value"),
        Input("species-community-facet-column-select", "value"),
        Input("species-community-facet-row-select", "value"),
        State("dataset-options", "data"),
        State("dataset-category-orders", "data"),
    )
    def draw_figure(
        dataset_name: str,
        filters: Dict[str, Any],
        threshold: float,
        axis_group: str,
        facet_col: str,
        facet_row: str,
        options: Dict[str, List[str]],
        category_orders: Dict[str, List[str]],
    ) -> go.Figure:
        data = fetch_data(dataset_name, filters)
        data["detected"] = (data["confidence"] > threshold).astype(int)
        fig = plot(data, axis_group, facet_col, facet_row, category_orders)
        fig.update_layout(title_text="Species by Site")
        return fig

    @callback(
        Output("species-community-data-download", "data"),
        State("dataset-select", "value"),
        State("filter-store", "data"),
        Input({"type": "species-community-data-download-button", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def download_data(
        dataset_name: str,
        filters,
        clicks,
    ) -> Dict[str, Any]:
        return send_download(
            fetch_data(dataset_name, filters),
            f"{dataset_name}_birdnet_detections",
            ctx.triggered_id["index"],
        )
