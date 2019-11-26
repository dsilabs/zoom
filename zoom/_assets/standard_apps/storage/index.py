"""
    storage index
"""

import zoom
from zoom.helpers import url_for, link_to, link_to_page
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

        engines = (
            '<H3>Engines</H3>' + ', '.join(str(e[0])
            for e in db('show engines'))
        )

        entities = (
            '<H3>Entities</H3>' + ', '.join([
                link_to(kind, 'storage', 'entity', kind)
                for kind, in db(index_query)
            ])
        )

        tables = (
            '<H3>Tables</H3>' + ', '.join([
                link_to(kind, 'storage', 'table', kind)
                for kind, in db('show tables')
            ])
        )

        zap = link_to_page('clear queues', 'clear_queues') + '<br>'
        queues = (
            '<H3>Queues</H3>' + zap + ', '.join([
                link_to(kind, 'storage', 'queue', kind)
                for kind in Queues(db).topics()
            ])
        )

        content = tables + entities + queues
        database_info = 'database: %s' % zoom.system.site.db.connect_string

        return Page(content, title='Storage', subtitle=database_info)

    def entity(self, name):
        items = EntityStore(self.model.site.db, MyModel, kind=name)
        if len(items) == 1:
            footer_name = 'record'
        else:
            footer_name = 'records'
        footer = len(items) and '%s %s' % (len(items), footer_name) or ''
        return page(browse(items, footer=footer), title='Entity: '+name)

    def table(self, name, limit='6'):
        db = self.model.site.db
        items = RecordStore(db, MyModel, name=name)
        if len(items) == 1:
            footer_name = 'record'
        else:
            footer_name = 'records'
        footer = len(items) and '%s %s' % (len(items), footer_name) or ''

        # If there is an id column we will use it to select the last N items,
        # otherwise we'll just select the whole thing and then take what we
        # want from the list.
        columns = db.get_column_names(name)
        limit = int(limit)
        data = 'id' in columns and items[-limit:] or list(items)[-limit:]

        content = browse(data, footer=footer, title='Sample Data')

        if name in db.get_tables():
            content += browse(db('describe ' + name), title='Structure')

        if name in db.get_tables():
            content += browse(db('show index from ' + name), title='Index')

        database = db.database.name
        if database:
            content += browse(db('show table status in {} where name=%s'.format(
                database
            ), name), title='Metadata')

        return page(content, title='Record: '+name)

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

    def clear_queues(self):
        zoom.system.site.queues.clear()
        zoom.alerts.success('queues cleared')
        return zoom.home()

def main(route, request):
    view = IndexView(request)
    controller = IndexController(request)
    return controller(*route, **request.data) or view(*route, **request.data)
