"""
    test sample app
"""

from zoom.testing.apptest import AppTestCase


class SampleAppTestCase(AppTestCase):

    username = 'admin'

    def test_index(self):
        self.get('/sample')
        self.assertContains('Sample')
        self.assertContains('Paragraph of Text')

    def test_static(self):
        self.get('/sample/static/test.json')
        self.assertContains('this is JSON')

        self.get('/sample/static/test.js')
        self.assertContains(b'this is javascript')

        self.get('/sample/static/test.css')
        self.assertContains(b'this is CSS')

    def test_redirect(self):
        self.get('/sample')
        self.assertNotRedirectResponse()

        self.get('/login')
        self.assertRedirectResponse()
        self.assertRedirectResponse('/')
        self.assertNotRedirectResponse('/nowhere')
