import bigtree as bt
import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from typing import Dict, List

def TreeNodeChip(
    node: bt.Node,
) -> dmc.Chip:
    node_path_name = f'{node.sep}'.join(node.path_name.strip(node.sep).split(node.sep)[1:])
    return dmc.Chip(
        node_path_name,
        value=node.path_name,
        variant="filled",
        size="xs"
    )

def SiteLevelChipGroup(
    level_name: str,
    level_depth: int,
    nodes: List[bt.Node],
) -> dmc.Box:
    return dmc.Stack(
        children=[
            dmc.Text(level_name, size="sm", ta="left"),
            dmc.Group(
                justify="flex-start",
                children=dmc.ChipGroup(
                    id={"type": "checklist-locations-hierarchy", "index": level_depth},
                    multiple=True,
                    persistence=True,
                    value=[node.path_name for node in nodes],
                    children=[TreeNodeChip(node) for node in nodes],
                ),
            )
        ]
    )

def SiteLevelHierarchyAccordion(
    tree: bt.Node,
    config: Dict[str, str],
) -> dmc.Accordion:
    return [
        SiteLevelChipGroup(
            level_name=config.get(
                f"sitelevel_{depth}",
                f"Level {depth}/{tree.max_depth - 1}"
            ),
            level_depth=depth,
            nodes=list(sorted(
                bt.levelorder_iter(
                    tree,
                    filter_condition=lambda node: node.depth == depth + 1
                ),
                key=lambda node: node.path_name
            )),
        )
        for depth in range(1, tree.max_depth)
    ]

def SiteLevelFilter():
    return dmc.Box(
        children=[
            dmc.Group(
                justify="space-between",
                children=[
                    dmc.Text(
                        "By Site Level",
                        size="md",
                        ta="left"
                    ),
                    dmc.Button(
                        id="site-filter-reset",
                        children="Reset",
                        color="blue",
                        w=100
                    )
                ]
            ),
            dmc.Space(h="sm"),
            dmc.Stack(
                id="site-level-filter-group",
                children=[]
            )
        ]
    )
