"""
    Test the collect module
"""

import logging
import sys
import unittest
import difflib
from decimal import Decimal

import faker
import zoom

from zoom.helpers import url_for_page
from zoom.context import context
from zoom.collect import Collection, CollectionModel
from zoom.exceptions import UnauthorizedException
from zoom.fields import Fields, TextField, DecimalField
from zoom.users import Users
from zoom.validators import required

fake = faker.Faker()

VIEW_EMPTY_LIST = """<div class="baselist">

<table>
<thead><tr>
<th>Name</th>
<th>Address</th>
<th>Salary</th>
</tr></thead>
<tbody>
</tbody>
<tr><td colspan=3>None</td></tr>
</table>
<div class="footer">0 people</div>
</div>"""

VIEW_SINGLE_RECORD_LIST = """<div class="baselist">

<table>
<thead><tr>
<th>Name</th>
<th>Address</th>
<th>Salary</th>
</tr></thead>
<tbody>
<tr id="row-1">
<td nowrap><a href="<dz:app_url>/people/joe">Joe</a></td>
<td nowrap>123 Somewhere St</td>
<td nowrap>40,000</td>
</tr>
</tbody>
</table>
<div class="footer">1 person</div>
</div>"""

VIEW_TWO_RECORD_LIST = """<div class="baselist">

<table>
<thead><tr>
<th>Name</th>
<th>Address</th>
<th>Salary</th>
</tr></thead>
<tbody>
<tr id="row-1">
<td nowrap><a href="<dz:app_url>/people/joe">Joe</a></td>
<td nowrap>123 Somewhere St</td>
<td nowrap>40,000</td>
</tr>
<tr id="row-2">
<td nowrap><a href="<dz:app_url>/people/sally">Sally</a></td>
<td nowrap>123 Special St</td>
<td nowrap>45,000</td>
</tr>
</tbody>
</table>
<div class="footer">2 people</div>
</div>"""

VIEW_ALL_RECORDS_LIST = """<div class="baselist">

<table>
<thead><tr>
<th>Name</th>
<th>Address</th>
<th>Salary</th>
</tr></thead>
<tbody>
<tr id="row-1" class="light">
<td nowrap><a href="/noapp//myapp/jim">Jim</a></td>
<td nowrap>123 Somewhere St</td>
<td nowrap>40,000</td>
</tr>
<tr id="row-2" class="dark">
<td nowrap><a href="/noapp//myapp/joe">Joe</a></td>
<td nowrap>123 Somewhere St</td>
<td nowrap>40,000</td>
</tr>
<tr id="row-3" class="light">
<td nowrap><a href="/noapp//myapp/sally">Sally</a></td>
<td nowrap>123 Special St</td>
<td nowrap>45,000</td>
</tr>
</tbody>
</table>
<div class="footer">3 peoples</div>
</div>"""

VIEW_NO_JOE_LIST = """<div class="baselist">

<table>
<thead><tr>
<th>Name</th>
<th>Address</th>
<th>Salary</th>
</tr></thead>
<tbody>
<tr id="row-1">
<td nowrap><a href="<dz:app_url>/people/sally">Sally</a></td>
<td nowrap>123 Special St</td>
<td nowrap>45,000</td>
</tr>
</tbody>
</table>
<div class="footer">1 person</div>
</div>"""

VIEW_UPDATED_JOE_LIST = """<div class="baselist">

<table>
<thead><tr>
<th>Name</th>
<th>Address</th>
<th>Salary</th>
</tr></thead>
<tbody>
<tr id="row-1" class="light">
<td nowrap><a href="/noapp//myapp/jim">Jim</a></td>
<td nowrap>123 Somewhere St</td>
<td nowrap>40,000</td>
</tr>
<tr id="row-2" class="dark">
<td nowrap><a href="/noapp//myapp/sally">Sally</a></td>
<td nowrap>123 Special St</td>
<td nowrap>45,000</td>
</tr>
</tbody>
</table>
<div class="footer">2 peoples</div>
</div>"""

def assert_same(t1, t2):
    try:
        assert t1 == t2
    except:
        s1 = t1.splitlines()
        s2 = t2.splitlines()
        print('\n'.join(difflib.context_diff(s1, s2)))
        raise

