"""
    Test the config module
"""

import os
from os.path import join, abspath, dirname
import unittest
import logging

import zoom
from zoom.config import Config


class TestConfig(unittest.TestCase):
    """test config module"""

    # pylint: disable=R0904
    # pylint: disable=missing-docstring
    # method names are more useful for testing

    def test_create(self):
        logger = logging.getLogger('zoom.unittest.test_config')
        site_dir = zoom.tools.zoompath('zoom/_assets/web/sites/localhost')
        logger.debug(site_dir)
        config = Config(site_dir, 'site.ini')
        logger.debug(config.config_pathname)
        logger.debug(config.default_config_pathname)
        assert config
        self.assertEqual(config.config_pathname, join(site_dir, 'site.ini'))
        self.assertEqual(
            config.default_config_pathname,
            abspath(join(site_dir, '..', 'default', 'site.ini'))
        )
        self.assertEqual(config.get('site', 'name'), 'ZOOM')
        self.assertEqual(config.get('apps', 'home'), 'home')
        self.assertIsInstance(str(config), (str,))

    def test_missing_option(self):
        site_dir = abspath(join(dirname(__file__), '..', '..', 'web', 'sites', 'localhost'))
        config = Config(site_dir, 'site.ini')
        self.assertIsNotNone(config)
        self.assertEqual(config.get('apps', 'home'), 'home')  # found
        self.assertRaises(
            Exception,
            config.get,
            'ksjfklsjdfl',
            'skjfkls',
        )  # missing

    def test_has_option(self):
        site_dir = abspath(join(dirname(__file__), '..', '..', 'web', 'sites', 'localhost'))
        config = Config(site_dir, 'site.ini')
        self.assertIsNotNone(config)
        self.assertTrue(config.has_option('apps', 'home'))
        self.assertFalse(config.has_option('ksjfklsjdfl', 'skjfkls'))

    def test_section_failover_when_site_config_missing(self):

        site_dir = zoom.tools.zoompath('zoom', '_assets', 'web', 'sites', 'temptestsite')
        try:
            os.mkdir(site_dir)
            config = Config(site_dir, 'site.ini')
            self.assertTrue(config.items('apps'))
        finally:
            os.rmdir(site_dir)
