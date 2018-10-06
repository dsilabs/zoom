"""
    zoom.collect
"""

import io
import logging
import os

import zoom
from zoom.browse import browse
from zoom.buckets import Bucket
from zoom.context import context
from zoom.alerts import success, error, warning
from zoom.fields import ButtonField
from zoom.forms import form_for, delete_form
from zoom.helpers import link_to
from zoom.models import Model, Attachment
from zoom.store import EntityStore
from zoom.mvc import View, Controller
from zoom.utils import name_for, id_for, Record
from zoom.page import page
from zoom.tools import redirect_to, now
from zoom.logging import log_activity
from zoom.users import authorize


def shared_collection_policy(group):
    """Authourization policy for a shared collection
    """
    def policy(item, user, action):
        """Policy rules for shared collection"""

        def is_manager(user):
            """Return True if user is a member of the managing group
            """
            return user.is_member(group)

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
        """brute force scan"""
        for rec in store:
            if rec.key == key:
                return rec
    return (
        key.isdigit() and
        collection.store.get(key) or
        collection.store.first(**{collection.key_name: key}) or
        scan(collection.store, key)
    )


def image_response(name, data):
    """provide an image response based on the file extension"""
    _, ext = os.path.splitext(name.lower())
    if ext == '.png':
        return zoom.response.PNGResponse(data)
    elif ext == '.jpg':
        return zoom.response.JPGResponse(data)
    elif ext == '.gif':
        return zoom.response.GIFResponse(data)


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

    @property
    def url(self):
        return self.collection_url + '/' + self.key

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

        c = self.collection
        user = c.user

        if c.request.route[-1:] == ['index']:
            return redirect_to('/'+'/'.join(c.request.route[:-1]), **kwargs)

        actions = user.can('create', c) and ['New'] or []

        logger = logging.getLogger(__name__)
        if q:
            title = 'Selected ' + c.title
            records = c.search_engine(c).search(q)
        else:
            has_many_records = c.has_many_records
            logger.debug('has many records: %r', has_many_records)
            if has_many_records and not kwargs.get('all'):
                title = 'Most Recently Updated ' + c.title
                records = self._get_recent(15)
                actions.append(('Show All', c.url + '?all=1'))
            else:
                title = c.title
                records = c.store

        authorized = (i for i in records if user.can('read', i))
        filtered = c.filter and filter(c.filter, authorized) or authorized
        items = sorted(filtered, key=c.order)
        items = c.sorter and c.sorter(items) or items
        num_items = len(items)

        if num_items != 1:
            footer_name = c.title.lower()
        else:
            footer_name = c.item_title.lower()

        if q:
            msg = '%s searched %s with %r (%d found)' % (
                user.link, c.link, q, num_items
            )
            log_activity(msg)
            footer = '{:,} {} found in search of {:,} {}'.format(
                num_items,
                footer_name,
                len(c.store),
                c.title.lower(),
            )
        else:
            if has_many_records:
                footer = '{:,} {} shown of {:,} {}'.format(
                    num_items,
                    footer_name,
                    len(c.store),
                    c.title.lower(),
                )
            else:
                footer = '%s %s' % (len(items), footer_name)

        content = browse(
            [c.model(i) for i in items],
            labels=c.get_labels(),
            columns=c.get_columns(),
            fields=c.fields,
            footer=footer
        )

        return page(content, title=title, actions=actions, search=q)

    def clear(self):
        """Clear the search"""
        return redirect_to('/' + '/'.join(self.collection.request.route[:-1]))

    def _get_recent(self, number):
        c = self.collection
        cmd = """
            select row_id, max(value) as newest
            from attributes
            where kind = %s and attribute in ("created", "updated")
            group by row_id
            order by newest desc
            limit %s
        """
        ids = [id for id, _ in c.store.db(cmd, c.store.kind, number)]
        return c.store.get(ids)

    def new(self, *args, **kwargs):
        """Return a New Item form"""
        c = self.collection
        c.user.authorize('create', c)
        form = form_for(c.fields, ButtonField('Create', cancel=c.url))
        return page(form, title='New '+c.item_title)

    def show(self, key):
        """Show a record"""
        def action_for(record, name):
            return name, '/'.join([record.url, id_for(name)])

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
                    'updated %(when)s by %(who)s'
                    '</div>'
                    '<div style="clear:both"></div>'
                ) % dict(
                    when=zoom.helpers.when(record['updated']),
                    who=zoom.helpers.who(record['updated_by'])
                )
            else:
                memo = ''

            if c.verbose:
                msg = '%s viewed %s %s' % (
                    user.link,
                    c.link,
                    record.link,
                )
                log_activity(msg)

            return page(
                c.fields.show() + memo,
                title=c.item_title,
                actions=actions
            )

    def image(self, key, name):
        """Respond with image field contents"""
        record = locate(self.collection, key)
        if record:
            return zoom.response.PNGResponse(
                record[name],
                max_age=0,
            )

    def edit(self, key, **data):
        """Display an edit form for a record"""
        c = self.collection
        user = c.user

        user.authorize('update', c)

        record = locate(c, key)
        if record:
            user.authorize('read', record)
            user.authorize('update', record)

            c.fields.initialize(record)
            c.fields.update(data)
            form = form_for(c.fields, ButtonField('Save', cancel=record.url))

            if c.verbose:
                msg = '%s edited %s %s' % (
                    user.link,
                    c.link,
                    record.link,
                )
                log_activity(msg)

            return page(form, title=c.item_title)
        else:
            return page('%s missing' % key)

    def delete(self, key, confirm='yes'):
        """Show a delete form for a collection record"""
        if confirm == 'yes':
            record = locate(self.collection, key)
            if record:
                return page(delete_form(record.name))

    def list_images(self, key=None, value=None):
        """return list of images for an ImagesField value for this record"""
        attachments = zoom.store.store_of(Attachment)
        t = [dict(
            name=a.attachment_name,
            size=a.attachment_size,
            item_id=a.attachment_id,
            url=zoom.helpers.url_for('get-image', item_id=a.attachment_id),
        ) for a in attachments.find(field_value=value)]
        return zoom.jsonz.dumps(t)

    def get_image(self, *a, **k):  # pylint: disable=W0613
        """return one of the images from an ImagesField value"""
        item_id = k.get('item_id', None)
        path = os.path.join(zoom.system.site.data_path, 'buckets')
        bucket = Bucket(path)
        return image_response('house.png', bucket.get(item_id))


