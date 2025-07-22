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
    return dmc.AccordionItem(
        value=f"level_{level_depth}",
        children=[
            dmc.AccordionControl(level_name),
            dmc.AccordionPanel(
                children=dmc.Group(
                    justify="flex-start",
                    children=dmc.ChipGroup(
                        id={"type": "checklist-locations-hierarchy", "index": level_depth},
                        multiple=True,
                        persistence=True,
                        value=[node.path_name for node in nodes],
                        children=[TreeNodeChip(node) for node in nodes],
                    ),
                ),
            ),
        ],
    )

def SiteLevelHierarchyAccordion(
    tree: bt.Node,
    config: Dict[str, Dict[str, str]],
) -> dmc.Accordion:
    return dmc.Accordion(
        chevronPosition="right",
        variant="separated",
        radius="sm",
        multiple=True,
        children=[
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
        ],
    )

def SiteLevelFilter():
    return dmc.Accordion(
        chevronPosition="right",
        variant="separated",
        radius="sm",
        children=[
            dmc.AccordionItem(
                value="site-level",
                children=[
                    dmc.AccordionControl("Site Level"),
                    dmc.AccordionPanel(
                        id="site-level-filter-group",
                        children=[]
                    )
                ]
            )
        ],
    )
