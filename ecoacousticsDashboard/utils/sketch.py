import itertools
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

from plotly.subplots import make_subplots
from typing import Any, Dict, List

__ALL__ = [
    "bar_polar",
    "scatter_polar",
]

def safe_polar_subplot_params(rows=1, cols=1, target_spacing=0.05):
    if rows < 1 or cols < 1:
        raise ValueError("rows and cols must be >= 1")
    num_h_gaps = max(cols - 1, 0)
    num_v_gaps = max(rows - 1, 0)
    max_validator_h = 0 if num_h_gaps == 0 else 1 / num_h_gaps
    max_validator_v = 0 if num_v_gaps == 0 else 1 / num_v_gaps
    total_width = 1.0
    total_height = 1.0
    max_domain_h = 0 if num_h_gaps == 0 else total_width / cols / 2
    max_domain_v = 0 if num_v_gaps == 0 else total_height / rows / 2
    h_spacing = min(target_spacing, max_validator_h, max_domain_h)
    v_spacing = min(target_spacing, max_validator_v, max_domain_v)
    col_width = (total_width - num_h_gaps * h_spacing) / cols
    row_height = (total_height - num_v_gaps * v_spacing) / rows
    return {
        "column_widths": [col_width] * cols,
        "row_heights": [row_height] * rows,
        "horizontal_spacing": h_spacing,
        "vertical_spacing": v_spacing,
    }

def dedup(l: List[Any]):
    seen = []
    return [x for x in l if not (x in seen or seen.append(x))]

def get_hover_template(hover_name, hover_data, labels):
    template = ""
    start_idx = 0
    seen = []
    hover_data = list(filter(None, dedup(hover_data)))
    if hover_name:
        template += f"<b>%{{customdata[0]}}</b><br>"
        start_idx += 1
        columns = [hover_name] + hover_data
    else:
        columns = hover_data

    for i, column in enumerate(columns[start_idx:], start=start_idx):
        template += f"<b>{labels.get(column, column)}</b>: %{{customdata[{i}]}}<br>"

    template += "<extra></extra>"
    return template, columns

