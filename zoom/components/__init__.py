"""
    zoom.components
"""

import logging
import uuid

import zoom
from zoom.mvc import DynamicView
from zoom.utils import id_for
from zoom.helpers import url_for, tag_for
from zoom.html import a, div, ul, tag, li
from zoom.component import compose
from .flags import TextFlag, CheckboxFlag, IconFlag

def as_actions(items):
    """returns actions

    >>> from zoom.context import context as ctx
    >>> ctx.site = lambda: None
    >>> ctx.site.url = ''

    >>> as_actions(['New'])
    '<div class="actions"><ul><li><a class="action" href="<dz:request_path>/new" id="new-action">New</a></li></ul></div>'

    >>> as_actions(['New','Delete'])
    '<div class="actions"><ul><li><a class="action" href="<dz:request_path>/delete" id="delete-action">Delete</a></li><li><a class="action" href="<dz:request_path>/new" id="new-action">New</a></li></ul></div>'

    """
    if not items:
        return ''
    result = []
    for item in reversed(items):
        if type(item) == str:
            text = item
            url = url_for('./' + id_for(item))
        elif hasattr(item, '__iter__'):
            text, url = item[:2]
        else:
            raise Exception('actions require str or (str,url)')
        result.append(
            a(
                text,
                Class='action',
                id=id_for(text)+'-action',
                href=url
            )
        )
    return div(ul(result), Class='actions')


class Link(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def as_links(items, select=None, filter=None):
    """generate an unordered list of links

    >>> as_links(['one', 'two'])
    '<ul><li><a href="<dz:app_url>">one</a></li><li><a href="<dz:app_url>/two">two</a></li></ul>'

    >>> as_links([('one', '/1'), 'two'])
    '<ul><li><a href="/1">one</a></li><li><a href="<dz:app_url>/two">two</a></li></ul>'

    >>> as_links([('uno', 'one', '/1'), 'two'], select=lambda a: a.name=='uno')
    '<ul><li class="active"><a class="active" href="/1">one</a></li><li><a href="<dz:app_url>/two">two</a></li></ul>'

    >>> as_links(['one', 'two'], select=lambda a: a.name=='two')
    '<ul><li><a href="<dz:app_url>">one</a></li><li class="active"><a class="active" href="<dz:app_url>/two">two</a></li></ul>'
    """
    logger = logging.getLogger(__name__)

    def as_link_item(n, item):

        if type(item) == str:
            # only the label was provided
            name = n and id_for(item) or ''
            url = tag_for('app_url') + (n and '/' + name or '')
            return Link(name=name or 'index', label=item, url=url)

        elif len(item) == 2:
            # the label and the URL were provided
            name = n and id_for(item[0]) or ''
            url = tag_for('app_url') + (n and '/' + name or '')
            return Link(name=name or 'index', label=item[0], url=item[1])

        elif len(item) == 3:
            # the name, label and URL were provided
            return Link(name=item[0], label=item[1], url=item[2])

        else:
            raise Exception('unkown menu item {}'.format(repr(item),))

    def as_link_items(items):
        for n, item in enumerate(items):
            link_item = as_link_item(n, item)
            if not filter or filter(link_item):
                yield link_item

    links = []

    for link_item in as_link_items(items):
        selected = select and select(link_item)
        attributes = {}
        if selected:
            attributes['class'] = 'active'
        links.append(
            tag(
                'li',
                a(
                    link_item.label,
                    href=link_item.url,
                    **attributes
                ),
                **attributes
            )
        )
    return tag('ul', ''.join(links))


def success(message):
    compose(success=message)

def warning(message):
    compose(warning=message)

def error(message):
    compose(error=message)


class HeaderBar(DynamicView):
    """Header Bar

    A horizontal header bar with a left and right content sections.  Useful
    for section headers that may contain actions or other features.

    >>> content = HeaderBar(left='Left Part', right='Right Part')
    >>> print(content)
    <div class="header-container">
        <div class="header-bar clearfix">
            <div class="header-bar-left">
                Left Part
            </div>
            <div class="header-bar-right">
                Right Part
            </div>
        </div>
    </div>
    <BLANKLINE>
    """
    left = ''
    right = ''


def spinner():
    """A progress spinner

    >>> isinstance(spinner(), str)
    True
    """
    zoom.requires('spin')
    return div(id='spinner')


def dropzone(url, **kwargs):
    """Dropzone component

    A basic dropzone component that supports drag and drop uploading
    of files which are posted to the URL provided.

    >>> zoom.system.site = zoom.sites.Site()
    >>> zoom.system.site.packages = {}
    >>> zoom.system.request = zoom.utils.Bunch(app=zoom.utils.Bunch(name='hello', packages={}))
    >>> c = dropzone('/app/files')
    >>> isinstance(c, zoom.Component)
    True
    """
    zoom.requires('dropzone')

    id = 'dropzone_' + uuid.uuid4().hex

    js = """
    var %(id)s = new Dropzone("#%(id)s", {url: "%(url)s"});
    """ % dict(id=id, url=url)

    html = div(classed='dropzone', id=id, **kwargs)
    return zoom.Component(html)#, js=js)
