""" zoom.apps handles requests by locating and calling a suitable app """

import configparser
import imp
import importlib
import logging
import os
import sys
import urllib

import zoom
import zoom.components.apps
from zoom.components import as_links
from zoom.database import Database
import zoom.html as html
from zoom.utils import existing
from zoom.users import Users
from zoom.background import load_app_background_jobs


DEFAULT_SYSTEM_APPS = ['register', 'profile', 'settings', 'login', 'logout']
DEFAULT_MAIN_APPS = ['home', 'admin', 'apps']
DEFAULT_SETTINGS = dict(
    title='',
    icon='cube',
    enabled=True,
    visible=True,
    theme='',
    description='',
    categories='',
    tags='',
    keywords='',
    in_development=False,
)

logger = logging.getLogger(__name__)


class app_context:
    """App Context Manager"""

    def __init__(self, path):
        self.path = path
        self.save_dir = os.getcwd()

    def __enter__(self):
        sys.path.insert(0, self.path)
        os.chdir(self.path)

    def __exit__(self, exc_type, exc_value, traceback):
        os.chdir(self.save_dir)
        sys.path.remove(self.path)


def load_module(module, filename):
    """Dynamically load a module"""

    pathname = os.path.realpath(filename)
    if os.path.exists(pathname):
        if module in sys.modules:
            del sys.modules[module]
        path = os.path.dirname(pathname)
        with app_context(path):
            importlib.invalidate_caches()
            m = importlib.import_module(module)
            return m


class App(object):
    """A Zoom application

    Looks for a method to satisfy the request.  If the method is
    not specified, it falls back to 'index'.  If there is no
    method on the app object to satisfy the method then it looks
    for a file in the app directory by that same name.  If it
    finds such a file it looks for the an entrypoint and if found
    it calls the entrypoint with the parameters the entrypoint
    expects.
    """

    def __init__(self, menu=None):
        self.menu = [] if menu is None else menu
        self.request = None

    def static(self, *args):
        return zoom.middleware.serve_response('static', *args)

    def process(self, *route, **data):
        """Process request parameters"""

        def if_callable(method):
            """test if callable and return it or None"""
            return callable(method) and method

        isfile = os.path.isfile
        logger.debug('app called with route %r', route)

        if len(route) > 1:
            module = route[1]
            rest = route[2:]
        else:
            module = 'index'
            rest = route[1:]

        try:
            method = getattr(self, module)
        except AttributeError:
            method = None

        if method:
            result = method(*rest, **data)
            return result

        if len(route) > 1 and isfile('%s.py' % route[1]):
            module = route[1]
            rest = route[2:]
        else:
            module = 'index'
            rest = route[1:]

        filename = '{}.py'.format(module)
        if isfile(filename):
            source = load_module(module, os.path.realpath(filename))
            main = if_callable(getattr(source, 'main', None))
            app = if_callable(getattr(source, 'app', None))
            view = if_callable(getattr(source, 'view', None))
            controller = if_callable(getattr(source, 'controller', None))
        else:
            main = app = view = controller = None

        return (
            main and main(rest, self.request) or
            app and app(*rest, **data) or
            controller and controller(*rest, **data) or
            view and view(*rest, **data)
        )

    def __call__(self, request):
        self.request = request
        return self.process(*request.route, **request.data)


