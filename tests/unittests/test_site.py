"""
    test site
"""

from datetime import timedelta, datetime
import unittest

import zoom
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
