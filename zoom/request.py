# -*- coding: utf-8 -*-

"""
    zoom.request

    Web requsets.
"""

import os
import sys
import cgi
import json
import urllib
import uuid
from timeit import default_timer as timer

from zoom.cookies import (
    get_cookies,
    SESSION_COOKIE_NAME,
    SUBJECT_COOKIE_NAME,
)


class Webvars(object):
    """Extracts parameters sent as part of the request"""

    # pylint: disable=too-few-public-methods

    def __init__(self, env=None, body=None):
        """gather query fields"""

        env = env or os.environ

        # switch to binary mode on windows systems
        # msvcrt and O_BINARY are only defined in Windows Python
        # pylint: disable=import-error
        # pylint: disable=no-member
        try:
            import msvcrt
            msvcrt.setmode(0, os.O_BINARY)  # stdin  = 0
            msvcrt.setmode(1, os.O_BINARY)  # stdout = 1
        except ImportError:
            pass

        module = env.get('wsgi.version', None) and 'wsgi' or 'cgi'

        if env.get('REQUEST_METHOD', 'GET').upper() in ['GET']:
            cgi_fields = cgi.FieldStorage(environ=env, keep_blank_values=1)
        else:
            if module == 'wsgi':
                body_stream = body
                post_env = env.copy()
                post_env['QUERY_STRING'] = ''
                keep_blanks = True
            else:
                body_stream = body
                post_env = env.copy()
                keep_blanks = 1

            cgi_fields = cgi.FieldStorage(
                fp=body_stream,
                environ=post_env,
                keep_blank_values=keep_blanks
            )

        items = {}
        for key in cgi_fields.keys():

            # ignore legacy setup
            if key == '_route':
                continue

            if type(cgi_fields[key]) == list:
                items[key] = [item.value for item in cgi_fields[key]]
            elif cgi_fields[key].filename:
                items[key] = cgi_fields[key]
            else:
                items[key] = cgi_fields[key].value
        self.__dict__.update(items)

    def __getattr__(self, name):
        return ''  # return blank for missing attributes

    def __str__(self):
        return repr(self.__dict__)

    def __repr__(self):
        return str(self)


def get_parent_dir():
    """get the directory above the current directory"""
    return os.path.split(os.path.abspath(os.getcwd()))[0]


class Request(object):
    """A web request"""

    # pylint: disable=too-few-public-methods

    def __init__(self, env=None, instance=None, start_time=None):
        self.env = env or os.environ
        self.start_time = start_time or timer()
        self.ip_address = None
        self.session_token = None
        self.server = None
        self.route = []
        self.setup(self.env, instance)

    @property
    def body(self):
        self.body_consumed = True
        return self._body

    @property
    def data(self):
        if not self.body_consumed:
            return Webvars(self.env, self._body).__dict__
        else:
            return {}

    @property
    def json_body(self):
        return json.loads(self.body.read().decode('utf-8'))

    def setup(self, env, instance=None):
        """setup the Request attributes"""

        def new_subject():
            """generate a new subject ID"""
            return uuid.uuid4().hex

        def calc_domain(host):
            """calculate just the high level domain part of the host name

            remove the port and the www. if it exists

            >>> calc_domain('www.dsilabs.ca:8000')
            'dsilabs.ca'

            >>> calc_domain('test.dsilabs.ca:8000')
            'test.dsilabs.ca'

            """
            if host:
                return host.split(':')[0].split('www.')[-1:][0]
            return ''

        self._data = None
        self._body = None
        self.body_consumed = False

        path = env.get('PATH_INFO', env.get('REQUEST_URI', '').split('?')[0])
        current_route = path != '/' and path.split('/')[1:] or []
        cookies = get_cookies(env.get('HTTP_COOKIE'))

        module = env.get('wsgi.version', None) and 'wsgi' or 'cgi'

        if module == 'wsgi':
            server = (env.get('HTTP_HOST') or '').split(':')[0]
            home = os.getcwd()
            self._body = env.get('wsgi.input')
        else:
            server = env.get('SERVER_NAME', 'localhost')
            home = os.path.dirname(env.get('SCRIPT_FILENAME', ''))
            self._body = sys.stdin

        instance = instance or get_parent_dir()
        root = os.path.join(instance, 'sites', server)
        mode = env.get('mod_wsgi.process_group', None) \
            and 'daemon' or 'embedded'

        # gather some commonly required environment variables
        attributes = dict(
            instance=instance,
            path=path,
            host=env.get('HTTP_HOST'),
            domain=calc_domain(env.get('HTTP_HOST')),
            uri=env.get('REQUEST_URI', 'index.py'),
            query=env.get('QUERY_STRING'),
            ip=env.get('REMOTE_ADDR'),  # deprecated
            ip_address=env.get('REMOTE_ADDR'),
            user=env.get('REMOTE_USER'),
            cookies=cookies,
            session_token=cookies.get(SESSION_COOKIE_NAME, None),
            subject=cookies.get(SUBJECT_COOKIE_NAME, new_subject()),
            port=env.get('SERVER_PORT'),
            root=root,
            server=server,
            script=env.get('SCRIPT_FILENAME'),
            home=home,
            agent=env.get('HTTP_USER_AGENT'),
            method=env.get('REQUEST_METHOD'),
            module=module,
            mode=mode,
            protocol=env.get('HTTPS', 'off') == 'on' and 'https' or 'http',
            referrer=env.get('HTTP_REFERER'),
            wsgi_version=env.get('wsgi.version'),
            wsgi_urlscheme=env.get('wsgi.urlscheme'),
            wsgi_multiprocess=env.get('wsgi.multiprocess'),
            wsgi_multithread=env.get('wsgi.multithread'),
            wsgi_filewrapper=env.get('wsgi.filewrapper'),
            wsgi_runonce=env.get('wsgi.runonce'),
            wsgi_errors=env.get('wsgi.errors'),
            wsgi_input=env.get('wsgi.input'),
            route=current_route,
            env=env
        )
        self.__dict__.update(attributes)

    def __str__(self):
        return '{\n%s\n}' % '\n'.join('  %s: %r' % (
            key,
            self.__dict__[key]) for key in self.__dict__
        )