class AppProxy:
    """App Proxy

    Contains the various extra supporting parts of an app besides
    the actual functionality.  Apps themselves are simply callables
    that accept a request and return a response.  They can be implemented
    as simple functions or as something more substantial such as
    a subclass of the App class above.  That's entirely up to the
    app developer.  The AppProxy takes care of the other parts that
    an app needs, from it's location to it's icon to it's config files.
    """

    def __init__(self, name, filename, site):

        self.name = name
        self.filename = filename

        request = getattr(zoom.system, 'request')
        if request:
            user = zoom.system.request.user
        else:
            user = Users(site.db).first(username='guest')

        self._method = None

        default_app_name = get_default_app_name(site, user)

        slug = '/' + name
        if name == default_app_name:
            slug = '/'

        self.url = site.url + slug
        self.abs_url = site.abs_url + slug
        self.path = os.path.dirname(filename)
        self.site = site
        self.config_parser = configparser.ConfigParser()
        self.config = self.get_config(DEFAULT_SETTINGS)
        self.link = zoom.helpers.link_to(self.title, self.url)
        self.request = None
        self.packages = {}
        self.common_packages = {}

        get = self.config.get
        self.visible = get('visible') not in zoom.utils.NEGATIVE
        self.enabled = get('enabled')
        self.author = get('author')
        self.version = get('version')
        self.theme = get('theme') or site.theme
        self.theme_path = existing(site.themes_path, self.theme)
        self.icon = get('icon')
        self.as_icon = self.get_icon_view()
        self.in_development = get('in_development')

        self._templates_paths = None

    @property
    def icon_class(self):
        icon = self.config.get('icon')
        is_bootstrap_icon = icon.startswith('bi-')
        if is_bootstrap_icon:
            return 'bi ' + icon
        return 'fa fa-' + icon

    @property
    def templates_paths(self):
        """Calculate Templates Paths"""
        if self._templates_paths:
            return self._templates_paths
        if self.theme:
            template_path = existing(self.theme_path, 'templates')
            paths = list(filter(bool, [
                template_path,
                self.theme_path,
            ]))
        else:
            paths = []
        self._templates_paths = paths
        return paths

    def get_icon_view(self):
        return """
        <div class="zoom-app-as-icon">
            <a href="{self.url}">
                <div class="zoom-app-icon">
                    <i class="{self.icon_class}" aria-hidden="true"></i>
                </div>
                <div class="zoom-app-title">
                    {self.title}
                </div>
            </a>
        </div>
        """.format(self=self)

    @property
    def method(self):
        """Returns the app callable entry point"""
        if self._method is None:
            split, join = os.path.split, os.path.join
            module = load_module('app', self.filename)
            self._method = getattr(module, 'app')
            self.packages = zoom.packages.load(join(self.path, 'packages.json'))
            apps_dir = split(self.path)[0]
            self.common_packages = zoom.packages.load(join(apps_dir, 'packages.json'))
        return self._method

    @property
    def title(self):
        """Returns the app title"""
        return self.config.get('title', self.name) or self.name.capitalize()

    @property
    def description(self):
        """Returns the app description"""
        return self.config.get('description') or \
            'The {} app.'.format(self.title)

    @property
    def keywords(self):
        """Returns the app keywords"""
        return self.config.get('keywords') or ', '.join(self.description.split())

    @property
    def background_jobs(self):
        return load_app_background_jobs(self)

    def run(self, request):
        """run the app"""
        self.request = request
        request.app = self
        app_callable = self.method
        self.request.profiler.add('app loaded')
        with app_context(self.path):
            response = app_callable(request)
            result = respond(response, request)
        return result

    def menu(self):
        """generate an app menu"""

        def by_name(name):
            """Returns a function that selects an item by name"""
            def selector(item):
                """Returns True if the item name matches"""
                return name == item.name
            return selector

        route = self.site.request.route
        logger.debug('constructing menu')

        menu = getattr(self.method, 'menu', [])
        if callable(menu):
            menu = menu()  #pylint: disable=not-callable

        selected = (
            len(route) > 2 and route[0] == 'content' and route[2] or
            len(route) > 1 and route[1] or
            len(route) == 1 and route[0] != 'content' and 'index'
        )
        logger.debug('selected: %s', selected)

        result = as_links(menu, select=by_name(selected))
        return result

    def read_config(self, section, key, default=None):
        """read app config file values"""
        path = self.path
        join = os.path.join
        split = os.path.split

        local_config_file = join(path, 'config.ini')
        shared_config_file = join(split(path)[0], 'default.ini')
        system_config_file = join(split(path)[0], '..', '..', 'default.ini')

        config = self.config_parser
        try:
            config.read(local_config_file)
            return config.get(section, key)
        except BaseException:
            try:
                config.read(shared_config_file)
                return config.get(section, key)
            except BaseException:
                try:
                    config.read(system_config_file)
                    return config.get(section, key)
                except BaseException:
                    if default is not None:
                        return default
                    else:
                        tpl = 'config setting [{}]{} not found in {} or {} or {}'
                        msg = tpl.format(section, key, local_config_file, shared_config_file, system_config_file)
                        raise Exception(msg)

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
            try:
                self.config_parser.read(pathname)
            except BaseException as e:
                logger.error('Unable to read %r\n%s', pathname, e)
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
    theme = None
    title = ''
    description = ''
    keywords = ''
    common_packages = {}
    packages = {}

    def run(self, request):
        status = '404 Not Found'
        template = zoom.templates.page_not_found
        response = zoom.page(template, status=status)
        return response.render(request)


