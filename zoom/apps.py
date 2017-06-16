"""
    zoom.apps

    handles requests by locating and calling a suitable app
"""

import configparser
import imp
import logging
import os
import sys

import zoom.render
from zoom.response import Response, HTMLResponse, RedirectResponse
from zoom.helpers import url_for, link_to
from zoom.tools import load_content
from zoom.components import as_links
import zoom.html as html


DEFAULT_SYSTEM_APPS = ['register', 'profile', 'login', 'logout']
DEFAULT_MAIN_APPS = ['home', 'admin', 'apps', 'info']
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

        if len(route) > 1 and isfile('%s.py' % route[1]):
            module = route[1]
            rest = route[2:]
        else:
            module = 'index'
            rest = route[1:]

        filename = '{}.py'.format(module)
        if isfile(filename):
            logger.debug('file {}.py exists'.format(module))
            source = imp.load_source(module, filename)
            main = if_callable(getattr(source, 'main', None))
            app = if_callable(getattr(source, 'app', None))
            view = if_callable(getattr(source, 'view', None))
            controller = if_callable(getattr(source, 'controller', None))
        else:
            main = None
            app = None
            view = None
            controller = None

        return (
            main and main(rest, self.request) or
            app and app(*rest, **data) or
            controller and controller(*rest, **data) or
            view and view(*rest, **data)
        )

    def __call__(self, request):
        self.request = request
        return self.process(*request.route, **request.data)


class AppProxy(object):
    """App Proxy

    Contains the various extra supporting parts of an app besides
    the actual functionality.  Apps themselves are simply callables
    that accept a requset and return a response.  They can be implemented
    as simple functions or as something more substantial such as
    a subclass of the App class above.  That's entirely up to the
    app developer.  The AppProxy takes care of the other parts that
    an app needs, from it's location to it's icon to it's config files.
    """

    def __init__(self, name, filename, site):
        self.name = name
        self.filename = filename
        self.url = site.url + '/' + name
        self.abs_url = site.abs_url + '/' + name
        self.path = os.path.dirname(filename)
        self.site = site
        self.config_parser = configparser.ConfigParser()
        self.config = self.get_config(DEFAULT_SETTINGS)
        self.link = link_to(self.title, self.url)

        self.visible = self.config.get('visible')
        self.enabled = self.config.get('enabled')
        self.in_development = self.config.get('in_development')
        self._method = None

    @property
    def method(self):
        if self._method == None:
            self._method = getattr(imp.load_source('app', self.filename), 'app')
        return self._method

    @property
    def title(self):
        return self.config.get('title', self.name) or self.name.capitalize()

    def run(self, request):
        """run the app"""
        save_dir = os.getcwd()
        try:
            os.chdir(self.path)
            request.app = self
            response = self.method(request)
            result = respond(response, request)
        finally:
            os.chdir(save_dir)
        return result

    def menu(self):
        """generate an app menu"""
        def by_name(name):
            def selector(item):
                return name == item.name
            return selector

        route = self.site.request.route
        logger = logging.getLogger(__name__)
        logger.debug('constructing menu')
        menu = getattr(self.method, 'menu', [])
        selected = (
            len(route) > 2 and route[0] == 'content' and route[2] or
            len(route) > 1 and route[1] or
            len(route) == 1 and route[0] != 'content' and 'index'
        )
        logger.debug('selected: %s', selected)
        result = as_links(menu, select=by_name(selected))
        return result

    def menu_items(self):
        """get app menu items"""
        menu = getattr(self.method, 'menu')
        return

    def get_config(self, default=None):
        """get the app config"""

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
            """read a config file"""
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


class NoApp(object):
    """default app used when no app is available

    This is mostly used so the helpers remain valid
    and return reasonable values when no app is available.
    """
    url = ''
    menu_items = []
    menu = ''
    name = 'none'


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


def get_apps(request):
    """get list of apps installed on this site"""
    logger = logging.getLogger(__name__)
    result = []
    names = []

    apps_paths = request.site.apps_paths

    for app_path in apps_paths:
        path = os.path.abspath(
            os.path.join(
                request.site.path,
                app_path,
            )
        )
        logger.debug('app path: %s', path)
        for app in os.listdir(path):
            if app not in names:
                filename = os.path.join(path, app, 'app.py')
                if os.path.exists(filename):
                    result.append(AppProxy(app, filename, request.site))
                    names.append(app)

    logger.debug('%s apps found', len(result))
    return result


