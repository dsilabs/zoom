"""
    test sites module
"""

from datetime import timedelta, datetime
import unittest
import logging
from io import StringIO

import zoom
import zoom.request
import zoom.sites
from zoom.tools import (
    get_timezone, get_timezone_offset, get_timezone_str,
    get_timezone_names
)


class TestSite(unittest.TestCase):

    @unittest.skip
    def test_default_site_database_logging_defaults(self):
        path = zoom.tools.zoompath('zoom/_assets/web/sites/default')
        site = zoom.sites.Site(path)
        self.assertTrue(site.logging)
        self.assertFalse(site.profiling)
        self.assertFalse(site.monitor_app_database)
        self.assertFalse(site.monitor_system_database)

    def test_developer_site_database_logging_defaults(self):
        site = zoom.sites.Site()
        self.assertTrue(site.logging)
        self.assertTrue(site.profiling)
        self.assertTrue(site.monitor_app_database)
        self.assertFalse(site.monitor_system_database)

    def test_timezone_attribute(self):
        site = zoom.sites.Site()
        self.assertIsNotNone(site.timezone)
        self.assertEqual(get_timezone_str(site.timezone), 'UTC')

    def test_timezone_offset(self):
        timezone = get_timezone('Asia/Tokyo')
        self.assertEqual(
            get_timezone_offset(timezone),
            timedelta(seconds=32400)
        )

        timezone = get_timezone('America/Vancouver')

        # PST
        self.assertEqual(
            get_timezone_offset(timezone, datetime(2024, 1, 25)),
            timedelta(days=-1, seconds=57600)
        )

        # PDT
        self.assertEqual(
            get_timezone_offset(timezone, datetime(2024, 7, 25)),
            timedelta(days=-1, seconds=61200)
        )

    def test_timezone_names(self):
        names = get_timezone_names()
        self.assertIn('UTC', names)
        self.assertIn('Asia/Tokyo', names)
        self.assertIn('America/Vancouver', names)

    def test_site_module_deprecation_message(self):

        # Set up a string buffer and handler to capture log output
        log_output = StringIO()
        handler = logging.StreamHandler(log_output)
        logger = logging.getLogger('zoom.site')  # Adjust logger name if needed
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)  # Ensure warnings are captured

        request = zoom.request.build('http://localhost')
        zoom.site.Site(request)

        # Get the log output
        log_contents = log_output.getvalue()

        # Clean up
        logger.removeHandler(handler)
        handler.close()

        # Assert that the deprecation warning is in the log
        self.assertIn("deprecated", log_contents.lower())  # Adjust to match actual message


class TestSiteDatabase(unittest.TestCase):

    def setUp(self):
        zoom.sites.set_site(zoom.sites.Site())
        site = zoom.sites.get_site()
        expected = zoom.tools.zoompath('zoom/_assets/web/sites/localhost')
        self.assertEqual(site.path, expected)

    def tearDown(self):
        del zoom.system.site

    def test_get_db(self):
        db = zoom.sites.get_db()
        names = [a for a, in db('show tables')]
        self.assertIn('users', names)

    def test_db(self):
        db = zoom.sites.db
        names = [a for a, in db('show tables')]
        self.assertIn('users', names)
