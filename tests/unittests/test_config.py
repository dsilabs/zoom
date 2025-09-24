"""
Test the config module
"""

import os
from os.path import join, abspath, dirname
import unittest
import logging
import tempfile

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


class TestConfigEnvSubstitution(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test config files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.site_dir = self.temp_dir.name

        # Create a sample site.ini file with explicit section
        self.config_content = """
        [test]
        log_level = ${LOG_LEVEL:INFO}
        database_url = ${DB_URL:sqlite:///default.db}
        api_key = ${API_KEY}
        static_value = unchanged
        """
        self.config_path = join(self.site_dir, 'site.ini')
        with open(self.config_path, 'w') as f:
            f.write(self.config_content)

        # Clear environment variables to ensure a clean test environment
        os.environ.pop('LOG_LEVEL', None)
        os.environ.pop('DB_URL', None)
        os.environ.pop('API_KEY', None)

    def tearDown(self):
        # Clean up the temporary directory
        self.temp_dir.cleanup()

    def test_env_var_with_default(self):
        config = Config(self.site_dir, 'site.ini')
        self.assertEqual(config.get('test', 'log_level'), 'INFO')
        self.assertEqual(config.get('test', 'database_url'), 'sqlite:///default.db')

    def test_env_var_with_default_overridden(self):
        os.environ['LOG_LEVEL'] = 'DEBUG'
        os.environ['DB_URL'] = 'postgresql://user:pass@localhost:5432/dbname'
        config = Config(self.site_dir, 'site.ini')
        self.assertEqual(config.get('test', 'log_level'), 'DEBUG')
        self.assertEqual(config.get('test', 'database_url'), 'postgresql://user:pass@localhost:5432/dbname')

    def test_env_var_without_default(self):
        config = Config(self.site_dir, 'site.ini')
        self.assertEqual(config.get('test', 'api_key'), '${API_KEY}')

    def test_env_var_without_default_set(self):
        os.environ['API_KEY'] = 'secret123'
        config = Config(self.site_dir, 'site.ini')
        self.assertEqual(config.get('test', 'api_key'), 'secret123')

    def test_non_placeholder_value(self):
        config = Config(self.site_dir, 'site.ini')
        self.assertEqual(config.get('test', 'static_value'), 'unchanged')