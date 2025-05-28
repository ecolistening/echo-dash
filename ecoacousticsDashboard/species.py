import numpy as np
import pathlib
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

threshold = 0.5

df = pd.read_parquet(f"../data/sounding_out_chorus/birdnet.parquet")

df["file_name"] = df["file_path"].map(pathlib.Path).map(lambda p: p.name)
df = df[["file_name", "species"]]
df.columns = df.columns.to_flat_index().str.join('_').str.strip("species").str.strip("_")
metadata = pd.read_parquet(f"../data/sounding_out_chorus/metadata.parquet")
metadata_fields = ["file_name", "timestamp", "location"]
df = df.merge(metadata[metadata_fields], left_on="file_name", right_on="file_name", how="left")
df = df.groupby(metadata_fields).max().reset_index().melt(id_vars=metadata_fields, var_name="species_name", value_name="prob")

# different fields to group by
df["date"] = df.timestamp.dt.date
df["month"] = df.timestamp.dt.month_name()
df["hour"] = df.timestamp.dt.hour
df['date_hour'] = pd.to_datetime(df['date'].astype(str)) + pd.to_timedelta(df['hour'], unit='h')

group_by = "date_hour"

df = df[df["prob"] > 0.5].groupby(["location", "species_name", group_by])["prob"].agg(presence="count").reset_index()
df["common_name"] = df["species_name"].str.split("_").map(lambda s: s[1])

figs = []
for location in df.location.unique():
    fig = px.area(
        df[df.location == location],
        x="date_hour",
        y="presence",
        color="common_name",
        color_discrete_sequence=px.colors.qualitative.Dark24,
        title=f"Count of Species Presence Detections by Date at {location}"
    )
    figs.append(fig)

from dash import Dash, dcc, html

app = Dash()
app.layout = html.Div([
    html.Div([
        dcc.Graph(figure=fig)
    ])
    for fig in figs
])

app.run_server(debug=True, use_reloader=False)  # Turn off reloader if inside Jupyter
