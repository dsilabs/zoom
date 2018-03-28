"""
    zoom.mvc

    classes to support the model, view, controller pattern
"""
# pylint: disable=R0903

import logging
from inspect import getfile
from os.path import abspath, split, join, isfile

import zoom
from zoom.component import component
from zoom.utils import kind


MISSING = '<span class="missing-view">{} missing</span>'
MISSING_CSS = '.missing-view { color: red }'


def as_attr(text):
    """Replace hyphens with underscores

    >>> as_attr('this-page')
    'this_page'
    """
    return text.replace('-', '_').lower()


def evaluate(obj, name, route, data):
    """Get the value of an attribute

    >>> thing = zoom.utils.Bunch(name='Thing', show=lambda a, name: 'showing %s' % name)
    >>> route, data = ('app',), {'name': 'one'}
    >>> evaluate(thing, 'name', route, data)
    'Thing'
    >>> evaluate(thing, 'show', route, data)
    'showing one'
    """
    try:
        attr = getattr(obj, as_attr(name))
    except AttributeError:
        attr = None
    if attr:
        method = callable(attr) and attr
        if method:
            return method(*route, **data)
    return attr


def remove_buttons(data):
    """Remove buttons from input data

    >>> data = dict(name='Pat', age=20, save_button='Save')
    >>> zoom.utils.pp(remove_buttons(data))
    [
      {
        "save_button": "Save"
      },
      {
        "age": 20,
        "name": "Pat"
      }
    ]

    """
    buttons = {}
    names = list(data.keys())
    for name in names:
        lname = name.lower()
        if lname.endswith('_button'):
            buttons[lname] = data[name]
            del data[name]
    return buttons, data


class Dispatcher(object):
    """dispatches actions to a method

    Accepts incoming user input actions and calls the appropriate method to
    handle the request.  Unlike the Controller and the View, the Dispatcher
    doesn't alter the incoming input in any way, but rather passes it along
    verbatim to the method handling the request.

    >>> class MyDispatcher(Dispatcher):
    ...     def add(self, a, b):
    ...         return a + b
    >>> dispatcher = MyDispatcher()
    >>> dispatcher('add', 1, 2)
    3
    """
    home = None

    def __init__(self, model=None, **kwargs):
        self.model = model
        self.__dict__.update(kwargs)

    def __call__(self, *args, **kwargs):
        method_name = args[0] if args else 'index'
        return evaluate(self, method_name, args[1:], kwargs)


class View(Dispatcher):
    """Views a model

    Use to view a model without altering it.

    >>> class MyView(View):
    ...     def index(self):
    ...         return 'index page'
    ...     def show(self, item):
    ...         return 'showing %s' % item
    ...     def throw(self, item):
    ...         raise Exception('thrown')
    >>> view = MyView()
    >>> view()
    'index page'
    >>> view('100')
    'showing 100'
    >>> view('100', data=dict(d='extra'))
    'showing 100'

    >>> thrown = False
    >>> try:
    ...     view('throw')
    ... except Exception:
    ...     thrown = True
    >>> thrown
    True
    """

    def __call__(self, *args, **kwargs):

        logger = logging.getLogger(__name__)
        logger.debug('view called: %r %r', args, kwargs)

        _, inputs = remove_buttons(kwargs)

        if args:

            view_name = as_attr(args[0])

            if hasattr(self, view_name):
                # show a specific collection view
                result = evaluate(self, view_name, args[1:], inputs)

            elif len(args) == 1:
                # show the default view of an item
                try:
                    result = self.show(args[0], **inputs)
                except TypeError as err:
                    error_messages = 'takes exactly', 'got an unexpected'
                    if any(m in str(err) for m in error_messages):
                        # if unable to show object with parameters, try
                        # showing without them
                        result = self.show(args[0])
                    else:
                        raise

            elif len(args) > 1:
                result = evaluate(
                    self, args[-1:][0], ('/'.join(args[:-1]),), inputs
                )

            else:
                # no view
                result = None
        else:
            # default collection view
            result = evaluate(self, 'index', (), inputs)

        if result:
            return result

        return self.home

    def show(self, *args, **kwargs):
        """View a specific item (stub)"""
        pass


