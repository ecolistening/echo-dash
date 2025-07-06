from dash import dcc

DATASET_CONFIG_STORE = "dataset-config"
SITES_TREE_STORE = "sites-tree"
UMAP_FILTER_STORE = "umap-filter"

global_store = [
    dcc.Store(id=DATASET_CONFIG_STORE),
    dcc.Store(id=SITES_TREE_STORE),
    dcc.Store(id=UMAP_FILTER_STORE),
]
