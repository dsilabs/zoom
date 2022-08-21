"""Charts samples."""

import datetime

import zoom

from zoom.mvc import View
from zoom.charts.pivot import PivotTable, PivotWidget


class ChartSampleView(View):

    def index(self):
        db = zoom.system.site.db
        data = db('select id, app, path, status, user_id, address from log where timestamp > %s', datetime.date.today())

        my_pivot_table = PivotTable(
            data=data,
            rows=['status', 'app'],
            columns=['user_id', 'path'],
            renderer_name='Heatmap',
            aggregator_name='Count',
            values=['Party']
        )
        widget = PivotWidget()
        content = widget.format(chart=my_pivot_table)
        return zoom.page(
            '<h2>Pivot Table</h2>',
            content,
            title='Charts'
        )

view = ChartSampleView()
