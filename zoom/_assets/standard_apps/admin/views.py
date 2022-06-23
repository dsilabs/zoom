"""
    admin views
"""

from zoom.mvc import DynamicView
from zoom.component import Component
from model import get_index_metrics


class PanelView(DynamicView):
    subtitle = ''


class IndexPageLayoutView(DynamicView):
    pass


class MetricView(DynamicView):

    def __init__(self, model):
        DynamicView.__init__(self)
        self.name, self.url, self.value = model

    def as_upper(self):
        return self.name.upper()

    @property
    def title(self):
        return 'tooltip'


class MetricsView(DynamicView):

    @property
    def metrics(self):
        return Component(MetricView(m) for m in self.model)


class TestView(DynamicView):
    pass

def index_metrics_view(db):
    return MetricsView(get_index_metrics(db))
