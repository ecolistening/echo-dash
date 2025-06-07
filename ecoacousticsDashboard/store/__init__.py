from dash import dcc

DATASET_STORE = "dataset-name"
DATASETS_STORE = "datasets"

global_store = [
    dcc.Store(id=DATASET_STORE),
    dcc.Store(id=DATASETS_STORE),
]
