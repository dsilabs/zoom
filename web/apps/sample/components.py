"""
    sample components
"""

import uuid

import zoom
import zoom.html as h
import zoom.components as c



def view():

    hr = '<hr>\n'

    content = zoom.Component(

        'zoom.components.HeaderBar',
        c.HeaderBar(
            left=h.h2('HeaderBar Left'),
            right='HeaderBar right'
        ),
        hr,

        'zoom.components.spinner',
        h.div(c.spinner(), classed="clearfix", style="margin: 40px auto; width: 0;"),
        hr,

        'zoom.components.dropzone',
        c.dropzone('/sample/components'),
        hr,
    )

    return zoom.page(content, title='Components')