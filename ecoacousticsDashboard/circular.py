import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

dataset = "sounding out"
features = ["spectral entropy", "spectral flux", "bioacoustic index", "spectral centroid"]
colour_category = "location"
temporal_field = "Hour (degrees)"

months_of_year = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

tick_params = {
    "Hour (degrees)": dict(
        tickvals=np.arange(24) * 360 / 24,
        ticktext=[f"{h:02d}:00" for h in range(24)],
    ),
    "Month (degrees)": dict(
        tickvals=np.arange(12) * (360 / 12),
        ticktext=[months_of_year[h] for h in range(12)],
    ),
}

df = pd.read_parquet(f"../data/{dataset}/indices.parquet")
df["Hour (degrees)"] = ((df.timestamp.dt.hour * 60 + df.timestamp.dt.minute) * 0.25)
df["Month (degrees)"] = 360 / 12 * df.timestamp.dt.month

fig = make_subplots(
    rows=2,
    cols=2,
    specs=[[{'type': 'polar'}]*2]*2,
    subplot_titles=features,
    horizontal_spacing=0.1,
    vertical_spacing=0.1,
)

for i, feature in enumerate(features):
    row_i, col_i = i // 2, i % 2
    feature_df = df[df["feature"] == feature]
    mean_feature_df = feature_df.groupby([temporal_field, colour_category])["value"].mean().reset_index()
    for field, colour in zip(mean_feature_df[colour_category].unique(), px.colors.qualitative.Set2):
        fig.add_trace(go.Scatterpolar(
            r=mean_feature_df.loc[mean_feature_df[colour_category] == field, "value"],
            theta=mean_feature_df.loc[mean_feature_df[colour_category] == field, temporal_field],
            mode='lines',
            name=field,
            line_color=colour,
            showlegend=i == 0,
        ), row_i + 1, col_i + 1)

angularaxis_config=dict(
    rotation=90,
    direction="clockwise",
    tickmode='array',
    tickfont=dict(size=10),
    **tick_params[temporal_field],
)
for k in fig['layout']:
    if k.startswith('polar'):
        fig['layout'][k]['angularaxis'] = angularaxis_config

for ann in fig.layout.annotations:
    ann.y += 0.03

fig.update_layout(
    margin=dict(t=100, b=50, l=50, r=50),
    height=800,
    width=800,
    title_text=f"Acoustic Indices by {temporal_field}",
)
from dash import Dash, dcc, html

app = Dash()
app.layout = html.Div([
    dcc.Graph(figure=fig)
])

app.run_server(debug=True, use_reloader=False)  # Turn off reloader if inside Jupyter
