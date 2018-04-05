
# -*- coding: utf-8 -*-

"""
    zoom.tests.webdriver_tests.test_content

    test content app functions
"""


from zoom.testing.webtest import WebdriverTestCase


class ContentTests(WebdriverTestCase):
    """Content App"""

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

    def test_index(self):
        self.get('/content')
        self.assertContains('Overview')
        self.assertContains('Pages')
        self.assertContains('Snippets')