class CollectionController(Controller):
    """Perform operations on a Collection"""

    def __init__(self, collection):
        Controller.__init__(self)
        self.collection = collection

    def create_button(self, *args, **data):
        """Create a record"""

        collection = self.collection
        user = collection.user

        logger = logging.getLogger(__name__)

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

                self.before_insert(record)

                collection.store.put(record)

                collection.search_engine(collection).add(
                    record._id,
                    collection.fields.as_searchable(),
                )

                self.after_insert(record)

                msg = '%s added %s %s' % (
                    user.link,
                    collection.link,
                    record.link
                )
                logger.info(msg)
                log_activity(msg)

                return redirect_to(collection.url)

        else:
            logger.debug('field validation failed: %r', collection.fields)

    def save_button(self, key, *a, **data):
        """Save a record"""
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
                    # record key should always be a str, even if the actual
                    # record.id is being used as the key.
                    error('That {} already exists'.format(collection.item_name))
                else:
                    record.updated = now()
                    record.updated_by = user._id

                    # convert property to data attribute
                    # so it gets stored as data
                    record.key = record.key

                    self.before_update(record)

                    collection.store.put(record)

                    collection.search_engine(collection).update(
                        record._id,
                        collection.fields.as_searchable(),
                    )

                    self.after_update(record)

                    msg = '%s updated %s %s' % (
                        user.link,
                        collection.link,
                        record.link
                    )
                    logger = logging.getLogger(__name__)
                    logger.info(msg)
                    log_activity(msg)
                    if record.key != key:
                        log_activity(
                            '%s changed %s %s to %s' % (
                                user.link,
                                collection.link,
                                key,
                                record.key
                            )
                        )
                    return redirect_to(record.url)


    def delete(self, key, confirm='yes'):
        """Delete a record"""
        c = self.collection
        c.user.authorize('delete', c)

        if confirm == 'no':
            record = locate(c, key)
            if record:
                c.user.authorize('delete', record)

                self.before_delete(record)

                c.store.delete(record)

                c.search_engine(c).delete(
                    record._id,
                )

                self.after_delete(record)

                msg = '%s deleted %s %s' % (
                    c.user.link,
                    c.link,
                    record.name
                )

                logger = logging.getLogger(__name__)
                logger.info(msg)
                log_activity(msg)
                return redirect_to(c.url)

    def delete_image(self, key, name):
        """Delete an image field"""
        record = locate(self.collection, key)
        if record:
            del record[name]
            record.save()
            return redirect_to(zoom.helpers.url_for(record.url, 'edit'))

    def add_image(self, *_, **kwargs):
        """accept uploaded images and attach them to the record"""
        logger = logging.getLogger(__name__)

        dummy = Record(
            filename='dummy.png',
            file=io.StringIO('test'),
        )

        # put the uploaded image data in a bucket
        path = os.path.join(zoom.system.site.data_path, 'buckets')
        bucket = Bucket(path)
        f = kwargs.get('file', dummy)
        name = f.filename
        data = f.file.read()
        item_id = bucket.put(data)

        # create an attachment record for this bucket
        c = self.collection
        field_name = kwargs.get('field_name', 'unknown')
        field_value = kwargs.get('field_value', 'unknown')
        attachment = Attachment(
            record_kind=c.store.kind,
            field_name=field_name,
            field_value=field_value,
            attachment_id=item_id,
            attachment_size=len(data),
            attachment_name=name,
        )
        attachments = zoom.store.store_of(Attachment)
        attachments.put(attachment)

        return item_id

    def remove_image(self, *_, **kwargs):
        """remove a dropzone image"""
        # k contains item_id and filename for file to be removed
        item_id = kwargs.get('id', None)

        # detach the image from the record
        if item_id:
            attachments = zoom.store.store_of(Attachment)
            key = attachments.first(attachment_id=item_id)
            if key:
                attachments.delete(key)

            # delete the bucket
            path = os.path.join(zoom.system.site.data_path, 'buckets')
            bucket = Bucket(path)
            items = bucket.keys()
            if item_id in bucket.keys():
                bucket.delete(item_id)
                return 'ok'
            return 'empty'


    def before_update(self, record):
        """Things to do before updating a record"""
        pass

    def after_update(self, record):
        """Things to do after updating a record"""
        pass

    def before_insert(self, record):
        """Things to do before inserting a record"""
        pass

    def after_insert(self, record):
        """Things to do after inserting a record"""
        pass

    def before_delete(self, record):
        """Things to do before deleting a record"""
        pass

    def after_delete(self, record):
        """Things to do after deleting a record"""
        pass

    @authorize('administrators')
    def reindex(self):
        """Reindex the collection"""
        self.collection.search_engine(self.collection).reindex()
        success('reindexing completed')
        return page('complete!', title='Reindex')


