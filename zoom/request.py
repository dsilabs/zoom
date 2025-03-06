# -*- coding: utf-8 -*-

"""
    zoom.request

    Web requests.
"""

import os
import sys
import cgi
import json
import logging
import platform
import uuid
import urllib
from timeit import default_timer as timer

import zoom
import zoom.utils
import zoom.cookies
import zoom.exceptions

from zoom.context import context
from zoom.profiler import SystemTimer


logger = logging.getLogger(__name__)


def make_request_id():
    """make a unique request id"""
    return uuid.uuid4().hex


def cgi_to_dict(cgi_fields):

    items = {}
    for key in cgi_fields.keys():

        save = items.__setitem__

        if isinstance(cgi_fields[key], list):
            if cgi_fields[key] and cgi_fields[key][0].filename:
                value = (key, cgi_fields[key])
            else:
                value = (key, [item.value for item in cgi_fields[key]])
        elif cgi_fields[key].filename:
            value = (key, cgi_fields[key])
        else:
            value = (key, cgi_fields[key].value)

        if '[' in key and key.endswith(']'):
            # some libs append an index myfield[0], we choose to put them
            # in a list
            param = key[:key.find('[')]
            items.setdefault(param, [])
            save = items[param].append
            value = value[1:]

        save(*value)

    return items


