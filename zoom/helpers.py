"""
    zoom.helpers
"""

from urllib.parse import quote_plus

import zoom.html as html


def username():
    """Returns the username."""
    return tag_for('username')


def owner_name():
    """Returns the name of the site owner."""
    return '<dz:owner_name>'


def owner_email():
    """Returns the email address of the site owner."""
    return '<dz:owner_email>'


def owner_url():
    """Returns the URL of the site owner."""
    return '<dz:owner_url>'


def owner_link():
    """Returns a link for the site owner."""
    name = owner_name()
    url = owner_url()
    if url:
        return html.a(name, href=url)
    email = owner_email()
    if email:
        return html.a(name, href='mailto:%s' % email)
    return name


def tag_for(name, *a, **k):
    """create a zoom tag
    
    >>> tag_for('name')
    '<dz:name>'

    >>> tag_for('name', default=1)
    '<dz:name default=1>'
    """
    return '<dz:{}{}{}>'.format(
        name,
        a and (' ' + ' '.join(str(a))) or '',
        k and (' ' + ' '.join(
            '{}={!r}'.format(k, v) for k, v in sorted(k.items())
        )) or ''
    )


def url_for(*a, **k):
    """creates urls

    >>> url_for()
    ''

    >>> url_for('')
    ''

    >>> url_for('/')
    '<dz:site_url>'

    >>> url_for('/', 'home')
    '<dz:site_url>/home'

    >>> url_for('/home')
    '<dz:site_url>/home'

    >>> url_for('home')
    'home'

    >>> url_for('/user', 1234)
    '<dz:site_url>/user/1234'

    >>> url_for('/user', 1234, q='test one', age=15)
    '<dz:site_url>/user/1234?age=15&q=test+one'

    >>> url_for('/user', q='test one', age=15)
    '<dz:site_url>/user?age=15&q=test+one'

    >>> url_for('/', q='test one', age=15)
    '<dz:site_url>?age=15&q=test+one'

    >>> url_for(q='test one', age=15)
    '?age=15&q=test+one'

    >>> url_for('https://google.com', q='test one')
    'https://google.com?q=test+one'

    """

    root = tag_for('site_url')
    a = [str(i) for i in a]

    if a and a[0] and a[0][0] == '/':
        if len(a[0]) > 1:
            uri = root + '/'.join(a)
        else:
            uri = '/'.join([root] + a[1:])

    elif a and (a[0].startswith('http://') or a[0].startswith('https://')):
        uri = '/'.join(a)

    else:
        uri = '/'.join(a)

    if k:
        params = quote_plus(
            '&'.join('{}={}'.format(*i) for i in sorted(k.items())),
            safe="/=&"
        )
        return '?'.join([uri, params])
    else:
        return uri


def abs_url_for(*a, **k):
    """calculates absolute url

    >>> abs_url_for()
    '<dz:abs_site_url><dz:request_path>'

    >>> abs_url_for('')
    '<dz:abs_site_url><dz:request_path>'

    >>> abs_url_for('/')
    '<dz:abs_site_url>'

    >>> abs_url_for('/', 'home')
    '<dz:abs_site_url>/home'

    >>> abs_url_for('/home')
    '<dz:abs_site_url>/home'

    >>> abs_url_for('home')
    '<dz:abs_site_url><dz:request_path>/home'

    >>> abs_url_for('/user', 1234)
    '<dz:abs_site_url>/user/1234'

    >>> abs_url_for('/user', 1234, q='test one', age=15)
    '<dz:abs_site_url>/user/1234?age=15&q=test+one'

    >>> abs_url_for('/user', q='test one', age=15)
    '<dz:abs_site_url>/user?age=15&q=test+one'

    >>> abs_url_for('/', q='test one', age=15)
    '<dz:abs_site_url>?age=15&q=test+one'

    >>> abs_url_for(q='test one', age=15)
    '<dz:abs_site_url><dz:request_path>?age=15&q=test+one'

    >>> abs_url_for('https://google.com', q='test one')
    'https://google.com?q=test+one'

    """

    if a and a[0].startswith('http'):
        root = a[0]
        args = a[1:]
    else:
        root = tag_for('abs_site_url')
        path = tag_for('request_path')
        if a == ('/',):
            args = []
        elif a and a[0] == '/':
            args = list(a[1:])
            root = root + '/'
        elif a and a[0] and a[0][0] == '/':
            args = list(a)
        elif a:
            args = [path] + list(a)
        else:
            args = [path]
    result = root + '/'.join(filter(bool, (str(i) for i in args)))
    if k:
        items = sorted(k.items())
        result = result + '?' + (
            '&'.join('%s=%s' % (j, quote_plus(str(v))) for j, v in items)
        )
    return result


def link_to(label, *args, **kwargs):
    """produce a link"""
    return html.tag('a', label, href=url_for(*args, **kwargs))