class BasicSearch(object):
    """Provides basic search capability"""

    def __init__(self, collection):
        self.collection = collection
        logger = logging.getLogger(__name__)
        logger.debug(
            'starting BasicSearch for %s collection',
            self.collection.name
        )

    def search(self, text):
        """Return records that match search text"""

        def matches(item, terms):
            """match a search by field values"""
            fields.initialize(item)
            v = ';'.join(
                map(str, fields.as_searchable())
            ).lower()
            return terms and not any(t not in v for t in terms)

        fields = self.collection.fields
        terms = text and [t.lower() for t in text.split()]

        return [
            record for record in self.collection.store
            if matches(record, terms)
        ]

    def add(self, key, values):
        """Add record values to index"""
        pass

    def update(self, key, values):
        """Update indexed record values"""
        pass

    def delete(self, key):
        """Delete indexed record values"""
        pass

    def reindex(self):   # pragma: no cover
        warning('BasicSearch does not use indexing')


def as_tokens(values, max_len=20):
    """Return values as a set of tokens

    >>> sorted(list(as_tokens(['this is a test', 'other', 'tokentoolongtobecapturedasis'])))
    ['a', 'is', 'other', 'test', 'this', 'tokentoolongtobecapt']
    """
    tokens = set([
        t[:max_len] for v in values
        for t in v.lower().split()
    ])
    return tokens


