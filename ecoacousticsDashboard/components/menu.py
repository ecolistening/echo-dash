import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash import html
from loguru import logger

def Menu():
    pages = {m: m.split('.')[1:] for m in dash.page_registry}
    children = {}
    for p in pages:
        page = dash.page_registry[p]
        if len(pages[p]) == 0:
            logger.warning(f"Can't find page {p}")
            continue
        elif len(pages[p]) == 1:
            link = dmc.NavLink(
                label=page['name'],
                href=page["relative_path"],
            )
            children[pages[p][0]] = link
        else:
            if pages[p][0] not in children:
                link = dmc.NavLink(
                    label=pages[p][0],
                    children=[],
                )
                children[pages[p][0]] = link
            link = dmc.NavLink(
                label=page['name'],
                href=page["relative_path"],
            )
            children[pages[p][0]].children.append(link)

    logger.info(children)
    return_list = [children["home"], children["Overview"], children["Metadata"],]
    # Put groups in desired order. Adjust file name to sort individual pages within groups alphabetically
    # for group in ('home','Metadata','Overview','Diel','Seasonal'):
        # return_list.append(children[group])
    return html.Div(return_list)
