"""
    zoom.components
"""

import logging

from zoom.utils import id_for
from zoom.helpers import url_for, tag_for
from zoom.html import a, div, ul, tag, li
from zoom.component import compose


def as_actions(items):
    """returns actions

    >>> as_actions(['New'])
    '<div class="actions"><ul><li><a class="action" href="new" id="new-action">New</a></li></ul></div>'
    >>> as_actions(['New','Delete'])
    '<div class="actions"><ul><li><a class="action" href="delete" id="delete-action">Delete</a></li><li><a class="action" href="new" id="new-action">New</a></li></ul></div>'

    """
    if not items:
        return ''
    result = []
    for item in reversed(items):
        if type(item) == str:
            text = item
            url = url_for(id_for(item))
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
            logger.debug('menu item url: %r', url)
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
