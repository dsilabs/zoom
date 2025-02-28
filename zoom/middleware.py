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

import zoom
import zoom.apps
from zoom.response import (
    PNGResponse,
    JPGResponse,
    CSSResponse,
    JavascriptResponse,
    HTMLResponse,
    ICOResponse,
    RedirectResponse,
    TTFResponse,
    WOFFResponse,
    WOFF2Response,
    BinaryResponse,
    JSONResponse,
    SVGResponse,
    MP4Response,
)
import zoom.context
import zoom.cookies
import zoom.html as html
import zoom.logging
import zoom.session
import zoom.sites
import zoom.templates
import zoom.users
import zoom.component
import zoom.request
import zoom.profiler
from zoom.page import page
from zoom.helpers import tag_for
from zoom.tools import websafe
from zoom.utils import create_csrf_token
import zoom.components.flags


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
    >>> print(list(result.headers.items()))
    [('Location', '/home')]
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

    >>> zoom_js = zoom.tools.zoompath('zoom/_assets/web/www/static/zoom/zoom.js')
    >>> response = serve_response(zoom_js)
    >>> isinstance(response, JavascriptResponse)
    True

    >>> zoom_path = zoom.tools.zoompath('zoom', '_assets', 'web')
    >>> response = serve_response(zoom_path, 'www/static/zoom/nada.js')
    >>> isinstance(response, JavascriptResponse)
    False

    >>> response.content
    "file not found: 'www/static/zoom/nada.js'"
    >>> response.status
    '404 Not Found'

    >>> zoom_path = zoom.tools.zoompath('zoom', '_assets', 'web')
    >>> response = serve_response(zoom_path, 'www/static/zoom/images')
    >>> isinstance(response, JavascriptResponse)
    False

    >>> response.content
    "unknown file type ''"
    >>> response.status
    '415 Unsupported Media Type'
    """
    known_types = dict(
        png=PNGResponse,
        jpg=JPGResponse,
        gif=PNGResponse,
        ico=ICOResponse,
        css=CSSResponse,
        sass=CSSResponse,
        js=JavascriptResponse,
        ttf=TTFResponse,
        json=JSONResponse,
        woff=WOFFResponse,
        woff2=WOFF2Response,
        map=BinaryResponse,
        svg=SVGResponse,
        mp4=MP4Response,
    )
    exists = os.path.exists
    isfile = os.path.isfile
    t = os.path.join(*path)
    pathname = os.path.realpath(t)

    logger = logging.getLogger(__name__)
    logger.debug('attempting to serve up file %r', pathname)

    if not isfile(pathname) and pathname.endswith('.css'):
        alt_pathname = pathname[:-3] + 'sass'
        logger.debug('trying alt_pathname %r', alt_pathname)
        if isfile(alt_pathname):
            pathname = alt_pathname
        else:
            raise Exception('not a file')

    if exists(pathname):
        pathnamel = pathname.lower()
        _, file_type = os.path.splitext(pathnamel)
        file_type = file_type[1:]
        response_type = known_types.get(file_type)
        if response_type:

            if file_type == 'json':

                with open(pathname, 'rb') as f:
                    data = f.read()

                # JSONResponse expects an object which it will seriaize
                # so this unserializaing / reserializing an extra step
                # which may be unnecessary.  For now, we'll use the
                # JSONResponse as designed but we may eventually want to
                # create a different response type in this case.
                data = zoom.jsonz.loads(data)

            elif file_type == 'sass':
                logger.debug('rendering sass file response %r', pathname)
                data = zoom.tools.sass(pathname).encode('utf8')

            else:
                with open(pathname, 'rb') as f:
                    data = f.read()

            return response_type(data)

        msg = 'unknown file type {!r}'.format(file_type)
        logger.warning(msg)
        return HTMLResponse(msg, status='415 Unsupported Media Type')
    else:
        logger.warning('unable to serve file %r', pathname)
        relative_path = os.path.join(*path[1:])
        msg = 'file not found: {!r}'
        return HTMLResponse(msg.format(relative_path), status='404 Not Found')


def serve_static(request, handler, *rest):
    """Serve a static file

    Static files can be served in serveral ways.  This particular
    middleware intended to be inserted into the middleware stack
    near the front before most other things.  The reason being is
    that in many cases the static files are not site specific or
    app specific but rather are shared by the entire instance.  In
    addition, many times static files require no authorization or
    special rights.  This means that in many cases static files
    can be served without knowing who is asking or what site they
    are for.  That is what this middleware does.

    This handler is mainly intended for development purposes as
    in a production evironment this type of content would typically
    be served up by the HTTP server or a caching layer.

    Note: This layer looks in four separate places for static files
    to serve.  Three related to the zoom instance, and one, as a last
    resort, from the zoom library itself.  If you are concerned
    about exposing the wrong files, be careful what you put in those
    directories or better yet, use a proxy.

    In addition to this instance wide static serving Sites and Apps
    may implement static file serving.  If they do, this layer is
    unaware of that fact.

    The locations this handler will look are relative to the zoom
    instance. They are:
        <instance>/static
        <instance>/www/static
        <instance>/../static
        zoom/web/www/static

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
        logger = logging.getLogger(__name__)
        isdir, join = os.path.isdir, os.path.join
        locations = list(filter(isdir, [
            join(request.instance, 'static'),
            join(request.instance, 'www', 'static'),
            join(request.instance, '..', 'static'),
            zoom.tools.zoompath('zoom', '_assets', 'web', 'www', 'static'),
        ]))
        for location in locations:
            pathname = join(location, *request.route[1:])
            logger.debug('looking for %r', pathname)
            if os.path.isfile(pathname):
                return serve_response(pathname)
        path = '/'.join(request.route[1:])
        logger.warning('static resource %r not found in %r', path, locations)
        msg = 'resource not found: {!r}'
        return HTMLResponse(msg.format(path), status='404 Not Found')
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
    >>> request.site = zoom.sites.Site()
    >>> serve_themes(request, lambda a: False)
    False
    """

    def existing(*path):
        """Return existing file pathname or none"""
        pathname = os.path.join(*path)
        if pathname and os.path.isfile(pathname):
            return pathname

    path = request.path[1:]
    site = request.site

    pathname = path and (
        existing(site.theme_path, path) or
        existing(site.theme_path, path[:-4]+'.sass') or
        existing(site.default_theme_path, path) or
        existing(site.default_theme_path, path[:-4]+'.sass')
    )
    if pathname:
        return serve_response(pathname)
    elif request.path.startswith('/themes/'):
        return serve_response(site.themes_path, *request.route[1:])
    else:
        return handler(request, *rest)


def serve_content_images(request, handler, *rest):
    """Serve Images from the Content app

    Direct a request for an image to the content app.

    >>> site = zoom.sites.Site()
    >>> url = 'http://localhost/images/some-image.png'
    >>> request = zoom.request.build(url)
    >>> request.path == '/images/some-image.png'
    True
    >>> response = serve_content_images(request, lambda a: None)
    >>> request.path
    '/content/images/some-image.png'

    """
    if request.path.startswith('/images/'):
        logger = logging.getLogger(__name__)
        request.path = '/content' + request.path
        request.route = request.path.split('/')[1:]
        logger.debug('calling content app for image (%r, %r)', request.path, request.route)
        return handler(request, *rest)
    else:
        return handler(request, *rest)


def serve_content_files(request, handler, *rest):
    """Serve Files from the Content app

    Direct a request for a file to the content app.

    >>> site = zoom.sites.Site()
    >>> url = 'http://localhost/files/some-file.pdf'
    >>> request = zoom.request.build(url)
    >>> request.path == '/files/some-file.pdf'
    True
    >>> response = serve_content_files(request, lambda a: None)
    >>> request.path
    '/content/files/some-file.pdf'

    """
    if request.path.startswith('/files/'):
        logger = logging.getLogger(__name__)
        request.path = '/content' + request.path
        request.route = request.path.split('/')[1:]
        logger.debug('calling content app for file (%r, %r)', request.path, request.route)
        return handler(request, *rest)
    else:
        return handler(request, *rest)


def serve_favicon(request, handler, *rest):
    """Serve a favicon file

    This function only handles the case where the favicon
    reference is /favicon.ico, as would be typical in a local
    dev environment.  For production environments the favicon
    would typically be either part of the theme or would
    be stored statically, both of which would typically be
    served up by your proxy or your web server depending on
    your config.

    If your web sever is not configured to handle static or
    themes for you, Zoom will happily serve them up via
    the serve_theme or serve_static middleware found
    elsewhere in this module.

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
        pathname = zoom.tools.zoompath(
            'zoom', '_assets', 'web', 'themes', 'default', 'images', 'favicon.ico'
        )
        return serve_response(pathname)
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
    if request.path.endswith('.html') or request.path == '/sitemap':
        logger = logging.getLogger(__name__)
        request.path = '/content' + request.path
        request.route = request.path.split('/')[1:]
        logger.debug('calling content app (%r, %r)', request.path, request.route)
        return handler(request, *rest)
    else:
        return handler(request, *rest)


