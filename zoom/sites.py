"""
    zoom.sites

    Updated Zoom sites module.  Eventually, the functionality
    currently in zoom.site will make it's way here.

    Note: experimental
"""

import os
import logging


class SiteProxy(object):
    """Site proxy"""

    def __init__(self, path):
        self.name = os.path.split(path)[-1]
        self.path = path

    def run_background_jobs(self):
        """Run background jobs

        Iterates through the apps in the site and calls
        run_background_jobs on each one.

        >>> import zoom
        >>> site_directory = zoom.tools.zoompath('web/sites/localhost')
        >>> site = SiteProxy(site_directory)
        >>> site.run_background_jobs()
        localhost
        """
        logger = logging.getLogger(__name__)
        logger.info('running background jobs for site %r', self.name)
        print(self.name)
        logger.info('finished background jobs for site %r',self.name)

    def __repr__(self):
        return 'Site(%r)' % (self.name)

