"""
    zoom.apps

    handles requests by locating and calling a suitable app
"""

import os
import imp
import logging

from zoom.response import Response, HTMLResponse


def get_apps(request):
    """get list of apps installed on this site"""
    logger = logging.getLogger(__name__)
    result = []
    apps_paths = request.site.config.get('apps', 'path').split(';')

    for app_path in apps_paths:
        path = os.path.join(
            request.site.directory,
            app_path,
        )
        logger.debug('app path: %s', path)
        for app in os.listdir(path):
            filename = os.path.join(path, app, 'app.py')
            if os.path.exists(filename):
                result.append((app, filename))

    logger.debug(apps_paths)
    logger.debug('%s apps found', len(result))
    return result


def locate_app(request):
    logger = logging.getLogger(__name__)
    default_app = 'hello'
    app_name = request.route and request.route[0] or default_app
    apps_paths = request.site.config.get('apps', 'path').split(';')
    for path in apps_paths:
        app_path = os.path.abspath(os.path.join(request.site.path, path, app_name))
        logger.debug('checking %s', app_path)
        if os.path.exists(os.path.join(app_path, 'app.py')):
            logger.debug('located app %s', app_path)
            return app_path


def respond(content, request):
    """construct a response"""
    if content:
        if isinstance(content, Response):
            result = content

        elif hasattr(content, 'render') and content.render:
            result = content.render(request)

        elif isinstance(content, (list, set, tuple)):
            result = HTMLResponse(''.join(content))

        elif isinstance(content, str):
            result = HTMLResponse(content)

        else:
            result = HTMLResponse('OK')

    return result


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
        return respond(response, request)


def helpers(request):
    return dict(
        app_url='/' + (request.route and request.route[0] or ''),
    )


def apps_handler(request, handler, *rest):
    """Dispatch request to an application"""
    return handle(request) or handler(request, *rest)
