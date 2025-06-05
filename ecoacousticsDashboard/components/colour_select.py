import dash_mantine_components as dmc

from dash import ctx, callback, Output, Input, State, html
from loguru import logger

from utils.data import dataset_loader, DatasetDecorator

# colour_select_id = f'{PAGE_NAME}-plot-options-color-by',

DEFAULT_SELECT_OPTIONS = dict(
    searchable=True,
    clearable=True,
    persistence=True
)

def ColourDropdown(
    id: str,
    default=None,
    style: Dict[str, Any] = dict(width=200),
) -> html.Div:
    dataset_select_id = 'dataset-select'
    select = dmc.Select(
        id=id,
        label="Colour by",
        value=default,
        style=style,
        **DEFAULT_SELECT_OPTIONS
    )

    @callback(
        Output(select, 'data'),
        Input(dataset_select_id, 'value'),
        State(select, 'value'),
    )
    def update(dataset_name: str, colour_by: str) -> Tuple:
        logger.debug(f"Trigger ID={ctx.triggered_id}: dataset={dataset_name} {colour_by=}")

        decorator = DatasetDecorator(dataset_loader.get_dataset(dataset_name))
        cat_options = decorator.categorical_drop_down_select_options()

        val_cat_options = [opt['value'] for opt in cat_options]

        if colour_by_cat:
            options = cat_options
            val_options = val_cat_options
        else:
            options = decorator.drop_down_select_options()
            val_options = [opt['value'] for opt in options]

        if colour_by not in val_options:
            colour_by = None

        return options

    return component
