
# -*- coding: utf-8 -*-

"""
    zoom.tests.webdriver_tests.test_admin

    test admin app functions
"""


from .common import WebdriverTestCase


class SystemTests(WebdriverTestCase):
    """MyApp system tests"""

    headless = False

    def setUp(self):
        WebdriverTestCase.setUp(self)
        self.login('admin', 'admin')

    def tearDown(self):
        self.logout()
        WebdriverTestCase.tearDown(self)

    def add_page(self, **parts):
        assert parts.get('title')
        self.get('/content/pages/new')
        self.fill(parts)
        self.click('create_button')

    def delete_page(self, locator):
        self.get('/content/pages')
        self.click_link(locator)
        self.click_link('Delete')
        self.click('delete_button')

    def test_add_remove_page(self):
        self.add_page(
            title='Test Page',
            path='test-page',
            body='This is a test page.'
        )
        self.assertContains('Test Page')
        self.delete_page('Test Page')

    # def add_user(self, first_name, last_name, email, username):
    #     self.get('/admin')
    #     self.get('/admin/users')
    #     self.get('/admin/users/new')
    #     self.fill(
    #         dict(
    #             first_name=first_name,
    #             last_name=last_name,
    #             email=email,
    #             username=username,
    #         )
    #     )
    #     self.chosen('groups', ['managers'])
    #     self.click('create_button')
    #
    # def delete_user(self, username):
    #     self.get('/admin')
    #     self.get('/admin/users')
    #     self.click_link(username)
    #     self.click('id=delete-action')
    #     self.click('name=delete_button')
    #
    # def test_admin_login_logout(self):
    #     self.login('admin', 'admin')
    #     self.logout()

    def test_index(self):
        self.get('/content')
        self.assertContains('Overview')
        self.assertContains('Pages')
        self.assertContains('Snippets')
