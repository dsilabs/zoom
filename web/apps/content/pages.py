"""
    page collection
"""
import os
import logging

import zoom.collect
from zoom.context import context
from zoom.fields import (Fields, TextField, DateField, RadioField, EditField, MemoField, MarkdownField)
from zoom.validators import required, MinimumLength
from zoom.helpers import link_to
from zoom.utils import id_for
from zoom.tools import load_content
from zoom.store import EntityStore
from zoom.render import render
from zoom.tools import markdown

class PageCollection(zoom.collect.CollectionModel):
    """CollectionModel"""

    @property
    def key(self):
        """Return a key"""
        # use numeric key because user will name pages however they like
        # including names like "index".
        return str(self._id)

    @property
    def name(self):
        """Return a name"""
        return self.title

    @property
    def link(self):
        """Return a link"""
        return link_to(self.name, self.url)


class PageStore(EntityStore):
    def before_update(self, page):
        page.update(path=id_for(page.title))


def get_pages():
    return PageStore(context.site.db, PageCollection)


def load_page(path):

    page = get_pages().first(path=path)
    if page:
        return markdown(render(page.body))

    filename = os.path.splitext(path or 'index.html')[0] + '.md'
    if os.path.exists(filename):
        return load_content(filename)

    logger = logging.getLogger(__name__)
    logger.debug('file not found %r', path + '.md')


def page_fields():
    """Return page fields"""
    return Fields(
        TextField('Title', required, maxlength=80),
        # TextField('Name', maxlength=80),
        TextField('Path', maxlength=80),
        # TextField('Template'),
        # TextField('Title', required, MinimumLength(3)),
        MemoField('Description'),
        MarkdownField('Body', browse=False),
        # DateField('Publish Date', format='%A %b %d, %Y'),
    )


main = zoom.collect.Collection(
    page_fields,
    model=PageCollection,
    # store=PageStore,
)
main.order = lambda a: a.path
