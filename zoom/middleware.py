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
import logging
import uuid

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
from zoom.tools import websafe


def debug(request):  # pragma: no cover
    """Debugging page

    >>> type(debug(zoom.request.build('http://localhost/')))
    <class 'zoom.response.HTMLResponse'>
    """

    def section(title, content):
        """format a section for debugging output in raw form"""
        return '<h2>%s</h2>%s' % (title, content)

    pretty = zoom.utils.pretty

    content = []

    try:

        if request.module == 'wsgi':
            title = 'Hello from WSGI!'
        else:
            title = 'Hello from CGI!'

        content.extend([
            '<img src="/static/zoom/images/checkmark.png" />ZOOM Debug',
            '<hr>',
            '<h1>',
            title,
            '</h1>',
        ])

        content.extend(
            section('request', '<pre>%s</pre>' % request) +
            section(
                'paths',
                '<pre>%s</pre>' % pretty(
                    dict(
                        path=[sys.path],
                        directory=os.path.abspath('.'),
                        pathname=__file__,
                    )
                )
            ) +
            section('request.env', '<pre>%s</pre>' % pretty(request.env)) +
            section('os.env', '<pre>%s</pre>' % pretty(os.environ))
        )

    except Exception:
        content = ['<pre>{}</pre>'.format(traceback.format_exc())]

    return HTMLResponse(''.join(content))


def serve_redirects(request, handler, *rest):
    """Serves redirects

    >>> request = zoom.request.build('http://localhost')
    >>> result = serve_redirects(request, lambda a: False)
    >>> print(result)
    False

    >>> request.site = zoom.utils.Bunch(abs_url='http://localhost')
    >>> redirect_home = zoom.response.RedirectResponse('/home')
    >>> result = serve_redirects(request, lambda a: redirect_home)
    >>> print(result.headers)
    OrderedDict([('Location', '/home')])
    """
    result = handler(request, *rest)
    if isinstance(result, RedirectResponse):
        tag = tag_for('abs_site_url')
        location = result.headers['Location'].replace(tag, request.site.abs_url)
        result.headers['Location'] = location
        logger = logging.getLogger(__name__)
        logger.debug('redirecting to %s', location)
    return result


def serve_response(*path):
    """Serve up various respones with their correct response type

    >>> zoom_js = zoom.tools.zoompath('web/www/static/zoom/zoom.js')
    >>> response = serve_response(zoom_js)
    >>> isinstance(response, JavascriptResponse)
    True

    >>> zoom_path = zoom.tools.zoompath('web')
    >>> response = serve_response(zoom_path, 'www/static/zoom/nada.js')
    >>> isinstance(response, JavascriptResponse)
    False

    >>> response.content
    'file not found: www/static/zoom/nada.js'

    >>> zoom_path = zoom.tools.zoompath('web')
    >>> response = serve_response(zoom_path, 'www/static/zoom/images')
    >>> isinstance(response, JavascriptResponse)
    False

    >>> response.content
    'unknown file type'
    """
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
    """Serve a static file

    >>> url = 'http://localhost/static/zoom/zoom.js'
    >>> request = zoom.request.build(url)
    >>> result = serve_static(request, lambda a: False)
    >>> isinstance(result, JavascriptResponse)
    True

    >>> url = 'http://localhost/notstatic/zoom/zoom.js'
    >>> request = zoom.request.build(url)
    >>> result = serve_static(request, lambda a: False)
    >>> isinstance(result, JavascriptResponse)
    False
    """
    if request.path.startswith('/static/'):
        libpath = os.path.dirname(__file__)
        return serve_response(libpath, '..', 'web', 'www', request.path[1:])
    else:
        return handler(request, *rest)


