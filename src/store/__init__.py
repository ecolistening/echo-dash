from dash import dcc

UMAP_FILTER_STORE = "umap-filter-store"

global_store = [
    dcc.Store(id="dataset-config", data={}),
    dcc.Store(id="dataset-category-orders", data={}),
    dcc.Store(id="dataset-options", data={}),
    dcc.Store(id="filter-store", storage_type="local"),
    dcc.Store(id="species-store", storage_type="local", data=[]),
    dcc.Store(id="precache"),
    dcc.Store(id="color-scheme", data="light", storage_type="local"),
    dcc.Store(id="plotly-theme", data="plotly", storage_type="local")
]
