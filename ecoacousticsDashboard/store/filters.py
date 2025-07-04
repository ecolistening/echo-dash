from dash import dcc

UMAP_FILTER_STORE = "umap-filter"

stores = [
    dcc.Store(id=UMAP_FILTER_STORE),
]
