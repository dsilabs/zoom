"""
    test admin app
"""

from zoom.testing.apptest import AppTestCase


class AdminAppTestCase(AppTestCase):

    username = 'admin'

    def setUp(self):
        super().setUp()
        # group = self.site.groups.get(2)
        # # group.remove_apps('icons')
        # app_names = set(app.name for app in self.site.apps)
        # print(app_names)
        # group.add_apps(app_names)

    def test_index(self):
        self.get('/admin')
        self.assertContains('Overview')
        self.assertContains('Users')
        self.assertContains('Groups')
        self.assertContains('Requests Today')
        self.assertContains('Errors Today')
        self.assertContains('Performance')
        self.assertContains('Authorizations')
        self.assertContains('Search')
        self.assertContains('search-button')

    def test_apps(self):
        self.get('/admin/apps')
        self.assertContains('Apps')

    def test_add_remove_apps_model(self):
        self.get('/admin/apps')
        self.assertContains('Apps')

        group = self.site.groups.get(2)
        self.assertEqual(group.name, 'users')

        app_name = 'icons'
        site_app_names = {app.name for app in self.site.apps}
        self.assertIn(app_name, site_app_names)

        db = self.site.db

        group_app_names = {
            group.name[2:]
            for group in map(self.site.groups.get, group.apps)
        }
        self.assertNotIn(app_name, group_app_names)

        group.add_apps([app_name])
        group_app_names = {
            g.name[2:]
            for g in map(self.site.groups.get, group.apps)
        }
        self.assertIn(app_name, group_app_names)

        group.remove_apps([app_name])
        group_app_names = {
            g.name[2:]
            for g in map(self.site.groups.get, group.apps)
        }
        self.assertNotIn(app_name, group_app_names)