def bar_polar(
    data_frame: pd.DataFrame,
    r: str,
    theta: str,
    facet_row: str,
    facet_col: str,
    color: str | None = None,
    hover_name: str = None,
    hover_data: List[str] = None,
    labels: Dict[str, str] = None,
    category_orders: Dict[str, List[Any]] = {},
    radialaxis: Dict[str, Any] = {},
    angularaxis: Dict[str, Any] = {},
    **kwargs
) -> go.Figure:
    """
    Plotly express doesn't yet support faceted grids for polar plots, hence...
    """
    labels = labels or {}
    hover_data = hover_data or []
    custom_cols = [col for col in hover_data if col in data_frame.columns]
    customdata = data_frame[custom_cols].to_numpy() if custom_cols else None

    template = ""
    if hover_name:
        template += f"<b>%{{customdata[0]}}</b><br>"
        custom_cols = [hover_name] + custom_cols
        customdata = data_frame[custom_cols].to_numpy()

    template += (
        f"<b>{labels.get(r, r)}</b>: %{{r}}<br>"
        f"<b>{labels.get(theta, theta)}</b>: %{{theta}}<br>"
    )

    start_idx = 1 if hover_name else 0
    for i, col in enumerate(custom_cols[start_idx:], start=start_idx):
        template += f"<b>{labels.get(col, col)}</b>: %{{customdata[{i}]}}<br>"
    template += "<extra></extra>"

    if facet_row is None:
        data_frame["_row_facet"] = "All"
        facet_row = "_row_facet"
    if facet_col is None:
        data_frame["_col_facet"] = "All"
        facet_col = "_col_facet"

    row_categories = sorted(category_orders.get(facet_row, data_frame[facet_row].dropna().unique()))
    col_categories = sorted(category_orders.get(facet_col, data_frame[facet_col].dropna().unique()))
    categories = list(itertools.product(row_categories, col_categories))

    # figure out of we need to drop any plots
    subsets = []
    row_categories = []
    col_categories = []
    for i, (row_category, col_category) in enumerate(categories):
        if not data_frame[(data_frame[facet_row] == row_category) & (data_frame[facet_col] == col_category)].empty:
            row_categories.append(row_category)
            col_categories.append(col_category)

    row_categories = np.unique(row_categories).tolist()
    col_categories = np.unique(col_categories).tolist()
    num_rows = len(row_categories)
    num_cols = len(col_categories)
    categories = list(itertools.product(row_categories, col_categories))

    column_titles = []
    for col_category in col_categories:
        column_titles.append(col_category if facet_col != "_col_facet" else "")
    row_titles = []
    for row_category in row_categories:
        row_titles.append(row_category if facet_row != "_row_facet" else "")

    fig = make_subplots(
        rows=num_rows, cols=num_cols,
        specs=[[dict(type="polar")]*num_cols for _ in range(num_rows)],
        row_titles=row_titles,
        column_titles=column_titles,
        **safe_polar_subplot_params(rows=num_rows, cols=num_cols, target_spacing=0.1)
    )

    for i, (row_category, col_category) in enumerate(categories):
        row = i // num_cols + 1
        col = i % num_cols + 1
        show_colourbar = (row == 1 and col == 1)

        subset = data_frame[
            (data_frame[facet_row] == row_category) &
            (data_frame[facet_col] == col_category)
        ].sort_values(by=[theta, facet_row, facet_col])

        trace = go.Barpolar(
            r=subset[r],
            theta=subset[theta].unique() * 360 / 24,
            customdata=customdata,
            hovertemplate=template,
            **kwargs
        )
        fig.add_trace(trace, row=row, col=col)

    radialaxis["range"] = [0, data_frame[r].max()]
    for i in range(1, num_rows * num_cols + 1):
        fig.update_layout({
            f"polar{i if i > 1 else ''}": dict(radialaxis=radialaxis, angularaxis=angularaxis),
        })

    return fig

