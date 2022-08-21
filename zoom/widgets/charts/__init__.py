"""
    chart widget
"""

from random import randint
from uuid import uuid4

import zoom


class Chart(zoom.utils.Record):
    """Chart"""

    classed = 'bg-gradient-primary'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        n = 12
        today = zoom.tools.today()
        day = zoom.tools.one_day
        self.data = [1500 + randint(-100, 500) for _ in range(n)]
        self.labels = [
            '{:%Y-%m-%d}'.format((today - day * n) + i * day) for i in range(n)
        ]
        self.format = '{:,}'
        self.smooth = True
        self.type = 'line'
        self.message = 'this is the message'
        self.description = 'Online users'
        self.uid = uuid4().hex
        self.height = '120px'
        self.point_background_color = '#d0dce6'
        self.line_color = '#337ab7'
        self.fill_color = '#d0dce6'
        self.__dict__.update(kwargs)
        self.line_tension = 0.5 if self.smooth else 0.00001

    @property
    def value(self):
        return self.format.format(self.data[-1])


class ChartWidget(zoom.DynamicComponent):
    """ChartWidget

    ChartWidget provides a UI for metrics.

    >>> import zoom
    >>> zoom.system.parts = zoom.Component()
    >>> zoom.system.site = zoom.sites.Site()
    >>> zoom.system.request.app = zoom.utils.Bunch(common_packages={}, packages={})

    >>> data = [100, 200, 700, 400]
    >>> labels = ['January', 'February', 'March', 'April']
    >>> metric = Chart(title='Chart One', data=data, labels=labels)
    >>> metric_widget = ChartWidget()
    >>> component = metric_widget.format(metric)

    """

    def format(self, chart):
        """Format a Chart"""
        zoom.requires('chartjs')
        return zoom.DynamicComponent.format(self, chart=chart)