def respond(content, request):
    """construct a response"""

    html_response = zoom.response.HTMLResponse
    json_response = zoom.response.JSONResponse

    if content:
        if isinstance(content, zoom.response.Response):
            result = content

        elif isinstance(content, (str, zoom.Component)):
            result = zoom.Page(content).render(request)

        elif hasattr(content, 'render') and content.render:
            result = content.render(request)

        elif isinstance(content, (list, set, tuple)):
            result = html_response(''.join(content))

        elif isinstance(content, (dict, )):
            result = json_response(content)

        else:
            result = html_response('OK')

        return result


def load_app(site, name):
    """get the location of an app by name"""
    apps_paths = site.apps_paths
    for path in apps_paths:
        app_path = os.path.abspath(
            os.path.join(site.path, path, name)
        )
        filename = os.path.join(app_path, 'app.py')
        if os.path.exists(filename):
            return AppProxy(name, filename, site)


def get_default_app_name(site, user):
    """get the default app for the currrent user"""
    if user.is_authenticated:
        default_app = site.home_app_name
    else:
        default_app = site.index_app_name
    return default_app


def make_source_url(app_name, request):
    """URL to pass to recovery apps"""
    original_url = ''.join([
        request.protocol,
        '://',
        request.host,
        request.path
    ])
    params = dict(
        original_url=original_url,
    )
    if request.referrer:
        params['original_referrer_url'] = request.referrer
    url = ''.join([
        '/',
        app_name,
        '?',
        urllib.parse.urlencode(params)
    ])
    return url


def handle(request):
    """handle a request"""

    def run_app(app):
        """Run an app"""
        request.app = app
        zoom.render.add_helpers(helpers(request))

        saved_database_debug_setting = Database.debug
        try:
            Database.debug = request.site.monitor_app_database
            request.profiler.add('system ready')
            result = app.run(request)
            request.profiler.add('app finished')
        finally:
            Database.debug = saved_database_debug_setting
        return result

    site = request.site
    user = request.user
    if user.is_authenticated:
        logger.debug('user is authenticated')
    else:
        logger.debug('user is a guest')
    app_name = request.route and request.route[0] or None
    redirect_response = zoom.response.RedirectResponse

    if not app_name:
        logger.debug('no app name provided')
        app_name = get_default_app_name(request.site, request.user)
        if app_name:
            logger.debug('loading default app %r', app_name)
            app = load_app(request.site, app_name)

            if not app:
                logger.warning('unable to load default app %r', app_name)

            elif not app.enabled:
                logger.warning('default app %r deactivated', app_name)

            elif not user.can_run(app):
                msg = (
                    '%r has insufficient privileges to run default app %s (%r), '
                    'returning 404'
                )
                logger.warning(msg, user.username, app_name, app.path)

            else:
                return run_app(app)

        app = NoApp()
        return run_app(app)

    logger.debug('app_name is: %r', app_name)
    app = app_name and load_app(request.site, app_name)

    if not app:
        logger.debug('app %r not found in site.apps_paths', app_name)
        logger.debug('site.apps_paths: %r', request.site.apps_paths)

        if site.locate_app_name:
            locate_url = make_source_url(site.locate_app_name, request)
            logger.debug('redirecting to %r', locate_url)
            return redirect_response(locate_url)

        app_name = get_default_app_name(request.site, request.user)
        logger.debug('default app is %r', app_name)
        request.route.insert(0, app_name)
        logger.debug('updated route is %r', request.route)
        if app_name:
            logger.debug('loading default app %r', app_name)
            app = load_app(request.site, app_name)

            if not app:
                logger.warning('unable to load default app %r', app_name)

            elif not app.enabled:
                logger.warning('default app %r deactivated', app_name)

            elif not user.can_run(app):
                msg = (
                    '%r has insufficient privileges to run default app %s (%r), '
                    'returning 404'
                )
                logger.warning(msg, user.username, app_name, app.path)

            else:
                return run_app(app)

            app = NoApp()
            return run_app(app)

        logger.debug('app not found redirecting to /')
        return redirect_response('/')

    elif not app.enabled:
        msg = 'app %s (%r) deactivated, redirecting to default'
        logger.warning(msg, app_name, app.path)
        return redirect_response('/')

    elif user.can_run(app):
        logger.debug('running requested app')
        return run_app(app)

    elif not user.is_authenticated:
        logger.debug('redirecting to login')
        if site.login_app_name:
            login_url = make_source_url(site.login_app_name, request)
            return redirect_response(login_url)
        return redirect_response('/login')

    else:
        msg = (
            '%r has insufficient privileges to run app %s (%r), '
            'redirecting to default'
        )
        logger.warning(msg, user.username, app_name, app.path)

        if site.auth_app_name:
            auth_url = make_source_url(site.auth_app_name, request)
            return redirect_response(auth_url)

        return redirect_response('/')


