"""
    zoom.collect
"""

import logging

from zoom.browse import browse
from zoom.components import success, error
from zoom.fields import ButtonField
from zoom.forms import form_for, delete_form
from zoom.helpers import link_to
from zoom.models import Model
from zoom.store import EntityStore
from zoom.mvc import View, Controller
from zoom.utils import name_for, id_for
from zoom.page import page
from zoom.tools import redirect_to, now


def shared_collection_policy(group):
    """Authourization policy for a shared collection
    """
    def policy(item, user, action):
        """Policy rules for shared collection"""
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
    return policy


def locate(collection, key):
    """locate a record"""
    def scan(store, key):
        for rec in store:
            if rec.key == key:
                return rec
    return (
        key.isdigit() and
        collection.store.get(key) or
        collection.store.first(key=key) or
        scan(collection.store, key)
    )


class CollectionStore(object):
    """Decorate a Store

    Provide additional features to a Store class
    to make it work with collections.
    """

    def __init__(self, store):
        self.store = store


class CollectionModel(Model):
    """CollectionModel"""

    @property
    def link(self):
        """Return a link"""
        return link_to(self.name, self.url)

    def allows(self, user, action):
        """Item level policy"""
        return True


CollectionRecord = CollectionModel
# Typically these are the same thing but occassionally
# a Model is more than just a Record.  So, we provide
# both names purely for readability so you can use whatever
# makes sense in your app.


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
            fields.update(item)
            v = repr(fields.display_value()).lower()
            return terms and not any(t.lower() not in v for t in terms)

        c = self.collection
        user = c.user
        fields = c.fields

        if c.request.route[-1:] == ['index']:
            return redirect_to('/'+'/'.join(c.request.route[:-1]), **kwargs)

        actions = user.can('create', c) and ['New'] or []

        authorized = (i for i in c.store if user.can('read', i))
        matching = (i for i in authorized if not q or matches(i, q))
        filtered = (not q and hasattr(c, 'filter') and
                    c.filter and filter(c.filter, matching)) or matching
        items = sorted(matching, key=c.order)

        if len(items) != 1:
            footer_name = c.title
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

        return page(content, title=c.title, actions=actions, search=q)

    def clear(self):
        """Clear the search"""
        return redirect_to('/' + '/'.join(self.collection.request.route[:-1]))

    def new(self, *args, **kwargs):
        """Return a New Item form"""
        c = self.collection
        c.user.authorize('create', c)
        form = form_for(c.fields, ButtonField('Create', cancel=c.url))
        return page(form, title='New '+c.item_title)

    def show(self, key):
        """show a record"""
        def action_for(record, name):
            return name, '/'.join([record.url, id_for(name)])

        def actions_for(record, *names):
            return [action_for(record, n) for n in names]

        c = self.collection
        user = c.user
        record = locate(c, key)
        if record:
            user.authorize('read', record)

            actions = []
            if user.can('update', record):
                actions.append(action_for(record, 'Edit'))
            if user.can('delete', record):
                actions.append(action_for(record, 'Delete'))
            c.fields.initialize(c.model(record))

            if 'updated' in record and 'updated_by' in record:
                memo = (
                    '<div class="meta" style="float:right">'
                    ' record updated %(updated)s by %(updated_by)s'
                    '</div>'
                    '<div style="clear:both"></div>'
                ) % record
            else:
                memo = ''

            return page(
                c.fields.show() + memo,
                title=c.item_title,
                actions=actions
            )
        else:
            raise PageMissingException

    def edit(self, key, **data):
        c = self.collection
        user = c.user

        user.authorize('update', c)

        record = locate(c, key)
        if record:
            user.authorize('read', record)
            user.authorize('update', record)

            c.fields.initialize(record)
            c.fields.update(data)
            form = form_for(c.fields, ButtonField('Save', cancel=c.url))
            return page(form, title=c.item_title)
        else:
            return page('%s missing' % key)

    def delete(self, key, confirm='yes'):
        if confirm == 'yes':
            record = locate(self.collection, key)
            if record:
                return page(delete_form(record.name))


