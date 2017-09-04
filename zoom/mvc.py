"""
    zoom.mvc

    classes to support the model, view, controller pattern
"""
# pylint: disable=R0903

import logging
from inspect import getargspec, getfile
from os.path import abspath, split, join, isfile

import zoom
from zoom.component import component
from zoom.utils import kind


MISSING = '<span class="missing-view">{} missing</span>'
MISSING_CSS = '.missing-view { color: red }'


def as_attr(text):
    return text.replace('-', '_').lower()


def evaluate(obj, name, route, data):
    """Get the value of an attribute"""
    try:
        attr = getattr(obj, as_attr(name))
    except AttributeError:
        attr = None
    if attr:
        method = callable(attr) and attr
        if method:
            return method(*route, **data)
        else:
            return attr


def remove_buttons(data):
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
    def __init__(self, model=None, **kwargs):
        self.model = model
        self.__dict__.update(kwargs)

    def __call__(self, *args, **kwargs):
        method_name = len(args) and args[0] or 'index'
        return evaluate(self, method_name, args[1:], kwargs)


class View(Dispatcher):
    """View

    Use to display a model.
    """

    def __call__(self, *a, **k):

        logger = logging.getLogger(__name__)
        logger.debug('view called: %r %r', a, k)

        buttons, inputs = remove_buttons(k)

        if len(a):

            view_name = as_attr(a[0])

            if hasattr(self, view_name):
                """Show a specific collection view"""
                result = evaluate(self, view_name, a[1:], inputs)

            elif len(a) == 1:
                """Show the default view of an item"""
                try:
                    result = self.show(a[0], **inputs)
                except TypeError as e:
                    error_messages = 'takes exactly', 'got an unexpected'
                    if any(m in e.message for m in error_messages):
                        # if unable to show object with parameters, try
                        # showing without them
                        result = self.show(a[0])
                    else:
                        raise

            elif len(a) > 1:
                result = evaluate(self, a[-1:][0], ('/'.join(a[:-1]),), inputs)

            else:
                """No view"""
                result = None
        else:
            """Default collection view"""
            result = evaluate(self, 'index', (), inputs)

        if result:
            return result

    def show(self, *a, **k):
        pass


class DynamicView(View):
    """dynamic view - experimental!

    A class that provides views of other objects dynamically loading
    its own templates in the process.  Templates are rendered using
    python format() function so object structures can be taversed
    in the usual way within templates.

    The the view is referred to as self.  Any attribtues or properties
    can be simply accessed using self.<name> for whatever the name is.

    The object optionally passed as the first parameter upon construction
    is referred to as self.model.  Additional objects can be added as
    keyword parameters, which can then also be referenced with self.<name>.
    """

    # The js_wrapper is something we should have introduced earlier.  The
    # existing js rendering does not do this but it should have.  Consequently
    # we have apps having to test for themselves whether the document is
    # loaded when the framework could have done this.  Introducing it here
    # so that at least new apps using DynamicView do not have to do this
    # but ideally this logic would be implemented further along in the
    # rendering process so that it could be done once for the entire rendered
    # js code section.  We cant count on that yet so we're going to try
    # doing it here for every DynamicView - which is not ideal, but at least
    # it frees up the developer from having to do it now.  We will fix the
    # actual implementation once we know we wont break any legacy apps
    # in the process.

    asset_types = ['html', 'css', 'js']

    js_wrapper = """
        $(function(){{
            {}
        }});
    """

    def __init__(self, model=None, **k):
        View.__init__(self, model, **k)
        path, _ = split(abspath(getfile(self.__class__)))
        self._asset_path = path + '/views'

    def get_assets(self, name=None):
        def load(pathname):
            with open(pathname) as f:
                return f.read()
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
        assets = self.get_assets(view)
        if assets:
            result = {}
            for k, v in assets.items():
                if k in ['html']:
                    result[k] = v.format(self=self)
                elif k in ['js']:
                    result[k] = self.js_wrapper.format(v)
                else:
                    result[k] = v
            return component(**result)

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
        except AttributeError as e:
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
    """Controller

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

        method_name = len(args) and as_attr(args[0]) or 'index'

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



#
#
# def can(action):
#     """activity based authentication
#
#     Tests to see if user can perform some activity.
#
#         >>> class TheUser(object):
#         ...
#         ...     def __init__(self, name):
#         ...         self.name = name
#         ...
#         ...     def can(self, action, thing):
#         ...         return thing and thing.allows(self, action)
#
#         >>> class Thing(object):
#         ...
#         ...     def __init__(self, name):
#         ...         self.name = name
#         ...
#         ...     def allows(self, user, action):
#         ...         return bool(user.name == 'joe' and action == 'edit') or \\
#         ...                bool(user.name == 'sam' and action == 'delete')
#         ...
#         ...     def delete(self):
#         ...         return 'deleted!'
#         ...
#         ...     @can('edit')
#         ...     def update(self, name):
#         ...         self.name = name
#         ...         return 'hello {}!'.format(name)
#         ...
#         ...     @can('delete')
#         ...     def zap(self):
#         ...         return 'zapped!'
#         ...
#
#         >>> user.name = 'joe'
#         >>> user.name
#         'joe'
#
#         >>> user.can('edit', None)
#         False
#
#         >>> thing = Thing(name='rain')
#
#         >>> user.can('edit', thing)
#         True
#
#         >>> user.can('delete', thing)
#         False
#
#         >>> try:
#         ...    thing.zap()
#         ... except UnauthorizedException, e:
#         ...    'access denied'
#         'access denied'
#
#         >>> user.name = 'sam'
#         >>> try:
#         ...    thing.update('clouds')
#         ... except UnauthorizedException, e:
#         ...    'sunshine prevails'
#         'sunshine prevails'
#
#         >>> thing.zap()
#         'zapped!'
#
#         >>> user = TheUser(name='sally')
#         >>> user.can('edit', thing)
#         False
#
#     """
#     def wrapper(func):
#         def authorize_and_call(self, *args, **kwargs):
#             if self.allows(user, action):
#                 return func(self, *args, **kwargs)
#             raise UnauthorizedException('Unauthorized')
#         return authorize_and_call
#     return wrapper
