"""
    sample components
"""

import decimal
import uuid

import zoom
import zoom.html as h
import zoom.components as c


def use_common_package(message):
    zoom.requires('common_package_test')
    return zoom.Component(
        h.tag('div', message, id='common_package_test')
    )


def view():

    hr = '<hr>\n'

    data = [
        ('String', 'Integer', 'Decimal'),
        ('One', 1, decimal.Decimal(1234)),
        ('Two', 2, decimal.Decimal(2345))
    ]

    content = zoom.Component(

        'zoom.browse',
        zoom.browse(
            data,
            title='Sample Header',
            footer='sample footer'
        ),
        hr,

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

        use_common_package('not updated yet')
    )

    return zoom.page(content, title='Components')