"""
    instance components
"""

import datetime
import os
import platform

import zoom


def get_info_page(request):

    pathname, _ = os.path.split(__file__)

    html = zoom.load(os.path.join(pathname, 'instance.html'))
    css = zoom.load(os.path.join(pathname, 'instance.css'))

    values = dict(
        request=request,
        node=platform.node(),
        date=datetime.datetime.now(),
        version=zoom.__version__,
        css=css,
        elapsed=request.elapsed * 1000
    )

    content = html.format(**values)

    return content
