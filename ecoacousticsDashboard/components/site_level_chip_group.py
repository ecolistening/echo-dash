import bigtree as bt
import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from typing import List

def path_name(node):
    return f'{node.sep}'.join(node.path_name.strip(node.sep).split(node.sep)[1:])

def SiteLevelChipGroup(
    level_name: str,
    level_depth: int,
    nodes: List[bt.Node],
) -> dmc.Box:
    return dmc.Box(
        id={ "type": "site-level-filter-group", "index": level_depth },
        children=dmc.Group(
            justify="flex-start",
            children=[
                dmc.Text(level_name, size="sm", span=True),
                dmc.ChipGroup(
                    id={ 'type': 'checklist-locations-hierarchy', 'index': level_depth },
                    multiple=True,
                    persistence=True,
                    value=[node.path_name for node in nodes],
                    children=[
                        dmc.Chip(
                            path_name(node),
                            value=node.path_name,
                            variant='filled',
                            size='xs'
                        )
                        for node in nodes
                    ],
                ),
            ]
        )
    )
