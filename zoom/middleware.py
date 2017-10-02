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


import io
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
    RedirectResponse,
    TTFResponse,
    WOFFResponse,
    BinaryResponse,
)
import zoom.context
import zoom.cookies
import zoom.html as html
import zoom.logging
import zoom.models
import zoom.queues
import zoom.session
import zoom.site
import zoom.templates
import zoom.users
import zoom.component
import zoom.request
import zoom.profiler
from zoom.page import page
from zoom.helpers import tag_for
from zoom.forms import csrf_token as csrf_token_generator
from zoom.tools import websafe

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


def serve_redirects(request, handler, *rest):
    result = handler(request, *rest)
    if isinstance(result, RedirectResponse):
        tag = tag_for('abs_site_url')
        location = result.headers['Location'].replace(tag, request.site.abs_url)
        result.headers['Location'] = location#.encode('utf8')
        logger = logging.getLogger(__name__)
        logger.debug('redirecting to %s', location)
    return result


def serve_response(*path):
    """Serve up various respones with their correct response type"""
    known_types = dict(
        png=PNGResponse,
        jpg=JPGResponse,
        gif=PNGResponse,
        ico=ICOResponse,
        css=CSSResponse,
        js=JavascriptResponse,
        ttf=TTFResponse,
        woff=WOFFResponse,
        map=BinaryResponse,
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
        # TODO: use site.theme_path
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
        logger = logging.getLogger(__name__)
        # request.path = '/content' + request.path[:-5] + '/show'
        request.path = '/content' + request.path
        request.route = request.path.split('/')[1:]
        logger.debug('calling content app (%r, %r)', request.path, request.route)
        return handler(request, *rest)
    else:
        return handler(request, *rest)


def check_csrf(request, handler, *rest):
    """Check csrf token"""

    if request.method == 'POST' and request.site.csrf_validation:
        logger = logging.getLogger(__name__)

        form_token = request.data.pop('csrf_token', None)
        csrf_token = getattr(request.session, 'csrf_token', None)

        logger.debug('csrf session %s form %s', csrf_token, form_token)

        if csrf_token and csrf_token == form_token:
            del request.session.csrf_token
            csrf_token_generator(request.session)  # create a new one
        else:
            if csrf_token:
                logger.warning('csrf token invalid')
            else:
                logger.warning('csrf token missing')
            return RedirectResponse('/')

    return handler(request, *rest)


def not_found(request):
    """return a 404 page for site"""
    logger = logging.getLogger(__name__)
    logger.debug('responding with 404 for %r', request.path)
    response = page(zoom.templates.page_not_found).render(request)
    response.status = '404 Not Found'
    return response


def capture_stdout(request, handler, *rest):
    """Capture printed output for debugging purposes"""
    real_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        result = handler(request, *rest)
    finally:
        printed_output = sys.stdout.getvalue()
        sys.stdout.close()
        sys.stdout = real_stdout
        if 'result' in locals() and isinstance(result.content, str) and '{*stdout*}' in result.content:
            result.content = result.content.replace(
                '{*stdout*}', html.pre(websafe(printed_output)))
    logger = logging.getLogger(__name__)
    logger.debug('captured stdout')
    return result


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


def display_errors(request, handler, *rest):
    """Display errors for developers
    """
    try:
        return handler(request, *rest)
    except Exception:
        msg = traceback.format_exc()
        logger = logging.getLogger(__name__)
        logger.error(msg)
        content = """
        <h2>Exception</h2>
        {}

        <h2>Request</h2>
        <pre>{}</pre>
        """.format(
            html.pre(msg),
            str(request),
        )
        return page(
                content,
                title='Application Error'
            ).render(request)


def reset_modules(request, handler, *rest):
    """reset the modules to a known starting set

    Memorizes the modules currently in use and then removes any other
    modules when called again.  This is useful during development
    so changes can be tried without restarting the server.
    """
    # pylint: disable=global-variable-undefined, invalid-name
    # We know init_modules is undefined.  We are using it this
    # way intentionally.
    global init_modules
    if 'init_modules' in globals():
        current_modules = list(sys.modules)
        removable = [x for x in current_modules if x not in init_modules]
        for module in removable:
            del sys.modules[module]
        logger = logging.getLogger(__name__)
        logger.debug('reset_modules removed: %r', removable)
    else:
        init_modules = list(sys.modules)
    return handler(request, *rest)


def _handle(request, handler, *rest):
    """invoke the next handler"""
    return handler(request, *rest)


def handle(request, handlers=None):
    """handle a request"""
    default_handlers = (
        trap_errors,
        zoom.profiler.handler,
        zoom.request.handler,
        serve_redirects,
        serve_favicon,
        serve_static,
        serve_images,
        serve_html,
        reset_modules,
        capture_stdout,
        zoom.site.handler,
        zoom.cookies.handler,
        serve_themes,
        zoom.database.handler,
        zoom.queues.handler,
        zoom.models.handler,
        zoom.logging.handler,
        zoom.session.handler,
        zoom.component.handler,
        check_csrf,
        zoom.users.handler,
        zoom.render.handler,
        display_errors,
        zoom.apps.handler,
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
