"""
    zoom.collect
"""

import logging

from zoom.browse import browse
from zoom.fields import ButtonField
from zoom.forms import form_for
from zoom.helpers import url_for_item
from zoom.models import Model
from zoom.store import EntityStore
from zoom.mvc import View, Controller
from zoom.utils import name_for
from zoom.page import page
from zoom.tools import redirect_to


class CollectionStore(object):
    """Decorate a Store

    Provide additional features to a Store class
    to make it work with collections.
    """

    def __init__(self, store):
        self.store = store

    # def create(self):
    #     record.created = now
    #     record.updated = now
    #     record.owner = user.username
    #     record.owner_id = user.user_id
    #     record.created_by = user.username
    #     record.updated_by = user.username


class CollectionModel(Model):
    pass


class CollectionView(View):
    """View a collection"""

    def __init__(self, collection):
        View.__init__(self)
        self.collection = collection

    def index(self, q='', *args, **kwargs):
        """collection landing page"""

        def matches(item, search_text):
            """match a search by field values"""
            terms = search_text and search_text.split()
            f.update(item)
            v = repr(f.display_value()).lower()
            return terms and not any(t.lower() not in v for t in terms)

        c = self.collection
        user = c.user

        if c.request.route[-1:] == ['index']:
            return redirect_to('/'+'/'.join(c.request.route[:-1]), **kwargs)

        actions = user.can('create', c) and ['New'] or []

        authorized = (i for i in c.store if user.can('read', i))
        matching = (i for i in authorized if not q or matches(i, q))
        filtered = (not q and hasattr(c, 'filter') and
                    c.filter and filter(c.filter, matching)) or matching
        items = sorted(filtered, key=c.order)

        if len(items) != 1:
            footer_name = c.name
        else:
            footer_name = c.item_name
        footer = '%s %s' % (len(items), footer_name.lower())

        content = browse(
            [c.model(i) for i in items],
            labels=c.labels,
            columns=c.columns,
            fields=c.fields,
            footer=footer
        )

        return page(content, title=c.name, actions=actions, search=q)


    def new(self, *args, **kwargs):
        """Return a New Item form"""
        c = self.collection
        c.user.authorize('create', c)
        form = form_for(c.fields, ButtonField('Create', cancel=c.url))
        return page(form, title='New '+c.item_name)


class CollectionController(Controller):
    """Perform operations on a Collection"""

    def __init__(self, collection):
        Controller.__init__(self)
        self.collection = collection

    def create_button(self, *args, **data):
        """Create a record"""
        pass
        # store = self.collection.store
        #
        # self.collection.form.save(data)


class Collection(object):
    """A collection of Records"""

    controller = CollectionController
    view = CollectionView
    store_type = EntityStore
    store = None

    def __init__(self, fields, **kwargs):

        def name_from(fields):
            """make a name from the field function provided"""
            return name_for(
                fields.__name__.rstrip('_fields').rstrip('_form')
            ).capitalize()

        get = kwargs.pop
        self.fields = callable(fields) and fields() or fields
        self.item_name = get('item_name', name_from(fields))
        self.name = get('name', self.item_name + 's')
        self.url = get('url', url_for_item())
        self.filter = get('filter', None)
        self.labels = get('labels', self.calc_labels())
        self.columns = get('labels', self.calc_columns())
        self.model = get('model', CollectionModel)
        self.store = get('store', None)
        self.filter = get('filter', None)

    def order(self, item):
        return item.name.lower()

    def calc_labels(self):
        """Calculate labels based on fields"""
        return [f.label for f in self.fields.as_list()]

    def calc_columns(self):
        """Calculate columns based on fields"""
        return [
            (n == 0 and 'link' or f.name.lower())
            for n, f in enumerate(self.fields.as_list())
        ]

    def allows(self, user, action):

        def is_manager(user):
            return user.is_member('managers')

        actions = {
            'create': is_manager,
            'read': is_manager,
            'update': is_manager,
            'delete': is_manager,
        }

        if action not in actions:
            raise Exception('action missing: {}'.format(action))

        return actions.get(action)(user)

    def handle(self, route, request):
        """handle a request"""
        logger = logging.getLogger(__name__)
        logger.debug('Collection handler called')
        self.user = request.user
        self.request = request
        self.route = route
        self.store = self.store or (
            self.store_type(
                request.site.db,
                self.item_name + '_collection',
            )
        )
        return (
            self.controller(self)(*route, **request.data) or
            self.view(self)(*route, **request.data)
        )

    def __call__(self, route, request):
        return self.handle(route, request)

    def __str__(self):
        return 'collection of ' + str(self.store)
