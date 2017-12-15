
# -*- coding: utf-8 -*-

"""
    zoom.tests.webdriver_tests.test_404

    test site missing page
"""


from .common import WebdriverTestCase


class MissingSiteTests(WebdriverTestCase):
    """MyApp system tests"""

    def test_site_missing(self):
        self.url = 'http://127.0.0.1'
        self.get('/')
        self.assertContains('ZOOM')
        self.assertContains('127.0.0.1')
