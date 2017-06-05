"""
    zoom.render

    rendering tools
"""


import logging

import zoom.context
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
        helpers.update(provider)
    return fill(template, filler(helpers))


# def render(pathname, *a, **k):
#     """render a view"""
#     with open(pathname) as reader:
#         template = reader.read()
#         content = apply_helpers(template, None, [k]).format(*a, **k)
#
#         if pathname.endswith('.md'):
#             result = markdown(content)
#         else:
#             result = content
#
#         return result
#     return ''
def add_helpers(*providers):
    for provider in providers:
        zoom.context.context.providers.append(provider)

def render(template):
    return apply_helpers(template, None, zoom.context.context.providers)

def handler(request, handle, *rest):
    """render handler"""

    logger = logging.getLogger(__name__)
    zoom.context.context.providers = [
        zoom.helpers.__dict__,
        request.helpers(),
        request.site.helpers(),
        request.user.helpers(),
    ]

    response = handle(request, *rest)

    providers = zoom.context.context.providers
    if response.content and isinstance(response.content, str):
        response.content = apply_helpers(response.content, None, providers)

    logger.debug('render handler called')
    return response
