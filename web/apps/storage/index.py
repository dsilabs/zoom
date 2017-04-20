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
from zoom.tools import load_content



class MyModel(Record):
    pass


class IndexView(View):

    def index(self,**k):
        index_query = "select distinct kind from entities"
        db = self.model.site.db
        entities = '<br>'.join([link_to(kind, 'storage', kind, 'browse') for kind, in db(index_query)])
        return Page('<H1>Storage</H1><H3>Entities</H3><br>%s' % entities)

    def browse(self, name):
        items = EntityStore(self.model.site.db, MyModel, kind=name)
        if len(items) == 1:
            footer_name = 'record'
        else:
            footer_name = 'records'
        footer = len(items) and '%s %s' % (len(items), footer_name) or ''
        return page(browse(items, footer=footer), title='Entity: '+name)

    def about(self):
        return page(load_content('about.md'))


class IndexController(Controller):
    pass

def main(route, request):
    view = IndexView(request)
    controller = IndexController(request)
    return controller(*route, **request.data) or view(*route, **request.data)