class Person(CollectionModel):
    pass
    key = property(lambda self: zoom.utils.id_for(self.name))
    url = property(lambda self: url_for_page('people', self.key))
    # link = property(lambda self: self.name)
    link = property(lambda self: zoom.helpers.link_to(self.name, self.url))
#class TestPerson(CollectionRecord): pass

# define the fields for the collection
def person_fields():
    return Fields(
        TextField('Name', required),
        TextField('Address'),
        DecimalField('Salary'),
    )


class FakeRequest(object):
    def __init__(self, *args, **kwargs):
        self.data = {}
        self.route = args
        self.__dict__.update(kwargs)

    def get_elapsed(self):
        return 0


class FakeSite(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TestCollect(unittest.TestCase):

    def setUp(self):
        # setup the system and install our own test database
        # system.setup(os.path.expanduser('~'))
        self.db = zoom.database.setup_test()
        self.users = Users(self.db)
        self.user = self.users.first(username='admin')
        self.site = zoom.system.site = FakeSite(
            db=self.db,
            url='',
            logging=False,
        )
        self.request = context.request = FakeRequest(
            '/myapp',
            user=self.user,
            site=self.site,
            path='/myapp',
            ip_address='127.0.0.1',
            remote_user='',
            host='localhost',
            data={},
        )
        zoom.component.composition.parts = zoom.component.component()

        # user.initialize('guest')
        # self.user.groups = ['managers']

        # create the test collection
        self.collection = Collection(
            person_fields,
            name='People',
            model=Person,
            url='/myapp',
            store=zoom.store.EntityStore(self.db, Person)
        )

        # so we can see our print statements
        self.save_stdout = sys.stdout
        sys.stdout = sys.stderr

        self.logger = logging.getLogger(__name__)

    def tearDown(self):
        # remove our test data
        # self.collection.store.zap()
        self.db.close()
        sys.stdout = self.save_stdout

    def collect(self, *route, **data):
        self.request.route = list(route)
        self.request.data = data
        return self.collection(route, self.request)

    def assert_response(self, content, *args, **kwargs):
        assert_same(content, self.collect(*args, **kwargs).content)

    def test_empty(self):
        self.collection.store.zap()
        self.assert_response(VIEW_EMPTY_LIST)

    def test_index_redirect(self):
        response = self.collect('index')
        self.assertEqual(type(response), zoom.tools.Redirector)

    def test_index_many(self):
        self.collection.store.zap()
        self.assert_response(VIEW_EMPTY_LIST)

        insert_record_input = dict(
            create_button='y',
            name='Joe',
            address='123 Somewhere St',
            salary=Decimal('40000'),
        )
        self.collect('new', **insert_record_input)
        self.assert_response(VIEW_SINGLE_RECORD_LIST)

        for _ in range(51):
            self.collect('new', **dict(
                create_button='y',
                name=fake.name(),
                address=fake.street_address(),
                salary=Decimal('40000'),
            ))

        content = self.collect().content
        assert '15 people shown of 52 people' in content

        content = self.collect(all='y').content
        assert '52 people shown of 52 people' in content

    def test_basic_search(self):
        self.collection.store.zap()
        self.assert_response(VIEW_EMPTY_LIST)

        insert_record_input = dict(
            create_button='y',
            name='Joe Zzzzz',
            address='123 Somewhere St',
            salary=Decimal('40000'),
        )
        self.collect('new', **insert_record_input)

        for _ in range(5):
            self.collect('new', **dict(
                create_button='y',
                name=fake.name(),
                address=fake.street_address(),
                salary=Decimal('40000'),
            ))

        content = self.collect(q='Zzzz').content
        assert '1 person found in search of 6 people' in content

        content = self.collect(q='Xzzz').content
        assert '0 people found in search of 6 people' in content


    def test_indexed_search(self):
        self.collection.store.zap()
        self.assert_response(VIEW_EMPTY_LIST)
        self.collection.search_engine = zoom.collect.IndexedCollectionSearch

        insert_record_input = dict(
            create_button='y',
            name='Joe Zzzzz',
            address='123 Somewhere St',
            salary=Decimal('40000'),
        )
        self.collect('new', **insert_record_input)

        for _ in range(5):
            self.collect('new', **dict(
                create_button='y',
                name=fake.name(),
                address=fake.street_address(),
                salary=Decimal('40000'),
            ))

        content = self.collect(q='Zzzz').content
        assert '1 person found in search of 6 people' in content

        content = self.collect(q='Xzzz').content
        assert '0 people found in search of 6 people' in content

        self.collect('reindex')

        content = self.collect(q='Zzzz').content
        assert '1 person found in search of 6 people' in content

        content = self.collect(q='Xzzz').content
        assert '0 people found in search of 6 people' in content

        self.collect('delete', 'joe-zzzzz', **{'confirm': 'no'})

        content = self.collect(q='Zzzz').content
        assert '0 people found in search of 5 people' in content

    def test_insert(self):
        self.collection.store.zap()
        self.assert_response(VIEW_EMPTY_LIST)

        insert_record_input = dict(
            create_button='y',
            name='Joe',
            address='123 Somewhere St',
            salary=Decimal('40000'),
        )
        self.collect('new', **insert_record_input)
        self.logger.debug(str(self.collection.store))
        self.assert_response(VIEW_SINGLE_RECORD_LIST)

    def test_show(self):
        self.collection.store.zap()
        self.assert_response(VIEW_EMPTY_LIST)

        insert_record_input = dict(
            create_button='y',
            name='Joe',
            address='123 Somewhere St',
            salary=Decimal('40000'),
        )
        self.collect('new', **insert_record_input)
        response = self.collect('show', 'joe').content
        assert '123 Somewhere St' in response
        assert '123 Nowhere St' not in response

    def test_new(self):
        response = self.collect('new').content
        assert 'Name' in response

    def test_edit(self):
        self.collection.store.zap()
        self.assert_response(VIEW_EMPTY_LIST)

        insert_record_input = dict(
            create_button='y',
            name='Joe',
            address='123 Somewhere St',
            salary=Decimal('40000'),
        )
        self.collect('new', **insert_record_input)
        response = self.collect('edit', 'joe').content
        assert '123 Somewhere St' in response
        assert '123 Nowhere St' not in response

    def test_save(self):
        self.collection.store.zap()
        self.assert_response(VIEW_EMPTY_LIST)

        insert_record_input = dict(
            create_button='y',
            name='Joe',
            address='123 Somewhere St',
            salary=Decimal('40000'),
        )
        self.collect('new', **insert_record_input)
        response = self.collect('edit', 'joe').content
        assert '123 Somewhere St' in response
        assert '123 Nowhere St' not in response

        update_record_input = dict(
            save_button='y',
            name='Joe',
            address='123 Somewhere Else St',
            salary=Decimal('50000'),
        )
        response = self.collect('joe', **update_record_input)

        response = self.collect('show', 'joe').content
        assert '123 Somewhere Else St' in response
        assert '123 Somewhere St' not in response
        assert '123 Nowhere St' not in response

    def test_delete(self):
        self.collection.store.zap()
        self.assert_response(VIEW_EMPTY_LIST)

        joe_input = dict(
            create_button='y',
            name='Joe',
            address='123 Somewhere St',
            salary=Decimal('40000'),
        )
        self.collect('new', **joe_input)
        sally_input = dict(
            create_button='y',
            name='Sally',
            address='123 Special St',
            salary=Decimal('45000'),
        )
        self.collect('new', **sally_input)
        self.assert_response(VIEW_TWO_RECORD_LIST)

        self.collect('delete', 'joe', **{'confirm': 'no'})
        self.assert_response(VIEW_NO_JOE_LIST)

        self.collect('delete', 'sally', **{'confirm': 'no'})
        self.assert_response(VIEW_EMPTY_LIST)

    def test_get_columns(self):
        savecols = self.collection.get_columns()
        try:
            self.collection.columns = ['one', 'two']
            self.assertEqual(
                self.collection.get_columns(),
                ['one', 'two']
            )
        finally:
            self.collection.columns = savecols

    def test_get_labels(self):
        saved = self.collection.get_labels()
        try:
            self.collection.labels = ['One', 'Two']
            self.assertEqual(
                self.collection.get_labels(),
                ['One', 'Two']
            )
        finally:
            self.collection.labels = saved


    # def test_update(self):
    #     self.collection.store.zap()
    #     t = self.collection()
    #     assert_same(VIEW_EMPTY_LIST, t.content)
    #
    #     joe_input = dict(
    #         CREATE_BUTTON='y',
    #         NAME='Joe',
    #         ADDRESS='123 Somewhere St',
    #         SALARY=Decimal('40000'),
    #     )
    #     t = self.collection('new', **joe_input)
    #
    #     sally_input = dict(
    #         CREATE_BUTTON='y',
    #         NAME='Sally',
    #         ADDRESS='123 Special St',
    #         SALARY=Decimal('45000'),
    #     )
    #     t = self.collection('new', **sally_input)
    #
    #     self.collection('joe', 'edit', **dict(
    #         SAVE_BUTTON='y',
    #         NAME='Jim',
    #         ADDRESS='123 Somewhere St',
    #         SALARY=Decimal('40000'),
    #     ))
    #     t = self.collection()
    #     assert_same(VIEW_UPDATED_JOE_LIST, t.content)
    #
    #     self.collection('delete', 'jim', **{'CONFIRM': 'NO'})
    #     t = self.collection()
    #     assert_same(VIEW_NO_JOE_LIST, t.content)
    #
    #     self.collection('delete', 'sally', **{'CONFIRM': 'NO'})
    #     t = self.collection()
    #     assert_same(VIEW_EMPTY_LIST, t.content)
    #
    # def test_authorized_editors(self):
    #     self.collection.store.zap()
    #     t = self.collection()
    #     assert_same(VIEW_EMPTY_LIST, t.content)
    #
    #     joe_input = dict(
    #         CREATE_BUTTON='y',
    #         NAME='Joe',
    #         ADDRESS='123 Somewhere St',
    #         SALARY=Decimal('40000'),
    #     )
    #     t = self.collection('new', **joe_input)
    #
    #     sally_input = dict(
    #         CREATE_BUTTON='y',
    #         NAME='Sally',
    #         ADDRESS='123 Special St',
    #         SALARY=Decimal('45000'),
    #     )
    #     t = self.collection('new', **sally_input)
    #     t = self.collection()
    #     assert_same(VIEW_TWO_RECORD_LIST, t.content)
    #
    #     # only authorized users can edit collections
    #     user.groups = []
    #     with self.assertRaises(UnauthorizedException):
    #         self.collection('joe', 'edit', **dict(
    #             SAVE_BUTTON='y',
    #             NAME='Jim',
    #             ADDRESS='123 Somewhere St',
    #             SALARY=Decimal('40000'),
    #         ))
    #     t = self.collection()
    #     assert_same(VIEW_TWO_RECORD_LIST, t.content)
    #
    #     user.groups = ['managers']
    #     self.collection('joe', 'edit', **dict(
    #         SAVE_BUTTON='y',
    #         NAME='Jim',
    #         ADDRESS='123 Somewhere St',
    #         SALARY=Decimal('40000'),
    #     ))
    #     t = self.collection()
    #     assert_same(VIEW_UPDATED_JOE_LIST, t.content)
    #
    #     user.groups = []
    #     with self.assertRaises(UnauthorizedException):
    #         self.collection('delete', 'jim', **{'CONFIRM': 'NO'})
    #     t = self.collection()
    #     assert_same(VIEW_UPDATED_JOE_LIST, t.content)
    #
    #     user.groups = ['managers']
    #     self.collection('delete', 'jim', **{'CONFIRM': 'NO'})
    #     t = self.collection()
    #     assert_same(VIEW_NO_JOE_LIST, t.content)
    #
    #     self.collection('delete', 'sally', **{'CONFIRM': 'NO'})
    #     t = self.collection()
    #     assert_same(VIEW_EMPTY_LIST, t.content)
    #
    #
    # def test_private(self):
    #
    #     class PrivatePerson(Person):
    #         def allows(self, user, action=None):
    #
    #             def is_owner(user):
    #                 return user.user_id == self.owner_id
    #
    #             def is_user(user):
    #                 return user.is_authenticated
    #
    #             actions = {
    #                 'create': is_user,
    #                 'read': is_owner,
    #                 'update': is_owner,
    #                 'delete': is_owner,
    #             }
    #
    #             return actions.get(action)(user)
    #
    #     #def private(rec, user, action=None):
    #         #return rec.owner == user.user_id
    #
    #     self.collection = Collection('People', person_fields, PrivatePerson, url='/myapp')
    #     self.collection.can_edit = lambda: True
    #     #self.collection.authorization = private
    #
    #     self.collection.store.zap()
    #     t = self.collection()
    #     assert_same(VIEW_EMPTY_LIST, t.content)
    #
    #     # user one inserts two records
    #     joe_input = dict(
    #         CREATE_BUTTON='y',
    #         NAME='Jim',
    #         ADDRESS='123 Somewhere St',
    #         SALARY=Decimal('40000'),
    #     )
    #     t = self.collection('new', **joe_input)
    #
    #     sally_input = dict(
    #         CREATE_BUTTON='y',
    #         NAME='Sally',
    #         ADDRESS='123 Special St',
    #         SALARY=Decimal('45000'),
    #     )
    #     t = self.collection('new', **sally_input)
    #     t = self.collection()
    #     assert_same(VIEW_UPDATED_JOE_LIST, t.content)
    #
    #     # user two inserts one record
    #     user.initialize('admin')
    #     self.collection('new', **dict(
    #         CREATE_BUTTON='y',
    #         NAME='Joe',
    #         ADDRESS='123 Somewhere St',
    #         SALARY=Decimal('40000'),
    #     ))
    #     t = self.collection()
    #     assert_same(VIEW_SINGLE_RECORD_LIST, t.content)
    #
    #     # user one can still only see theirs
    #     user.initialize('guest')
    #     t = self.collection()
    #     assert_same(VIEW_UPDATED_JOE_LIST, t.content)
    #
    #     # user can't read records that belong to others
    #     with self.assertRaises(UnauthorizedException):
    #         t = self.collection('joe')
    #
    #     # user can't edit records that belong to others
    #     with self.assertRaises(UnauthorizedException):
    #         t = self.collection('joe', 'edit')
    #
    #     # user can't do delete confirmation for records that belong to others
    #     with self.assertRaises(UnauthorizedException):
    #         t = self.collection('joe', 'delete')
    #
    #     # user can't update records that belong to others
    #     with self.assertRaises(UnauthorizedException):
    #         t = self.collection('joe', 'edit', **dict(
    #             SAVE_BUTTON='y',
    #             NAME='Andy',
    #             ADDRESS='123 Somewhere St',
    #             SALARY=Decimal('40000'),
    #         ))
    #
    #     # user can't delete records that belong to others
    #     with self.assertRaises(UnauthorizedException):
    #         self.collection('joe', 'delete', **{'CONFIRM': 'NO'})
    #
    #     # switch back to owner and do the same operations
    #     user.initialize('admin')
    #     self.collection('joe')
    #     self.collection('joe', 'edit')
    #     self.collection('joe', 'delete')
    #     self.collection('joe', 'edit', **dict(
    #         SAVE_BUTTON='y',
    #         NAME='Andy',
    #         ADDRESS='123 Somewhere St',
    #         SALARY=Decimal('40000'),
    #     ))
    #     self.collection('andy', 'delete', **{'CONFIRM': 'NO'})
    #
    #
    #     user.initialize('guest')
    #     user.groups = ['managers']
    #     self.collection('delete', 'jim', **{'CONFIRM': 'NO'})
    #     t = self.collection()
    #     assert_same(VIEW_NO_JOE_LIST, t.content)
    #
    #     self.collection('delete', 'sally', **{'CONFIRM': 'NO'})
    #     t = self.collection()
    #     assert_same(VIEW_EMPTY_LIST, t.content)
    #
    #
    # def test_published(self):
    #
    #     class PrivatePerson(Person):
    #         def allows(self, user, action=None):
    #
    #             def is_owner(user):
    #                 return user.user_id == self.owner_id
    #
    #             def is_user(user):
    #                 return user.is_authenticated
    #
    #             actions = {
    #                 'create': is_user,
    #                 'read': is_user,
    #                 'update': is_owner,
    #                 'delete': is_owner,
    #             }
    #
    #             return actions.get(action)(user)
    #
    #     self.collection = Collection('People', person_fields, PrivatePerson, url='/myapp')
    #     self.collection.can_edit = lambda: True
    #
    #     self.collection.store.zap()
    #     t = self.collection()
    #     assert_same(VIEW_EMPTY_LIST, t.content)
    #
    #     # user one inserts two records
    #     user.initialize('user')
    #     assert user.is_authenticated
    #     user.groups = ['managers']
    #
    #     joe_input = dict(
    #         CREATE_BUTTON='y',
    #         NAME='Jim',
    #         ADDRESS='123 Somewhere St',
    #         SALARY=Decimal('40000'),
    #     )
    #     t = self.collection('new', **joe_input)
    #
    #     sally_input = dict(
    #         CREATE_BUTTON='y',
    #         NAME='Sally',
    #         ADDRESS='123 Special St',
    #         SALARY=Decimal('45000'),
    #     )
    #     t = self.collection('new', **sally_input)
    #     t = self.collection()
    #     assert_same(VIEW_UPDATED_JOE_LIST, t.content)
    #
    #     # user two inserts one record
    #     user.initialize('admin')
    #     self.collection('new', **dict(
    #         CREATE_BUTTON='y',
    #         NAME='Joe',
    #         ADDRESS='123 Somewhere St',
    #         SALARY=Decimal('40000'),
    #     ))
    #     t = self.collection()
    #     assert_same(VIEW_ALL_RECORDS_LIST, t.content)
    #
    #     # user one can also see all
    #     user.initialize('user')
    #     t = self.collection()
    #     assert_same(VIEW_ALL_RECORDS_LIST, t.content)
    #
    #     # guest can't read records
    #     user.initialize('guest')
    #     with self.assertRaises(UnauthorizedException):
    #         t = self.collection('joe')
    #
    #     # authenticated user can read records that belong to others
    #     user.initialize('user')
    #     t = self.collection('joe')
    #
    #     # user can't edit records that belong to others
    #     user.initialize('guest')
    #     with self.assertRaises(UnauthorizedException):
    #         t = self.collection('joe', 'edit')
    #
    #     # user can't edit records that belong to others
    #     user.initialize('user')
    #     with self.assertRaises(UnauthorizedException):
    #         t = self.collection('joe', 'edit')
    #
    #     # guest can't do delete confirmation for records that belong to others
    #     user.initialize('guest')
    #     with self.assertRaises(UnauthorizedException):
    #         t = self.collection('joe', 'delete')
    #
    #     # user can't do delete confirmation for records that belong to others
    #     user.initialize('user')
    #     with self.assertRaises(UnauthorizedException):
    #         t = self.collection('joe', 'delete')
    #
    #     # user can't update records that belong to others
    #     with self.assertRaises(UnauthorizedException):
    #         t = self.collection('joe', 'edit', **dict(
    #             SAVE_BUTTON='y',
    #             NAME='Andy',
    #             ADDRESS='123 Somewhere St',
    #             SALARY=Decimal('40000'),
    #         ))
    #
    #     # user can't delete records that belong to others
    #     with self.assertRaises(UnauthorizedException):
    #         self.collection('joe', 'delete', **{'CONFIRM': 'NO'})
    #
    #     # switch back to owner and do the same operations
    #     user.initialize('admin')
    #     self.collection('joe')
    #     self.collection('joe', 'edit')
    #     self.collection('joe', 'delete')
    #     self.collection('joe', 'edit', **dict(
    #         SAVE_BUTTON='y',
    #         NAME='Andy',
    #         ADDRESS='123 Somewhere St',
    #         SALARY=Decimal('40000'),
    #     ))
    #     self.collection('andy', 'delete', **{'CONFIRM': 'NO'})
    #
    #     # guest can't delete
    #     user.initialize('guest')
    #     user.groups = ['managers']
    #     with self.assertRaises(UnauthorizedException):
    #         self.collection('delete', 'jim', **{'CONFIRM': 'NO'})
    #
    #     # guest can't delete
    #     with self.assertRaises(UnauthorizedException):
    #         self.collection('delete', 'sally', **{'CONFIRM': 'NO'})
    #
    #     # non-owner can't delete
    #     user.initialize('admin')
    #     user.groups = ['managers']
    #     with self.assertRaises(UnauthorizedException):
    #         self.collection('delete', 'jim', **{'CONFIRM': 'NO'})
    #
    #     # non-owner can't delete
    #     with self.assertRaises(UnauthorizedException):
    #         self.collection('delete', 'sally', **{'CONFIRM': 'NO'})
    #
    #     # owner can delete
    #     user.initialize('user')
    #     user.groups = ['managers']
    #     self.collection('delete', 'jim', **{'CONFIRM': 'NO'})
    #     t = self.collection()
    #     assert_same(VIEW_NO_JOE_LIST, t.content)
    #
    #     self.collection('delete', 'sally', **{'CONFIRM': 'NO'})
    #     t = self.collection()
    #     assert_same(VIEW_EMPTY_LIST, t.content)
    #
