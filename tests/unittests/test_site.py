"""
    test site
"""

import unittest

import zoom


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
