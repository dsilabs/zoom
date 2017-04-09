"""
    zoom.tools
"""

from markdown import Markdown
from zoom.response import RedirectResponse
from zoom.helpers import abs_url_for, url_for_page
from zoom.utils import trim


def is_listy(obj):
    """test to see if an object will iterate like a list

    >>> is_listy([1,2,3])
    True

    >>> is_listy(set([3,4,5]))
    True

    >>> is_listy((3,4,5))
    True

    >>> is_listy(dict(a=1, b=2))
    False

    >>> is_listy('123')
    False
    """
    return isinstance(obj, (list, tuple, set))


def ensure_listy(obj):
    """ensure object is wrapped in a list if it can't behave like one

    >>> ensure_listy('not listy')
    ['not listy']

    >>> ensure_listy(['already listy'])
    ['already listy']
    """
    return is_listy(obj) and obj or [obj]


def redirect_to(*args, **kwargs):
    """Return a redirect response for a URL."""
    abs_url = abs_url_for(*args, **kwargs)
    return RedirectResponse(abs_url)


def home(view=None):
    """Redirect to application home.

    >>> home().content
    b''
    >>> home('old').headers['Location']
    '<dz:abs_site_url><dz:request_path>/<dz:site_url>/<dz:app_name>/old'

    """
    if view:
        return redirect_to(url_for_page(view))
    return redirect_to(url_for_page())


def unisafe(val):
    """safely convert to unicode"""
    if val is None:
            return u''
    elif isinstance(val, bytes):
        try:
            val = val.decode('utf-8')
        except:
            val = val.decode('Latin-1')
    elif not isinstance(val, str):
        val = str(val)
    return val


def websafe(val):
    return htmlquote(unisafe(val))


def htmlquote(text):
    """
    Encodes `text` for raw use in HTML.

        >>> htmlquote(u"<'&\\">")
        '&lt;&#39;&amp;&quot;&gt;'

        >>> htmlquote("<'&\\">")
        '&lt;&#39;&amp;&quot;&gt;'
    """
    replacements = (
        ('&', '&amp;'),
        ('<', '&lt;'),
        ('>', '&gt;'),
        ("'", '&#39;'),
        ('"', '&quot;'),
    )
    for replacement in replacements:
        text = text.replace(*replacement)
    return text


def markdown(content):
    def make_page_name(text):
        result = []
        for c in text.lower():
            if c in 'abcdefghijklmnopqrstuvwxyz01234567890.-/':
                result.append(c)
            elif c == ' ':
                result.append('-')
        text = ''.join(result)
        if text.endswith('.html'):
            text = text[:-5]
        return text

    def url_builder(label, base, end):
        return make_page_name(label) + '.html'

    extras = ['tables', 'def_list', 'wikilinks', 'toc']
    configs = {'wikilinks': [('build_url', url_builder)]}
    md = Markdown(extensions=extras, extension_configs=configs)
    return md.convert(unisafe(trim(content)))
