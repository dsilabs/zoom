"""
    zoom.html
"""


def tag(element, content=None, *args, **kwargs):
    """
    generates an HTML tag

        >>> tag('div', 'some content')
        '<div>some content</div>'

        >>> tag('a', href='http://www.google.com')
        '<a href="http://www.google.com" />'

    """
    empty = ['area', 'base', 'br', 'col', 'command', 'embed', 'hr', 'img',
             'input', 'link', 'meta', 'param', 'source']

    name = element.lower()
    parts = \
        [name] + \
        [str(arg).lower for arg in args] + \
        ['{}="{}"'.format(k.lower(), v) for k, v in kwargs.items()]

    if content is None or name in empty:
        return '<{} />'.format(' '.join(parts))
    else:
        return '<{}>{}</{}>'.format(' '.join(parts), content, name)


def a(content, *args, **kwargs):
    """generate an anchor tag

    >>> a('home', href='/home')
    '<a href="/home">home</a>'
    """
    # pylint: disable=invalid-name
    return tag('a', content, *args, **kwargs)