def get_csrf_token(session):
    """generate a csrf token

    >>> zoom.system.request.session = session = zoom.utils.Bunch()
    >>> hasattr(session, 'csrf_token')
    False
    >>> bool(get_csrf_token(session))
    True
    >>> hasattr(session, 'csrf_token')
    False
    >>> _ = zoom.forms.form_for('test')
    >>> hasattr(session, 'csrf_token')
    True
    """
    def _get_token():
        if not hasattr(session, 'csrf_token'):
            session.csrf_token = create_csrf_token()
        return session.csrf_token
    return _get_token


def check_csrf(request, handler, *rest):
    """Check csrf token

    >>> zoom.system.providers = []
    >>> data = dict(csrf_token='1234', name='Pat')
    >>> request = zoom.request.build('http://localhost/', data)
    >>> request.session = zoom.utils.Bunch()
    >>> request.site = zoom.sites.Site()
    >>> result = check_csrf(request, lambda a: False)
    >>> isinstance(result, zoom.response.RedirectResponse)
    True

    >>> data = dict(csrf_token='1234', name='Pat')
    >>> request = zoom.request.build('http://localhost/', data)
    >>> request.session = zoom.utils.Bunch(csrf_token='4321')
    >>> request.site = zoom.sites.Site()
    >>> result = check_csrf(request, lambda a: False)
    >>> isinstance(result, zoom.response.RedirectResponse)
    True

    >>> data = dict(csrf_token='1234', name='Pat')
    >>> request = zoom.request.build('http://localhost/', data)
    >>> request.session = zoom.utils.Bunch(csrf_token='1234')
    >>> request.site = zoom.sites.Site()
    >>> result = check_csrf(request, lambda a: False)
    >>> isinstance(result, zoom.response.RedirectResponse)
    False
    """

    zoom.render.add_helpers(dict(csrf_token=get_csrf_token(request.session)))

    protected_methods = ['POST', 'PUT', 'PATCH', 'DELETE']

    if request.method in protected_methods:
        logger = logging.getLogger(__name__)

        form_token = request.data.pop('csrf_token', None)

        if request.site.csrf_validation:

            csrf_token = getattr(request.session, 'csrf_token', None)

            logger.debug('csrf session %s form %s', csrf_token, form_token)

            if not (csrf_token and csrf_token == form_token):
                if csrf_token:
                    logger.warning('invalid csrf token passed %r', form_token)
                else:
                    logger.warning('internal csrf token missing')
                return RedirectResponse('/')

    return handler(request, *rest)


