from dash import dcc

UMAP_FILTER_STORE = "umap-filter-store"
WEATHER_VARIABLE_FILTER_STORE = "weather-variable-range-store"
WEATHER_VARIABLE_CURRENT_BOUNDS = "weather-variable-current-bounds"

global_store = [
    dcc.Store(id="dataset-config", data={}),
    dcc.Store(id="dataset-category-orders", data={}),
    dcc.Store(id="dataset-options", data={}),
    dcc.Store(id="filter-store", storage_type='local'),
    dcc.Store(id=UMAP_FILTER_STORE, data={}),
    # FIXME: Ideally this should be entirely data driven, scoped by dataset,
    # where on dataset load, we render a div which contains all dataset-relevant stores
    # I made a mistake on the approach to the others (learnings...),
    # now we're just hacking this in to get it working for the moment,
    # but it shouldn't be much work to streamline this and would significantly simplify the code
    dcc.Store({"index": "temperature_2m", "type": WEATHER_VARIABLE_CURRENT_BOUNDS}, data=[]),
    dcc.Store({"index": "precipitation", "type": WEATHER_VARIABLE_CURRENT_BOUNDS}, data=[]),
    dcc.Store({"index": "rain", "type": WEATHER_VARIABLE_CURRENT_BOUNDS}, data=[]),
    dcc.Store({"index": "snowfall", "type": WEATHER_VARIABLE_CURRENT_BOUNDS}, data=[]),
    dcc.Store({"index": "wind_speed_10m", "type": WEATHER_VARIABLE_CURRENT_BOUNDS}, data=[]),
    dcc.Store({"index": "wind_speed_100m", "type": WEATHER_VARIABLE_CURRENT_BOUNDS}, data=[]),
    dcc.Store({"index": "wind_direction_10m", "type": WEATHER_VARIABLE_CURRENT_BOUNDS}, data=[]),
    dcc.Store({"index": "wind_direction_100m", "type": WEATHER_VARIABLE_CURRENT_BOUNDS}, data=[]),
    dcc.Store({"index": "wind_gusts_10m", "type": WEATHER_VARIABLE_CURRENT_BOUNDS}, data=[]),
]
