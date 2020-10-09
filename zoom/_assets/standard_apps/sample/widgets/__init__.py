"""
    sample widgets
"""

import zoom
import zoom.html as h

from zoom.widgets.progress import ProgressWidget
from zoom.widgets.cards import Card
from zoom.widgets.metrics import Metric, MetricWidget
from zoom.widgets.charts import ChartWidget, Chart

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

    metric = MetricWidget()
    metrics = zoom.Component(
        h.h2('Metrics'),
        zoom.html.div(
            layout.format(
                card(metric(title='Queries', value=100, hint='numeric value')),
                card(metric(title='Items', value='1,123', hint='string')),
                card(metric(title='Revenue', value='$1,323', hint='formatted')),
                card(metric(title='Date', value=zoom.tools.today(), hint='other types')),
            ),
            classed='metrics-layout',
        ),
        css='.metrics-layout .widgets-layout { min-height: auto; }'
    )

    progress_widgets = (
        card(
            ProgressWidget().format(
                10 + n*20,
                title='Metric %s' % n,
                hint='Metric %s hint' % n if n in [1,3] else '',
            )
        )
        for n in range(4)
    )
    progress = zoom.Component(
        h.h2('Progress'),
        layout.format(*progress_widgets),
    )

    charts = [
        Chart(
            title='Pipeline',
            format='${:,.2f}',
        ),
        Chart(
            title='Inventory',
            classed='bg-gradient-info',
            smooth=False,
        ),
        Chart(
            title='Expenses',
            classed='bg-gradient-warning',
            data=[100, 200, 700, 400],
            labels=['January', 'February', 'March', 'April'],
            type='bar',
        ),
        Chart(
            title='Errors',
            classed='bg-gradient-danger',
            fill_color='#fff',
        ),
    ]
    chart_widget = ChartWidget()
    chart_widgets = (
        card(chart_widget.format(chart)) for chart in charts
    )
    charts_section = zoom.Component(
        h.h2('Charts'),
        layout.format(*chart_widgets)
    )


    return zoom.page(
        cards,
        metrics,
        progress,
        charts_section,
        title='Widgets'
    )