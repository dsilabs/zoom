"""
    test the user module
"""
import unittest
import datetime
import logging
import os
import sys

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
        self.request.app = zoom.utils.Bunch(
            name='App',
            description='An app',
            url='/app',
            menu=[],
            keywords='one,two'
        )
        self.request.user = zoom.users.Users(self.db).first(username='user')

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

    def test_load_module(self):
        target = __file__
        my = zoom.apps.load_module('my', target)
        self.assertEqual(my.__file__, __file__)

    def test_load_module_missing(self):
        target = 'not_a_file.py'
        load = zoom.apps.load_module
        self.assertIsNone(load('x', target))

    def test_load_module_error(self):
        target = 'erroring_file.py'
        f = open(target, 'w')
        try:
            f.write('import not_a_module')
        finally:
            f.close()
        try:
            load = zoom.apps.load_module
            if sys.version_info < (3, 6):
                my_exception = ImportError
            else:
                my_exception = ModuleNotFoundError
            self.assertRaises(my_exception, load, 'x', target)
        finally:
            os.remove(target)

    def test_helpers(self):
        helpers = zoom.apps.helpers(self.request)
        self.assertTrue(isinstance(helpers, dict))
        self.assertTrue(helpers.get('app_name'), 'App')