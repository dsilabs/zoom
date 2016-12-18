# -*- coding: utf-8 -*-

"""
    zoom.server

    runs an instance of Zoom using the builtin Python WSGI server.

    >>> server = WSGIApplication()
"""

import os
import sys
from wsgiref.simple_server import make_server
from timeit import default_timer as timer

from zoom.request import Request
import zoom.middleware as middleware

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
        for module in [x for x in sys.modules.keys() if x not in init_modules]:
            del sys.modules[module]
    else:
        init_modules = sys.modules.keys()


class WSGIApplication(object):
    """a WSGI Application wrapper
    """
    # pylint: disable=too-few-public-methods
    def __init__(self, instance='.', handlers=None):
        self.handlers = handlers
        self.instance = os.path.abspath(instance)

    def __call__(self, environ, start_response):
        reset_modules()
        start_time = timer()
        request = Request(environ, self.instance, start_time)
        status, headers, content = middleware.handle(
            request,
            self.handlers,
        )
        start_response(status, headers)
        return [content]


def run(port=80, instance='.', handlers=None):
    """run using internal HTTP Server

    The instance variable is the path of the directory on the system where the
    sites folder is located. (e.g. /work/web)
    """

    the_appliation = WSGIApplication(instance, handlers)
    server = make_server('', int(port), the_appliation)
    try:
        print('serving {} on port {}'.format(instance, port))
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
    """
    os.chdir(environ.get('DOCUMENT_ROOT'))
    return WSGIApplication(instance='..')(environ, start_response)
