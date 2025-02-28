"""
    zoom.site
"""

import logging
import os

import zoom
import zoom.apps
import zoom.config
from zoom.context import context
import zoom.helpers
from zoom.helpers import link_to, mail_to
from zoom.utils import dedup, existing
from zoom.tools import zoompath, get_timezone, get_timezone_offset


isdir = os.path.isdir
isfile = os.path.isfile
split = os.path.split
realpath = os.path.realpath
join = os.path.join
exists = os.path.exists
listdir = os.listdir
dirname = os.path.dirname

DEFAULT_OWNER_URL = 'https://www.dynamic-solutions.com'


class ConfigSection(zoom.utils.Record):
    """site configuration section"""


class SiteConfig(object):
    """Site Config Reader

    Site configuration is managed with the site.ini files provided
    in the site directory and the default directory.

    The SiteConfig class maps unique config keywords used by the system
    into the section/name pairs used in the physical configuration files
    and provides default values in the event that no value is provided
    in the config files.

    >>> site = zoom.sites.Site()
    >>> site.config.get('site', 'name') # without SiteConfig
    'ZOOM'
    >>> conf = SiteConfig(site.config) # using SiteConfig
    >>> conf.site.get('name')
    'ZOOM'

    >>> conf.section('sessions')
    <ConfigSection {'secure_cookies': True}>

    >>> conf.section('notasection')
    <ConfigSection {}>

    >>> conf.site['name']
    'ZOOM'

    >>> conf.site.get('notaname', 'Nope')
    'Nope'

    >>> conf.site.notaname == None
    True

    >>> conf.mail.get('smtp_port')
    '587'

    >>> conf.mail.smtp_port
    '587'

    """

    defaults = {
        'site': {
            'name': 'ZOOM',
            'url': '',
            'owner_name': 'Company Name',
            'owner_email': '',
            'owner_url': DEFAULT_OWNER_URL,
            'admin_email': '',
            'register_email': '',
            'support_email': '',
        },
        'users': {
            'default': 'guest',
            'administrators_group': 'administrators',
            'developers_group': 'developers',
            'override': None,
        },
        'apps': {
            'index': 'content',
            'home': 'home',
            'login': 'login',
            'path': 'apps;../../apps',
            'include_basics': True,
        },
        'theme': {
            'name': 'default',
            'path': None,
        },
        'monitoring': {
            'profiling': False,
            'logging': False,
            'app_database': False,
            'system_database': False,
        },
        'error': {
            'users': False,
        },
        'sessions': {
            'secure_cookies': True,
        },
        'mail': {
            'smtp_host': '',
            'smtp_port': '587',
            'smtp_user': '',
            'smtp_passwd': '',
            'logo': '',
            'from_addr': '',
            'from_name': 'ZOOM Support',
            'gnupg_home': None,
        }
    }

    def __init__(self, config):
        self.config = config

    def items(self, section):
        result = {}
        result.update(self.defaults.get(section, {}))
        result.update(self.config.items(section))
        return result

    def section(self, name):
        return ConfigSection(self.items(name))

    def __getattr__(self, name):
        return self.section(name)


def locate_theme(path, name):
    """return a valid theme directory or None"""

    def valid_theme(pathname):
        for ext in ['html', 'pug', 'md']:
            if isfile(join(pathname, 'default.{}'.format(ext))):
                return True

    logger = logging.getLogger(__name__)

    if name != 'default':
        possibility = path, name
        if valid_theme(join(*possibility)):
            logger.debug('using theme %s', join(*possibility))
            return possibility

    possibility = path, 'default'
    if valid_theme(join(*possibility)):
        logger.debug('using theme %s', join(*possibility))
        return possibility

    default_path = zoompath('zoom', '_assets', 'web', 'themes')
    possibility = default_path, 'default'
    if valid_theme(join(*possibility)):
        logger.debug('using theme %s', join(*possibility))
        return possibility

