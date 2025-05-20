import plotly.express as px
import pandas as pd

dataset = "sounding out"
feature = "spectral centroid"

df = pd.read_parquet(f"../data/{dataset}/indices.parquet").merge(
    pd.read_parquet(f"../data/{dataset}/locations.parquet"),
    left_on="site",
    right_on="site",
    how="left"
)
df = df[(df.location == "KN") & (df.feature == feature)]

df = df.sort_values(by="timestamp")
df['timestamp_str'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')

time_index = pd.date_range(start=df['timestamp'].min(), end=df['timestamp'].max(), freq='15min')
full_index = pd.MultiIndex.from_product(
    [df['recorder'].unique(), time_index],
    names=['recorder', 'timestamp']
)
df_interp = df.set_index(['recorder', 'timestamp'])
df_interp = df_interp.reindex(full_index)
df_interp['value'] = (
    df_interp
    .groupby(level=0)  # level 0 is 'recorder'
    .apply(lambda g: g.sort_index(level=1)['value'].interpolate(method='linear'))
    .reset_index(level=0, drop=True)  # optional cleanup of extra index
)
df_interp = df_interp.reset_index()
df_interp['timestamp_str'] = df_interp['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
df_interp['size_norm'] = (df_interp['value'] - df_interp['value'].min()) / (df_interp['value'].max() - df_interp['value'].min()) * 40 + 10

# Create the map figure
fig = px.scatter_mapbox(
    df_interp,
    lat='latitude',
    lon='longitude',
    color='value',
    size='size_norm',
    range_color=[df_interp['value'].min(), df_interp['value'].max()],
    animation_frame=df_interp["timestamp_str"],
    animation_group='recorder',
    hover_name='recorder',
    color_continuous_scale='Viridis',
    zoom=3,
    height=600,
)

# Set the layout for the map
fig.update_layout(
    mapbox=dict(
        style='open-street-map',  # You can use 'mapbox://styles/...' if you have a Mapbox token
        center=dict(lat=df_interp.latitude.mean(), lon=df_interp.longitude.mean()),
        zoom=14,
    ),
    margin={"r":0,"t":0,"l":0,"b":0},
    updatemenus=[{
        'type': 'buttons',
        'showactive': False,
        'buttons': [{
            'label': 'Play',
            'method': 'animate',
            'args': [None, {
                'frame': {'duration': 100, 'redraw': True },
                'fromcurrent': True,
                'transition': {'duration': 50, 'easing': 'linear'}
            }]
        }, {
            'label': 'Pause',
            'method': 'animate',
            'args': [[None], {
                'frame': {'duration': 0, 'redraw': False},
                'mode': 'immediate',
                'transition': {'duration': 0}
            }]
        }]
    }]
)

fig.show()
