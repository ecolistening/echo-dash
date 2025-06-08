from dash import dcc

DATASET_STORE = "dataset-name"
DATASETS_STORE = "datasets"
DATASET_CONFIG_STORE = "dataset-config"
SITES_TREE_STORE = "sites-tree"

global_store = [
    dcc.Store(id=DATASET_STORE),
    dcc.Store(id=DATASETS_STORE),
    dcc.Store(id=DATASET_CONFIG_STORE),
    dcc.Store(id=SITES_TREE_STORE),
]
