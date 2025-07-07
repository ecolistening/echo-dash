# EchoDash Filter

Each source of filtration is setup with its own **global** store. This store contains a JSONified list of `file_id`s to **disclude**.

When adding data to the filter, simply append the list of files you want to omit from all plots.

For example, when using the lasso select within by plotly's plots. We do the following:

1. Catch all points selected and extract the `file_id`s from the `hovertext` field.
2. When a include button is pressed, we fetch all file ids not included in the list and append those to the UMAP store
3. When a disclude button is pressed, we append that list of files to the store.

Note that JSONified files should be persisted as a dictionary, where the file_id is the key and a dummy value of `1` i.e. `True` is used.
When new records are added to the filter, iterate over file_ids and add each to the store with its `file_id` as the key.
