
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


class SnippetTests(WebdriverTestCase):
    """Snippet Feature of Content App"""

    def setUp(self):
        WebdriverTestCase.setUp(self)
        self.login('admin', 'admin')

    def tearDown(self):
        self.logout()
        WebdriverTestCase.tearDown(self)

    def add_snippet(self, **parts):
        assert parts.get('name')
        self.get('/content/snippets/new')
        self.fill(parts)
        self.click('create_button')

    def delete_snippet(self, locator):
        self.get('/content/snippets')
        self.click_link(locator)
        self.click_link('Delete')
        self.click('delete_button')

    def test_index(self):
        self.get('/content/snippets')
        self.assertContains('<h1>Snippets</h1>')

    def test_add_remove_snippet(self):
        self.get('/content/snippets')
        self.add_snippet(
            name='Test Snippet',
            body='This is a test snippet.'
        )
        self.assertContains('Test Snippet')
        self.delete_snippet('Test Snippet')

