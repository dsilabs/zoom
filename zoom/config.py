"""
    zoom.config
"""

import os
import configparser
import logging


def get_config(pathname):
    if os.path.exists(pathname):
        logger = logging.getLogger(__name__)
        logger.debug('reading config: %r', pathname)
        config = configparser.ConfigParser(strict=False)
        config.read(pathname)
        return config


class Config(object):
    """config file parser
    """

    def __init__(self, directory, name, alternate=None):
        self.config_pathname = os.path.join(directory, name)
        self.config = get_config(self.config_pathname)
        parent, _ = os.path.split(directory)
        self.default_config_pathname = os.path.join(parent, 'default', name)
        self.default_config = get_config(self.default_config_pathname)

    def get(self, section, option, default=None):

        def missing_report(section, option):
            raise Exception('Unable to read [%s]%s from configs:\n%s\n%s' % (
                section, option,
                self.config_pathname,
                self.default_config_pathname,
                ))

        if self.config.has_option(section, option):
            return self.config.get(section, option)
        elif self.default_config.has_option(section, option):
            return self.default_config.get(section, option)
        elif default is not None:
            return default
        else:
            missing_report(section, option)

    def __str__(self):
        return '<Config: %s>' % repr([
            self.default_config_pathname,
            self.config_pathname
        ])