class Site(object):
    """a Zoom site"""

    def __init__(self, request):

        logger = logging.getLogger(__name__)

        self.request = request
        instance = request.instance
        self.name = name = request.domain
        self.__apps = None
        self.__settings = None

        site_path = request.site_path
        if os.path.exists(site_path):

            self.name = name
            self.path = site_path
            self.config = zoom.config.Config(site_path, 'site.ini')
            self.conf = SiteConfig(self.config)

            get = self.config.get
            self.url = get('site', 'url', '')
            self.title = get('site', 'name', self.name)
            self.system = get('site', 'system', self.name)
            self.link = '<a href="{}">{}</a>'.format(self.url, self.name)
            self.csrf_validation = get('site', 'csrf_validation', True) in zoom.utils.POSITIVE
            self.timezone = get_timezone(get('site', 'timezone', 'UTC'))
            self.timezone_offset = get_timezone_offset(self.timezone)
            self.tracking_id = get('site', 'tracking_id', '')

            self.owner = get('site', 'owner', 'Company Name')
            self.owner_name = get('site', 'owner', 'Company Name')
            self.owner_url = get('site', 'owner_url', DEFAULT_OWNER_URL)
            self.owner_email = get('site', 'owner_email', 'info@testco.com')
            self.admin_email = get('site', 'admin_email', 'admin@testco.com')

            self.home_app_name = get('apps', 'home', 'home')
            self.index_app_name = get('apps', 'index', 'content')
            self.login_app_name = get('apps', 'login', '')
            self.auth_app_name = get('apps', 'authorize', '')
            self.locate_app_name = get('apps', 'locate', '')

            self.smtp_host = get('mail', 'smtp_host', '')
            self.smtp_port = get('mail', 'smtp_port', '')
            self.smtp_user = get('mail', 'smtp_user', '')
            self.smtp_passwd = get('mail', 'smtp_passwd', '')
            self.mail_logo = get('mail', 'logo', '')
            self.mail_from_addr = get('mail', 'from_addr', '')
            self.mail_from_name = get('mail', 'from_name', self.title + ' Support')
            self.mail_delivery = get('mail', 'delivery', '')

            self.guest = get('users', 'default', 'guest')
            self.administrators_group = get(
                'users', 'administrator_group', 'administrators'
            )
            self.developers_group = get(
                'users', 'developer_group', 'developers'
            )

            self.secure_cookies = (
                request.protocol == 'https' and
                get('sessions', 'secure_cookies', True)
            )

            theme_dir = realpath(get('theme', 'path', join(instance, 'themes')))
            theme = get('theme', 'name', 'default')

            # establish main theme
            location = locate_theme(theme_dir, theme)
            if not location:
                raise zoom.exceptions.ThemeTemplateMissingException(
                    'theme %r not found in %r' % (theme, theme_dir)
                )
            self.themes_path, self.theme = location
            self.theme_path = join(self.themes_path, self.theme)

            # establish default theme
            if self.theme == 'default':
                # same as main theme
                self.default_theme_path = self.theme_path
            else:
                default_location = locate_theme(theme_dir, 'default')
                if not default_location:
                    raise zoom.exceptions.ThemeTemplateMissingException(
                        'theme %r not found in %r' % (theme, theme_dir)
                    )
                self.default_theme_path = default_location[0]

            # theme options
            self.theme_comments = get('theme', 'comments', 'name')
            self.default_template = (
                get('theme', 'template', 'default')
            )

            # theme templates
            self.template_path = existing(self.theme_path, 'templates')
            self.default_template_path = existing(
                self.default_theme_path, 'templates')
            self.templates_paths = list(filter(bool, dedup([
                self.template_path,
                self.default_template_path,
                self.theme_path,
                self.default_theme_path,
                ])))
            self.templates = {}

            self.packages = zoom.packages.load(
                join(site_path, 'packages.json'),
            )

            self.apps_paths = [
                realpath(join(self.path, p))
                for p in str(get('apps', 'path')).split(';')
                if exists(realpath(join(self.path, p)))
            ]
            basic_apps = zoompath('zoom', '_assets', 'standard_apps') # deprecated
            standard_apps = zoompath('zoom', '_assets', 'web', 'apps')

            positive = zoom.utils.POSITIVE
            if self.conf.section('apps').get('include_basics') in positive:
                if standard_apps not in self.apps_paths:
                    logger.debug('including standard apps (%r)', basic_apps)
                    self.apps_paths.append(standard_apps)
                if basic_apps not in self.apps_paths:
                    logger.debug('including default apps (%r)', basic_apps)
                    self.apps_paths.append(basic_apps)
            else:
                logger.debug('not including default apps')

            self.data_path = realpath(
                get('data', 'path', join(self.path, 'data'))
            )

            self.logging = get('monitoring', 'logging', True) in positive
            self.profiling = get('monitoring', 'profiling', False) in positive
            self.monitor_app_database = get('monitoring', 'app_database', False) in positive
            self.monitor_system_database = get('monitoring', 'system_database', False) in positive

            logger.debug('instance path: %r', instance)
            logger.debug('site path: %r', site_path)
            logger.debug('site themes path: %r', self.themes_path)
            logger.debug('site theme path: %r', self.theme_path)

        else:
            logger.error('Site directory missing: %r', site_path)
            raise zoom.exceptions.SiteMissingException('site {!r} does not exist'.format(site_path))

    @property
    def settings(self):
        if not self.__settings:
            self.__settings = zoom.settings.SiteSettingsManager(self.name, self.conf)
        return self.__settings

    @property
    def tracker(self):
        """Returns a Google analytics tracker code snippet"""
        if self.tracking_id:
            path = os.path.join(os.path.dirname(__file__), 'views', 'google_tracker.html')
            with open(path) as reader:
                return reader.read() % self.tracking_id
        return ''

    @property
    def abs_url(self):
        """Calculate an absolute URL for this site"""
        request = self.request
        return '{}://{}'.format(
            request.protocol,
            request.host,
        )

    @property
    def apps(self):
        """Return list of apps available to this site"""
        if self.__apps is None:
            result = []
            names = []

            for app_path in self.apps_paths:
                path = realpath(
                    join(
                        self.path,
                        app_path,
                    )
                )
                for app in listdir(path):
                    if app not in names:
                        filename = join(path, app, 'app.py')
                        if exists(filename):
                            result.append(
                                zoom.apps.AppProxy(app, filename, self)
                            )
                            names.append(app)
            self.__apps = result
        return self.__apps

    def get_owner_link(self):
        """Returns a link for the site owner."""
        if self.owner_url:
            return link_to(self.owner_name, self.owner_url)
        if self.owner_email:
            return mail_to(self.owner_name, self.owner_email)
        return self.owner_name

    def helpers(self):
        """provide helpers"""
        return dict(
            system=self.system,
            site_name=self.title,
            site_url=self.url,
            abs_site_url=self.abs_url,
            owner_name=self.owner_name,
            owner_url=self.owner_url,
            owner_email=self.owner_email,
            owner_link=self.get_owner_link(),
            admin_email=self.admin_email,
            tracker=self.tracker,
        )

    def __repr__(self):
        return '<Site {!r} {!r}>'.format(self.abs_url, self.path)

    def __str__(self):
        return zoom.utils.pretty(self)
