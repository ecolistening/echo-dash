import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from typing import Any, Dict

PLOT_HEIGHT = 800

def plot(
    df: pd.DataFrame,
    **kwargs: Any,
) -> go.Figure:
    fig = px.histogram(
        data_frame=df,
        x="value",
        marginal="rug",
        opacity=0.75,
        **kwargs,
    )
    fig.update_layout(
        height=PLOT_HEIGHT,
        title=dict(
            x=0.5,
            y=0.97,
            font=dict(size=24),
        )
    )
    return fig
