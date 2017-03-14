"""
    zoom.site
"""

import logging
import os

import zoom.config
import zoom.database


class EmptyDatabaseException(Exception):
    pass


class Site(object):

    def __init__(self, directory):

        self.directory = self.path = directory
        self.config = zoom.config.Config(self.directory, 'site.ini')
        self.db = zoom.database.connect_database(self.config)

        if self.db.get_tables() == []:
            raise EmptyDatabaseException('Database is empty')

        logger = logging.getLogger(__name__)
        logger.debug('site loaded: %r', directory)


def site_handler(request, handler, *rest):
    site_directory = os.path.join(request.instance, request.domain)
    if os.path.exists(site_directory):
        logger = logging.getLogger(__name__)
        logger.debug('site directory: %r', site_directory)
        request.site = Site(site_directory)
    else:
        raise Exception('site {!r} does not exist'.format(site_directory))

    return handler(request, *rest)