def load_app(site, name):
    """get the location of an app by name"""
    logger = logging.getLogger(__name__)

    apps_paths = site.apps_paths
    for path in apps_paths:
        app_path = os.path.abspath(
            os.path.join(site.path, path, name)
        )
        filename = os.path.join(app_path, 'app.py')
        if os.path.exists(filename):
            logger.debug('located app %s', app_path)
            return AppProxy(name, filename, site)


def get_default_app_name(site, user):
    """get the default app for the currrent user"""
    msg = 'Configuration error: user %r unable to run default app %r'
    if user.is_authenticated:
        default_app = site.config.get('apps', 'home', 'home')
        # if not user.can_run(default_app):
        #     raise Exception(msg % (user.username, default_app))
    else:
        default_app = site.config.get('apps', 'index', 'content')
        # if not user.can_run(default_app):
        #     raise Exception(msg % (user.username, default_app))
    return default_app


def handle(request):
    """handle a request"""

    logger = logging.getLogger(__name__)
    logger.debug('apps.handle')

    user = request.user
    app_name = request.route and request.route[0] or None
    app = app_name and load_app(request.site, app_name)

    if app and app.enabled and user.can_run(app):
        logger.debug('running requested app')
        request.app = app
        zoom.render.add_helpers(helpers(request))
        return app.run(request)

    elif app and app.enabled and user.is_guest:
        logger.debug('redirecting to login')
        return RedirectResponse('/login')

    elif app and app.enabled:
        logger.warning('unable to run app %s (%r), redirecting to default', app_name, app.path)
        return RedirectResponse('/')

    elif app:
        logger.warning('app %s (%r) disabled, redirecting to default', app_name, app.path)
        return RedirectResponse('/')

    else:
        if app_name:
            logger.debug('unable to run requested app %r', app_name)
        app_name = get_default_app_name(request.site, request.user)
        app = load_app(request.site, app_name)
        if app and app.enabled and user.can_run(app):
            logger.debug('redirecting to default app %r', app_name)
            request.app = app
            zoom.render.add_helpers(helpers(request))
            return app.run(request)

        elif app and app.enabled:
            logger.debug('user %r cannot run %r', user.username, app_name)

        elif app:
            logger.debug('app %r is disabled', app_name)

        else:
            logger.debug('unable to load app %r', app_name)

    logger.debug('using NoApp()')
    request.app = NoApp()


def get_system_apps(request):
    """get a list of system apps"""
    names = DEFAULT_SYSTEM_APPS
    user = request.user
    apps = filter(user.can_run, [
        load_app(request.site, name) for name in names
        ])
    return apps


def system_menu_items(request):
    """Returns the system menu."""
    return html.li([
        app.link for app in get_system_apps(request)
        if app.visible and app.name != request.app.name
    ])


def system_menu(request):
    """Returns the system menu."""
    if request.user.is_authenticated:
        path = os.path.dirname(__file__)
        filename = os.path.join(path, 'views', 'system_pulldown_menu.html')
        return load_content(filename)
    else:
        return '<div class="system-menu"><ul>{}</ul></div>'.format(
            system_menu_items(request)
        )


def get_main_apps(request):
    """Returns the main apps."""
    names = DEFAULT_MAIN_APPS
    user = request.user
    apps = filter(user.can_run, [
        load_app(request.site, name) for name in names
        ])
    return apps


def main_menu_items(request):
    """Returns the main menu."""
    default_app_name = get_default_app_name(request.site, request.user)
    return html.li([
        app.name == default_app_name and '<a href="<dz:site_url>/">{}</a>'.format(app.title) or app.link
        for app in get_main_apps(request) if app.visible
    ])


def main_menu(request):
    """Returns the main menu."""
    return '<ul>%s</ul>' % main_menu_items(request)


def helpers(request):
    """return a dict of app helpers"""
    return dict(
        app_url=request.app.url,
        app_menu_items=request.app.menu_items,
        app_menu=request.app.menu,
        app_name=request.app.name,
        system_menu_items=system_menu_items(request),
        system_menu=system_menu(request),
        main_menu_items=main_menu_items(request),
        main_menu=main_menu(request),
        page_name=len(request.route)>1 and request.route[1] or '',
    )


def handler(request, handler, *rest):
    """Dispatch request to an application"""
    logger = logging.getLogger(__name__)
    logger.debug('apps_handler')
    if '.' not in sys.path:
        sys.path.insert(0, '.')
    return handle(request) or handler(request, *rest)