class IndexedCollectionSearch(object):
    """Provides token index for fast lookups

    We only provide enough room for tokens up to length 20 only because
    we have to draw the line somewhere.  This may result in some records
    not being found if the search would have mached on characters beyond
    the position 20.
    """

    max_token_len = 20

    def __init__(self, collection):
        logger = logging.getLogger(__name__)
        self.collection = collection
        self.db = collection.store.db
        self.kind = self.collection.store.kind
        logger.debug(
            'starting IndexedCollectionSearch for %s collection',
            self.collection.name
        )

        if 'tokens' not in self.db.get_tables():
            self.db("""
            create table if not exists tokens (
                kind varchar(100),
                row_id int unsigned not null,
                token char({})
            )
            """.format(self.max_token_len))

    def reindex(self):
        """Rebuild the collection index

        This method indexes a few records at a time, in batches.  It
        can be very slow so should be done only by admins or as part
        of a maintenance cycle in the background.   Once the table is
        indexed this routine should not be needed.  It's mainly provided
        to index an already existing table or to replace a damaged
        index.
        """

        collection = self.collection
        fields = collection.fields

        logger = logging.getLogger(__name__)
        count = 0
        tick = 100
        total = len(collection.store)

        block = []
        cmd = 'insert into tokens values ({!r}, %s, %s)'.format(
            self.kind
        )

        msg = 'indexed %s of %s records (%0.4s%%)'

        self.zap()
        for record in collection.store:

            if not count % tick:
                if block:
                    self.db.execute_many(cmd, block)
                    block.clear()
                    logger.debug(msg, count, total, 100.0*count/total)
            count += 1

            fields.initialize(collection.model(record))
            values = as_tokens(fields.as_searchable(), self.max_token_len)
            block.extend(zip([record._id] * len(values), values))

        if block:
            self.db.execute_many(cmd, block)
            block.clear()
        logger.debug(msg, count, total, 100.0*count/total)

    def add(self, key, values):
        """Add record values to index"""
        tokens = [(t,) for t in as_tokens(values, self.max_token_len)]
        cmd = 'insert into tokens values ({!r}, {!r}, %s)'.format(
            self.kind, key
        )
        self.db.execute_many(cmd, tokens)

    def delete(self, key):
        """Delete indexed record values"""
        self.db(
            'delete from tokens where kind=%s and row_id=%s',
            self.kind,
            key
        )

    def update(self, key, values):
        """Update indexed record values"""
        self.delete(key)
        self.add(key, values)

    def zap(self):
        """Delete values for all records"""
        self.db('delete from tokens where kind=%s', self.kind)

    def search(self, text):
        """Return records that match search text"""

        terms = text and [t.lower()[:self.max_token_len] for t in text.split()]
        cmd = 'select distinct row_id from tokens where kind=%s and token like %s'

        result = []
        for term in sorted(terms, key=len, reverse=True):
            target = '%{}%'.format(term)
            result.append(
                set(i for i, in self.db(cmd, self.kind, target))
            )

        keys = list(set.intersection(*result))
        return self.collection.store.get(keys)