def get_system_apps(request):
    """Returns a list containing the system apps.

    System apps are apps that appear in the system menu, which is usually found
    at the top right of a web site.  The system menu typically includes apps such
    as login, logout, profile, settings and register.

    This list can be defined in the site.ini file in the [apps] section using the
    key `system`.  A example is provided in the default site.ini file.
    """
    get = request.site.config.get
    names = get('apps', 'system', '')
    names = names and [s.strip() for s in names.split(',')] or DEFAULT_SYSTEM_APPS
    user = request.user
    apps = filter(user.can_run, [
        load_app(request.site, name) for name in names
        ])
    return apps


def system_menu_items(request):
    """Returns the system menu."""
    return html.li([
        app.link for app in get_system_apps(request)
        if app.visible
    ])


def system_menu(request):
    """Returns the system menu."""
    if request.user.is_authenticated:
        path = os.path.dirname(__file__)
        filename = os.path.join(path, 'views', 'system_pulldown_menu.html')
        return zoom.tools.load_content(filename)
    else:
        return '<div class="system-menu"><ul>{}</ul></div>'.format(
            system_menu_items(request)
        )


def get_main_apps(request):
    """Returns a list of the main apps.

    Main apps are apps that appear in the main menu, which is usually found
    at the top of a web site's pages.  The system menu typically includes apps
    such as home, admin and the apps app.

    This list can be defined in the site.ini file in the [apps] section using the
    key `main`.  A example is provided in the default site.ini file.
    """
    get = request.site.config.get
    names = get('apps', 'main', '')
    names = names and [s.strip() for s in names.split(',')] or DEFAULT_MAIN_APPS
    user = request.user
    apps = filter(user.can_run, [
        load_app(request.site, name) for name in names
        ])
    return apps


def main_menu_items(request):
    """Returns the main menu."""

    def style(app):
        return app.name == current_app_name and 'class="active" ' or ''

    default_app_name = get_default_app_name(request.site, request.user)
    current_app_name = request.route and request.route[0] or default_app_name

    return html.li([
        app.name == default_app_name
        and '<a {}href="<dz:site_url>/">{}</a>'.format(
            style(app), app.title
        )
        or '<a {}href="<dz:site_url>{}">{}</a>'.format(
            style(app), app.url, app.title
        )
        for app in get_main_apps(request) if app.visible
    ])


def main_menu(request):
    """Returns the main menu."""
    return '<ul>%s</ul>' % main_menu_items(request)


def apps_menu(request):
    """Returns a menu of available apps"""

    def calc_position(app):
        """position of app"""
        name = app.name
        return names.index(name) if name in names else 9999

    site = request.site
    user = request.user
    get = site.config.get

    names = get('apps', 'apps', '')
    names = names and [s.strip() for s in names.split(',')] or []

    system_apps = list(get_system_apps(request))
    main_apps = list(get_main_apps(request))
    exclude = list(a.name for a in system_apps + main_apps)

    if not 'content' in names:
        exclude.append('content')

    apps = [
        app for app in sorted(site.apps, key=calc_position)
        if app.name not in exclude and app.visible
        and app.name in user.apps
    ]

    menu_item = zoom.components.apps.AppMenuItem()
    active_app = request.app.name

    return html.div(
        html.ul(
            menu_item.format(
                app=app,
                active=' active' if app.name == active_app else ''
            ) for app in apps
            if app.name in user.apps and
            app.visible and app.name not in exclude
        ), classed='apps-menu'
    )


def helpers(request):
    """return a dict of app helpers"""
    app = request.app
    return dict(
        app_title=app.title,
        app_url=request.app.url,
        app_menu=request.app.menu,
        app_name=request.app.name,
        app_class=zoom.utils.id_for(request.app.name.strip()),
        app_description=request.app.description,
        app_keywords=request.app.keywords,
        system_menu_items=system_menu_items(request),
        system_menu=system_menu(request),
        main_menu_items=main_menu_items(request),
        main_menu=main_menu(request),
        apps_menu=apps_menu(request),
        page_name=len(request.route) > 1 and request.route[1] or '',
    )


def handler(request, next_handler, *rest):
    """Dispatch request to an application"""
    logger.debug('apps_handler')
    response = handle(request)
    if isinstance(response, zoom.response.RedirectResponse):
        logger.debug('app redirecting to %s', response.headers['Location'])
    else:
        logger.debug('app responded with type %s', type(response))
    return response or next_handler(request, *rest)


def get_app():
    """Return the current app"""
    return getattr(zoom.system.request, 'app', None)
