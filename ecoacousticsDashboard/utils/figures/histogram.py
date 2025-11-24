import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from typing import Any, Dict

PLOT_HEIGHT = 800

def plot(
    df: pd.DataFrame,
    **kwargs: Any,
) -> go.Figure:
    return px.histogram(
        data_frame=df,
        x="value",
        marginal="rug",
        opacity=0.75,
        **kwargs,
    )