def scatter_polar(
    data_frame: pd.DataFrame,
    r: str,
    theta: str,
    facet_row: str,
    facet_col: str,
    hover_name: str = None,
    hover_data: List[str] = None,
    color: str | None = None,
    category_orders: Dict[str, List[Any]] = {},
    radialaxis: Dict[str, Any] = {},
    angularaxis: Dict[str, Any] = {},
    labels: Dict[str, str] = None,
    mode: str = "markers+lines",
    line_close: bool = True,
    **kwargs
) -> go.Figure:
    """
    Plotly express doesn't yet support faceted grids for polar plots, hence...
    """
    if data_frame.empty:
        return go.Figure()

    labels = labels or {}
    hover_data = hover_data or []
    hover_template, hover_columns = get_hover_template(hover_name, hover_data, labels)

    if facet_row is None:
        data_frame["_row_facet"] = "All"
        facet_row = "_row_facet"
    if facet_col is None:
        data_frame["_col_facet"] = "All"
        facet_col = "_col_facet"
    if color is None:
        data_frame["_color"] = "All"
        color = "_color"

    row_categories = sorted(category_orders.get(facet_row, data_frame[facet_row].dropna().unique()))
    col_categories = sorted(category_orders.get(facet_col, data_frame[facet_col].dropna().unique()))
    color_categories = sorted(category_orders.get(color, data_frame[color].dropna().unique()))
    categories = list(itertools.product(row_categories, col_categories))

    # figure out of we need to drop any plots
    subsets = []
    row_categories = []
    col_categories = []
    for i, (row_category, col_category) in enumerate(categories):
        if not data_frame[(data_frame[facet_row] == row_category) & (data_frame[facet_col] == col_category)].empty:
            row_categories.append(row_category)
            col_categories.append(col_category)

    row_categories = np.unique(row_categories).tolist()
    col_categories = np.unique(col_categories).tolist()
    num_rows = len(row_categories)
    num_cols = len(col_categories)
    categories = list(itertools.product(row_categories, col_categories))

    column_titles = []
    for col_category in col_categories:
        column_titles.append(col_category if facet_col != "_col_facet" else "")
    row_titles = []
    for row_category in row_categories:
        row_titles.append(row_category if facet_row != "_row_facet" else "")

    fig = make_subplots(
        rows=num_rows, cols=num_cols,
        specs=[[dict(type="polar")]*num_cols for _ in range(num_rows)],
        row_titles=row_titles,
        column_titles=column_titles,
        **safe_polar_subplot_params(rows=num_rows, cols=num_cols, target_spacing=0.05)
    )

    palette = px.colors.qualitative.Plotly
    color_map = {cat: palette[i % len(palette)] for i, cat in enumerate(color_categories)}
    for i, (row_category, col_category) in enumerate(categories):
        row = i // num_cols + 1
        col = i % num_cols + 1
        for j, color_category in enumerate(color_categories):
            subset = data_frame[
                (data_frame[facet_row] == row_category) &
                (data_frame[facet_col] == col_category) &
                (data_frame[color] == color_category)
            ].sort_values(by=theta)
            # plot boundary points
            subset_max = (
                subset
                .groupby(list(set([theta, facet_row, facet_col, color])))[r]
                .max()
                .reset_index(name=r)
            )

            if subset_max.empty:
                _r = [None]
                _theta = [None]
            else:
                _r = subset_max[r].tolist()
                _theta = (360 * subset_max[theta]).tolist()
                # add first element to complete the line
                _r = _r + [_r[0]]
                _theta = _theta + [_theta[0]]

            trace = go.Scatterpolar(
                r=_r,
                theta=_theta,
                name=color_category,
                line=dict(color=color_map[color_category]),
                marker=dict(color=color_map[color_category]),
                mode="markers+lines",
                showlegend=False,
                fill="toself",
                **kwargs
            )
            fig.add_trace(trace, row=row, col=col)

            if subset.empty:
                subset["r"] = [None]
                subset["theta"] = [None]
            else:
                subset["r"] = subset[r].tolist()
                # NB: this makes an assumption that we have a sample for the min and max of the angular axis
                # the alternative would be to normalise beforehand, but this was a simple quick fix
                subset["theta"] = (360 * subset[theta]).tolist()

            # plot individual points
            trace = go.Scatterpolar(
                r=subset["r"],
                theta=subset["theta"],
                customdata=subset[hover_columns].to_numpy(),
                hovertemplate=hover_template,
                name=color_category,
                mode="markers",
                marker=dict(color=color_map[color_category]),
                showlegend=(row == 1 and col == len(col_categories)),
                **kwargs
            )
            fig.add_trace(trace, row=row, col=col)

    radialaxis["range"] = [0, data_frame[r].max()]
    radialaxis["title"] = dict(text=labels.get(r, ""))
    # FIXME: outstanding feature request on plotly as of 10/11/25: https://github.com/plotly/plotly.js/issues/6332
    # angularaxis["title"] = dict(text=labels.get(theta, ""))

    for i in range(1, num_rows * num_cols + 1):
        fig.update_layout({
            f"polar{i if i > 1 else ''}": dict(radialaxis=radialaxis, angularaxis=angularaxis),
        })

    return fig

def default_layout(fig, max_height: int = 1600, row_height: int = 400):
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    try:
        num_rows = len(fig._grid_ref)
    except AttributeError:
        num_rows = 1
    return dict(
        height=min(max_height, row_height * num_rows),
        coloraxis_colorbar_title_side="right",
        title=dict(
            automargin=True,
            x=0.5,
            y=1.00,
            xanchor="center",
            yanchor="top",
            font=dict(size=24, color="black"),
        ),
    )
