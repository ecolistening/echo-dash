import dash_mantine_components as dmc
from dash import ctx, callback, Output, Input, State
from loguru import logger

from utils.data import dataset_loader, DatasetDecorator

def get_filter_drop_down(pagename, set_callback=True, select_width=200,
                            colour_default=None, colour_by_cat=False, #include_colour=True,
                            symbol_default=None, include_symbol=True,
                            row_facet_default=None, #include_row_facet=True, 
                            col_facet_default=None, #include_col_facet=True,
                        ):
    
    colour_select = dmc.Select(
        id=f'{pagename}-plot-options-color-by',
        label="Colour by",
        value=colour_default,
        searchable=True,
        clearable=True,
        style={"width": select_width},
        persistence=True
    )

    row_facet_select = dmc.Select(
        id=f'{pagename}-plot-options-rowfacet-by',
        label="Facet Rows by",
        value=row_facet_default,
        searchable=True,
        clearable=True,
        style={"width": select_width},
        persistence=True
    )
    
    col_facet_select = dmc.Select(
        id=f'{pagename}-plot-options-colfacet-by',
        label="Facet Columns by",
        value=col_facet_default,
        searchable=True,
        clearable=True,
        style={"width": select_width},
        persistence=True
    )

    if include_symbol:
        symbol_select = dmc.Select(
            id=f'{pagename}-plot-options-symbol-by',
            label="Symbolise by",
            value=symbol_default,
            searchable=True,
            clearable=True,
            style={"width": select_width},
            persistence=True
        )

        if set_callback:
            @callback(
                Output(colour_select, component_property='data'),
                Output(symbol_select, component_property='data'),
                Output(row_facet_select, component_property='data'),
                Output(col_facet_select, component_property='data'),

                Output(colour_select, component_property='value'),
                Output(symbol_select, component_property='value'),
                Output(row_facet_select, component_property='value'),
                Output(col_facet_select, component_property='value'),

                Input('dataset-select', component_property='value'),

                State(colour_select, component_property='value'),
                State(symbol_select, component_property='value'),
                State(row_facet_select, component_property='value'),
                State(col_facet_select, component_property='value'),
            )
            def update_options(dataset_name, colour_by, symbol_by, row_facet, col_facet):
                logger.debug(f"Trigger ID={ctx.triggered_id}: dataset={dataset_name} {colour_by=} {symbol_by=} {row_facet=} {col_facet=}")

                dataset = dataset_loader.get_dataset(dataset_name)
                cat_options = dataset.categorical_drop_down_select_options()

                # Ensure option is available for dataset
                val_cat_options = [opt['value'] for opt in cat_options]

                if colour_by_cat:
                    colour_options = cat_options
                    val_colour_options = val_cat_options
                else:
                    colour_options = dataset.drop_down_select_options()
                    val_colour_options = [opt['value'] for opt in colour_options]

                if colour_by not in val_colour_options: colour_by = None
                if symbol_by not in val_cat_options: symbol_by = None
                if row_facet not in val_cat_options: row_facet = None
                if col_facet not in val_cat_options: col_facet = None

                return colour_options, cat_options, cat_options, cat_options, colour_by, symbol_by, row_facet, col_facet
        
        return colour_select, symbol_select, row_facet_select, col_facet_select
    
    else:
        if set_callback:
            @callback(
                Output(colour_select, component_property='data'),
                Output(row_facet_select, component_property='data'),
                Output(col_facet_select, component_property='data'),

                Output(colour_select, component_property='value'),
                Output(row_facet_select, component_property='value'),
                Output(col_facet_select, component_property='value'),

                Input('dataset-select', component_property='value'),

                State(colour_select, component_property='value'),
                State(row_facet_select, component_property='value'),
                State(col_facet_select, component_property='value'),
            )
            def update_options(dataset_name, colour_by, row_facet, col_facet):
                logger.debug(f"Trigger ID={ctx.triggered_id}: dataset={dataset_name} {colour_by=} {row_facet=} {col_facet=}")

                decorator = DatasetDecorator(dataset_loader.get_dataset(dataset_name))
                cat_options = decorator.categorical_drop_down_select_options()

                # Ensure option is available for dataset
                val_cat_options = [opt['value'] for opt in cat_options]

                if colour_by_cat:
                    colour_options = cat_options
                    val_colour_options = val_cat_options
                else:
                    colour_options = decorator.drop_down_select_options()
                    val_colour_options = [opt['value'] for opt in colour_options]

                if colour_by not in val_colour_options: colour_by = None
                if row_facet not in val_cat_options: row_facet = None
                if col_facet not in val_cat_options: col_facet = None

                return colour_options, cat_options, cat_options, colour_by, row_facet, col_facet
        
        return colour_select, row_facet_select, col_facet_select

def get_size_slider(pagename, size_slider_default=6):
    size_slider_text = dmc.Text('Dot Size', size='sm', align='right')

    size_slider = dmc.Slider(
        id=f'{pagename}-plot-size',
        min=1, max=20, step=1, value=size_slider_default,
        marks=[
            {'value': i, 'label': f'{i}'} for i in (1,10,20)
        ],
        persistence=True
    )

    return size_slider_text, size_slider


def get_time_aggregation(pagename):
    time_aggregation = dmc.SegmentedControl(
        id=f'{pagename}-time-aggregation',
        data=[
            {'value': 'time', 'label': '15 minutes'},
            {'value': 'hour', 'label': '1 hour'},
            {'value': 'dddn', 'label': 'Dawn-Day-Dusk-Night'}
        ],
        value='dddn',
        persistence=True
    )

    return time_aggregation
