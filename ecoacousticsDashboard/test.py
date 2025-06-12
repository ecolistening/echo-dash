import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Simulate sample data
timestamps = pd.date_range('2023-01-01', periods=100, freq='15min').strftime('%Y-%m-%d %H:%M')
recorders = ['rec1', 'rec2']
latitudes = [51.5, 51.51]
longitudes = [-0.12, -0.11]

# Build full dataset
data = []
for t in timestamps:
    for i, r in enumerate(recorders):
        value = np.random.rand() * 100  # simulate changing value
        data.append({
            'timestamp_str': t,
            'recorder': r,
            'latitude': latitudes[i],
            'longitude': longitudes[i],
            'value': value
        })

df = pd.DataFrame(data)

# Normalize size
df['size_norm'] = (df['value'] - df['value'].min()) / (df['value'].max() - df['value'].min()) * 40 + 10

# Initial frame
init_df = df[df['timestamp_str'] == timestamps[0]]

fig = go.Figure()

# Add initial trace
fig.add_trace(go.Scattermapbox(
    lat=init_df['latitude'],
    lon=init_df['longitude'],
    mode='markers',
    marker=dict(
        size=init_df['size_norm'],
        color=init_df['value'],
        colorscale='Viridis',
        colorbar=dict(title='Value'),
        cmin=df['value'].min(),
        cmax=df['value'].max()
    ),
    text=init_df['recorder'],
    hoverinfo='text',
    name='frame0'  # force different trace name
))

# Create frames
frames = []
for i, t in enumerate(timestamps):
    frame_df = df[df['timestamp_str'] == t]
    frames.append(go.Frame(
        name=t,
        data=[go.Scattermapbox(
            lat=frame_df['latitude'],
            lon=frame_df['longitude'],
            mode='markers',
            marker=dict(
                size=frame_df['size_norm'],
                color=frame_df['value'],
                colorscale='Viridis',
                cmin=df['value'].min(),
                cmax=df['value'].max(),
            ),
            text=frame_df['recorder'],
            hoverinfo='text',
            name=f'frame{i}',  # key: force different name per frame
            uid=str(np.random.rand())  # optional: force fresh object
        )]
    ))

fig.frames = frames

fig.update_layout(
    mapbox=dict(
        style='open-street-map',
        center=dict(lat=np.mean(latitudes), lon=np.mean(longitudes)),
        zoom=12
    ),
    updatemenus=[{
        'type': 'buttons',
        'showactive': False,
        'buttons': [{
            'label': 'Play',
            'method': 'animate',
            'args': [None, {
                'frame': {'duration': 50, 'redraw': True },
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
