"""
    test home app

    A stub for now while we redesign app.
"""

from .common import AdminTestCase

class WebTest(AdminTestCase):

    def test_index(self):
        self.assertContains('Apps')
        self.assertContains('Admin')
        self.click_link('Admin')
        self.assertContains('Admin')
