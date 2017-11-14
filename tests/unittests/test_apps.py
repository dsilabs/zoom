"""
    test the user module
"""
import unittest
import datetime
import logging
import os

import zoom
import zoom.apps
import zoom.component
import zoom.request
import zoom.site

build = zoom.request.build
join = os.path.join

class TestApps(unittest.TestCase):

    def setUp(self):
        zoom.component.composition.parts = zoom.component.Component()
        zoom.system.providers = []
        self.request = build('http://localhost', {})
        self.request.profiler = set()
        self.db = zoom.database.setup_test()
        zoom.system.site = zoom.site.Site(self.request)
        self.request.site = zoom.system.site
        this_dir = os.path.dirname(__file__)
        self.apps_dir = os.path.join(this_dir, '../../web/apps')

    def tearDown(self):
        self.db.close()

    def test_respond_text(self):
        response = zoom.apps.respond('test', self.request)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content, 'test')

    def test_respond_none(self):
        response = zoom.apps.respond(None, self.request)
        self.assertEqual(response, None)

    def test_noapp(self):
        app = zoom.apps.NoApp()
        self.assertEqual(app.name, 'none')

    def test_hello_app(self):
        app_file = os.path.realpath(join(self.apps_dir, 'hello/app.py'))

        app = zoom.apps.AppProxy('hello', app_file, zoom.system.site)
        self.assertEqual(app.name, 'hello')

        response = app.run(self.request)
        self.assertEqual(response.status, '200 OK')
