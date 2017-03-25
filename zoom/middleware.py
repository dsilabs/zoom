# -*- coding: utf-8 -*-

"""
    zoom.middleware

    A set of functions that can be placed between the HTTP server and
    the application layer.  These functions can provide various services
    such as content serving, caching, error trapping, security, etc..
"""

# pylint: disable=broad-except
# We sometimes catch anything that hasn't already been handled and provide a
# useful respose to the browser.  That's not usually advised but in this
# case it's what we want.

import os
import sys
import traceback
import json
import logging

import zoom.apps
from zoom.response import (
    PNGResponse,
    JPGResponse,
    CSSResponse,
    JavascriptResponse,
    HTMLResponse,
    ICOResponse,
    TextResponse,
)
import zoom.cookies
import zoom.session
import zoom.site
import zoom.templates
import zoom.user
import zoom.apps

SAMPLE_FORM = """
<form action="" id="dz_form" name="dz_form" method="POST"
    enctype="multipart/form-data">
    first name: <input name="first_name" value="" type="text">
    last name: <input name="last_name" value="" type="text">
    picture: <input name="photo" value="" type="file">
    <input style="" name="send_button" value="send" class="button"
    type="submit" id="send_button">
</form>
"""


def debug(request):
    """fake app for development purposes"""

    def format_section(title, content):
        """format a section for debugging output"""
        return '<pre>\n====== %s ======\n%s\n</pre>' % (title, repr(content))

    def formatr(title, content):
        """format a section for debugging output in raw form"""
        return '<pre>\n====== %s ======\n%s</pre>' % (title, content)

    content = []

    try:
        status = '200 OK'

        if request.module == 'wsgi':
            title = 'Hello from WSGI!'
        else:
            title = 'Hello from CGI!'

        content.extend([
            '<br>\n',
            '<img src="/themes/default/images/banner_logo.png" />\n',
            '<hr>\n',
            # '<pre>{printed_output}</pre>\n',
            '<img src="/static/zoom/images/checkmark.png" />\n',
            '<br>\n',
            title,
        ])

        # content.append(formatr('printed output', '{printed_output}'))

        content.append(formatr('test form', SAMPLE_FORM))
        content.append(formatr('request', request))
        content.append(
            formatr(
                'paths',
                json.dumps(
                    dict(
                        path=[sys.path],
                        directory=os.path.abspath('.'),
                        pathname=__file__,
                    ), indent=2
                )
            )
        )
        content.append(
            formatr(
                'environment',
                json.dumps(list(os.environ.items()), indent=2)
            )
        )

        # print('testing printed output')

        data = request.data
        if 'photo' in data and data['photo'].filename:
            content.append(format_section('filename', data['photo'].filename))
            content.append(format_section('filedata', data['photo'].value))

    except Exception:
        content = ['<pre>{}</pre>'.format(traceback.format_exc())]

    return HTMLResponse(''.join(content), status=status)


def serve_response(*path):
    """Serve up various respones with their correct response type"""
    known_types = dict(
        png=PNGResponse,
        jpg=JPGResponse,
        gif=PNGResponse,
        ico=ICOResponse,
        css=CSSResponse,
        js=JavascriptResponse,
    )
    filename = os.path.realpath(os.path.join(*path))
    logger = logging.getLogger(__name__)
    logger.debug('attempting to serve up filename %r', filename)
    if os.path.exists(filename):
        filenamel = filename.lower()
        for file_type in known_types:
            if filenamel.endswith('.' + file_type):
                data = open(filename, 'rb').read()
                response = known_types[file_type](data)
                return response
        return HTMLResponse('unknown file type')
    else:
        logger.warning('unable to serve filename %r', filename)
        relative_path = os.path.join(*path[1:])
        msg = 'file not found: {}'
        return HTMLResponse(msg.format(relative_path))


def serve_static(request, handler, *rest):
    """Serve a static file"""
    if request.path.startswith('/static/'):
        libpath = os.path.dirname(__file__)
        return serve_response(libpath, '..', 'web', 'www', request.path[1:])
    else:
        return handler(request, *rest)


def serve_themes(request, handler, *rest):
    """Serve a theme file"""
    if request.path.startswith('/themes/'):
        theme_path = os.path.join(
            request.site_path,
            request.site.themes_path,
        )
        return serve_response(theme_path, *request.route[1:])
    else:
        return handler(request, *rest)


def serve_images(request, handler, *rest):
    """Serve an image file"""
    if request.path.startswith('/images/'):
        return serve_response(request.site_path, 'content', request.path[1:])
    else:
        return handler(request, *rest)


def serve_favicon(request, handler, *rest):
    """Serve a favicon file

        >>> from zoom.request import Request
        >>> def content_handler(request, *rest):
        ...     return '200 OK', [], 'nuthin'
        >>> request = Request(
        ...     dict(REQUEST_URI='/'),
        ... )
        >>> status, _, content = serve_favicon(
        ...     request,
        ...     content_handler,
        ... )
    """
    if request.path == '/favicon.ico':
        libpath = os.path.dirname(__file__)
        return serve_response(libpath, '..', 'web', 'themes', 'default',
                              'images', request.path[1:])
    else:
        return handler(request, *rest)


def serve_html(request, handler, *rest):
    """Direct a request for an HTML page to the content app"""
    if request.path.endswith('.html'):
        request.path = '/content' + request.path[:-5]
        request.route = request.path.split('/')[1:]
        return handler(request, *rest)
    else:
        return handler(request, *rest)


def not_found(request):
    """return a 404 page"""
    msg = zoom.templates.app_not_found(request)
    response = msg.format(request.instance)
    return HTMLResponse(response, status='404 Not Found')


def trap_errors(request, handler, *rest):
    """Trap exceptions and raise a server error

        >>> def exception_handler(request, *rest):
        ...     raise Exception('error!')
        >>> def content_handler(request, *rest):
        ...     return HTMLResponse('nuthin')
        >>> request = {}
        >>> response = trap_errors(request, content_handler)
        >>> status, headers, content = response.as_wsgi()
        >>> content
        b'nuthin'
        >>> status
        '200 OK'
        >>> response = trap_errors(request, exception_handler)
        >>> status, headers, content = response.as_wsgi()
        >>> status
        '500 Internal Server Error'
        >>> 'Exception: error!' in str(content)
        True
    """
    try:
        return handler(request, *rest)
    except Exception:
        status = '500 Internal Server Error'
        return TextResponse(traceback.format_exc(), status)


def _handle(request, handler, *rest):
    """invoke the next handler"""
    return handler(request, *rest)


def handle(request, handlers=None):
    """handle a request"""
    default_handlers = (
        trap_errors,
        serve_favicon,
        serve_static,
        serve_images,
        serve_html,
        zoom.cookies.cookie_handler,
        zoom.site.site_handler,
        serve_themes,
        zoom.database.database_handler,
        zoom.session.session_handler,
        zoom.user.user_handler,
        zoom.apps.apps_handler,
        not_found,
    )
    return _handle(request, *(handlers or default_handlers))


DEBUGGING_HANDLERS = (
    trap_errors,
    serve_favicon,
    serve_static,
    serve_themes,
    serve_images,
    debug,
)
