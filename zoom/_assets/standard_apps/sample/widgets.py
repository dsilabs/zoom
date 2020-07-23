"""
    sample widgets
"""


import zoom
import zoom.html as h

from zoom.components.widgets.progress import ProgressWidget

from components.widgets_layout import WidgetsLayout


def view():

    widgets = (
        ProgressWidget().format(n*25)
        for n in range(4)
    )

    content = zoom.Component(
        h.div('ProgressWidget'),
        WidgetsLayout().format(*widgets),
    )

    return zoom.page(content, title='Widgets')