def get_web_vars(env):
    """return web parameters as a dict"""

    get = env.get
    module = get('wsgi.version', None) and 'wsgi' or 'cgi'
    method = get('REQUEST_METHOD')

    if method not in ('GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'PATCH'):
        logger.warning('ignoring unsupported HTTP method %r', method)
        return {}

    if method in ('GET', 'HEAD'):
        cgi_fields = cgi.FieldStorage(environ=env, keep_blank_values=1)

    else:
        post_env = env.copy()
        if module == 'wsgi':
            body_stream = get('wsgi.input')
        else:
            body_stream = sys.stdin

        cgi_fields = cgi.FieldStorage(
            fp=body_stream,
            environ=post_env,
            keep_blank_values=True
        )

    return cgi_to_dict(cgi_fields)


def get_parent_dir():
    """get the directory above the current directory"""
    return os.path.split(os.path.abspath(os.getcwd()))[0]


def get_library_instance():
    """get the location of the library instance

    If the user doesn't provide an instance whith which to
    run the server then the request assumes the user wants
    to run using the built-in instance.  This is most common
    in development environments.
    """
    return zoom.tools.zoompath('zoom/_assets/web')


def get_instance(directory):
    """Figures out which instance to run

    This function will first check to see if the instance directory passed
    contains a sites directory, the miniumum bar to be considered an instance
    directory.  If so, it returns it's absolute path.  If not, it raises
    an exception.

    If no directory is passed it will attempt to locate a Zoom configuration
    file (zoom.conf or .zoomrc) which specifies the instance path.

    If that doesn't work it will use the built-in instance.
    """

    if directory:
        if os.path.isdir(os.path.join(directory, 'sites')):
            # user wants to run a specific instance overriding the config files
            instance = os.path.realpath(directory)
            logger.debug('instance: %s', instance)
            return instance
        else:
            raise zoom.exceptions.NotAnInstanceExecption(
                '%s is not an instance' % directory)

    else:
        if os.path.isdir(os.path.join('.', 'sites')):
            # or, we may be in an instance directory now
            instance = os.path.realpath('.')
            logger.debug('instance: %s', instance)
            return instance

    config_file = (
        zoom.utils.locate_config('zoom.conf') or
        zoom.utils.locate_config('.zoomrc') or
        False
    )
    logger.debug('instance config file: %s', config_file)

    if config_file:
        instance = zoom.utils.Config(config_file).get('sites', 'path', None)
    else:
        instance = None

    if not instance:
        logger.debug('no instance configured, using internal instance')
        instance = get_library_instance()

    return instance


def calc_domain(host):
    """calculate just the high level domain part of the host name

    Remove the port and the www. if it exists.

    >>> calc_domain('www.dsilabs.ca:8000')
    'dsilabs.ca'

    >>> calc_domain('test.dsilabs.ca:8000')
    'test.dsilabs.ca'

    """
    if host:
        return host.split(':')[0].split('www.')[-1:][0]
    return ''


def strim(url):
    """trim off the trailing '/' character if there is one

    >>> strim('http://localhost/')
    'http://localhost'
    """
    if url and url.endswith('/'):
        return url[:-1]
    return url



class Request(object):
    """A web request

    >>> url = 'http://localhost/test?name=joe&age=40'
    >>> request = build(url)
    >>> request.body_consumed
    False
    >>> request.data == {'age': '40', 'name': 'joe'}
    True
    >>> request.path == '/test'
    True
    >>> request.route == ['test']
    True
    >>> request.helpers()['host']
    'localhost'
    >>> request.method
    'GET'
    >>> request.port
    '80'

    >>> request = build(url)
    >>> request.body == sys.stdin
    True
    >>> request.body_consumed
    True
    >>> request.data == {}
    True
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, env=None, instance=None, start_time=None, username=None):

        self.env = env or os.environ
        get = env.get

        self.start_time = start_time or timer()
        self.username = username

        self.session_token = None
        self.session_timeout = None
        self.session = zoom.utils.Bunch()
        self.subject_token = None
        self.request_id = make_request_id()
        self.server = None
        self._body = None
        self.body_consumed = False
        self.method = get('REQUEST_METHOD')
        self.module = get('wsgi.version', None) and 'wsgi' or 'cgi'
        self.data_values = {}

        self.path = get('PATH_INFO', get('REQUEST_URI', '').split('?')[0])
        self.route = self.path != '/' and self.path.split('/')[1:] or []

        self.host = get('HTTP_HOST')
        self.domain = calc_domain(get('HTTP_HOST'))
        self.uri = get('REQUEST_URI', 'index.py')
        self.query = get('QUERY_STRING')
        self.remote_addr = get('REMOTE_ADDR')
        self.ip_address = get('HTTP_X_REAL_IP', get('REMOTE_ADDR'))
        self.remote_user = get('REMOTE_USER')
        self.cookies = zoom.cookies.get_cookies(get('HTTP_COOKIE'))
        self.port = get('SERVER_PORT')
        self.script = get('SCRIPT_FILENAME')
        self.agent = get('HTTP_USER_AGENT')
        self.protocol = get('HTTPS', 'off') == 'on' and 'https' or 'http'
        self.referrer = get('HTTP_REFERER')
        self.node = platform.node()
        self.profiler = SystemTimer(self.start_time)
        self.profiling = False
        self.abs_url = f'{self.protocol}://{self.host}'

        if self.module == 'wsgi':
            self.server = (get('HTTP_HOST') or '').split(':')[0]
            self.home = os.getcwd()
            self._body = get('wsgi.input')
        else:
            self.server = get('SERVER_NAME', 'localhost')
            self.home = os.path.dirname(get('SCRIPT_FILENAME', ''))
            self._body = sys.stdin

        self.location = strim(instance)
        logger.debug('request.location: %s', self.location)

        self.instance = get_instance(instance)
        logger.debug('request.instance: %s', self.instance)

        self.site_path = os.path.join(self.instance, 'sites', self.server)
        logger.debug('request.site_path: %s', self.site_path)

        logger.debug('request.home: %s', self.home)

    @property
    def body(self):
        """access the body in raw form"""
        if not self.body_consumed:
            logger.debug('consuming body')
            self.body_consumed = True
            if self.module == 'wsgi':
                result = self.env.get('wsgi.input')
            else:
                result = sys.stdin
            return result

    @property
    def data(self):
        """access the body as data"""
        if not self.body_consumed:
            self.body_consumed = True
            self.data_values.update(get_web_vars(self.env))
            return self.data_values
        else:
            return self.data_values

    @property
    def json_body(self):
        """access and parse the body as json"""
        return json.loads(self.body.read().decode('utf-8'))

    @property
    def elapsed(self):
        """Elapsed time"""
        return timer() - self.start_time

    @property
    def parent_path(self):
        """Path of resource parent"""
        return '/' + '/'.join(self.route[:-1])

    def helpers(self):
        """provide helpers"""
        def get_elapsed():
            """Return formatted elapsed time"""
            return '{:1.3f}'.format(self.elapsed)

        return dict(
            protocol=self.protocol,
            domain=self.domain,
            host=self.host,
            remote_address=self.ip_address,
            ip_address=self.ip_address,
            elapsed=get_elapsed,
            request_path=self.path,
            parent_path=self.parent_path,
            node=self.node,
        )

    def __str__(self):
        return zoom.utils.pretty(self)


def build(url, data=None, instance_path=None):
    """Build a request object

    >>> request = build('http://localhost')
    >>> request.path
    ''
    >>> request.host
    'localhost'

    >>> request = build('http://testsite.local:8000/info')
    >>> request.host
    'testsite.local'
    >>> request.port
    8000
    >>> request.path
    '/info'

    >>> request = build('http://localhost/hello')
    >>> request.path
    '/hello'

    >>> build('https://localhost/hello?name=Sally').data
    {'name': 'Sally'}

    """
    parsed = urllib.parse.urlparse(url)
    logger.debug(parsed)
    request = Request(
        dict(
            REQUEST_METHOD=data and 'POST' or 'GET',
            SCRIPT_NAME='index.wsgi',
            PATH_INFO=parsed.path,
            QUERY_STRING=parsed.query,
            SERVER_NAME=parsed.hostname,
            SERVER_PORT=parsed.port or '80',
            HTTP_HOST=parsed.hostname,
        ),
        instance_path,
    )
    if data:
        request.body_consumed = True
        request.data_values = data
    return request


def handler(request, handle, *rest):
    """request handler"""
    context.request = request
    zoom.system.providers = []
    return handle(request, *rest)
