"""
    zoom.site
"""

import logging
import os

import zoom.config


class Site(object):

    def __init__(self, directory, name):

        self.directory = self.path = directory
        self.config = zoom.config.Config(self.directory, 'site.ini')
        self.name = name

        logger = logging.getLogger(__name__)
        logger.debug('site loaded: %r', directory)


def site_handler(request, handler, *rest):
    site_directory = os.path.join(request.instance, request.domain)
    if os.path.exists(site_directory):
        logger = logging.getLogger(__name__)
        logger.debug('site directory: %r', site_directory)
        request.site = Site(site_directory, request.domain)
    else:
        raise Exception('site {!r} does not exist'.format(site_directory))

    return handler(request, *rest)
