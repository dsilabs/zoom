"""
    sample widgets
"""

import zoom
import zoom.html as h

from zoom.components.widgets.progress import ProgressWidget
from zoom.components.widgets.cards import Card
from zoom.components.widgets.metrics import Metric, MetricWidget

from components.widgets_layout import WidgetsLayout



class Cards(zoom.DynamicComponent):
    pass


def view():

    layout = WidgetsLayout()

    card = Card()
    cards = Cards().format(
        cards=zoom.Component(
            card.format('basic card'),
            card.format('card with title', title='Title'),
            card.format('Card with footer', footer='Footer'),
            card.format('Card with title and footer', title='Title', footer='Footer'),
        ),
    )

    progress_widgets = (
        card.format(
            ProgressWidget().format(
                10 + n*20,
                title='Metric %s' % n,
                hint='Metric %s hint' % n if n in [1,3] else ''
            )
        )
        for n in range(4)
    )
    progress = zoom.Component(
        h.h2('ProgressWidget'),
        layout.format(*progress_widgets),
    )

    metrics = [
        Metric(
            title='Pipeline',
            format='${:,.2f}',
        ),
        Metric(
            title='Inventory',
            classed='bg-gradient-info'
        ),
        Metric(
            title='Expenses',
            classed='bg-gradient-warning',
            data=[100, 200, 700, 400],
            labels=['January', 'February', 'March', 'April']
        ),
        Metric(
            title='Errors',
            classed='bg-gradient-danger'
        ),
    ]

    metric_widget = MetricWidget()
    metric_widgets = (
        card.format(metric_widget.format(metric)) for metric in metrics
    )

    metrics_section = zoom.Component(
        h.h2('MetricWidget'),
        layout.format(*metric_widgets)
    )

    return zoom.page(
        cards,
        progress,
        metrics_section,
        title='Widgets'
    )