"""
    zoom.helpers
"""

from urllib.parse import quote_plus
import datetime

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

    elif a and a[0] == '..':
        uri = tag_for('parent_path')

    elif a and a[0].startswith('./'):
        uri = tag_for('request_path') + '/' + '/'.join([a[0][2:]] + a[1:])

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


def url_for_page(*args, **kwargs):
    """returns a url for a page of the current app

    >>> url_for_page()
    '<dz:site_url>/<dz:app_name>'

    >>> url_for_page('page1')
    '<dz:site_url>/<dz:app_name>/page1'
    """
    return url_for('/<dz:app_name>', *args, **kwargs)


def url_for_item(*args, **kwargs):
    """returns a url for an item on the curren page

    >>> url_for_item()
    '<dz:site_url>/<dz:app_name>/<dz:page_name>'

    >>> url_for_item(100)
    '<dz:site_url>/<dz:app_name>/<dz:page_name>/100'
    """
    return url_for('/<dz:app_name>/<dz:page_name>', *args, **kwargs)


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
    """produce a link

    >>> link_to('Company', 'http://company.com')
    '<a href="http://company.com">Company</a>'

    >>> link_to('http://company.com')
    '<a href="http://company.com">http://company.com</a>'

    >>> link_to('http://company.com', q='test')
    '<a href="http://company.com?q=test">http://company.com</a>'
    """
    nargs = args or [label]
    return html.tag('a', label, href=url_for(*nargs, **kwargs))


def mail_to(name, *args, **kwargs):
    """produce an email link

    >>> mail_to('Tester', 'test@testco.com')
    '<a href="test@testco.com">Tester</a>'

    >>> mail_to('test@testco.com')
    '<a href="test@testco.com">test@testco.com</a>'

    """
    nargs = args or [name]
    return html.tag('a', name, href=url_for(*nargs, **kwargs))


def lorem():
    """Returns some sample latin text to use for prototyping."""
    return """
        Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do
        eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut
        enim ad minim veniam, quis nostrud exercitation ullamco laboris
        nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor
        in reprehenderit in voluptate velit esse cillum dolore eu fugiat
        nulla pariatur. Excepteur sint occaecat cupidatat non proident,
        sunt in culpa qui officia deserunt mollit anim id est laborum.
        """

def upper(text):
    """Returns the given text in upper case."""
    return text.upper()

def date():
    """Returns the current date in text form."""
    return '%s' % datetime.date.today()

def year():
    """Returns the current year in text form."""
    return datetime.date.today().strftime('%Y')