def serve_themes(request, handler, *rest):
    """Serve a theme file

    >>> url = 'http://localhost/themes/default/css/style.css'
    >>> request = zoom.request.build(url)
    >>> request.site = zoom.sites.Site()
    >>> result = serve_themes(request, lambda a: False)
    >>> isinstance(result, CSSResponse)
    True

    >>> url = 'http://localhost/notthemes/default/default.html'
    >>> request = zoom.request.build(url)
    >>> serve_themes(request, lambda a: False)
    False
    """
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
    """Serve an image file

    >>> url = 'http://localhost/images/banner_logo.png'
    >>> request = zoom.request.build(url)
    >>> request.site = zoom.sites.Site()
    >>> result = serve_images(request, lambda a: False)
    >>> isinstance(result, PNGResponse)
    True

    >>> url = 'http://localhost/notimages/banner_logo.png'
    >>> request = zoom.request.build(url)
    >>> serve_images(request, lambda a: False)
    False
    """
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
    ...     dict(REQUEST_URI='/favicon.ico'),
    ... )
    >>> response = serve_favicon(
    ...     request,
    ...     content_handler,
    ... )
    >>> isinstance(response, ICOResponse)
    True

    >>> request = Request(
    ...     dict(REQUEST_URI='/'),
    ... )
    >>> status, _, content = serve_favicon(
    ...     request,
    ...     content_handler,
    ... )
    >>> content
    'nuthin'
    """
    if request.path == '/favicon.ico':
        libpath = os.path.dirname(__file__)
        return serve_response(libpath, '..', 'web', 'themes', 'default',
                              'images', request.path[1:])
    else:
        return handler(request, *rest)


def serve_html(request, handler, *rest):
    """Serve HTML from the Content app

    Direct a request for an HTML page to the content app

    >>> site = zoom.sites.Site()
    >>> url = 'http://localhost/index.html'
    >>> request = zoom.request.build(url)
    >>> request.path == '/index.html'
    True
    >>> response = serve_html(request, lambda a: None)
    >>> request.path == '/content/index.html'
    True

    >>> url = 'http://localhost/index.css'
    >>> request = zoom.request.build(url)
    >>> request.path == '/index.css'
    True
    >>> response = serve_html(request, lambda a: None)
    >>> request.path == '/index.css'
    True

    """
    if request.path.endswith('.html'):
        logger = logging.getLogger(__name__)
        # request.path = '/content' + request.path[:-5] + '/show'
        request.path = '/content' + request.path
        request.route = request.path.split('/')[1:]
        logger.debug('calling content app (%r, %r)', request.path, request.route)
        return handler(request, *rest)
    else:
        return handler(request, *rest)


def reset_csrf_token(session):
    """generate a csrf token"""
    if not hasattr(session, 'csrf_token'):
        session.csrf_token = uuid.uuid4().hex
    return session.csrf_token


def check_csrf(request, handler, *rest):
    """Check csrf token"""

    if request.method == 'POST' and request.site.csrf_validation:
        logger = logging.getLogger(__name__)

        form_token = request.data.pop('csrf_token', None)
        csrf_token = getattr(request.session, 'csrf_token', None)

        logger.debug('csrf session %s form %s', csrf_token, form_token)

        if csrf_token and csrf_token == form_token:
            del request.session.csrf_token
        else:
            if csrf_token:
                logger.warning('csrf token invalid')
            else:
                logger.warning('csrf token missing')
            return RedirectResponse('/')

    new_token = reset_csrf_token(request.session)
    zoom.render.add_helpers(dict(csrf_token=new_token))

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
                '{*stdout*}', websafe(printed_output))
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
        if not (hasattr(zoom.system, 'user') and zoom.system.user.is_admin):
            return page(zoom.templates.friendly_error).render(request)
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

    def keeper(module):
        """modules that we will not delete"""
        sigs = ['pymysql', 'pstats']
        return any(filter(module.startswith, sigs))

    logger = logging.getLogger(__name__)
    removed = []

    global init_modules
    if 'init_modules' in globals():
        current_modules = list(sys.modules)
        removable = [x for x in current_modules if x not in init_modules]
        for module in removable:
            if not keeper(module):
                del sys.modules[module]
                removed.append(module)
        logger.debug('reset_modules removed: %r', removed)
    else:
        init_modules = list(sys.modules)
    return handler(request, *rest)


def _handle(request, handler, *rest):  # pragma: no cover
    """invoke the next handler"""
    return handler(request, *rest)


def handle(request, handlers=None):  # pragma: no cover
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
    serve_images,
    debug,
)
