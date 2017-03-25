"""
    zoom.site
"""

import logging
import os

import zoom.config


DEFAULT_OWNER_URL = 'https://www.dynamic-solutions.com'

class Site(object):
    """a Zoom site"""
    # pylint: disable=too-many-instance-attributes, too-few-public-methods

    def __init__(self, request):

        self.request = request
        instance = request.instance
        name = request.domain

        site_path = request.site_path
        if os.path.exists(site_path):

            self.name = name
            self.path = site_path
            self.config = zoom.config.Config(site_path, 'site.ini')

            get = self.config.get
            self.url = get('site', 'url', '')

            self.owner_name = get('site', 'owner', 'dynamic solutions')
            self.owner_url = get('site', 'owner_url', DEFAULT_OWNER_URL)
            self.owner_email = get('site', 'owner_email', 'info@testco.com')

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

    def get_template(self, name=None):
        template = name or 'default'
        filename = os.path.join(self.theme_path, template + '.html')
        with open(filename) as reader:
            return reader.read()

    def helpers(self):
        """provide helpers"""
        return dict(
            site_name=self.name,
            site_url=self.url,
            owner_name=self.owner_name,
            owner_url=self.owner_url,
            owner_email=self.owner_email,
            theme=self.theme,
            theme_uri='/themes/' + self.theme,
        )


def site_handler(request, handler, *rest):
    """install site object"""
    request.site = Site(request)
    return handler(request, *rest)
