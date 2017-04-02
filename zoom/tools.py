"""
    zoom.tools
"""

from markdown import Markdown
from zoom.response import RedirectResponse
from zoom.helpers import abs_url_for


def has_iterator_protocol(obj):
    # does the parameter support the iteration protocol
    # (sequences do, but not a string)
    return hasattr(a, '__iter__')


def wrap_iterator(obj):
    # wrap the argument in a list if it does not support the
    # iteration protocol (i.e. to avoid iterating over a string)
    has_iterator_protocol(obj) and a or [a]


def redirect_to(*args, **kwargs):
    """Return a redirect response for a URL."""
    abs_url = abs_url_for(*args, **kwargs)
    return RedirectResponse(abs_url)


def warning(message):
    pass


def unisafe(val):
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
    return md.convert(unisafe(content))
