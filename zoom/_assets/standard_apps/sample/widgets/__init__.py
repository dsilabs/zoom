"""
    sample widgets
"""

import zoom
import zoom.html as h

from zoom.components.widgets.progress import ProgressWidget
from zoom.components.widgets.cards import Card

from components.widgets_layout import WidgetsLayout


class Cards(zoom.DynamicComponent):
    pass


def view():

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
        WidgetsLayout().format(*progress_widgets),
    )

    return zoom.page(
        cards,
        progress,
        title='Widgets'
    )