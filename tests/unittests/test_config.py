"""
    Test the config module
"""


from os.path import join, split, abspath, exists, dirname
import unittest
import logging

from zoom.config import Config


class TestConfig(unittest.TestCase):
    """test config module"""

    # pylint: disable=R0904
    # pylint: disable=missing-docstring
    # method names are more useful for testing

    def test_create(self):

        def find_config(directory):
            """climb the directory tree looking for config"""
            pathname = join(directory, 'dz.conf')
            if exists(pathname):
                return directory
            parent, _ = split(directory)
            if parent != '/':
                return find_config(parent)

        logger = logging.getLogger('zoom.unittest.test_config')
        site_dir = abspath(join(dirname(__file__), '..', '..', 'web', 'sites', 'localhost'))
        logger.debug(site_dir)
        # standard_config_file = join(split(__file__)[0], config_location)
        # config_location = find_config(abspath('.'))
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
