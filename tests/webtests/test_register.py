
# -*- coding: utf-8 -*-

"""
    zoom.tests.webdriver_tests.test_admin

    test register app
"""

import zoom


from zoom.testing.webtest import WebdriverTestCase


class RegisterTests(WebdriverTestCase):
    """Register App Tests"""

    def setUp(self):
        WebdriverTestCase.setUp(self)
        self.delete_user('joe3')
        self.add_register_app()

    def tearDown(self):
        self.delete_user('joe3')
        if self.added_register:
            self.remove_register_app()

        WebdriverTestCase.tearDown(self)

    def add_register_app(self):
        """ checks if register app is visible to guest group and adds it if not """
        self.login('admin', 'admin')
        # TODO: get by group name instead of id
        self.get('/admin/groups/3')
        if not self.contains('Register'):
            self.get('/admin/groups/3/edit')
            self.chosen('apps', ['Forgot', 'Login', 'Register'])
            self.click('id=save_button')
            self.added_register = True
        else:
            self.added_register = False
        self.logout()

    def remove_register_app(self):
        """ sets the guest group apps to just Forgot and Login, dropping Register """
        self.login('admin', 'admin')
        # TODO: get by group name instead of id
        self.get('/admin/groups/3/edit')
        self.chosen('apps', ['Forgot', 'Login'])
        self.click('name=save_button')
        self.logout()

    def delete_user(self, username):
        """Delete a user using the admin app"""
        self.login('admin', 'admin')
        self.get('/admin')
        self.get('/admin/users')
        if username in self.page_source:
            self.click_link(username)
            self.click('id=delete-action')
            self.click('name=delete_button')
        self.logout()

    def test_registration_available(self):
        self.get('/register')
        self.find('register_now_button')

    def test_register(self):
        self.get('/register')
        self.fill(
            dict(
                first_name='Joe',
                last_name='Smith',
                username='joe3',
                email='joe3@testco.com',
                password='mysecret',
                confirm='mysecret',
            )
        )
        self.click('register_now_button')
        self.assertContains('Step 2')

        self.get('/register/1234/confirm')
        self.assertContains('Registration Complete!')

    def test_user_already_registered(self):
        self.get('/register')
        self.fill(
            dict(
                first_name='Joe',
                last_name='Smith',
                username='joe3',
                email='joe3@testco.com',
                password='mysecret',
                confirm='mysecret',
            )
        )
        self.click('register_now_button')
        self.assertContains('Step 2')

        self.get('/register/1234/confirm')
        assert 'Registration Complete!' in self.page_source

        self.get('/register')
        self.fill(
            dict(
                first_name='Joe',
                last_name='Smith',
                username='joe3',
                email='joe3@testco.com',
                password='mysecret',
                confirm='mysecret',
            )
        )
        self.click('register_now_button')
        self.assertContains('Step 2')

        self.get('/register/1234/confirm')
        self.assertContains('Registration Already Completed')
