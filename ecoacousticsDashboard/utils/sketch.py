import itertools
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from plotly.subplots import make_subplots
from typing import Any, Dict, List

__ALL__ = [
    "bar_polar",
    "scatter_polar",
]

def scatter(
    data: pd.DataFrame,
    x: str,
    y: str,
    facet_row: str,
    facet_col: str,
    color: str | None = None,
    width: str | None = None,
    category_orders: Dict[str, List[Any]] = {},
    trace_height: int = 200,
    **kwargs,
) -> go.Figure:
    if facet_row is None:
        data["_row_facet"] = "All"
        facet_row = "_row_facet"
    if facet_col is None:
        data["_col_facet"] = "All"
        facet_col = "_col_facet"

    row_categories = category_orders.get(facet_row, sorted(data[facet_row].dropna().unique()))
    num_rows = len(row_categories)

    fig = px.scatter(
        data,
        x=x,
        y=y,
        facet_row=facet_row,
        facet_col=facet_col,
        category_orders=category_orders,
    )

    fig.update_traces(**kwargs)

    fig.update_layout(
        height=num_rows * trace_height,
    )
    return fig

def bar_polar(
    data: pd.DataFrame,
    r: str,
    theta: str,
    facet_row: str,
    facet_col: str,
    color: str | None = None,
    width: str | None = None,
    category_orders: Dict[str, List[Any]] = {},
    radialaxis: Dict[str, Any] = {},
    angularaxis: Dict[str, Any] = {},
    trace_height: int = 200,
    # trace_width: int = 200,
    **kwargs
) -> go.Figure:
    """
    Plotly express doesn't yet support faceted grids for polar plots, hence...
    """
    if facet_row is None:
        data["_row_facet"] = "All"
        facet_row = "_row_facet"
    if facet_col is None:
        data["_col_facet"] = "All"
        facet_col = "_col_facet"

    row_categories = category_orders.get(facet_row, sorted(data[facet_row].dropna().unique()))
    col_categories = category_orders.get(facet_col, sorted(data[facet_col].dropna().unique()))
    categories = list(itertools.product(row_categories, col_categories))

    subplot_titles = [str(col_category) for col_category in col_categories if facet_col != "_col_facet"]

    num_rows = len(row_categories)
    num_cols = len(col_categories)

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

        subset = data[
            (data[facet_row] == row_category) &
            (data[facet_col] == col_category)
        ].sort_values(by=[theta, facet_row, facet_col])

        trace = go.Barpolar(
            r=subset[r],
            theta=subset[theta].unique() * 360 / 24,
            **kwargs
        )
        fig.add_trace(trace, row=row, col=col)

    if facet_row != "_row_facet":
        for i, row_category in enumerate(row_categories):
            fig.add_annotation(dict(
                text=str(row_category),
                x=1.05,
                y=1 - (i + 0.5) / num_rows,
                xref="paper",
                yref="paper",
                align="right",
                xanchor="right",
                yanchor="middle",
                textangle=90,
                showarrow=False,
                font=dict(size=14),
            ))

    angular_title = angularaxis.pop("title", "")

    for row_i in range(num_rows):
        for col_i in range(num_cols):
            subplot_i = row_i * num_cols + col_i + 1
            polar_key = 'polar' if subplot_i == 1 else f'polar{subplot_i}'
            domain = fig.layout[polar_key].domain
            fig.add_annotation(dict(
                text=str(angular_title),
                x=domain.x[1] - 0.01,
                y=domain.y[1] - 0.01,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=14),
                align="center"
            ))

    for i in range(1, num_rows * num_cols + 1):
        fig.update_layout({
            f"polar{i if i > 1 else ''}": dict(radialaxis=radialaxis, angularaxis=angularaxis),
        })

    fig.update_layout(
        height=num_rows * trace_height,
    )

    return fig

def scatter_polar(
    data: pd.DataFrame,
    r: str,
    theta: str,
    facet_row: str,
    facet_col: str,
    color: str | None = None,
    width: str | None = None,
    category_orders: Dict[str, List[Any]] = {},
    radialaxis: Dict[str, Any] = {},
    angularaxis: Dict[str, Any] = {},
    trace_height: int = 200,
    **kwargs
) -> go.Figure:
    """
    Plotly express doesn't yet support faceted grids for polar plots, hence...
    """
    if facet_row is None:
        data["_row_facet"] = "All"
        facet_row = "_row_facet"
    if facet_col is None:
        data["_col_facet"] = "All"
        facet_col = "_col_facet"

    row_categories = category_orders.get(facet_row, sorted(data[facet_row].dropna().unique()))
    col_categories = category_orders.get(facet_col, sorted(data[facet_col].dropna().unique()))
    categories = list(itertools.product(row_categories, col_categories))

    subplot_titles = [str(col_category) for col_category in col_categories if facet_col != "_col_facet"]

    num_rows = len(row_categories)
    num_cols = len(col_categories)

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

        subset = data[
            (data[facet_row] == row_category) &
            (data[facet_col] == col_category)
        ].sort_values(by=[theta, facet_row, facet_col])

        trace = go.Scatterpolar(
            r=subset[r],
            theta=subset[theta].unique() * 360 / 24,
            **kwargs
        )
        fig.add_trace(trace, row=row, col=col)

    if facet_row != "_row_facet":
        for i, row_category in enumerate(row_categories):
            fig.add_annotation(dict(
                text=str(row_category),
                x=1.05,
                y=1 - (i + 0.5) / num_rows,
                xref="paper",
                yref="paper",
                align="right",
                xanchor="right",
                yanchor="middle",
                textangle=90,
                showarrow=False,
                font=dict(size=14),
            ))

    angular_title = angularaxis.pop("title", "")
    for row_i in range(num_rows):
        for col_i in range(num_cols):
            subplot_i = row_i * num_cols + col_i + 1
            polar_key = 'polar' if subplot_i == 1 else f'polar{subplot_i}'
            domain = fig.layout[polar_key].domain
            fig.add_annotation(dict(
                text=str(angular_title),
                x=domain.x[1] - 0.01,
                y=domain.y[1] - 0.01,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=14),
                align="center"
            ))

    for i in range(1, num_rows * num_cols + 1):
        fig.update_layout({
            f"polar{i if i > 1 else ''}": dict(radialaxis=radialaxis, angularaxis=angularaxis),
        })

    fig.update_layout(
        height=num_rows * trace_height,
    )

    return fig
