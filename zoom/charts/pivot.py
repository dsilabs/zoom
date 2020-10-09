from uuid import uuid4

import zoom

class PivotTable(zoom.DynamicComponent):
    """
        Pivot Table
        See documentation on options:
        https://github.com/nicolaskruchten/pivottable/wiki/Parameters#options-object-for-pivotui
    """
    
    def __init__(self, data, rows=[], columns=[], values=[], 
                 aggregator_name='Count',
                 renderer_name='Table', row_order='key_a_to_z',
                 col_order='key_a_to_z', show_ui=True,
                 uid=uuid4().hex, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.data = self.prepare_data(data)
        self.rows = rows
        self.columns = columns
        self.values = values
        self.aggregator_name = aggregator_name
        self.renderer_name = renderer_name
        self.row_order = row_order
        self.col_order = col_order
        self.show_ui = 'true' if show_ui else 'false'
        self.selector = uid

    def prepare_data(self, data):
        """ Prepare the data for the pivottable library."""

        if hasattr(data, 'cursor'):
            # Result Object
            fields = list(col[0] for col in data.cursor.description)
            records = (list(data))
            data = [dict(zip(fields, row)) for row in records]
            # Change None value to a string for JS
            for _dict in data:
                for k, v in _dict.items():
                    if v is None:
                        _dict[k] = 'None'
        return data

class PivotWidget(zoom.DynamicComponent):
    """
    Pivot Widget

    """
    def format(self, chart):
        """Format a Chart"""
        zoom.requires('pivottable', 'pivot-d3', 'pivot-c3')
        return (
            zoom.Component("<div class='pivot-table' id='%s'></div>" % chart.selector)  +
            zoom.DynamicComponent.format(self, chart=chart)
        )