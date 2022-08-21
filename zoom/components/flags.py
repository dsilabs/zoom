"""Flag components.

Flag components are persistantly stateful components that are either "on" or
"off". Their state is modified in asynchronously in the client. The base
Flag class may be subclassed to create more complex presentations then are
implemented here.

Flag states are per-user, and their IDs must be namespaced within that scope.
in this module. IDs default to the path of the current request in which they're
constructed.

>>> import zoom
>>> zoom.system.site = zoom.sites.Site()
>>> zoom.system.parts = zoom.Component()
>>> from zoom.components.flags import TextFlag
>>> my_flag = TextFlag('test_flag')
>>> my_flag.is_toggled
False
>>> rendered = my_flag.render()
>>> 'data-flag-id="test_flag"' in rendered
True
>>> my_flag.toggle()
>>> my_flag.is_toggled
True
>>> my_flag.toggle()
>>> my_flag.is_toggled
False
"""

import zoom

from zoom.context import context
from zoom.store import Entity, store_of
from zoom.response import JSONResponse
from zoom.render import add_helpers

ROUTE = '/_zoom/flags'


def current_user_id():
    """Return the ID of the currently authenticated user, or a placeholder
    string if none is avialable."""
    try:
        return str(context.user.user_id)
    except:
        return 'anonymous'


def get_current_path():
    """Retrieve the current request path or die if there isn't one."""
    request = getattr(context, 'request', None)
    if not request:
        raise ValueError("No active request")

    return request.path


class _FlagSet(Entity):
    """The entity used to persist flag state. Reserved for internal use.
    Presence in it's parent store implies the corresponding flag is set."""

    def __init__(self, flag_id=None, user_id=None, **kwargs):
        super().__init__(flag_id=flag_id, user_id=user_id, **kwargs)

    @classmethod
    def store(cls):
        return store_of(cls)


class Flag:
    """The base flag component."""

    def __init__(self, id=None, user_id=None, **data):
        """The given ID is the ID of the individual flag, which must be
        namespaced within its scope (global per-user), if provided. If none is,
        the URL of the current page is used.

        If no user ID is provided, the currently authenticated users ID will be
        used if available. If it isn't, the flags scope will be "anonymous".

        Optional data used for rendering the flag can be supplied as additional
        keyword arguments.

        Subclasses must implement generate_id() and render_in_state()"""
        self.user_id = user_id or current_user_id()
        self.data = data

        self.id = id or self.generate_id()

    def generate_id(self):
        """Generate a default ID if none is provided."""
        raise NotImplementedError()

    @classmethod
    def get(cls, id=None, user_id=None, **render_data):
        """A constructor alias that will often be more semantic."""
        return cls(id, user_id, **render_data)

    @property
    def set_entity(self):
        """The _FlagSet entity which indicates this flag is set, or None if it
        isn't."""
        return _FlagSet.store().first(
            flag_id=self.id,
            user_id=self.user_id
        )

    @property
    def is_toggled(self):
        """Whether or not this flag is "on"."""
        return bool(self.set_entity)

    def toggle(self):
        """Toggle the persistant state of this flag."""
        existing = self.set_entity
        if existing:
            _FlagSet.store().delete(existing._id)
        else:
            created = _FlagSet(self.id, self.user_id)
            _FlagSet.store().put(created)

    def render_in_state(self, state):
        """Render the flag content based on state."""
        raise NotImplementedError()

    def render(self):
        """Render this flag. Flags are rendered in both states, and those views
        are switched on the client when a flag is toggled. This allows
        server-side state based render logic to be respected without page
        reloads."""
        # Render this flag in both states.
        on_render = self.render_in_state(True)
        off_render = self.render_in_state(False)

        hide = 'display: none;'
        toggled = self.is_toggled

        # Return the flag container in the format the front-end management
        # logic expects.
        return '''<span data-flag-id="%s" data-state="%s">
            <span data-flag-case="true" style="%s">%s</span>
            <span data-flag-case="false" style="%s">%s</span>
        </span>'''%(
            self.id, str(toggled).lower(),
            hide if not toggled else str(), on_render,
            hide if toggled else str(), off_render
        )

    def __str__(self):
        """An alias for render()."""
        return self.render()


