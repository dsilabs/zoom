
# -*- coding: utf-8 -*-

"""
    zoom.tests.webdriver_tests.test_admin

    test admin app functions
"""


from zoom.testing.webtest import WebdriverTestCase


class SystemTests(WebdriverTestCase):
    """MyApp system tests"""

    def add_user(self, first_name, last_name, email, username):
        self.get('/admin')
        self.get('/admin/users')
        self.get('/admin/users/new')
        self.fill(
            dict(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username,
            )
        )
        self.chosen('memberships', ['managers'])
        self.click('create_button')

    def delete_user(self, username):
        self.get('/admin')
        self.get('/admin/users')
        self.click_link(username)
        self.click('id=delete-action')
        self.click('name=delete_button')

    def test_admin_login_logout(self):
        self.login('admin', 'admin')
        self.logout()

    def test_admin_add_remove_user(self):
        self.login('admin', 'admin')
        self.add_user('Sally', 'Jones', 'sally@testco.com', 'sally')
        self.delete_user('sally')
        self.logout()
