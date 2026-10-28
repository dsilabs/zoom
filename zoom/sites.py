"""
    zoom.sites

    Updated Zoom sites module.  Eventually, the functionality
    currently in zoom.site will make it's way here.

    Note: experimental
"""

import logging
import os
from os.path import dirname

import zoom
from zoom.site import BasicSite
from zoom.background import run_background_jobs
from zoom.context import context
from zoom.exceptions import SiteMissingException

# The default path for sites is configurable based on an environment variable,
# which we read eagerly here to ensure we don't provide app code an opportunity
# to modify the environment first.
default_site_path = os.environ.get('ZOOM_DEFAULT_SITE')

logger = logging.getLogger(__name__)

class Site(BasicSite):
    """a Zoom site

    A zoom site can be completely determined by the path to the
    site directory.  That directory may contain a config file,
    apps, and other assets.  If any assets are required that are
    not found in the site directory, the system will look in
    the default site as a fallback.  Any site setttings not found
    in the site config file will be obtained from the default
    site.  Any settings not found there will rely on built-in
    defaults.

    This Site object is not to be confused with the zoom.site.Site
    object, renamed here as BasicSite, which will eventually be
    phased out as that functionality is brought into this module.

    >>> site = Site()
    >>> site.name
    'localhost'

    >>> 'users' in site.db.get_tables()
    True
    """

    def __init__(self, path=None):
        # Resolve the site path from a parameter, environment variable, or
        # logical default.
        path = path or default_site_path or \
                zoom.tools.zoompath('zoom', '_assets', 'web', 'sites', 'localhost')
        if not os.path.isdir(path):
            raise SiteMissingException('Site missing: %s' % path)

        # prepare a request adapter to satisfy the legacy api
        rest, name = os.path.split(path)
        instance = os.path.dirname(rest)
        request_adapter = zoom.utils.Bunch(
            site_path=path,
            instance=instance,
            domain=name,
            protocol='http',
            host=name,
        )

        BasicSite.__init__(self, request_adapter)
        self.instance_path = instance

        # attach the supporting database attributes
        self.db = db = zoom.database.connect_database(self.config)
        self.queues = zoom.queues.Queues(db)
        self.groups = zoom.models.Groups(db)
        self.users = zoom.models.Users(db)

    @property
    def abs_url(self):
        if context.request:
            return context.request.abs_url

    @property
    def background_jobs(self):
        """All background jobs for this site. Value is a list."""
        result = list()
        for app in self.apps:
            result.extend(app.background_jobs)
        return result

    def run_background_jobs(self):
        """Run background jobs for a site"""
        self.activate()
        for app in self.apps:
            run_background_jobs(app)

    def activate(self):
        """Activate this site in Zoom's thread-local context."""
        zoom.system.site = self


def get_site():
    """Return the currrent site object"""
    return zoom.system.site


def set_site(site=None):
    """Set the current site"""
    zoom.system.site = Site() if site is None else site


def get_db(name=None):
    """Return a db object

    Returns the current site db if no name is passed. If
    a name is passed we return the named db on the same
    connection as the site db.

    >>> set_site()
    >>> db = get_db()
    >>> rows = db('select count(*) from users')
    >>> len(rows)
    1

    """
    db = get_site().db
    if name is not None:
        return db.use(name)
    return db


def db(*args, **kwargs):
    """Run a database command and return the result"""
    return get_db()(*args, **kwargs)


def handler(request, next_handler, *rest):
    """install site object"""
    try:
        request.site = context.site = Site(request.site_path)
        request.profiler.add('site initialized')
        return next_handler(request, *rest)
    except SiteMissingException:
        logger.warning('responding with 404 for %r', request.path)
        return zoom.response.SiteNotFoundResponse(request)
