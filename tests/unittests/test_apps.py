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
import zoom.request
import zoom.site

build = zoom.request.build
join = os.path.join

class TestApps(unittest.TestCase):

    def setUp(self):
        zoom.system.parts = zoom.component.Component()
        zoom.system.providers = []
        self.request = zoom.system.request = build('http://localhost', {})
        self.request.profiler = set()
        self.db = zoom.database.setup_test()
        zoom.system.site = zoom.site.Site(self.request)
        self.request.site = zoom.system.site
        this_dir = os.path.dirname(__file__)
        # self.apps_dir = os.path.join(this_dir, '../../web/apps')
        self.apps_dir = zoom.tools.zoompath('web', 'apps')
        self.request.app = zoom.system.request.app = zoom.utils.Bunch(
            name='App',
            description='An app',
            url='/app',
            menu=[],
            keywords='one,two',
            theme=None,
            packages={},
        )
        self.request.user = zoom.users.Users(self.db).first(username='user')

    def tearDown(self):
        self.db.close()

    def test_app_process_index(self):
        save_dir = os.getcwd()
        try:
            os.chdir(zoom.tools.zoompath('web/apps/sample'))
            app = zoom.App()
            request = build('http://localhost/sample', {})
            request.site = zoom.site.Site(self.request)
            request.site.db = zoom.database.setup_test()
            response = app(request)
            self.assertEqual(type(response), zoom.Page)
        finally:
            os.chdir(save_dir)

    def test_app_process_method(self):
        save_dir = os.getcwd()
        try:
            os.chdir(zoom.tools.zoompath('web/apps/sample'))
            app = zoom.App()
            request = build('http://localhost/sample/about', {})
            request.site = zoom.site.Site(self.request)
            request.site.db = zoom.database.setup_test()
            response = app(request)
            self.assertEqual(type(response), zoom.Page)
        finally:
            os.chdir(save_dir)

    def test_app_process_module(self):
        save_dir = os.getcwd()
        try:
            os.chdir(zoom.tools.zoompath('web/apps/sample'))
            app = zoom.App()
            request = build('http://localhost/sample/parts', {})
            request.site = zoom.site.Site(self.request)
            request.site.db = zoom.database.setup_test()
            response = app(request)
            self.assertEqual(type(response), zoom.Page)
        finally:
            os.chdir(save_dir)

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

    def test_system_menu(self):
        menu = zoom.apps.system_menu(self.request)
        self.assertFalse(self.request.user.is_authenticated)
        self.assertEqual(menu, (
            '<div class="system-menu">'
            '<ul><li><a href="/logout">Logout</a></li></ul>'
            '</div>'
            )
        )
        self.request.user.is_authenticated = True
        menu = zoom.apps.system_menu(self.request)
        self.assertTrue(self.request.user.is_authenticated)
        self.assertTrue('<li class="dropdown">' in menu)

    def test_app_menu(self):
        site = zoom.system.site
        pathname = zoom.tools.zoompath('web', 'apps', 'hello', 'app.py')
        app = zoom.apps.AppProxy('Hello', pathname, site)
        app.request = self.request
        self.assertEquals(app.menu(), '<ul></ul>')

        pathname = zoom.tools.zoompath('web', 'apps', 'sample', 'app.py')
        app = zoom.apps.AppProxy('Sample', pathname, site)
        app.request = self.request
        self.assertEquals(app.menu(), (
            '<ul>'
            '<li><a href="<dz:app_url>">Content</a></li>'
            '<li><a href="<dz:app_url>/fields">Fields</a></li>'
            '<li><a href="<dz:app_url>/collection">Collection</a></li>'
            '<li><a href="<dz:app_url>/components">Components</a></li>'
            '<li><a href="<dz:app_url>/alerts">Alerts</a></li>'
            '<li><a href="<dz:app_url>/parts">Parts</a></li>'
            '<li><a href="<dz:app_url>/tools">Tools</a></li>'
            '<li><a href="<dz:app_url>/missing">Missing</a></li>'
            '<li><a href="<dz:app_url>/about">About</a></li>'
            '</ul>'
        ))

    def test_app_description(self):
        site = zoom.system.site
        pathname = zoom.tools.zoompath('web', 'apps', 'hello', 'app.py')
        app = zoom.apps.AppProxy('Hello', pathname, site)
        app.request = self.request
        self.assertEquals(app.description, 'The Hello app.')

    def test_app_keywords(self):
        site = zoom.system.site
        pathname = zoom.tools.zoompath('web', 'apps', 'hello', 'app.py')
        app = zoom.apps.AppProxy('Hello', pathname, site)
        app.request = self.request
        self.assertEquals(app.keywords, 'The, Hello, app.')

    def test_app_str(self):
        site = zoom.system.site
        pathname = zoom.tools.zoompath('web', 'apps', 'hello', 'app.py')
        app = zoom.apps.AppProxy('Hello', pathname, site)
        app.request = self.request
        self.assertEquals(str(app), '<a href="/Hello">Hello</a>')

    def test_respond_response(self):
        content = zoom.response.JSONResponse('true')
        response = zoom.apps.respond(content, self.request)
        self.assertEqual(type(response), zoom.response.JSONResponse)

    def test_respond_str(self):
        response = zoom.apps.respond('test', self.request)
        self.assertEqual(type(response), zoom.response.HTMLResponse)

    def test_respond_component(self):
        response = zoom.apps.respond(zoom.Component('my html', css='my css'), self.request)
        self.assertEqual(type(response), zoom.response.HTMLResponse)

    def test_respond_list(self):
        response = zoom.apps.respond(['one', 'two'], self.request)
        self.assertEqual(type(response), zoom.response.HTMLResponse)

    def test_respond_other(self):
        response = zoom.apps.respond(1, self.request)
        self.assertEqual(type(response), zoom.response.HTMLResponse)

    def test_handler(self):
        def next(request, *rest):
            return 'foo'
        path = sys.path.copy()
        try:
            if '.' in sys.path:
                del sys.path[sys.path.index('.')]

            result = zoom.apps.handler(self.request, next)

            self.assertEqual(result, 'foo')

            self.assertTrue('.' in sys.path)
        finally:
            sys.path = path

    def test_default_app_name(self):
        site, user = self.request.site, self.request.user
        default_app = zoom.apps.get_default_app_name(site, user)
        self.assertEqual(default_app, 'content')
        self.request.user.is_authenticated = True
        default_app = zoom.apps.get_default_app_name(site, user)
        self.assertEqual(default_app, 'home')

    def test_app_proxy_call(self):
        site = zoom.system.site
        pathname = zoom.tools.zoompath('web', 'apps', 'hello', 'app.py')
        zoom.system.request.app = app = zoom.apps.AppProxy('hello', pathname, site)
        app.request = self.request
        method = app.method
        response = method(self.request).render(self.request)
        self.assertEqual(type(response), zoom.response.HTMLResponse)

    def test_app_proxy_process(self):
        site = zoom.system.site
        pathname = zoom.tools.zoompath('web', 'apps', 'hello', 'app.py')
        app = zoom.apps.AppProxy('hello', pathname, site)
        response = app.run(self.request)
        self.assertEqual(type(response), zoom.response.HTMLResponse)
        self.assertTrue('<!DOCTYPE html>' in response.content)

    def test_handle(self):
        site = zoom.system.site
        pathname = zoom.tools.zoompath('web', 'apps', 'hello', 'app.py')
        app = zoom.apps.AppProxy('hello', pathname, site)
        response = app.run(self.request)
        self.assertEqual(type(response), zoom.response.HTMLResponse)
        self.assertTrue('<!DOCTYPE html>' in response.content)

    def call(self, uri, as_username='admin', tag='content'):
        def clear():
            clearable = ('app', 'index')
            for module in clearable:
                if module in sys.modules:
                    del sys.modules[module]
        request = build('http://localhost/' + uri, {})
        request.profiler = set()
        request.site = zoom.system.site
        request.user = zoom.users.Users(self.db).first(username=as_username)
        clear()
        response = zoom.apps.handle(request)
        if isinstance(response, zoom.response.HTMLResponse):
            return zoom.render.render('{{' + tag + '}}')
        else:
            return response

    def test_handle_redirect_to_index(self):
        response = self.call('home', 'guest')
        self.assertTrue(response.headers['Location'] == '/')

    def test_handle_insufficient_privileges(self):
        response = self.call('admin', 'user')
        self.assertTrue(response.headers['Location'] == '/')

    def test_handle_unknown(self):
        response = self.call('aaa')
        self.assertTrue(response is None)

    def test_read_config(self):
        site = zoom.system.site
        pathname = zoom.tools.zoompath('web', 'apps', 'sample', 'app.py')
        app = zoom.apps.AppProxy('Sample', pathname, site)
        self.assertTrue(app.read_config('settings', 'title', 'notfound'), 'Sample')

    def test_read_config_missing(self):
        site = zoom.system.site
        pathname = zoom.tools.zoompath('web', 'apps', 'ping', 'app.py')
        app = zoom.apps.AppProxy('Ping', pathname, site)
        self.assertTrue(app.read_config('settings', 'icon', 'notfound'), 'cube')
        
