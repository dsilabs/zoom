"""
    zoom.apps

    handles requests by locating and calling a suitable app
"""

import os
import imp
import logging
import configparser

from zoom.response import Response, HTMLResponse
from zoom.helpers import url_for, link_to
from zoom.components import as_links
import zoom.html as html


DEFAULT_SYSTEM_APPS = ['register', 'profile', 'login', 'logout']
DEFAULT_MAIN_APPS = ['home', 'apps', 'users', 'groups', 'info']
DEFAULT_SETTINGS = dict(
    title='',
    icon='blank_doc',
    version=0.0,
    enabled=True,
    visible=True,
    theme='',
    description='',
    categories='',
    tags='',
    keywords='',
    in_development=False,
)


class App(object):
    """a Zoom application"""

    def __init___(self):
        self.menu = []

    def process(self, *route, **data):

        def if_callable(method):
            """test if callable and return it or None"""
            return callable(method) and method

        logger = logging.getLogger(__name__)

        isfile = os.path.isfile
        logger.debug('route {!r}'.format(route))

        if len(route) > 1:
            module = route[1]
            rest = route[2:]
        else:
            module = 'index'
            rest = route[1:]

        logger.debug('module is {!r}'.format(module))
        try:
            method = getattr(self, module)
            logger.debug('got method for {!r}'.format(module))
        except AttributeError:
            method = None

        if method:
            logger.debug('calling method {!r}'.format(module))
            result = method(*rest, **data)
            logger.debug(result)
            return result

        filename = '{}.py'.format(module)
        if isfile(filename):
            logger.debug('file {}.py exists'.format(module))
            source = imp.load_source(module, filename)
            app = if_callable(getattr(source, 'app', None))
            view = if_callable(getattr(source, 'view', None))
            controller = if_callable(getattr(source, 'controller', None))
        else:
            app = None
            view = None
            controller = None

        return (
            app and app(*rest, **data) or
            controller and controller(*rest, **data) or
            view and view(*rest, **data)
        )

    def __call__(self, request):
        self.request = request
        return self.process(*request.route, **request.data)


class AppProxy(object):

    def __init__(self, name, filename, site):
        self.name = name
        self.filename = filename
        self.url = site.url + '/' + name
        self.link = link_to(self.name, self.url)
        self.path = os.path.dirname(filename)
        self.method = getattr(imp.load_source('app', self.filename), 'app')
        self.site = site
        self.config_parser = configparser.ConfigParser()
        self.config = self.get_config(DEFAULT_SETTINGS)

        self.visible = self.config.get('visible')

    def run(self, request):
        return self.method(request)

    def menu(self):
        def by_name(name):
            def selector(item):
                logger.debug('item.name: %r', item.name)
                logger.debug('selected: %r', name)
                return name == item.name
            return selector

        route = self.site.request.route
        logger = logging.getLogger(__name__)
        logger.debug('constructing menu')
        logger.debug(route)
        menu = getattr(self.method, 'menu', [])
        logger.debug(menu)
        selected = (
            len(route) > 2 and route[0] == 'content' and route[2] or
            len(route) > 1 and route[1] or
            len(route) == 1 and route[0] != 'content' and 'index'
        )
        logger.debug('selected: %s', selected)
        result = as_links(menu, select=by_name(selected))
        logger.debug('made it')
        logger.debug(result)
        return result

    def menu_items(self):
        menu = getattr(self.method, 'menu')
        return

    def get_config(self, default=None):

        def as_dict(config):
            """
            Converts a ConfigParser object into a dictionary.
            """
            the_dict = {}
            for section in config.sections():
                for key, val in config.items(section):
                    the_dict[key] = val
            return the_dict

        def get_config(pathname):
            self.config_parser.read(pathname)
            return as_dict(self.config_parser)

        path = self.path
        join = os.path.join
        split = os.path.split

        local_config_file = join(path, 'config.ini')
        shared_config_file = join(split(path)[0], 'default.ini')
        system_config_file = join(split(path)[0], '..', '..', 'default.ini')

        local_settings = get_config(local_config_file)
        shared_settings = get_config(shared_config_file)
        system_settings = get_config(system_config_file)

        result = {}
        result.update(default or {})
        result.update(system_settings)
        result.update(shared_settings)
        result.update(local_settings)
        return result

    def __str__(self):
        return self.link

    def __repr__(self):
        return str(self)


def get_apps(request):
    """get list of apps installed on this site"""
    logger = logging.getLogger(__name__)
    result = []
    apps_paths = request.site.config.get('apps', 'path').split(';')

    for app_path in apps_paths:
        path = os.path.abspath(
            os.path.join(
                request.site.path,
                app_path,
            )
        )
        logger.debug('app path: %s', path)
        for app in os.listdir(path):
            filename = os.path.join(path, app, 'app.py')
            if os.path.exists(filename):
                result.append(AppProxy(app, filename, request.site))

    logger.debug(apps_paths)
    logger.debug('%s apps found', len(result))
    return result


def locate_app(site, name):
    logger = logging.getLogger(__name__)
    apps_paths = site.config.get('apps', 'path').split(';')
    for path in apps_paths:
        app_path = os.path.abspath(
            os.path.join(site.path, path, name)
        )
        logger.debug('checking %s', app_path)
        filename = os.path.join(app_path, 'app.py')
        if os.path.exists(filename):
            logger.debug('located app %s', app_path)
            return AppProxy(name, filename, site)


def locate_current_app(request):
    default_app = request.site.config.get('apps', 'default', 'home')
    app_name = request.route and request.route[0] or default_app
    return locate_app(request.site, app_name)


def respond(content, request):
    """construct a response"""
    if content:
        if isinstance(content, Response):
            result = content

        elif hasattr(content, 'render') and content.render:
            result = content.render(request)

        elif isinstance(content, (list, set, tuple)):
            result = HTMLResponse(''.join(content))

        elif isinstance(content, str):
            result = HTMLResponse(content)

        else:
            result = HTMLResponse('OK')

        return result


def handle(request):
    """handle a request"""

    app = locate_current_app(request)
    if app:
        save_dir = os.getcwd()
        try:
            os.chdir(app.path)
            request.app = app
            response = app.run(request)
        finally:
            os.chdir(save_dir)
        return respond(response, request)


def get_system_apps(request):
    names = DEFAULT_SYSTEM_APPS
    # apps = [app for app in [locate_app(request.site, name) for name in names] if app]
    apps = filter(bool, [locate_app(request.site, name) for name in names])
    return apps


def system_menu_items(request):
    """Returns the system menu."""
    return html.li([
        app.link for app in get_system_apps(request) if app.visible
    ])


def system_menu(request):
    """Returns the system menu."""
    return '<ul>%s</ul>' % system_menu_items(request)


def helpers(request):
    return dict(
        app_url=request.app.url,
        app_menu_items=request.app.menu_items,
        app_menu=request.app.menu,
        app_name=request.app.name,
        system_menu_items=system_menu_items(request),
        system_menu=system_menu(request),
    )


def apps_handler(request, handler, *rest):
    """Dispatch request to an application"""
    return handle(request) or handler(request, *rest)
