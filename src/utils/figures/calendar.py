import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from plotly_calplot import calplot

def plot(df: pd.DataFrame, **kwargs):
    data = df.groupby("date").agg("count").reset_index()
    return calplot(data, x="date", y="file_name", **kwargs)
