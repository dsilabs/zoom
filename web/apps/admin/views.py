"""
    admin views
"""

from zoom.mvc import DynamicView
from zoom.component import Component
# from zoom.render import render
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
    # @property
    # def title(self):
    #     if self.name == 'Requests':
    #         return 'The number of successfully completed requests today'
    #     elif self.name == 'Authorizations':
    #         return 'The number of authorization changes made today'
    #     elif self.name == 'Errors':
    #         return 'The number of errors that have occurred today'
    #     return ''
    #

class MetricsView(DynamicView):

    @property
    def metrics(self):
        return Component(MetricView(m) for m in self.model)


class TestView(DynamicView):
    pass

def index_metrics_view(db):
    # print('index_metrics_view got called')
    return MetricsView(get_index_metrics(db))
    # return '{}'.format(Component([
    #         MetricView(('test', '/admin/users', 10)),
    #         MetricView(('test2', '/admin/users', 20)),
    #     ],
    #     '<div class="clearfix"></div>'
    # ))
    # return TestView()
