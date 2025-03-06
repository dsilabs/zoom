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
from zoom.server import reset_modules

build = zoom.request.build
join = os.path.join

logger = logging.getLogger(__name__)

class TestApps(unittest.TestCase):

    def setUp(self):
        reset_modules()
        zoom.system.parts = zoom.component.Component()
        zoom.system.providers = []
        self.request = zoom.system.request = build('http://localhost', {})
        self.request.profiler = set()
        self.db = zoom.database.setup_test()
        zoom.system.site = zoom.sites.Site()
        self.request.site = zoom.system.site
        self.apps_dir = zoom.tools.zoompath('zoom', '_assets', 'standard_apps')
        self.request.app = zoom.system.request.app = zoom.utils.Bunch(
            name='app',
            title='App',
            description='An app',
            url='/app',
            menu=[],
            keywords='one,two',
            theme=None,
            packages={},
            common_packages={},
        )
        self.request.user = zoom.users.Users(self.db).first(username='user')

    def tearDown(self):
        self.db.close()

    def test_app_process_index(self):
        save_dir = os.getcwd()
        try:
            os.chdir(zoom.tools.zoompath(self.apps_dir, 'sample'))
            app = zoom.App()
            request = build('http://localhost/sample', {})
            request.site = zoom.sites.Site()
            response = app(request)
            self.assertEqual(type(response), zoom.Page)
        finally:
            os.chdir(save_dir)

    def test_app_process_method(self):
        save_dir = os.getcwd()
        try:
            os.chdir(zoom.tools.zoompath(self.apps_dir, 'sample'))
            app = zoom.App()
            request = build('http://localhost/sample/about', {})
            request.site = zoom.site.Site(self.request)
            request.site.db = zoom.database.setup_test()
            response = app(request)
            self.assertEqual(type(response), str)
        finally:
            os.chdir(save_dir)

    def test_app_process_module(self):
        save_dir = os.getcwd()
        try:
            os.chdir(zoom.tools.zoompath(self.apps_dir, 'sample'))
            app = zoom.App()
            request = build('http://localhost/sample/parts', {})
            request.site = zoom.site.Site(self.request)
            request.site.db = zoom.database.setup_test()
            response = app(request)
            self.assertEqual(type(response), zoom.Page)
        finally:
            os.chdir(save_dir)

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
        target = zoom.tools.zoompath('zoom', '_assets', 'standard_apps', 'hello', 'app.py')
        app = zoom.apps.load_module('app', target)
        self.assertEqual(app.__file__, target)

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
            self.assertRaises(ModuleNotFoundError, load, 'x', target)
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
            '<ul>'
            '<li><a href="/profile" name="link-to-profile">Profile</a></li>'
            '<li><a href="/logout" name="link-to-logout">Logout</a></li>'
            '</ul>'
            '</div>'
            )
        )
        self.request.user.is_authenticated = True
        menu = zoom.apps.system_menu(self.request)
        self.assertTrue(self.request.user.is_authenticated)
        self.assertTrue('<li class="dropdown">' in menu)

    def test_no_app_menu(self):
        site = zoom.system.site
        pathname = zoom.tools.zoompath(self.apps_dir, 'hello', 'app.py')
        app = zoom.apps.AppProxy('Hello', pathname, site)
        app.request = self.request
        self.assertEqual(app.menu(), '<ul></ul>')

    def test_app_menu(self):
        site = zoom.system.site

        pathname = zoom.tools.zoompath(self.apps_dir, 'sample', 'app.py')
        logger.debug('creating AppProxy for %s', pathname)
        app = zoom.apps.AppProxy('Sample', pathname, site)
        app.request = self.request
        # print(app.menu)
        logger.debug('type(app)=%s', type(app))
        logger.debug('type(app.method)=%s', type(app.method))
        logger.debug('type(app.method.menu)=%s', type(app.method.menu))

        self.assertEqual(app.menu(), (
            '<ul>'
            '<li class="index-menu-item"><a href="<dz:app_url>">Content</a></li>'
            '<li class="fields-menu-item"><a href="<dz:app_url>/fields">Fields</a></li>'
            '<li class="collection-menu-item"><a href="<dz:app_url>/collection">Collection</a></li>'
            '<li class="components-menu-item"><a href="<dz:app_url>/components">Components</a></li>'
            '<li class="widgets-menu-item"><a href="<dz:app_url>/widgets">Widgets</a></li>'
            '<li class="charts-menu-item"><a href="<dz:app_url>/charts">Charts</a></li>'
            '<li class="alerts-menu-item"><a href="<dz:app_url>/alerts">Alerts</a></li>'
            '<li class="flags-menu-item"><a href="<dz:app_url>/flags">Flags</a></li>'
            '<li class="parts-menu-item"><a href="<dz:app_url>/parts">Parts</a></li>'
            '<li class="tools-menu-item"><a href="<dz:app_url>/tools">Tools</a></li>'
            '<li class="responses-menu-item"><a href="<dz:app_url>/responses">Responses</a></li>'
            '<li class="background-menu-item"><a href="<dz:app_url>/background">Background</a></li>'
            '<li class="about-menu-item"><a href="<dz:app_url>/about">About</a></li>'
            '</ul>'
        ))

    def test_app_description(self):
        site = zoom.system.site
        pathname = zoom.tools.zoompath(self.apps_dir, 'hello', 'app.py')
        app = zoom.apps.AppProxy('Hello', pathname, site)
        app.request = self.request
        self.assertEqual(app.description, 'The Hello app.')

    def test_app_keywords(self):
        site = zoom.system.site
        pathname = zoom.tools.zoompath(self.apps_dir, 'hello', 'app.py')
        app = zoom.apps.AppProxy('Hello', pathname, site)
        app.request = self.request
        self.assertEqual(app.keywords, 'The, Hello, app.')

    def test_app_str(self):
        site = zoom.system.site
        pathname = zoom.tools.zoompath(self.apps_dir, 'hello', 'app.py')
        app = zoom.apps.AppProxy('Hello', pathname, site)
        app.request = self.request
        self.assertEqual(str(app), '<a href="/Hello" name="link-to-hello">Hello</a>')

    def test_respond_response(self):
        content = zoom.response.JSONResponse('true')
        response = zoom.apps.respond(content, self.request)
        self.assertEqual(type(response), zoom.response.JSONResponse)

    def test_respond_str(self):
        response = zoom.apps.respond('test', self.request)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(type(response), zoom.response.HTMLResponse)

    def test_respond_component(self):
        response = zoom.apps.respond(zoom.Component('my html', css='my css'), self.request)
        self.assertEqual(type(response), zoom.response.HTMLResponse)

    def test_respond_none(self):
        response = zoom.apps.respond(None, self.request)
        self.assertEqual(response, None)

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
        pathname = zoom.tools.zoompath(self.apps_dir, 'hello', 'app.py')
        zoom.system.request.app = app = zoom.apps.AppProxy('hello', pathname, site)
        app.request = self.request = zoom.system.request
        method = app.method
        response = method(self.request).render(self.request)
        self.assertEqual(type(response), zoom.response.HTMLResponse)

    def test_app_proxy_process(self):
        site = zoom.system.site
        pathname = zoom.tools.zoompath(self.apps_dir, 'hello', 'app.py')
        app = zoom.apps.AppProxy('hello', pathname, site)
        response = app.run(self.request)
        self.assertEqual(type(response), zoom.response.HTMLResponse)
        self.assertTrue('<!DOCTYPE html>' in response.content)

    def test_handle(self):
        site = zoom.system.site
        pathname = zoom.tools.zoompath(self.apps_dir, 'hello', 'app.py')
        app = zoom.apps.AppProxy('hello', pathname, site)
        response = app.run(self.request)
        self.assertEqual(type(response), zoom.response.HTMLResponse)
        self.assertTrue('<!DOCTYPE html>' in response.content)

    def call(self, uri, as_username='admin', tag='content', adjust=None):
        def clear():
            clearable = ('app', 'index')
            for module in clearable:
                if module in sys.modules:
                    del sys.modules[module]
        request = build('http://localhost' + uri, {})
        request.uri = uri
        request.profiler = set()
        request.site = zoom.system.site
        request.user = zoom.users.Users(self.db).first(username=as_username)
        request.user.is_authenticated = as_username != 'guest'
        zoom.system.user = request.user
        clear()
        if adjust:
            adjust(request)
        response = zoom.apps.handle(request)
        if isinstance(response, zoom.response.HTMLResponse):
            return zoom.render.render('{{' + tag + '}}')
        else:
            return response

    def test_handle_unauth_guest(self):
        response = self.call('/home', 'guest')
        self.assertEqual(
            response.headers['Location'],
            '/login?original_url=http%3A%2F%2Flocalhost%2Fhome'
        )

    def test_handle_insufficient_privileges(self):
        response = self.call('/admin', 'user')
        self.assertEqual(response.status, '302 Found')
        self.assertEqual(
            response.headers['Location'],
            '/'
        )

    def test_handle_insufficient_privileges_with_auth(self):
        def add_auth_function(request):
            request.site.auth_app_name = 'authorize'
        response = self.call('/admin', 'user', adjust=add_auth_function)
        self.assertEqual(response.status, '302 Found')
        self.assertEqual(
            response.headers['Location'],
            '/authorize?original_url=http%3A%2F%2Flocalhost%2Fadmin'
        )

    def test_handle_missing_app(self):
        response = self.call('/aaa', as_username='admin')
        self.assertEqual(response.status, '302 Found')
        self.assertEqual(
            response.headers['Location'],
            '<dz:abs_site_url>/app'
        )

    def test_handle_default_app(self):
        response = self.call('aaa', as_username='guest')
        self.assertEqual(response, None)

    def test_read_config(self):
        site = zoom.system.site
        pathname = zoom.tools.zoompath(self.apps_dir, 'sample', 'app.py')
        app = zoom.apps.AppProxy('Sample', pathname, site)
        self.assertTrue(app.read_config('settings', 'title', 'notfound'), 'Sample')

    def test_read_config_missing(self):
        site = zoom.system.site
        pathname = zoom.tools.zoompath(self.apps_dir, 'ping', 'app.py')
        app = zoom.apps.AppProxy('Ping', pathname, site)
        self.assertTrue(app.read_config('settings', 'icon', 'notfound'), 'cube')

