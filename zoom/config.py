"""
    zoom.config
"""

import os
import configparser
import logging

import zoom


def get_config(pathname):
    """Read a config file into a Config parser"""
    if os.path.exists(pathname):
        logger = logging.getLogger(__name__)
        logger.debug('reading config: %r', pathname)
        config = configparser.ConfigParser(strict=False)
        config.read(pathname)
        return config


class Config(object):
    """Config file parser

    The Config class looks in two places for config settings.  First
    it looks in the site.ini file corresponding to the current site.
    If the value being read is not defined there it falls back to
    the site.ini in the default site.  If the value is not found there
    then it returns the default value provided in the parameter list.

    If no value is found it raises and exception.

    >>> from zoom.tools import zoompath
    >>> config = Config(zoompath('web/sites/default'), 'site.ini')
    >>> config.get('site', 'name')
    'ZOOM'

    >>> config.get('site', 'value_missing', 'Got Default!')
    'Got Default!'

    >>> missing = False
    >>> try:
    ...     config.get('site', 'value_missing')
    ... except Exception as e:
    ...     missing = True
    >>> missing
    True

    >>> config.has_option('site', 'name')
    True

    >>> config.has_option('section_missing', 'name')
    False

    >>> missing = False
    >>> try:
    ...     config.get('section_missing', 'name')
    ... except Exception as e:
    ...     missing = True
    >>> missing
    True

    >>> target = [
    ...     ('administrator_group', 'administrators'),
    ...     ('default', 'guest'),
    ...     ('developer_group', 'developers')
    ... ]
    >>> sorted(config.items('users')) == target
    True

    """

    def __init__(self, directory, name, alternate=None):
        self.config_pathname = os.path.join(directory, name)
        self.config = get_config(self.config_pathname)

        parent, _ = os.path.split(directory)
        pathname = os.path.join(parent, 'default', name)
        if not os.path.isfile(pathname):
            pathname = zoom.tools.zoompath('web', 'sites', 'default', name)
            if not os.path.isfile(pathname):
                raise Exception('Unable to find default config file %s.' % pathname)

        self.default_config_pathname = pathname
        self.default_config = get_config(self.default_config_pathname)

    def get(self, section, option, default=None):
        """Return a configuration value
        """

        def missing_report(section, option):
            """Raise an informative exception"""
            raise Exception('Unable to read [%s] %s from configs:\n%s\n%s' % (
                section, option,
                self.config_pathname,
                self.default_config_pathname,
                ))

        if self.config and self.config.has_option(section, option):
            result = self.config.get(section, option)
        elif (
                self.default_config
                and self.default_config.has_option(section, option)
            ):
            result = self.default_config.get(section, option)
        elif default is not None:
            result = default
        else:
            missing_report(section, option)

        return str(result)

    def has_option(self, section, option):
        return (
            self.config and self.config.has_option(section, option)
            or self.default_config.has_option(section, option)
        )

    def items(self, section):
        """Return a list of (name, value) tuples for each option in a section.

        Both the site config and the default sites config files are read and
        the results combined to produce the list of tuples.
        """
        result = {}
        if section in self.default_config.sections():
            result.update(self.default_config.items(section))
        if self.config and section in self.config.sections():
            result.update(self.config.items(section))
        return list(result.items())

    def __str__(self):    # pragma: no cover
        return '<Config: %s>' % repr([
            self.config_pathname,
            self.default_config_pathname,
        ])
