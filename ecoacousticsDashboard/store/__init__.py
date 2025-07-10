from dash import dcc

# Global caches
DATASET_CONFIG_STORE = "dataset-config"

# Global filters track the parameters of each applied filter
START_DATE_STORE = "start-date-store"
END_DATE_STORE = "end-date-store"
ACOUSTIC_FEATURE_STORE = "acoustic-feature-store"
ACOUSTIC_FEATURE_RANGE_STORE = "acoustic-feature-range-store"
ACTIVE_SITES_STORE = "active-sites-store"

# Global Filter Stores
UMAP_FILTER_STORE = "umap-filter-store"

global_store = [
    dcc.Store(id=DATASET_CONFIG_STORE),
    dcc.Store(id=UMAP_FILTER_STORE),
]