def not_found(request):
    """return a 404 page for site

    >>> zoom.system.site = site = zoom.sites.Site()
    >>> site.theme = 'default'
    >>> site.title = 'My Site'
    >>> request = zoom.request.build('http://localhost')
    >>> request.app = zoom.utils.Bunch(theme='default')
    >>> request.site = site
    >>> response = not_found(request)
    >>> response.status
    '404 Not Found'
    """
    logger = logging.getLogger(__name__)
    logger.debug('responding with 404 for %r', request.path)
    response = page(zoom.templates.page_not_found).render(request)
    response.status = '404 Not Found'
    return response


def capture_stdout(request, handler, *rest):
    """Capture printed output for debugging purposes

    >>> request = zoom.request.build('http://localhost')
    >>> def get_content(request):
    ...     print('hey')
    ...     return zoom.response.HTMLResponse('I said {*stdout*}')
    >>> response = capture_stdout(request, get_content)
    >>> response.content
    'I said hey\\n'
    """
    real_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        result = handler(request, *rest)
    finally:
        printed_output = sys.stdout.getvalue()
        sys.stdout.close()
        sys.stdout = real_stdout
        content = 'result' in locals() and getattr(result, 'content', None)
        if isinstance(content, str) and '{*stdout*}' in result.content:
            result.content = result.content.replace(
                '{*stdout*}', websafe(printed_output))
    logger = logging.getLogger(__name__)
    logger.debug('captured stdout')
    return result


