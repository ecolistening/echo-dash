import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from datetime import datetime
from plotly.subplots import make_subplots

dataset = "cairngorms"
site_level_field = "location"
site = "Wood"
interval = 15
feature = "spectral centroid"
group_field = "Month"

def day_of_year_to_date(day_num, year):
    day_num.rjust(3 + len(day_num), '0')
    return datetime.strptime(year + "-" + day_num, "%Y-%j").strftime("%m-%d-%Y")

df = pd.read_parquet(f"../data/{dataset}/indices.parquet")
start_year = df.timestamp.dt.year.min()

df["Hour"] = (df.timestamp.dt.hour * 60 + df.timestamp.dt.minute) / 60
df["Day"] = df.timestamp.dt.day
df["Month"] = df.timestamp.dt.month
df["Week"] = df.timestamp.dt.isocalendar().week
df["Year Diff"] = df.timestamp.dt.year - df.timestamp.dt.year.min()
df["Day of Year"] = df.timestamp.dt.dayofyear + (df["Year Diff"] * 365)

feature_df = df[(df["feature"] == feature) & (df[site_level_field] == site)][["value", "Hour", group_field, "timestamp"]]
# NOTE: this data file must be a bit buggered, because we have dupliate timestamps when we shouldn't
feature_pivot = feature_df.drop_duplicates(['Hour', group_field]).pivot(index="Hour", columns=group_field, values="value")

# tick_params = {
#     "Hour": dict(
#         tickvals=np.arange(0, 24, 1),
#         ticktext=[f"{h:02d}:00" for h in np.arange(0, 24, 1)],
#     ),
# }

fig = go.Figure()
fig.add_trace(go.Contour(
    name=f"{site} Daily Patterns",
    x=feature_pivot.index,
    y=feature_pivot.columns,
    z=feature_pivot.to_numpy().T,
    colorscale='Plasma',
    colorbar=dict(
        title=feature,
        titleside="right",
        tickformat="~s",
    )
))

month_map = {
    "Month": {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December"
    }
}

fig.update_layout(
    title=dataset + "/" + site,
    height=600,
    width=1200,
    yaxis=dict(
        title=dict(text=group_field),
        tickfont=dict(size=10),
        tickvals=np.arange(feature_df[group_field].min(), feature_df[group_field].max(), 1),
        ticktext=[month_map[group_field][field] for field in np.arange(feature_df[group_field].min(), feature_df[group_field].max(), 1)]
        # ticktext=[day_of_year_to_date(str((day % 365) + 1), str(start_year + (day // 365))) for day in np.arange(feature_df["Day"].min(), feature_df["Day"].max(), 1)],
    ),
    xaxis=dict(
        title=dict(text="Time"),
        tickfont=dict(size=10),
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

