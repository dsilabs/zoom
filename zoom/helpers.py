"""
    zoom.helpers
"""

from urllib.parse import quote_plus
import datetime

import zoom
import zoom.html as html
from zoom.snippets import snippet

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

def standard_zoom_head_tags():
    zoom.requires('standard-zoom-assets')
    tags = 'styles', 'css', 'head', 'tracker'
    return ''.join('{{%s}}' % tag for tag in tags)

def standard_zoom_content_tags():
    tags = 'stdout', 'alerts', 'content'
    content = ''.join('{{%s}}' % tag for tag in tags)
    return html.div(content, classed='content')

def standard_zoom_tail_tags():
    tags = 'libs', 'js', 'tail'
    return ''.join('{{%s}}' % tag for tag in tags)

def tag_for(name, *a, **k):
    """create a dz tag

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


def ztag(name, *args, **kwargs):
    """return a zoom tag

    >>> ztag('name')
    '{{name}}'

    >>> ztag('name', 'upper', 2)
    "{{name 'upper' 2}}"

    >>> ztag('name', 10, 'test', default=1)
    "{{name 10 'test' default=1}}"
    """
    return ''.join([
        '{{',
        name,
        args and (' ' + ' '.join(map(repr, args))) or '',
        kwargs and (' ' + ' '.join(
            '{}={!r}'.format(k, v) for k, v in sorted(kwargs.items())
        )) or '',
        '}}',
    ])


def url_for(*a, **k):
    """creates urls

    >>> zoom.system.site = lambda: None
    >>> zoom.system.site.url = ''

    >>> url_for()
    ''

    >>> url_for('')
    ''

    >>> url_for('/')
    '/'

    >>> url_for('/', 'home')
    '/home'

    >>> url_for('/home')
    '/home'

    >>> url_for('home')
    'home'

    >>> url_for('/user', 1234)
    '/user/1234'

    >>> url_for('/user', 1234, q='test one', age=15)
    '/user/1234?age=15&q=test+one'

    >>> url_for('/user', q='test one', age=15)
    '/user?age=15&q=test+one'

    >>> url_for('/', q='test one', age=15)
    '/?age=15&q=test+one'

    >>> url_for(q='test one', age=15)
    '?age=15&q=test+one'

    >>> url_for('https://google.com', q='test one')
    'https://google.com?q=test+one'

    """

    root = zoom.system.site.url
    a = [str(i) for i in a]

    if a and a[0] and a[0][0] == '/':
        if len(a[0]) > 1:
            uri = root + '/'.join(a)
        elif len(a) == 1:
            uri = '/'.join([root, ''])
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
        result = '?'.join([uri, params])
    else:
        result = uri

    return result


def requires(*packages):
    zoom.requires(*packages)
    return ''


def url_for_page(*args, **kwargs):
    """returns a url for a page of the current app

    >>> zoom.system.request = lambda: None
    >>> zoom.system.request.app = lambda: None
    >>> zoom.system.request.app.url = '/home'

    >>> url_for_page()
    '/home'

    >>> url_for_page('page1')
    '/home/page1'
    """
    app = zoom.system.request.app
    return url_for(app.url, *args, **kwargs)


def url_for_item(*args, **kwargs):
    """returns a url for an item on the curren page

    >>> zoom.system.request = lambda: None
    >>> zoom.system.request.route = ['myapp', 'mypage']

    >>> url_for_item()
    '/myapp/mypage'

    >>> url_for_item(100)
    '/myapp/mypage/100'
    """
    route = ['/'] + zoom.system.request.route[:2] + list(args)
    return url_for(*route, **kwargs)


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

    >>> zoom.system.site = lambda: None
    >>> zoom.system.site.url = ''

    >>> link_to('Company', 'http://company.com')
    '<a href="http://company.com" name="link-to-company">Company</a>'

    >>> link_to('http://company.com')
    '<a href="http://company.com" name="link-to-http-company-com">http://company.com</a>'

    >>> link_to('http://company.com', q='test')
    '<a href="http://company.com?q=test" name="link-to-http-company-com">http://company.com</a>'
    """
    nargs = args or [label]
    return html.tag(
        'a', label,
        href=url_for(*nargs, **kwargs),
        name='link-to-' + zoom.utils.id_for(
            str(label).replace('.', '-').replace(':', '-')
        ),
    )


def link_to_page(label, *args, **kwargs):
    nargs = args or [label.lower().replace(' ', '_')]
    return html.tag('a', label, href=url_for_page(*nargs, **kwargs))


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
    return zoom.utils.trim("""
        Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do
        eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut
        enim ad minim veniam, quis nostrud exercitation ullamco laboris
        nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor
        in reprehenderit in voluptate velit esse cillum dolore eu fugiat
        nulla pariatur. Excepteur sint occaecat cupidatat non proident,
        sunt in culpa qui officia deserunt mollit anim id est laborum.
        """)

def upper(text):
    """Returns the given text in upper case."""
    return text.upper()

def date():
    """Returns the current date in text form."""
    return '%s' % datetime.date.today()

def year():
    """Returns the current year in text form."""
    return datetime.date.today().strftime('%Y')

def include(filename):
    """Return the included file"""
    return zoom.tools.load_template(filename)

def who(user_id):
    """Formats a user_id

    >>> zoom.system.site = site = zoom.sites.Site()
    >>> zoom.system.user = site.users.first(username='admin')
    >>> user_id = site.users.first(username='guest').user_id

    >>> zoom.system.user.is_admin = True
    >>> who(user_id)
    '<a href="/admin/users/guest" name="link-to-guest">guest</a>'
    >>> who(100)
    'unknown (100)'

    >>> zoom.system.user.is_admin = False
    >>> who(user_id)
    'guest'
    >>> who(100)
    'unknown'
    """
    subject = zoom.system.site.users.get(user_id)
    if subject:
        return subject.link
    else:
        if zoom.system.user.is_admin:
            return 'unknown (%s)' % user_id
        else:
            return 'unknown'

def when(date, since=None):
    """Formats a date

    >>> now = datetime.datetime(2018, 2, 24, 1, 2, 42)
    >>> when(now - zoom.tools.one_day * 2, now)
    '<span title="2018-02-22 01:02:42">2 days ago</span>'

    """
    if date:
        return zoom.html.span(
            zoom.tools.how_long_ago(date, since),
            title='%s' % date,
        )
    else:
        return 'never'