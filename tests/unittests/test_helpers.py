"""
    test helpers
"""

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# It's reasonable in this case.

import unittest

import zoom
import zoom.fill
import zoom.request


def app_url():
    return zoom.system.request.app.url


class TestHelpers(unittest.TestCase):
    """test the tools module"""

    site_url = 'http://localhost'

    def setUp(self):
        zoom.system.site = zoom.sites.Site()
        zoom.system.request = zoom.request.build(self.site_url)
        zoom.system.request.user = zoom.system.site.users.first(username='user')
        apps = {app.name: app for app in zoom.system.site.apps}
        zoom.system.request.app = apps['home']
        zoom.system.providers = [{'app_url': app_url}]


    def get(self, url):
        request = zoom.system.request = zoom.request.build(self.site_url + url)
        zoom.system.request.user = zoom.system.site.users.first(username='user')
        apps = {app.name: app for app in zoom.system.site.apps}
        if zoom.system.request.route:
            zoom.system.request.app = apps[request.route[0]]
        else:
            zoom.system.request.app = apps[zoom.apps.get_default_app_name(zoom.system.site, zoom.system.request.user)]

    def test_url_for(self):
        self.get('/sample')

        request = zoom.system.request

        self.assertEqual(zoom.system.site.url, '')
        self.assertEqual(request.path, '/sample')
        self.assertEqual(request.app.url, '/sample')

        self.assertEqual(
            zoom.helpers.url_for(),
            ''
        )

    def test_url_for_page_empty(self):
        self.get('/home')

        request = zoom.system.request

        self.assertEqual(zoom.system.site.url, '')
        self.assertEqual(request.path, '/home')
        self.assertEqual(request.app.url, '/home')

        self.assertEqual(
            zoom.render.render(zoom.helpers.url_for_page(), app_url=app_url),
            '/home'
        )

    def test_url_for_page_basic(self):
        self.get('/sample')

        request = zoom.system.request

        self.assertEqual(zoom.system.site.url, '')
        self.assertEqual(request.path, '/sample')
        self.assertEqual(request.app.url, '/sample')

        self.assertEqual(
            zoom.render.render(zoom.helpers.url_for_page('page1'), app_url=app_url),
            '/sample/page1'
        )

    def test_url_for_page_default(self):
        self.get('/content')

        request = zoom.system.request

        self.assertEqual(zoom.system.site.url, '')
        self.assertEqual(request.path, '/content')
        self.assertEqual(request.app.url, '/')
        self.assertEqual(request.app.name, 'content')

        self.assertEqual(
            zoom.render.render(zoom.helpers.url_for_page('page1'), app_url=app_url),
            '/page1'
        )
