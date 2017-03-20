"""
    zoom.helpers
"""

from urllib.parse import quote_plus

import zoom.html as html


def username():
    """Returns the username."""
    return 'auser'


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


def app_menu_items():
    """Returns app menu items."""
    return (
        '<li><a href="<dz:app_url>">Overview</a></li>'
        '<li><a href="<dz:app_url>/about">About</a></li>'
    )


def app_menu():
    """Returns app menu."""
    return '<ul>{}</ul>'.format(app_menu_items())


def main_menu_items():
    """Returns main menu items."""
    return '<li><a href="/info">Home</a></li>'


def main_menu():
    """Returns main menu."""
    return '<ul>{}</ul>'.format(main_menu_items())


def system_menu_items():
    """Returns system menu items."""
    return '<li><a href="/logout">Logout</a></li>'


def system_menu():
    """Returns system menu."""
    return '<ul>{}</ul>'.format(system_menu_items())


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

    if a and a[0][0] == '/':
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


def link_to(label, *args, **kwargs):
    """produce a link"""
    return html.tag('a', label, href=url_for(*args, **kwargs))
