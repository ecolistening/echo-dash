from dash import dcc

DATASET_CONFIG_STORE = "dataset-config"
SITES_TREE_STORE = "sites-tree"
UMAP_FILTER_STORE = "umap-filter-store"
PLOT_DATA_STORE = "plot-data"
DOWNLOAD_DATA = "download-dataframe"
REQUEST_PLOT = "rqst-plot"
DOWNLOAD_PLOT = "download-plot"

global_store = [
    dcc.Store(id=DATASET_CONFIG_STORE),
    dcc.Store(id=SITES_TREE_STORE),
    dcc.Store(id=UMAP_FILTER_STORE),
    dcc.Store(id=PLOT_DATA_STORE),
    dcc.Download(id=DOWNLOAD_DATA),
    dcc.Store(id=REQUEST_PLOT),
    dcc.Download(id=DOWNLOAD_PLOT),
]
