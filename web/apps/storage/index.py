"""
    storage index
"""

from zoom.helpers import url_for, link_to
from zoom.mvc import View, Controller
from zoom.page import page, Page
from zoom.utils import Record
from zoom.store import EntityStore
from zoom.records import RecordStore
from zoom.browse import browse
from zoom.queues import Queues
from zoom.tools import load_content



class MyModel(Record):
    pass


class IndexView(View):

    def index(self,**k):
        index_query = "select distinct kind from entities"
        db = self.model.site.db
        queues = Queues(db)

        entities = (
            '<H3>Entities</H3>' + '<br>'.join([link_to(kind, 'storage', 'entity', kind)
            for kind, in db(index_query)])
        )

        tables = (
            '<H3>Tables</H3>' + '<br>'.join([link_to(kind, 'storage', 'table', kind)
            for kind, in db('show tables')])
        )

        queues = (
            '<H3>Queues</H3>' + '<br>'.join([link_to(kind, 'storage', 'queue', kind)
            for kind in Queues(db).topics()])
        )

        content = entities + tables + queues
        return Page(content, title='Storage')

    def entity(self, name):
        items = EntityStore(self.model.site.db, MyModel, kind=name)
        if len(items) == 1:
            footer_name = 'record'
        else:
            footer_name = 'records'
        footer = len(items) and '%s %s' % (len(items), footer_name) or ''
        return page(browse(items, footer=footer), title='Entity: '+name)

    def table(self, name):
        db = self.model.site.db
        items = RecordStore(db, MyModel, name=name)
        if len(items) == 1:
            footer_name = 'record'
        else:
            footer_name = 'records'
        footer = len(items) and '%s %s' % (len(items), footer_name) or ''

        # If there is an id column we will use it to select the first N items,
        # otherwise we'll just select the whole thing and then take what we
        # want from the list.
        columns = db.get_column_names(name)
        data = 'id' in columns and items[:50] or list(items)[:50]

        return page(browse(data, footer=footer), title='Record: '+name)

    def queue(self, name):
        items = self.model.site.queues.topic(name, -1)
        items = [(n, repr(x)) for n, x in enumerate(items)]

        if len(items) == 1:
            footer_name = 'message'
        else:
            footer_name = 'messages'
        footer = len(items) and '%s %s' % (len(items), footer_name) or ''
        return page(browse(items, labels=('Position', 'Message'), footer=footer), title='Topic: '+name)

    def about(self):
        return page(load_content('about.md'))


class IndexController(Controller):
    pass

def main(route, request):
    view = IndexView(request)
    controller = IndexController(request)
    return controller(*route, **request.data) or view(*route, **request.data)
