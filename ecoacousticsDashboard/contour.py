import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from datetime import datetime
from plotly.subplots import make_subplots

dataset = "sounding out"
site_level_field = "location"
site = "KN"
year = 2023
interval = 15
feature = "spectral centroid"
colour_category = "location"

def day_of_year_to_date(day_num, year):
    day_num.rjust(3 + len(day_num), '0')
    return datetime.strptime(year + "-" + day_num, "%Y-%j").strftime("%m-%d-%Y")

df = pd.read_parquet(f"../data/{dataset}/indices.parquet")
df["Hour"] = (df.timestamp.dt.hour * 60 + df.timestamp.dt.minute) / 60
df["Year Diff"] = df.timestamp.dt.year - df.timestamp.dt.year.min()
df["Day"] = df.timestamp.dt.dayofyear + (df["Year Diff"] * 365)
feature_df = df[(df["feature"] == feature) & (df[site_level_field] == site)][["value", "Hour", "Day", "timestamp"]]
# NOTE: this data file must be a bit buggered, because we have dupliate timestamps when we shouldn't
feature_pivot = feature_df.drop_duplicates(['Hour', 'Day']).pivot(index="Hour", columns="Day", values="value")

# tick_params = {
#     "Hour": dict(
#         tickvals=np.arange(0, 24, 1),
#         ticktext=[f"{h:02d}:00" for h in np.arange(0, 24, 1)],
#     ),
# }

fig = go.Figure()
fig.add_trace(go.Contour(
    name=f"{site} Daily Patterns",
    x=feature_pivot.columns,
    y=feature_pivot.index,
    z=feature_pivot.to_numpy(),
    colorscale='Plasma',
    colorbar=dict(
        title=feature,
        titleside="right",
        tickformat="~s",
    )
))

fig.update_layout(
    height=800,
    width=1400,
    xaxis=dict(
        title=dict(text="Day"),
        tickvals=np.arange(feature_df["Day"].min(), feature_df["Day"].max(), 1),
        ticktext=[day_of_year_to_date(str(day), "2015") for day in np.arange(feature_df["Day"].min(), feature_df["Day"].max(), 1)],
        tickangle=-90,
    ),
    yaxis=dict(
        title=dict(text="Time"),
        tickvals=np.arange(0, 24, 1),
        ticktext=[f"{h:02d}:00" for h in np.arange(0, 24, 1)],
    ),
)

from dash import Dash, dcc, html

app = Dash()
app.layout = html.Div([
    dcc.Graph(figure=fig)
])

app.run_server(debug=True, use_reloader=True)

