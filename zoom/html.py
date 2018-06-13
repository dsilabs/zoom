"""
    zoom.html
"""
# pylint: disable=invalid-name


def tag(element, *args, **kwargs):
    """generates an HTML tag

    >>> tag('div', 'some content', classed='content-card')
    '<div class="content-card">some content</div>'

    >>> tag('a', href='http://www.google.com')
    '<a href="http://www.google.com"></a>'

    """
    empty = ['area', 'base', 'br', 'col', 'command', 'embed', 'hr', 'img',
             'input', 'link', 'meta', 'param', 'source']

    name = element.lower()
    params = list(args)

    if name not in empty and 'content' not in kwargs:
        if params:
            content = params.pop(0)
        else:
            content = ''
    elif 'content' in kwargs:
        content = kwargs.pop('content')
    else:
        content = ''

    keywords = dict(kwargs)

    # avoids use of python reserved words
    if 'classed' in keywords:
        keywords['class'] = keywords.pop('classed')
    if 'typed' in keywords:
        keywords['type'] = keywords.pop('typed')

    parts = \
        [name] + \
        [str(param).lower() for param in params if param] + \
        [
            '{}="{}"'.format(k.lower(), v)
            for k, v in sorted(keywords.items())
        ]

    if name in empty:
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
    if items:
        return tag('ul', li(items))
    return ''


def ol(items):
    """
    generate an ordered list

        >>> ol(['this','that'])
        '<ol><li>this</li><li>that</li></ol>'

    """
    if items:
        return tag('ol', li(items))
    return ''


def pre(content):
    if content:
        return tag('pre', content)
    return ''

def div(*content, **kwargs):
    """generates an HTML div tag

    Content can be any number of items that support str conversion.  Named
    arguments are used as tag attributes for the div tag.

        >>> div('some content')
        '<div>some content</div>'

        >>> div('some', ' content')
        '<div>some content</div>'

        >>> div('')
        '<div></div>'

        >>> div(Class='header')
        '<div class="header"></div>'


    """
    return tag('div', ''.join(map(str, content)), **kwargs)


def span(content='', **kwargs):
    """
    generates an div tag

        >>> span('some content')
        '<span>some content</span>'

        >>> span('')
        '<span></span>'

        >>> span(Class='header')
        '<span class="header"></span>'


    """
    return tag('span', content, **kwargs)


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


def input(*args, **kwargs):
    Type = kwargs.pop('type', 'text')
    return tag('input', type=Type, *args, **kwargs)


def hidden(*args, **kwargs):
    return tag('input', type='hidden', *args, **kwargs)


def glyphicon(icon, **kwargs):
    """generates a glpyhicon span

    >>> glyphicon('heart')
    '<span aria-hidden="true" class="glyphicon glyphicon-heart"></span>'

    >>> glyphicon('heart', Class="special")
    '<span aria-hidden="true" class="glyphicon glyphicon-heart special"></span>'

    >>> t = (
    ...     '<span aria-hidden="true" class="glyphicon '
    ...     'glyphicon-heart special" style="color:red"></span>'
    ... )
    >>> glyphicon('heart', Class="special", style="color:red") == t
    True
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


def img(src, **kwargs):
    """HTML Image Tag

    >>> img('/static/images/no_image.png', typed='standard-image')
    '<img src="/static/images/no_image.png" type="standard-image" />'
    """
    return tag('img', src=src, **kwargs)
