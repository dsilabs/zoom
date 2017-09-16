"""
    zoom.render

    rendering tools
"""


import logging

import zoom
import zoom.fill
import zoom.helpers


def apply_helpers(template, obj, providers):
    """employ helpers to fill in a template

    >>> class User(object): pass
    >>> user = User()
    >>> user.name = 'World'
    >>> apply_helpers('Hello <dz:name>!', user, {})
    'Hello World!'

    >>> apply_helpers('Hello <dz:other>!', user, [{'other': 'Sam'}])
    'Hello Sam!'

    >>> apply_helpers('Hello <dz:other>!', user, {})
    'Hello <dz:other>!'

    >>> apply_helpers('Hello {{other}}!', user, {})
    'Hello {{other}}!'
    """
    fill = zoom.fill.fill

    def filler(helpers):
        """callback for filling in templates"""

        def _filler(name, *args, **kwargs):
            """handle the details of filling in templates"""

            # TODO: phase this block out and get caller to provide
            #       helpers instead
            if hasattr(obj, name):
                attr = getattr(obj, name)
                if callable(attr):
                    repl = attr(obj, *args, **kwargs)
                else:
                    repl = attr
                return fill(repl, _filler)

            helper = helpers.get(name)
            if helper is not None:
                if callable(helper):
                    repl = helper(*args, **kwargs)
                else:
                    repl = helper
                return fill(repl, _filler)

            logger.debug('no help for %r', (name, args, kwargs))

        return _filler

    logger = logging.getLogger(__name__)

    helpers = {}
    for provider in providers:
        if callable(provider):
            helpers.update(provider())
        else:
            helpers.update(provider)
    return fill(template, filler(helpers))


def add_helpers(*providers):
    """Add helpers to the helpers registry
    """
    for provider in providers:
        zoom.system.providers.append(provider)


def render(template, *providers, **helpers):
    """Render a template

    Applies providers and helpers to the template to fill in the tags
    creating completed content.
    """
    return apply_helpers(
        template,
        None,
        zoom.system.providers + list(providers) + [helpers]
    )


def handler(request, handle, *rest):
    """Render handler"""

    logger = logging.getLogger(__name__)
    zoom.system.providers = [
        zoom.helpers.__dict__,
        request.helpers(),
        request.site.helpers(),
        request.user.helpers(),
    ]

    response = handle(request, *rest)

    providers = zoom.system.providers
    if response.content and isinstance(response.content, str):
        response.content = apply_helpers(response.content, None, providers)

    logger.debug('render handler called')
    request.profiler.add('response rendered')

    return response
