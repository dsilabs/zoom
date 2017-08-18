"""
    zoom.site
"""

import logging
import os

import zoom.apps
import zoom.config
from zoom.context import context
import zoom.helpers
from zoom.helpers import link_to


isdir = os.path.isdir
abspath = os.path.abspath
join = os.path.join
exists = os.path.exists
listdir = os.listdir

DEFAULT_OWNER_URL = 'https://www.dynamic-solutions.com'

class Site(object):
    """a Zoom site"""
    # pylint: disable=too-many-instance-attributes, too-few-public-methods

    def __init__(self, request):

        logger = logging.getLogger(__name__)

        self.request = request
        instance = request.instance
        self.name = name = request.domain
        self.__apps = None

        # TODO: consider getting site to do this calculation instead of reqeust
        site_path = request.site_path
        if os.path.exists(site_path):

            self.name = name
            self.path = site_path
            self.config = zoom.config.Config(site_path, 'site.ini')

            if not os.path.exists(os.path.join(site_path, 'site.ini')):
                raise zoom.exceptions.ConfigFileMissingException(
                    '%r missing' %
                    os.path.join(site_path, 'site.ini')
                )

            get = self.config.get
            self.url = get('site', 'url', '')
            self.title = get('site', 'name', self.name)
            self.link = '<a href="{}">{}</a>'.format(self.url, self.name)
            self.csrf_validation = True
            self.tracking_id = get('site', 'tracking_id', '')

            self.owner = get('site', 'owner', 'Company Name')
            self.owner_name = get('site', 'owner', 'Company Name')
            self.owner_url = get('site', 'owner_url', DEFAULT_OWNER_URL)
            self.owner_email = get('site', 'owner_email', 'info@testco.com')
            self.admin_email = get('site', 'admin_email', 'admin@testco.com')

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

            theme_dir = get('theme', 'path', join(instance, 'themes'))
            self.themes_path = theme_dir
            self.theme = get('theme', 'name', 'default')
            self.theme_path = os.path.join(theme_dir, self.theme)

            apps_paths = [
                abspath(join(self.path, p))
                for p in str(get('apps', 'path')).split(';')
            ]
            self.apps_paths = list(filter(isdir, apps_paths))

            self.logging = get('monitoring', 'logging', True) != '0'
            self.profiling = get('monitoring', 'profiling', True) != '0'
            self.monitor_app_database = get('monitoring', 'app_database', True) != '0'
            self.monitor_system_database = get('monitoring', 'system_database', False) != '0'

            logger.debug('site path: %r', site_path)
            logger.debug('theme path: %r', self.theme_path)

        else:
            logger.error('Site directory missing: %r', site_path)
            raise zoom.exceptions.SiteMissingException('site {!r} does not exist'.format(site_path))

    @property
    def tracker(self):
        if self.tracking_id:
            path = os.path.join(os.path.dirname(__file__), 'views', 'google_tracker.html')
            with open(path) as reader:
                return reader.read() % self.tracking_id
        return ''

    @property
    def abs_url(self):
        request = self.request
        return '{}://{}'.format(
            request.protocol,
            request.host,
        )

    @property
    def apps(self):
        """Return list of apps installed on this site"""
        if self.__apps is None:
            result = []
            names = []

            for app_path in self.apps_paths:
                path = abspath(
                    join(
                        self.path,
                        app_path,
                    )
                )
                for app in listdir(path):
                    if app not in names:
                        filename = join(path, app, 'app.py')
                        if exists(filename):
                            result.append(zoom.apps.AppProxy(app, filename, self))
                            names.append(app)
            self.__apps = result
        return self.__apps

    def get_template(self, name=None):
        template = name or 'default'
        filename = os.path.join(self.theme_path, template + '.html')
        if os.path.isfile(filename):
            with open(filename) as reader:
                return reader.read()
        else:
            logger = logging.getLogger(__name__)
            logger.warning('template %s missing', filename)
            return self.get_template('default')

    def get_owner_link(self):
        """Returns a link for the site owner."""
        if self.owner_url:
            return link_to(self.owner_name, self.owner_url)
        if self.owner_email:
            return mail_to(self.owner_name, self.owner_email)
        return name

    def helpers(self):
        """provide helpers"""
        return dict(
            site_name=self.title,
            site_url=self.url,
            abs_site_url=self.abs_url,
            owner_name=self.owner_name,
            owner_url=self.owner_url,
            owner_email=self.owner_email,
            admin_email=self.admin_email,
            theme=self.theme,
            theme_uri='/themes/' + self.theme,
            request_path=self.request.path,
            tracker=self.tracker,
        )

    def __repr__(self):
        from zoom.utils import pretty
        return '<Site {!r} {!r}>'.format(self.abs_url, self.path)

    def __str__(self):
        return zoom.utils.pretty(self)

def handler(request, handler, *rest):
    """install site object"""
    request.site = context.site = Site(request)
    request.profiler.add('site initialized')
    return handler(request, *rest)
