"""
    zoom.instances

    Mananage zoom instances
"""

import os

import zoom


class InstanceExistsException(Exception):
    """Instance directory exists"""
    pass


class InstanceMissingException(Exception):
    """Instance directory is missing"""
    pass


class SiteProxy(zoom.utils.Bunch):
    """Site proxy"""

    def __init__(self, name, **kwargs):
        zoom.utils.Bunch.__init__(self, **kwargs)
        self.name = name

    def __repr__(self):
        return repr(self.name)


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
    >>> instance.sites == []
    True
    >>> instance.destroy()
    >>> os.path.exists(instance.path)
    False
    """

    def __init__(self, path=None):
        self.path = path or zoom.tools.zoompath('web')

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
        """a list of sites for the instance

        >>> instance = Instance()
        >>> instance.sites
        ['localhost', 'default']

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
        listdir = os.listdir
        isdir = os.path.isdir
        join = os.path.join
        path = self.sites_path
        if not path:
            msg = 'The %r directory does not exist'
            raise InstanceMissingException(msg, self.path)
        return [
            SiteProxy(name) for name in listdir(path)
            if isdir(join(path, name))
        ]

