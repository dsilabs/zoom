"""
    zoom.components
"""

from zoom.utils import id_for
from zoom.helpers import url_for
from zoom.html import a, div, ul


def as_actions(items):
    """
        returns actions

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
