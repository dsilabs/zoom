"""
    zoom.instances

    Mananage zoom instances

    Note: Experimental!
"""

import logging
import os

import zoom
from zoom.sites import SiteProxy

# The default path for instances is configurable based on an environment
# variable, which we read eagerly here to ensure we don't provide app code an
# opportunity to modify the environment first.
default_instance_path = os.environ.get('ZOOM_DEFAULT_INSTANCE')

class InstanceExistsException(Exception):
    """Instance directory exists"""
    pass


class InstanceMissingException(Exception):
    """Instance directory is missing"""
    pass


subdirs = ['sites', 'apps', 'themes']


class Instance(object):
    """Zoom Instance

    A Zoom instance is a directory containing sites, apps and
    themes.  Zoom can host multiples sites using the same
    configuration under a single Instance.

    >>> import tempfile
    >>> instance_path = os.path.join(tempfile.gettempdir(), 'fakeinstance')
    >>> instance = Instance(instance_path)
    >>> instance.create()
    >>> os.path.exists(instance.path)
    True
    >>> os.path.exists(os.path.join(instance.path, 'sites'))
    True
    >>> instance.sites == {}
    True
    >>> instance.destroy()
    >>> os.path.exists(instance.path)
    False
    """

    def __init__(self, path=None):
        # Use the provided path, the default path specified in the environment,
        # or the internal instance path.
        self.path = path or default_instance_path or \
                zoom.tools.zoompath('web')

    def create(self):
        """Create a new instance"""
        if os.path.exists(self.path):
            msg = 'The %r directory already exists'
            raise InstanceExistsException(msg, self.path)
        os.mkdir(self.path)
        for subdir in subdirs:
            os.mkdir(os.path.join(self.path, subdir))

    def destroy(self):
        """Destroy an empty instance"""
        if not os.path.exists(self.path):
            msg = 'The %r directory does not exist'
            raise InstanceMissingException(msg, self.path)
        for subdir in subdirs:
            os.rmdir(os.path.join(self.path, subdir))
        os.rmdir(self.path)

    @property
    def sites_path(self):
        """the path to the sites of the instance

        >>> instance_directory = zoom.tools.zoompath('web')
        >>> instance = Instance(instance_directory)
        >>> instance.sites_path == instance_directory + '/sites'
        True
        """
        path = os.path.join(self.path, 'sites')
        return os.path.isdir(path) and path

    @property
    def sites(self):
        """a dict of sites for the instance

        >>> instance = Instance()
        >>> print(instance.sites)
        {'localhost': Site('localhost')}

        >>> import tempfile
        >>> instance_path = os.path.join(tempfile.gettempdir(), 'fakeinstance')
        >>> instance = Instance(instance_path)
        >>> got_it = False
        >>> try:
        ...     instance.sites
        ... except InstanceMissingException:
        ...     got_it = True
        >>> got_it
        True
        """
        def get_site_proxy(path, name):
            return SiteProxy(os.path.join(path, name))

        listdir = os.listdir
        isdir = os.path.isdir
        join = os.path.join
        path = self.sites_path
        if not path:
            msg = 'The %r directory does not exist'
            raise InstanceMissingException(msg % self.path)
        return {
            name: get_site_proxy(path, name)
            for name in listdir(path)
            if name != 'default' and isdir(join(path, name))
        }

    def run_background_jobs(self):
        """Run background jobs

        Iterates through the sites in the instance and calls
        run_background_jobs on each one.

        >>> instance = Instance()
        >>> instance.run_background_jobs()
        localhost
        """
        logger = logging.getLogger(__name__)
        logger.info('running background jobs for %r',self.path)
        for name, site in sorted(self.sites.items()):
            if name != 'default':
                site.run_background_jobs()
        logger.info('finished background jobs for %r',self.path)

    def __str__(self):  # pragma: nocover
        return 'Instance %r contains %s sites:\n%s' % (
            self.path,
            len(self.sites),
            '\n'.join(
                '  ' + str(site)
                for site in sorted(
                    self.sites.values(),
                    key=lambda a: a.name
                )
            ),
        )
