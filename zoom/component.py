"""
    zoom.component

    Components encapsulate all of the parts that are required to make a
    component appear on a page.  This can include HTML, CSS and Javascript
    parts and associated libraries.

    Components parts are assembled in the way that kind of part
    needs to be treated.  For example HTML parts are simply joined
    together in order and returned.  CSS parts on the other hand are
    joined together but any duplicate parts are ignored.

    When a caller supplies JS or CSS as part of the component being assembled
    these extra parts are submitted to the system to be included in thier
    proper place within a response (typically a page template).

    The Component object is currently experimental and is intended to be used
    in future releases.
"""

import logging
import threading
import sys

import zoom
from zoom.utils import OrderedSet


class Component(object):
    """component of a page response

    >>> c = Component()
    >>> c
    <Component: {'html': []}>

    >>> c += 'test'
    >>> c
    <Component: {'html': ['test']}>

    >>> c += dict(css='mycss')
    >>> c
    <Component: {'css': OrderedSet(['mycss']), 'html': ['test']}>

    >>> c += dict(css='mycss')
    >>> c
    <Component: {'css': OrderedSet(['mycss']), 'html': ['test']}>

    >>> c += 'test2'
    >>> sorted(c.parts.items())
    [('css', OrderedSet(['mycss'])), ('html', ['test', 'test2'])]

    >>> Component() + 'test1' + 'test2'
    <Component: {'html': ['test1', 'test2']}>

    >>> Component() + 'test1' + dict(css='mycss')
    <Component: {'css': OrderedSet(['mycss']), 'html': ['test1']}>

    >>> Component('test1', Component('test2'))
    <Component: {'html': ['test1', 'test2']}>

    >>> Component(
    ...    Component('test1', css='css1'),
    ...    Component('test2', Component('test3', css='css3')),
    ... )
    <Component: {'css': OrderedSet(['css1', 'css3']), 'html': ['test1', 'test2', 'test3']}>

    >>> Component((Component('test1', css='css1'), Component('test2', css='css2')))
    <Component: {'css': OrderedSet(['css1', 'css2']), 'html': ['test1', 'test2']}>

    >>> Component(Component('test1', css='css1'), Component('test2', css='css2'))
    <Component: {'css': OrderedSet(['css1', 'css2']), 'html': ['test1', 'test2']}>

    >>> zoom.system.parts = Component()
    >>> c = Component(Component('test1', css='css1'), Component('test2', css='css2'))
    >>> c.render()
    'test1test2'

    >>> page2 = \\
    ...    Component() + \\
    ...    '<h1>Title</h1>' + \\
    ...    dict(css='mycss') + \\
    ...    dict(js='myjs') + \\
    ...    'page body goes here'
    >>> t = (
    ...    "<Component: {'css': OrderedSet(['mycss']), "
    ...    "'html': ['<h1>Title</h1>', 'page body goes here'], "
    ...    "'js': OrderedSet(['myjs'])}>"
    ... )
    >>> #print(repr(page2) + '\\n' + t)
    >>> repr(page2) == t
    True
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, *args, **kwargs):
        """construct a Component

        >>> Component()
        <Component: {'html': []}>

        >>> Component('body')
        <Component: {'html': ['body']}>

        >>> Component('body', css='css1')
        <Component: {'css': OrderedSet(['css1']), 'html': ['body']}>

        >>> t = Component('body', css='css1', js='js1')
        >>> repr(t) == (
        ...     "<Component: {"
        ...     "'css': OrderedSet(['css1']), "
        ...     "'html': ['body'], "
        ...     "'js': OrderedSet(['js1'])"
        ...     "}>"
        ... )
        True
        """

        def is_iterable(obj):
            """Returns True if object is an iterable but not a string"""
            return hasattr(obj, '__iter__') and not isinstance(obj, str)

        def flatten(items):
            """Returns list of items with sublists incorporated into list"""
            items_as_iterables = list(is_iterable(i) and i or (i,) for i in items)
            return [i for j in items_as_iterables for i in j]

        self.parts = {
            'html': [],
        }
        for arg in flatten(args):
            self += arg
        self += kwargs

    def __iadd__(self, other):
        """add something to a component

        >>> page = Component('<h1>Title</h1>')
        >>> page += dict(css='mycss')
        >>> page += 'page body goes here'
        >>> page += dict(js='myjs')
        >>> result = (
        ...     "<Component: {"
        ...     "'css': OrderedSet(['mycss']), "
        ...     "'html': ['<h1>Title</h1>', 'page body goes here'], "
        ...     "'js': OrderedSet(['myjs'])"
        ...     "}>"
        ... )
        >>> #print(page)
        >>> #print(result)
        >>> result == repr(page)
        True

        >>> page = Component('test')
        >>> page += dict(html='text')
        >>> page
        <Component: {'html': ['test', 'text']}>

        """
        def rendered(obj):
            """call the render method if necessary"""
            if not isinstance(obj, Component) and hasattr(obj, 'render'):
                return obj.render()
            return obj

        other = rendered(other)

        if isinstance(other, str):
            self.parts['html'].append(other)
        elif isinstance(other, dict):
            for key, value in other.items():
                part = self.parts.setdefault(key, OrderedSet())
                if key == 'html':
                    if isinstance(value, list):
                        part.extend(value)
                    else:
                        part.append(value)
                else:
                    if isinstance(value, list):
                        part |= value
                    else:
                        part |= [value]
        elif isinstance(other, Component):
            for key, value in other.parts.items():
                part = self.parts.setdefault(key, OrderedSet())
                if key == 'html':
                    part.extend(value)
                else:
                    part |= value
        return self

    def __add__(self, other):
        """add a component to something else

        >>> (Component() + 'test1' + dict(css='mycss')) + 'test2'
        <Component: {'css': OrderedSet(['mycss']), 'html': ['test1', 'test2']}>

        >>> Component() + 'test1' + dict(css='mycss') + dict(css='css2')
        <Component: {'css': OrderedSet(['mycss', 'css2']), 'html': ['test1']}>
        """
        result = Component()
        result += self
        result += other
        return result

    def __repr__(self):
        return '<Component: {{{}}}>'.format(
            ', '.join(
                '{!r}: {!r}'.format(i, j)
                for i, j in sorted(self.parts.items())
            )
        )

    def render(self):
        """renders the component"""
        if not hasattr(zoom.system, 'parts'):
            zoom.system.parts = Component()
        zoom.system.parts += self
        return ''.join(map(str, self.parts['html']))

    def __str__(self):
        return self.render()


def render(*components):
    html_part = Component(*components).render()
    return html_part


component = Component


def compose(*args, **kwargs):
    """Compose a response - DEPRECATED"""
    zoom.system.parts += component(**kwargs)
    return ''.join(args)


def handler(request, handler, *rest):
    """Component handler"""

    pop = request.session.__dict__.pop

    zoom.system.parts = Component(
        success=pop('system_successes', []),
        warning=pop('system_warnings', []),
        error=pop('system_errors', []),
        stdout=pop('system_stdout', '')
    )

    result = handler(request, *rest)

    logger = logging.getLogger(__name__)
    logger.debug('component middleware')

    # TODO: clean this up, use a single alerts list with an alert type value
    success_alerts = zoom.system.parts.parts.get('success')
    if success_alerts:
        if not hasattr(request.session, 'system_successes'):
            request.session.system_successes = []
        request.session.system_successes = list(success_alerts)

    warning_alerts = zoom.system.parts.parts.get('warning')
    if warning_alerts:
        if not hasattr(request.session, 'system_warnings'):
            request.session.system_warnings = []
        request.session.system_warnings = list(warning_alerts)

    error_alerts = zoom.system.parts.parts.get('error')
    if error_alerts:
        if not hasattr(request.session, 'system_errors'):
            request.session.system_errors = []
        request.session.system_errors = list(error_alerts)

    stdout = sys.stdout.getvalue()
    if stdout:
        renderable = (
            isinstance(result.content, str) and '{*stdout*}' in result.content
        )
        if not renderable:
            request.session.system_stdout = stdout

    return result