def cause_error(request, handler, *rest):
    """Cause an error for testing"""
    raise Exception('Something unexpected happened!')


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
    >>> 'Server Error' in str(content)
    True
    """
    try:
        return handler(request, *rest)
    except Exception as e:

        logger = logging.getLogger(__name__)
        logger.error(str(e))
        msg = traceback.format_exc()
        logger.error(msg)

        status = '500 Internal Server Error'
        return HTMLResponse(
            zoom.templates.internal_server_error_500,
            status
        )


def display_errors(request, handler, *rest):
    """Display errors for developers

    """
    try:
        return handler(request, *rest)

    except zoom.exceptions.ThemeTemplateMissingException:
        return zoom.response.HTMLResponse(
            zoom.templates.template_missing
        )

    except zoom.exceptions.UnauthorizedException:
        return page(
            'Your account privileges are not sufficient to access the requested resource.'
            ' Please contact the system administrator if you need assistance.',
            title='Permission Required',
            status='403 Forbidden'
        ).render(request)

    except Exception as e:
        msg = traceback.format_exc()
        logger = logging.getLogger(__name__)
        logger.error(msg)

        as_api = request.env.get('HTTP_ACCEPT', '') == 'application/json'
        error_status = '500 Internal Server Error'

        if not (hasattr(zoom.system, 'user') and zoom.system.user.is_admin):
            if as_api:
                return JSONResponse(
                    dict(status=error_status), status=error_status)
            content = zoom.tools.load_template(
                'friendly_error', zoom.templates.friendly_error)
            return page(content, status=error_status).render(request)

        content = """
        <h2>Exception</h2>
        {}

        <h2>Request</h2>
        <pre>{}</pre>
        """.format(
            html.pre(msg),
            str(request),
        )

        if as_api:
            return JSONResponse(
                dict(
                    message=str(e),
                    status=error_status,
                ),
                status=error_status
            )

        return page(
            content,
            title='Application Error',
            status=error_status
        ).render(request)


def reset_modules(request, handler, *rest):
    """reset the modules to a known starting set

    Memorizes the modules in use on the first round.  Then
    on every subsequent round, it removes any extra modules
    before passing the request on.

    >>> def loader(request):
    ...     import zoom.audit

    >>> def not_a_loader(request):
    ...     pass

    >>> if 'zoom.audit' in sys.modules:
    ...     del sys.modules['zoom.audit']
    >>> fresh = list(sys.modules)
    >>> reset_modules(zoom.request.build('http://localhost'), loader)
    >>> fresh == list(sys.modules)
    False

    >>> reset_modules(zoom.request.build('http://localhost'), not_a_loader)
    >>> fresh == list(sys.modules)
    True
    """
    # pylint: disable=global-variable-undefined, invalid-name
    # We know init_modules is undefined.  We are using it this
    # way intentionally.

    def keeper(module):
        """modules that we will not delete"""
        sigs = ['pymysql', 'pstats']
        return (module in init_modules) or any(filter(module.startswith, sigs))

    global init_modules
    if 'init_modules' in globals():
        removable = [x for x in list(sys.modules) if not keeper(x)]
        for module in removable:
            del sys.modules[module]
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
        serve_html,
        reset_modules,
        capture_stdout,
        zoom.sites.handler,
        zoom.cookies.handler,
        serve_themes,
        zoom.logging.handler,
        zoom.session.handler,
        zoom.impersonation.handler,
        zoom.component.handler,
        zoom.users.handler,
        zoom.render.handler,
        display_errors,
        check_csrf,
        zoom.components.flags.handle,
        serve_content_images,
        serve_content_files,
        zoom.apps.handler,
        not_found,
    )
    return _handle(request, *(handlers or default_handlers))


DEBUGGING_HANDLERS = (
    trap_errors,
    serve_favicon,
    serve_static,
    serve_content_images,
    debug,
)
