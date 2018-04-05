
# -*- coding: utf-8 -*-

"""
    zoom.tests.webdriver_tests.test_404

    test site missing page
"""

import os

from zoom.testing.webtest import WebdriverTestCase


class MissingSiteTests(WebdriverTestCase):
    """MyApp system tests"""

    url = os.environ.get('ZOOM_TEST_MISSING_URL', 'http://127.0.0.1:8000')

    def test_site_missing(self):
        self.get('/')
        self.assertContains('ZOOM')
        self.assertContains('127.0.0.1')
