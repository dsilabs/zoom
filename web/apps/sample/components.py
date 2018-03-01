"""
    sample components
"""

import zoom
import zoom.html as h
import zoom.components as c

def view():

    content = zoom.Component(
        c.HeaderBar(
            left=h.h2('Title'),
            right='What\'s all this then?'
        ),
    )

    return zoom.page(content, title='Components')