"""
    zoom.apps

    handles requests by locating and calling a suitable app
"""

import os
import imp

from zoom.response import Response, HTMLResponse


def locate_app(request):
    """locate the app to run"""
    filename = os.path.join(request.instance, 'app.py')
    if os.path.isfile(filename):
        return request.instance


def respond(content):
    """construct a response"""
    if content:
        if isinstance(content, Response):
            result = content

        elif hasattr(content, 'render') and content.render:
            result = content.render()

        elif isinstance(content, (list, set, tuple)):
            result = HTMLResponse(''.join(content))

        elif isinstance(content, str):
            result = HTMLResponse(content)

        else:
            result = HTMLResponse('OK')

    return result.as_wsgi()


def handle(request):
    """handle a request"""

    location = locate_app(request)
    if location:
        save_dir = os.getcwd()
        try:
            os.chdir(os.path.split(location)[0])
            filename = os.path.join(location, 'app.py')
            app = getattr(imp.load_source('app', filename), 'app')
            response = app(request)
        finally:
            os.chdir(save_dir)
        return respond(response)
