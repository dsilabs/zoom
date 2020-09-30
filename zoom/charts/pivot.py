from uuid import uuid4

import zoom

pivot_js = r'''
$(function(){
            var derivers = $.pivotUtilities.derivers;
            var renderers = $.extend(
                $.pivotUtilities.renderers,
                $.pivotUtilities.c3_renderers,
                $.pivotUtilities.d3_renderers,
                $.pivotUtilities.export_renderers
                );

            $("#%(selector)s").pivotUI(%(data)s, {
                rows: %(rows)s,
                cols: %(cols)s,
                vals: %(vals)s,
                rowOrder: "%(rowOrder)s",
                colOrder: "%(colOrder)s",
                showUI: "%(showUI)s",
                aggregators: $.pivotUtilities.aggregators,
                aggregatorName: "%(aggregatorName)s",        
                rendererName: "%(rendererName)s",
            
            });
     });
'''

css = '''
body {font-family: Verdana;}
.node {
    border: solid 1px white;
    font: 10px sans-serif;
    line-height: 12px;
    overflow: hidden;
    position: absolute;
    text-indent: 2px;
}
'''

class PivotTable(zoom.Component):
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

        self.data = data
        self.rows = rows
        self.columns = columns
        self.values = values
        self.aggregator_name = aggregator_name
        self.renderer_name = renderer_name
        self.row_order = row_order
        self.col_order = col_order
        self.show_ui = show_ui
        self.uid = uid

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

    def render(self):
        """ Return a Pivottable as a Zoom Component."""
        zoom.requires('pivottable', 'pivot-d3', 'pivot-c3')
        options = {
            'data':self.prepare_data(self.data),
            'rows': self.rows,
            'cols': self.columns,
            'vals': self.values,
            'selector': self.uid,
            'rendererName': self.renderer_name,
            'aggregatorName': self.aggregator_name,
            'rowOrder': self.row_order,
            'colOrder': self.col_order,
            'showUI': self.show_ui
        }

        js = pivot_js % options
        return zoom.DynamicComponent("<div class='pivot-table' id='%s'></div>"% self.uid, js=js, css=css)
