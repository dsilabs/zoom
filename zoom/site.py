"""
    zoom.site
"""

import logging
import os

import zoom.config
import zoom.helpers


DEFAULT_OWNER_URL = 'https://www.dynamic-solutions.com'

class Site(object):
    """a Zoom site"""
    # pylint: disable=too-many-instance-attributes, too-few-public-methods

    def __init__(self, request):

        self.request = request
        instance = request.instance
        self.name = name = request.domain

        # TODO: consider getting site to do this calculation instead of reqeust
        site_path = request.site_path
        if os.path.exists(site_path):

            self.name = name
            self.path = site_path
            self.config = zoom.config.Config(site_path, 'site.ini')

            get = self.config.get
            self.url = get('site', 'url', '')
            self.title = get('site', 'name', self.name)
            self.link = zoom.helpers.link_to(self.name, self.url)
            self.csrf_validation = True
            self.tracking_id = get('site', 'tracking_id', '')

            self.owner = get('site', 'owner', 'Company Name')
            self.owner_name = get('site', 'owner', 'Company Name')
            self.owner_url = get('site', 'owner_url', DEFAULT_OWNER_URL)
            self.owner_email = get('site', 'owner_email', 'info@testco.com')
            self.admin_email = get('site', 'admin_email', 'admin@testco.com')

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

            theme_dir = get('theme', 'path', os.path.join(instance, 'themes'))
            self.themes_path = theme_dir
            self.theme = get('theme', 'name', 'default')
            self.theme_path = os.path.join(theme_dir, self.theme)

            logger = logging.getLogger(__name__)
            logger.debug('site path: %r', site_path)
            logger.debug('theme path: %r', self.theme_path)

        else:
            raise Exception('site {!r} does not exist'.format(site_path))

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
        port = (request.port not in ['80', '443']) and ':' + request.port or ''
        return '{}://{}{}'.format(
            request.protocol,
            request.server,
            port,
        )

    @property
    def apps_paths(self):
        isdir = os.path.isdir
        apps_paths = self.config.get('apps', 'path').split(';')
        return apps_paths
        return filter(isdir, apps_paths)

    def get_template(self, name=None):
        template = name or 'default'
        filename = os.path.join(self.theme_path, template + '.html')
        with open(filename) as reader:
            return reader.read()

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

def site_handler(request, handler, *rest):
    """install site object"""
    request.site = Site(request)
    return handler(request, *rest)
