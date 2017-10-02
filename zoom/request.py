# -*- coding: utf-8 -*-

"""
    zoom.request

    Web requsets.
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

import zoom.utils
import zoom.cookies
from zoom.context import context


def make_request_id():
    """make a unique request id"""
    return uuid.uuid4().hex


def get_web_vars(env):
    """return web parameters as a dict"""

    get = env.get
    module = get('wsgi.version', None) and 'wsgi' or 'cgi'
    method = get('REQUEST_METHOD')

    if method == 'GET':
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

    items = {}
    for key in cgi_fields.keys():

        save = items.__setitem__

        if isinstance(cgi_fields[key], list):
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
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '..',
            'web'
        )
    )


def get_instance(directory):
    """figures out what instance to run"""

    logger = logging.getLogger(__name__)

    if directory and os.path.isdir(os.path.join(directory, 'sites')):
        # user wants to run a specific instance overriding the config files
        instance = os.path.abspath(directory)
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


def get_site_path(request, location):
    """get the site path

    Find the site which the system is to run for any given
    domain name / instance combination.
    """
    logger = logging.getLogger(__name__)
    exists = os.path.exists
    join = os.path.join
    split = os.path.split
    isdir = os.path.isdir

    if location:
        if exists(location):
            if isdir(location):
                if exists(join(location, 'site.ini')):
                    logger.debug('using site.ini file: %s', location)
                    return location
            elif exists(location) and split(location)[-1] == 'site.ini':
                logger.debug('using site: %s', join(location))
                return split(location)[0]

    result = os.path.join(request.instance, 'sites', request.server)
    return result


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
    >>> request.body  == sys.stdin
    True
    >>> request.body_consumed
    True
    >>> request.data == {}
    True

    >>> request = build(url)
    >>> request.body_consumed
    False
    >>> request.data == {'age': '40', 'name': 'joe'}
    True
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, env=None, instance=None, start_time=None):

        self.env = env or os.environ
        get = env.get

        self.start_time = start_time or timer()
        self.ip_address = None
        self.session_token = None
        self.session_timeout = None
        self.subject_token = None
        self.request_id = make_request_id()
        self.server = None
        self.route = []
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
        self.ip_address = get('REMOTE_ADDR')
        self.remote_user = get('REMOTE_USER')
        self.cookies = zoom.cookies.get_cookies(get('HTTP_COOKIE'))
        self.port = get('SERVER_PORT')
        self.script = get('SCRIPT_FILENAME')
        self.agent = get('HTTP_USER_AGENT')
        self.method = get('REQUEST_METHOD')
        self.protocol = get('HTTPS', 'off') == 'on' and 'https' or 'http'
        self.referrer = get('HTTP_REFERER')
        self.env = env

        if self.module == 'wsgi':
            self.server = (get('HTTP_HOST') or '').split(':')[0]
            self.home = os.getcwd()
            self._body = get('wsgi.input')
        else:
            self.server = get('SERVER_NAME', 'localhost')
            self.home = os.path.dirname(get('SCRIPT_FILENAME', ''))
            self._body = sys.stdin

        logger = logging.getLogger(__name__)

        self.location = strim(instance)
        logger.debug('request.location: %s', self.location)

        self.instance = get_instance(instance)
        logger.debug('request.instance: %s', self.instance)

        self.site_path = get_site_path(self, instance)
        logger.debug('request.site_path: %s', self.site_path)

        logger.debug('request.home: %s', self.home)

    @property
    def body(self):
        """access the body in raw form"""
        logger = logging.getLogger(__name__)
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
            node=platform.node(),
        )

    def __str__(self):
        return zoom.utils.pretty(self)


def build(url, data=None):
    """Build a request object
    """
    parsed = urllib.parse.urlparse(url)
    logger = logging.getLogger(__name__)
    logger.debug(parsed)
    request = Request(
        dict(
            REQUEST_METHOD=data and 'POST' or 'GET',
            SCRIPT_NAME='index.wsgi',
            PATH_INFO=parsed.path,
            QUERY_STRING=parsed.query,
            SERVER_NAME=parsed.hostname,
            SERVER_PORT=parsed.port or '80',
        ),
    )
    if data:
        request.body_consumed = True
        request.data = data
    return request


def handler(request, handle, *rest):
    """request handler"""
    context.request = request
    return handle(request, *rest)
