"""
    test home app

    A stub for now while we redesign app.
"""

from zoom.testing.webtest import AdminTestCase

class WebTest(AdminTestCase):

    def test_index(self):
        self.assertContains('app-icons')
        self.assertContains('Admin')
        self.click_link('Admin')
        self.assertContains('Admin')
