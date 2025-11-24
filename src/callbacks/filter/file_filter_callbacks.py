from dash import callback, ctx, no_update
from dash import Output, Input, State

@callback(
    Output("umap-filter-store", "data", allow_duplicate=True),
    Input("dataset-select", "value"),
    prevent_initial_call=True,
)
def reset_file_filter_store(dataset_name):
    return {}
