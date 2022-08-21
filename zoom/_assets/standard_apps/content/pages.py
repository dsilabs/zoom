"""
    page collection
"""
import os
import logging

import zoom
import zoom.fields as f

from zoom.context import context
from zoom.fields import (Fields, TextField, MemoField, MarkdownEditField)
from zoom.validators import required, MinimumLength
from zoom.helpers import link_to
from zoom.utils import id_for
from zoom.tools import load_content
from zoom.store import EntityStore
from zoom.render import render
from zoom.tools import markdown, websafe

class PageCollection(zoom.collect.CollectionModel):
    """CollectionModel"""

    @property
    def url(self):
        return '/content/pages/' + self.key

    @property
    def key(self):
        """Return a key"""
        # use numeric key because user will name pages however they like
        # including names like "index".
        return str(self._id)

    @property
    def name(self):
        """Return a name"""
        return websafe(self.title)

    @property
    def link(self):
        """Return a link"""
        return link_to(self.name, self.url)

    @property
    def abs_path(self):
        return zoom.helpers.url_for(zoom.system.site.abs_url, self.path)

    @property
    def who(self):
        return zoom.helpers.who(self.updated_by)

    @property
    def when(self):
        return zoom.helpers.when(self.updated)


class PageStore(EntityStore):
    """Page EntityStore"""
    def before_update(self, record):
        record.update(path=id_for(record.title))


def get_pages():
    """Get the pages store"""
    return PageStore(context.site.db, PageCollection)


def load_page(path):
    """Load a page given it's path"""

    page = get_pages().first(path=path)
    if page:
        return markdown(render(page.body))

    filename = os.path.splitext(path or 'index.html')[0] + '.md'
    if os.path.exists(filename):
        return load_content(filename)

    logger = logging.getLogger(__name__)
    logger.debug('file not found %r', path + '.md')
    return None

def page_fields():
    """Return page fields"""
    return Fields(
        TextField('Title', required, MinimumLength(3), maxlength=80),
        # TextField('Name', maxlength=80),
        TextField('Path', maxlength=80),
        # TextField('Template'),
        # TextField('Title', required, MinimumLength(3)),
        MemoField('Description'),
        MarkdownEditField('Body', browse=False),
        f.CheckboxField('Exclude from Sitemap', default=False),
        # DateField('Publish Date', format='%A %b %d, %Y'),
    )


class MyCollectionView(zoom.collect.CollectionView):

    def edit(self, key, **data):
        page = zoom.collect.CollectionView.edit(self, key, **data)
        page.css = '.content .field_label { min-width: 15%; width: 15%; }'
        return page

    def show(self, key):
        page = zoom.collect.CollectionView.show(self, key)
        page.css = '.content .field_label { min-width: 15%; width: 15%; }'
        return page

main = zoom.collect.Collection(
    page_fields,
    model=PageCollection,
    view=MyCollectionView,
    labels=['Title', 'Path', 'Description', 'Who', 'When'],
    columns=['link', 'path', 'description', 'who', 'when']
    # store=PageStore,
)
main.order = lambda a: a.path
