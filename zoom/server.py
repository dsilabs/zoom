# -*- coding: utf-8 -*-

"""
    zoom.server

    runs an instance of Zoom using the builtin Python WSGI server.

    >>> server = WSGIApplication()
"""

import os
import logging
import sys
from wsgiref.simple_server import make_server, WSGIRequestHandler
from timeit import default_timer as timer

from zoom.request import Request
import zoom.middleware as middleware
import zoom.utils


class ZoomWSGIRequestHandler(WSGIRequestHandler):

    logger = logging.getLogger(__name__)

    def log_message(self, fmt, *args):
        def get_host():
            return dict(getattr(self.headers, '_headers')).get('Host', '-')
        host = get_host()
        fmt = '%(host)s %(command)s %(path)s (%(client_ip)s)'
        private_call = any(t.startswith('_') for t in self.path.split('/'))
        if self.path != '/favicon.ico' and not private_call:
            log = self.logger.info
        else:
            log = self.logger.debug
        log(
            fmt,
            dict(
                self.__dict__,
                host=host,
                client_ip=self.client_address[0],
            )
        )


def reset_modules():
    """reset the modules to a known starting set

    memorizes the modules currently in use and then removes any other
    modules when called again
    """
    # pylint: disable=global-variable-undefined, invalid-name
    # Maybe a bit of a hack but we know it's undefined, that's how we're using
    # it, and this is for develoment purposes only in any case.
    global init_modules
    if 'init_modules' in globals():
        for module in [x for x in sys.modules if x not in init_modules]:
            del sys.modules[module]
    else:
        init_modules = sys.modules.keys()


class WSGIApplication(object):
    """a WSGI Application wrapper
    """
    # pylint: disable=too-few-public-methods
    def __init__(self, instance='.', handlers=None):
        self.handlers = handlers
        self.instance = instance

    def __call__(self, environ, start_response):
        reset_modules()
        start_time = timer()
        request = Request(environ, self.instance, start_time)
        response = middleware.handle(request, self.handlers)
        status, headers, content = response.as_wsgi()
        start_response(status, headers)
        return [content]


def run(port=80, instance=None, handlers=None):  # pragma: no cover
    """run using internal HTTP Server

    The instance variable is the path of the directory on the system where the
    sites folder is located. (e.g. /work/web)
    """

    the_appliation = WSGIApplication(instance, handlers)
    server = make_server('', int(port), the_appliation, handler_class=ZoomWSGIRequestHandler)
    try:
        message = zoom.utils.trim("""
         * running on http://localhost{} (press Ctrl+C to quit)
        """).format(
            port != 80 and ':{}'.format(port) or '',
        )
        print(message)
        server.serve_forever()
    except KeyboardInterrupt:
        pass


def application(environ, start_response):
    """run Zoom using external WSGI Server

    Assumes that the WSGI script is located one directory below the instance
    directory.  In an typical installation the instance directory would be
    /work/web and the WSGI script would be located in /work/web/www.

    If you need to launch from somewhere else just build a function like this
    of your own and create the WSGIApplication instance using a path of your
    choosing.

    >>> save_dir = os.getcwd()
    >>> try:
    ...     env = dict(DOCUMENT_ROOT=zoom.tools.zoompath('web', 'www'))
    ...     response = application(env, lambda a, b: None)
    ... finally:
    ...     os.chdir(save_dir)
    >>> len(response)
    1
    """
    os.chdir(environ.get('DOCUMENT_ROOT'))
    return WSGIApplication(instance='..')(environ, start_response)


def debug(environ, start_response):
    """Configuration Debugging App"""
    request = Request(environ)
    response = middleware.handle(request, middleware.DEBUGGING_HANDLERS)
    status, headers, body = response.as_wsgi()
    start_response(status, headers)
    return [body]
