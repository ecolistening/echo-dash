from dash import dcc

# Global caches
DATASET_CONFIG_STORE = "dataset-config"
DATASET_CATEGORY_ORDERS = "dataset-category-orders"

# Global Filter Stores
DATE_RANGE_STORE = "date-range-store"
ACOUSTIC_FEATURE_RANGE_STORE = "acoustic-feature-range-store"
UMAP_FILTER_STORE = "umap-filter-store"

global_store = [
    dcc.Store(id=DATASET_CONFIG_STORE, data={}),
    dcc.Store(id=DATASET_CATEGORY_ORDERS, data={}),
    dcc.Store(id=DATE_RANGE_STORE, data=[]),
    dcc.Store(id=ACOUSTIC_FEATURE_RANGE_STORE, data=[]),
    dcc.Store(id=UMAP_FILTER_STORE, data=[]),
]
