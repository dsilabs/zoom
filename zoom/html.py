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
        [
            '{}="{}"'.format(k.lower(), v)
            for k, v in sorted(kwargs.items())
        ]

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


def li(items):
    """
    generate list items

        >>> li(['this','that'])
        '<li>this</li><li>that</li>'

    """
    return ''.join(map('<li>{}</li>'.format, items))


def ul(items):
    """
    generate an unordered list

        >>> ul(['this','that'])
        '<ul><li>this</li><li>that</li></ul>'

    """
    return tag('ul', li(items))


def ol(items):
    """
    generate an ordered list

        >>> ol(['this','that'])
        '<ol><li>this</li><li>that</li></ol>'

    """
    return tag('ol', li(items))


def div(content='', **kwargs):
    """
    generates an div tag

        >>> div('some content')
        '<div>some content</div>'

        >>> div('')
        '<div></div>'

        >>> div(Class='header')
        '<div class="header"></div>'


    """
    return tag('div', content, **kwargs)


def h1(text):
    """h1 tag

    >>> h1('my heading')
    '<h1>my heading</h1>'
    """
    return '<h1>{}</h1>'.format(text)


def h2(text):
    """h2 tag

    >>> h2('my subheading')
    '<h2>my subheading</h2>'
    """
    return '<h2>{}</h2>'.format(text)


def h3(text):
    """h3 tag

    >>> h3('my subsubheading')
    '<h3>my subsubheading</h3>'
    """
    return '<h3>{}</h3>'.format(text)


def glyphicon(icon, **kwargs):
    """generates a glpyhicon span

    >>> glyphicon('heart')
    '<span aria-hidden="true" class="glyphicon glyphicon-heart"></span>'

    >>> glyphicon('heart', Class="special")
    '<span aria-hidden="true" class="glyphicon glyphicon-heart special"></span>'

    >>> glyphicon('heart', Class="special", style="color:red")
    '<span aria-hidden="true" class="glyphicon glyphicon-heart special" style="color:red"></span>'
    """
    additional_css_classes = kwargs.pop('Class', kwargs.pop('_class', ''))
    css_class = ' '.join(i for i in ['glyphicon glyphicon-{}'.format(icon),
                                     additional_css_classes] if i)
    attributes = {
        'aria-hidden': 'true',
        'class': css_class,
    }
    attributes.update(kwargs)
    return tag('span', '', **attributes)
