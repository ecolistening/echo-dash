import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from plotly.subplots import make_subplots
from typing import Any, Dict, List, Tuple
from utils.sketch import default_layout

CELL_HEIGHT = 40

def species_matrix(
    df: pd.DataFrame,
    axis_group: str,
    facet_col: str | None = None,
    facet_row: str | None = None,
    category_orders: Dict[str, Any] | None = None,
    color: str = "#1f77b4",
) -> go.Figure:
    #FIXME : this code is now more complicated than it needs to be, species matrix used to support multiple row
    # subplots for each row_facet category, but I couldn't get the height set correctly across subplots
    # rather than re-write, it works as is, but could do with a refactor
    if df.empty:
        return go.Figure()

    # ensure faceting works regardless of whether specified
    if axis_group is None:
        df["_axis_group"] = "All"
        axis_group = "_axis_group"
    if facet_row is None:
        df["_row_facet"] = "All"
        facet_row = "_row_facet"
    if facet_col is None:
        df["_col_facet"] = "All"
        facet_col = "_col_facet"

    counts = (
        df.groupby([*list(filter(None, [axis_group, facet_col, facet_row])), "species"])["detected"]
        .sum()
        .reset_index()
        .sort_values(by="detected", ascending=True)
    )
    species_subset = (
        counts.groupby([facet_col, facet_row])['species']
        .unique()
        .reset_index()
        .rename(columns={'species': 'species_subset'})
    )
    axis_levels = df[axis_group].unique()
    facet_levels = species_subset[[facet_col, facet_row]].drop_duplicates()
    all_combos = pd.MultiIndex.from_product(
        [axis_levels, facet_levels[facet_col].unique(), facet_levels[facet_row].unique()],
        names=[axis_group, facet_col, facet_row]
    ).to_frame(index=False).merge(
        species_subset,
        on=[facet_col, facet_row],
        how="left"
    )
    rows = []
    for _, combo in all_combos.iterrows():
        axis, col, row, universe = combo
        if isinstance(universe, float) and pd.isna(universe):
            continue
        for sp in universe:
            rows.append({
                axis_group: axis,
                facet_col: col,
                facet_row: row,
                'species': sp
            })
    expanded = pd.DataFrame(rows)
    result = expanded.merge(
        counts[[axis_group, facet_col, facet_row, 'species', 'detected']],
        on=[axis_group, facet_col, facet_row, 'species'],
        how="left"
    ).fillna({'detected': 0})
    result['detected'] = result['detected'].astype(int)
    counts = result.sort_values([axis_group, facet_col, facet_row, 'species']).reset_index(drop=True)

    z_min = 0
    z_max = max(counts["detected"].max(), 1)
    all_x = counts[axis_group].unique().tolist()

    # calculate plot heights proportional to the number of species detected
    row_categories = []
    species_per_row = []
    for row_cat in category_orders.get(facet_row, counts[facet_row].unique()):
        species_sum = counts[counts[facet_row] == row_cat].groupby(["species"])[["detected"]].sum()
        species_count_by_row = len(species_sum[species_sum != 0].dropna().index.tolist())
        if species_count_by_row > 0:
            row_categories.append(row_cat)
            species_per_row.append(species_count_by_row)
    species_per_row = np.array(species_per_row)
    col_categories = category_orders.get(facet_col, counts[facet_col].unique())

    fig = make_subplots(
        rows=len(row_categories),
        cols=len(col_categories),
        subplot_titles=[
            "<br>".join(list(filter(None, [
                str(r) if r != 'All' else None,
                str(c) if c != 'All' else None
            ])))
            for r in row_categories
            for c in col_categories
        ],
        horizontal_spacing=0.01,
    )

    for i, row_cat in enumerate(row_categories):
        row = i + 1
        # species order by sum of detections across all columns
        species_sum = (
            counts[counts[facet_row] == row_cat]
            .groupby(["species"])[["detected"]]
            .sum()
            .sort_values(by="detected", ascending=True)
        )
        species_subset = species_sum[species_sum != 0].dropna().index.tolist()
        for j, col_cat in enumerate(col_categories):
            col = j + 1
            subset = counts[
                (counts[facet_row] == row_cat) &
                (counts[facet_col] == col_cat) &
                (counts["species"].isin(species_subset))
            ]
            # ensure all species are replicated across the row
            data = (
                subset[[axis_group, facet_row, facet_col]].drop_duplicates()
                .merge(pd.DataFrame({'species': species_subset}), how='cross')
                .merge(subset, on=[axis_group, facet_row, facet_col, 'species'], how='left')
            )
            data = (
                pd.DataFrame(0, index=species_subset, columns=all_x)
                if data.empty
                else data.pivot(index="species", columns=axis_group, values="detected").fillna(0).astype(int)
            )
            # re-order according to maximum sum of occurrences
            data = data.loc[species_subset]
            fig.add_trace(
                go.Heatmap(
                    z=data.values,
                    x=data.columns,
                    y=species_subset,
                    colorscale=[[0.0, "white"], [1.0, color]],
                    text=data.values,
                    texttemplate="%{text}",
                    textfont={"size": 10, "color": "black"},
                    showscale=False,
                    zmin=z_min,
                    zmax=z_max,
                ),
                row=row, col=col,
            )

    # y-tick labels are shared across row subplots
    updates = {}
    for i in range(len(row_categories)):
        for j in range(2, len(col_categories) + 1):
            axis_num = i * len(col_categories) + j
            updates[f"yaxis{axis_num}"] = dict(showticklabels=False)

    margin = dict(l=40, r=20, t=80, b=40)
    height = CELL_HEIGHT * species_per_row.sum() + margin["t"] + margin["b"]
    fig.update_layout(default_layout(fig))
    fig.update_layout(
        margin=margin,
        height=height,
        barmode='stack',
        **updates,
    )
    return fig
