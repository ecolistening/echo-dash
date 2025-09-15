import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from typing import Any, Dict, List, Tuple

PLOT_HEIGHT = 800

def plot(
    df: pd.DataFrame,
    time_agg: str = "1W",
    color: str | None = None,
    labels: Dict[str, str] | None = None,
    **kwargs: Any,
) -> go.Figure:
    df = (
        df.sort_values("timestamp")
        .groupby(list(filter(None, [color, "feature", "dddn", pd.Grouper(key="timestamp", freq=time_agg)])))
        .agg({"value": ["mean", "std"]})
        .reset_index()
    )
    df.columns = ["_".join(filter(None, col_levels)) for col_levels in df.columns.to_flat_index()]
    fig = px.line(
        data_frame=df,
        x="timestamp",
        y="value_mean",
        error_y="value_std",
        color=color,
        facet_row="dddn",
        markers=True,
        labels=labels,
        **kwargs,
    )
    fig.update_traces(marker=dict(size=4))
    fig.update_layout(
        height=PLOT_HEIGHT,
        title=dict(
            x=0.5,
            y=0.97,
            font=dict(size=24),
        )
    )
    return fig
