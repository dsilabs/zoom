"""
    metric widget

    a widget that displays a single number
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
        self.point_background_color = '#d0dce6'
        self.line_color = '#337ab7'
        self.fill_color = '#d0dce6'

    @property
    def value(self):
        return self.format.format(self.data[-1])


class MetricWidget(zoom.DynamicComponent):
    """MetricWidget

    MetricWidget provides a basic metric view.

    """

    def __call__(self, *args, **kwargs):
        return self.format(*args, **kwargs)
