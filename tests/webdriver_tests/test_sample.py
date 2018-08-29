
# -*- coding: utf-8 -*-

"""
    zoom.tests.webdriver_tests.test_sample

    test sample app functions
"""


from zoom.testing.webtest import AdminTestCase


class SampleTests(AdminTestCase):
    """Content App"""

    size = (1024, 2048)

    def test_content(self):
        self.get('/sample')
        self.assertContains('Site name: <strong>ZOOM</strong>')
        self.assertContains('&lt;dz:user_full_name&gt; : "Admin User"')

