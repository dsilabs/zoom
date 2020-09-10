"""
    metric widget
"""

from random import randint
from uuid import uuid4

import zoom


class Metric(zoom.utils.Record):
    """Metric"""

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
        self.__dict__.update(kwargs)
        self.message = 'this is the message'
        self.description = 'Online users'
        self.uid = uuid4().hex
        self.height = '120px'
        self.point_background_color = 'silver'
        self.line_color = 'grey'
        self.fill_color = 'silver'

    @property
    def value(self):
        return self.format.format(self.data[-1])


class MetricWidget(zoom.DynamicComponent):
    """MetricWidget

    MetricWidget provides a UI for metrics.

    >>> import zoom
    >>> zoom.system.parts = zoom.Component()
    >>> zoom.system.site = zoom.sites.Site()
    >>> zoom.system.request.app = zoom.utils.Bunch(common_packages={}, packages={})
    >>> data = [100, 200, 700, 400]
    >>> labels = ['January', 'February', 'March', 'April']
    >>> metric = Metric(title='Metric One', data=data, labels=labels)
    >>> metric_widget = MetricWidget()
    >>> component = metric_widget.format(metric)

    """

    def format(self, metric):
        zoom.requires('chartjs')
        return zoom.DynamicComponent.format(self, metric=metric)
