import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from plotly_calplot import calplot

PLOT_HEIGHT = 800

def plot(df: pd.DataFrame):
    data = df.groupby("date").agg("count").reset_index()
    fig = calplot(data, x="date", y="file_name")
    fig.update_layout(
        height=PLOT_HEIGHT,
        title=dict(
            automargin=True,
            x=0.5,
            y=1.00,
            xanchor="center",
            yanchor="top",
            font=dict(size=24),
        )
    )
    return fig