class _LabeledFlag(Flag):
    """An abstract subclass that implements default IDs based on optionally
    stateful labeling."""

    def get_label_in_state(self, state, stateful_default=False):
        state_label = self.data.get(('on' if state else 'off') + '_label')
        if state_label:
            return state_label
        std_label = self.data.get('label')
        if std_label:
            return std_label

        if not stateful_default or not state:
            return 'Toggle'
        return 'Un-toggle'

    def generate_id(self):
        return '_'.join((
            self.get_label_in_state(True),
            self.get_label_in_state(False),
            get_current_path()
        ))


class TextFlag(_LabeledFlag):
    """A flag that is presented as text."""

    def render_in_state(self, state):
        """Render this flag in the "on" or "off" state based on the parameter.
        Subclasses must implement this method."""
        label = self.get_label_in_state(state, True)
        hint = self.data.get('hint') or 'Click to toggle'

        return '<a title="%s" style="cursor: pointer;">%s</a>'%(hint, label)


class CheckboxFlag(_LabeledFlag):
    """A flag that is presented as a checkbox with optional labeling.

    >>> import zoom
    >>> zoom.system.site = zoom.sites.Site()
    >>> zoom.system.parts = zoom.Component()
    >>> from zoom.components.flags import CheckboxFlag
    >>> flag = CheckboxFlag('test_flag', on_label='On!', off_label='Off!')
    >>> 'On!' in flag.render() and 'Off!' in flag.render()
    True
    """

    def generate_id(self):
        return super().generate_id() + '_checkbox'

    def render_in_state(self, state):
        return '<input title="%s" type="checkbox" %s>'%(
            self.get_label_in_state(state), 'checked' if state else str()
        )


class IconFlag(_LabeledFlag):
    """A flag presented as an icon."""

    def get_icon_in_state(self, state):
        """Return the icon for the given state."""
        return self.data.get(('on' if state else 'off') + '_icon') \
            or self.data.get('icon') or 'star'

    def generate_id(self):
        return '_'.join((
            self.get_icon_in_state(True),
            self.get_icon_in_state(False),
            get_current_path()
        ))

    def render_in_state(self, state):
        zoom.requires('fontawesome')
        selector = '[data-flag-id="%s"]'%self.id

        # Maybe render styles. add_page_dependencies() doesn't work here in the
        # case that this is the result of a helper being used, since the head
        # of the document will already have been rendered.
        flag_style = '''
        <style>
            %s .icon-flag {
                cursor: pointer;
                color: %s;
            }
            %s .icon-flag[data-active="true"] {
                color: %s;
            }
        </style>
        '''%(
            selector,
            self.data.get('off_color') or 'gray',
            selector,
            self.data.get('on_color') or 'black'
        )
        fa_import = '''
            <link rel="stylesheet" href="//use.fontawesome.com/releases/v5.0.6/css/all.css"/>
        '''
        if getattr(context, '_flag_inc_fa', False):
            fa_import = str()
            context._flag_inc_fa = True

        return '''%s%s
            <i class="fa fa-%s icon-flag" title="%s" data-active="%s"></i>
        '''%(
            fa_import, flag_style,
            self.data.get('icon') or 'star',
            self.get_label_in_state(state),
            str(state).lower()
        )


def text_flag(id=None, label=None, on_label=None, off_label=None, \
        hint=None):
    return str(TextFlag(
        id=id, label=label,
        on_label=on_label, off_label=off_label,
        hint=hint
    ))


def icon_flag(id=None, on_icon=None, off_icon=None, icon=None, \
        on_color=None, off_color=None, on_label=None, off_label=None,
        label=None):
    return str(IconFlag(
        id=id, icon=icon,
        on_icon=on_icon, off_icon=off_icon,
        on_color=on_color, off_color=off_color,
        on_label=on_label, off_label=off_label, label=label
    ))


def checkbox_flag(id=None, on_label=None, off_label=None, label=None):
    return str(CheckboxFlag(
        id, on_label=on_label, off_label=off_label, label=label
    ))


def handle_flag_trigger(data):
    """Handles a flag trigger from the client, who provided the given data."""

    flag = Flag.get(data['id'])
    if not flag:
        return JSONResponse(
            {'error': 'No such flag'},
            status='422 Unprocessable Entity'
        )

    flag.toggle()
    return JSONResponse({'new_state': flag.is_toggled})


def handle(request, handler, *rest):
    """handle flags"""

    add_helpers({fn.__name__: fn for fn in (text_flag, icon_flag, checkbox_flag)})

    should_handle = (
        request.method == 'PUT' and \
        request.path == ROUTE
    )
    if should_handle:
        return handle_flag_trigger(request.data)

    return handler(request, *rest)