class DynamicView(View):
    """Dynamic View - experimental (may change)

    A decorator class that provides views of objects dynamically loading
    its own templates in the process.

    Within templates the object being decorated is referred to as self.  Any
    attribtues or properties can be simply accessed using self.<name> for
    whatever the name is.  Templates are rendered using python format()
    function so object structures can be taversed in the usual way within
    templates.

    The object optionally passed as the first parameter upon construction
    is referred to as self.model.  Additional objects can be added as
    keyword parameters, which can then also be referenced with self.<name>.
    """

    asset_types = ['html', 'css', 'js']

    def __init__(self, model=None, **k):
        View.__init__(self, model, **k)
        path, _ = split(abspath(getfile(self.__class__)))
        self._asset_path = path + '/views'

    def get_assets(self, name=None):
        """Get view assets"""
        def load(pathname):
            """Load a file into a string"""
            with open(pathname) as asset_file:
                return asset_file.read()
        start = join(self._asset_path, kind(self))
        if name:
            start += '.' + name
        result = {}
        for asset_type in self.asset_types:
            pathname = '{}.{}'.format(start, asset_type)
            if isfile(pathname):
                result[asset_type] = load(pathname)
        return result

    def render(self, view=None):
        """Render the view"""
        assets = self.get_assets(view)
        if assets:
            result = {}
            for k, v in assets.items():
                if k in ['html']:
                    result[k] = v.format(self=self)
                elif k in ['js']:
                    result[k] = v
                else:
                    result[k] = v
            return component(**result)
        return None

    def __getattr__(self, view):
        if view.startswith('_'):
            # This object is not an iterator but it sometimes gets asked this
            # way so since we're providing a catch-all attribute handler we
            # want to make sure we don't mislead the caller into thinking
            # we have an __iter__ method.  While we're at it we should make
            # sure we're not misleading about anything starting with '_'.
            raise AttributeError('{!r} object has no attribute {!r}'.format(
                self.__class__.__name__,
                view
            ))
        try:
            return getattr(self.model, view)

        except AttributeError:
            component(css=MISSING_CSS)
            return \
                self.render(view) or \
                MISSING.format('.'.join([self.__class__.__name__, view]))

    def __repr__(self):
        return self.render() or component(
            MISSING.format(self.__class__.__name__),
            css=MISSING_CSS
            )

    def __str__(self):
        return self.render().render()


class Controller(Dispatcher):
    """Controls a Model

    Use this class when an action is going to change the state
    of the model.
    """
    def __call__(self, *args, **kwargs):

        logger = logging.getLogger(__name__)
        logger.debug('controller called: %r %r', args, kwargs)

        result = None

        buttons, inputs = remove_buttons(kwargs)

        # Buttons
        if buttons:
            button_name = list(buttons.keys())[0]
            result = evaluate(self, button_name, args, inputs)
            if result:
                return result

        method_name = as_attr(args[0]) if args else 'index'

        # Collection methods
        if hasattr(self, method_name):
            result = evaluate(self, method_name, args[1:], inputs)

        # Object methods
        elif len(args) > 1:
            method_name = len(args) and as_attr(args[-1:][0])
            result = evaluate(self, method_name, args[:-1], inputs)

        # If controller returned a result, we're done
        if result:
            return result

        return self.home


def dispatch(*args):
    """Create and call dispatchers in order

    Returns a function that will handle a request by trying each argument
    in succession.  If the argument is a Dispatcher it will be created before
    being called.  If it is a callable, it will be called as-is.  As soon
    as one of them returns a response we exit.  If none of the returns a
    response we return None, which generally results in a 404.

    >>> class MyView(View):
    ...     def index(self):
    ...         return 'home page'
    ...     def show(self, key):
    ...         return 'showing %s' % key
    >>> main = zoom.dispatch(MyView)

    >>> main((), zoom.utils.Bunch(data={}))
    'home page'

    >>> main(('100',), zoom.utils.Bunch(data={}))
    'showing 100'
    """
    logger = logging.getLogger(__name__)
    def _dispatch(route, request):
        """Call each dispatcher in succession"""
        for arg in args:
            if issubclass(arg, Dispatcher):
                method = arg()
            elif callable(arg):
                method = arg
            else:
                msg = 'zoom.dispatch only works with Dispatchers or callables'
                raise Exception(msg)
            logger.debug('dispatching %r', method)
            response = method(*route, **request.data)
            if response:
                return response
        return None
    return _dispatch