class CollectionController(Controller):
    """Perform operations on a Collection"""

    def __init__(self, collection):
        Controller.__init__(self)
        self.collection = collection

    def create_button(self, *args, **data):
        """Create a record"""

        collection = self.collection
        user = collection.user

        if collection.fields.validate(data):

            record = collection.model(
                collection.fields,
            )

            record.pop('key', None)
            try:
                key = record.key
            except AttributeError:
                key = None

            if key and locate(collection, record.key) is not None:
                error('That {} already exists'.format(collection.item_name))
            else:

                try:
                    # convert property to data attribute
                    # so it gets stored as data
                    record.key = record.key
                except AttributeError:
                    # can happen when key depends on database
                    # auto-increment value.
                    pass

                record.update(dict(
                    created=now(),
                    updated=now(),
                    owner_id=user._id,
                    created_by=user._id,
                    updated_by=user._id,
                ))

                collection.store.put(record)
                logger = logging.getLogger(__name__)
                logger.info(
                    '%s added %s %s' % (
                        user.link,
                        collection.item_name.lower(),
                        record.link),
                    )

                return redirect_to(collection.url)

    def save_button(self, key, *a, **data):
        collection = self.collection
        user = collection.user

        user.authorize('update', collection)

        if collection.fields.validate(data):
            record = locate(collection, key)
            if record:
                user.authorize('update', record)
                record.update(collection.fields)
                record.pop('key', None)
                if record.key != key and locate(collection, record.key):
                    error('That {} already exists'.format(collection.item_name))
                else:
                    record.updated = now()
                    record.updated_by = user._id

                    # convert property to data attribute
                    # so it gets stored as data
                    record.key = record.key

                    collection.store.put(record)
                    logger = logging.getLogger(__name__)
                    logger.info(
                        '%s edited %s %s' % (
                            user.link,
                            collection.item_name.lower(),
                            record.link
                        )
                    )
                    return redirect_to(record.url)


    def delete(self, key, confirm='yes'):
        c = self.collection
        c.user.authorize('delete', c)

        if confirm == 'no':
            record = locate(c, key)
            if record:
                c.user.authorize('delete', record)
                c.store.delete(record)

                logger = logging.getLogger(__name__)
                logger.info(
                    self.collection.request.app.name,
                    '%s deleted %s %s' % (
                        c.user.link,
                        c.item_name.lower(),
                        record.link
                    )
                )
                return redirect_to(c.url)


class Collection(object):
    """A collection of Records"""

    controller = CollectionController
    view = CollectionView
    store_type = EntityStore
    store = None
    url = None
    allows = shared_collection_policy('managers')

    def __init__(self, fields, **kwargs):

        def name_from(fields):
            """make a name from the field function provided"""
            def rtrim(text, suffix):
                if text.endswith(suffix):
                    return text[:-len(suffix)]
                return text

            return name_for(
                rtrim(rtrim(fields.__name__, '_fields'), '_form')
            )

        get = kwargs.pop

        self.fields = callable(fields) and fields() or fields
        self.item_name = get('item_name', name_from(fields))
        self.name = get('name', self.item_name + 's')
        self.title = self.name.capitalize()
        self.item_title = self.item_name.capitalize()
        self.filter = get('filter', None)
        self.labels = get('labels', self.calc_labels())
        self.columns = get('labels', self.calc_columns())
        self.model = get('model', CollectionModel)
        self.store = get('store', None)
        self.filter = get('filter', None)

        if 'policy' in kwargs:
            self.allows = get('policy')

    def order(self, item):
        """Returns the sort key"""
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

    def handle(self, route, request):
        """handle a request"""

        def get_model(url):
            class CustomCollectionModel(CollectionModel):
                url = property(lambda self: '/'.join([url, self.key]))
            return CustomCollectionModel

        logger = logging.getLogger(__name__)
        logger.debug('Collection handler called')

        # store some handy references in case the View
        # or Controller need them.
        self.user = request.user
        self.request = request
        self.route = route

        # If we're not provided with a URL for the collection
        # we assume it is the most common case, which is where the
        # app is the first part of the URL and the collection
        # name is the second part of the URL.  Together they
        # make up the URL for the collection.
        if self.url is None:
            self.url = '/'.join(
                [request.site.abs_url] + request.route[:2],
            )
            logger.debug('Collection URL: %r', self.url)

        # If we're not provided with a place to store the data
        # we assume that the collection will be stored in an
        # entity store.
        self.store = self.store or (
            EntityStore(
                request.site.db,
                self.model or get_model(self.url),
                self.item_name + '_collection',
            )
        )

        # self.store_type.store = self.store
        # self.store_type.collection = self
        return (
            self.controller(self)(*route, **request.data) or
            self.view(self)(*route, **request.data)
        )

    def __call__(self, route, request):
        return self.handle(route, request)

    def __str__(self):
        return 'collection of ' + str(self.store.kind)