class Collection(object):
    """A collection of Records"""

    controller = CollectionController
    view = CollectionView
    store_type = EntityStore
    store = None
    url = None
    allows = shared_collection_policy('managers')
    verbose = True
    sorter = None

    @property
    def fields(self):
        """a fields callable may have data intensive operations, delay execution until it is needed"""
        if callable(self.__fields):
            self.__fields = self.__fields()
        return self.__fields

    def set_fields(self, fields):
        """Set the fields to a new value

        This can be used for switching fields on the fly, for example
        when your collection contains entities that are similar enough
        to be included in the same collection, but that require their
        own fields.
        """
        self.__fields = fields

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

        def calc_url():
            """calculate default collection URL"""
            return '/' + '/'.join(context.request.route[:2])

        get = kwargs.pop

        self.__fields = fields
        self.item_name = get('item_name', None) or name_from(fields)
        self.name = get('name', self.item_name + 's')
        self.title = self.name.title().replace('_',' ')
        self.item_title = self.item_name.title().replace('_',' ')
        self.filter = get('filter', None)
        self.columns = get('columns', None)
        self.labels = get('labels', None)
        self.model = get('model', None)
        self.store = get('store', None)
        self.url = get('url', calc_url())
        self.controller = get('controller', self.controller)
        self.view = get('view', self.view)
        self.link = link_to(self.name, self.url)
        self.key_name = get('key_name', 'key')
        self.user = None
        self.request = None
        self.route = None
        self.search_engine = get('search_engine', BasicSearch)
        self.many_records = 50

        if 'policy' in kwargs:
            self.allows = get('policy')

    @property
    def has_many_records(self):
        return len(self.store) >= self.many_records

    def order(self, item):
        """Returns the sort key"""
        return item.name.lower()

    def locate(self, key):
        """locate a record"""
        return locate(self, key)

    def get_columns(self):
        """Return the collection columns."""
        if self.columns:
            return self.columns
        return ['link'] + [f.name for f in self.fields.as_list()[1:]]

    def get_labels(self):
        """Return the collection labels."""
        if self.labels:
            return self.labels
        lookup = {f.name: f.label for f in self.fields.as_dict().values()}
        lookup.update(dict(
            link=self.fields.as_list()[0].label,
        ))
        labels = [lookup.get(name, name.capitalize()) for name in self.get_columns()]
        return labels

    def handle(self, route, request):
        """handle a request"""

        self.user = request.user
        self.request = request
        self.route = route

        logger = logging.getLogger(__name__)
        logger.debug('Collection handler called')

        if self.store is None:
            if self.model is None:
                self.model = CollectionModel
                self.model.collection_url = self.url
                self.store = EntityStore(
                    request.site.db,
                    self.model,
                    self.item_name + '_collection'
                )
            else:
                self.store = EntityStore(
                    request.site.db,
                    self.model,
                )

        return (
            self.controller(self)(*route, **request.data) or
            self.view(self)(*route, **request.data)
        )

    def process(self, *args, **data):
        """Process method parameters

        This style of calling collections is useful when you want to
        make your collection available as an attribute of a Dispatcher.
        """
        route = args
        request = context.request

        self.user = request.user
        self.request = request
        self.route = route

        logger = logging.getLogger(__name__)
        logger.debug('Collection process called')

        if self.store is None:
            if self.model is None:
                self.model = CollectionModel
                self.model.collection_url = self.url
                self.store = EntityStore(
                    request.site.db,
                    self.model,
                    self.item_name + '_collection'
                )
            else:
                self.store = EntityStore(
                    request.site.db,
                    self.model,
                )

        return (
            self.controller(self)(*route, **request.data) or
            self.view(self)(*route, **request.data)
        )

    def __call__(self, route, request):
        return self.handle(route, request)

    def __str__(self):
        return 'collection of ' + str(self.store.kind)


class SilentCollection(Collection):
    """A collection of Records where we do not audit "View" events"""
    verbose = False
