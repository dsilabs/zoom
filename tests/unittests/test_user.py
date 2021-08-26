"""
    test the user module
"""
import unittest
import datetime
import logging

import zoom
import zoom.request
from zoom.database import setup_test
from zoom.users import (
    User, Users, hash_password, get_current_username, set_current_user,
    get_user, get_users, locate_user
)
from zoom.models import Groups
from zoom.exceptions import UnauthorizedException

class TestUser(unittest.TestCase):

    def setUp(self):
        self.db = setup_test()
        self.users = Users(self.db)

        self.groups = Groups(self.db)
        zoom.system.request = zoom.utils.Bunch(
            app=zoom.utils.Bunch(
                name=__name__,
            ),
            session=zoom.utils.Bunch(),
            user=self.users.first(username='admin')
        )
        zoom.system.site = zoom.utils.Bunch(
            url='nosite',
            db=self.db,
            groups=self.groups,
            users=self.users
        )
        zoom.system.user = self.users.first(username='admin')

    def tearDown(self):
        self.db.close()

    def test_add(self):
        self.assertFalse(self.users.first(username='sam'))
        user = self.users.add('sam', 'sam', 'smith', 'sam@testco.com')
        self.assertTrue(isinstance(user, User))
        self.assertEqual(user.name, 'sam smith')
        sam = self.users.first(username='sam')
        self.assertTrue(sam)
        self.assertTrue(sam.created)
        self.assertTrue(sam.created_by)
        self.assertTrue(sam.updated)
        self.assertTrue(sam.updated_by)
        self.users.delete(username='sam')
        self.assertFalse(self.users.first(username='sam'))

    def test_add_invalid(self):
        self.assertFalse(self.users.first(username='sam'))
        with self.assertRaises(Exception):
            self.users.add('sam', '', 'smith', 'sam@testco.com')
        try:
            self.users.add('sam', '', 'smith', 'sam@testco.com')
        except BaseException as e:
            self.assertEqual(str(e), 'minimum length 2')
        with self.assertRaises(Exception):
            self.users.add('sam', 'sam', 'smith', 'sam')
        try:
            self.users.add('sam', 'sam', 'smith', 'sam')
        except BaseException as e:
            self.assertEqual(str(e), 'enter a valid email address')
        with self.assertRaises(Exception):
            self.users.add('sam', 'sam', 'smith', 'sam@test.co', '123')
        try:
            self.users.add('sam', 'sam', 'smith', 'sam@test.co', '123')
        except BaseException as e:
            self.assertEqual(str(e), 'enter valid phone number')
        self.assertFalse(self.users.first(username='sam'))

    def test_get_user(self):
        user = self.users.get(1)
        self.assertEqual(user._id, 1)
        self.assertEqual(user.username, 'admin')
        self.assertEqual(user.first_name, 'Admin')
        self.assertEqual(user.last_name, 'User')
        user = self.users.get(3)
        self.assertEqual(user._id, 3)

    def test_get_current_username_guest(self):
        site = zoom.sites.Site()
        request = zoom.utils.Bunch(
            site=site,
            session=zoom.utils.Bunch(),
            remote_user=None
        )
        self.assertEqual(get_current_username(request), 'guest')

    def test_get_current_username_remote_user(self):
        site = zoom.sites.Site()
        request = zoom.utils.Bunch(
            site=site,
            session=zoom.utils.Bunch(),
            remote_user='user'
        )
        self.assertEqual(get_current_username(request), 'user')

    def test_get_current_username_session(self):
        site = zoom.sites.Site()
        request = zoom.utils.Bunch(
            site=site,
            session=zoom.utils.Bunch(username='user'),
            remote_user='not_a_user'
        )
        self.assertEqual(get_current_username(request), 'user')

    def test_set_current_user_none(self):
        site = zoom.sites.Site()
        site.guest = None
        request = zoom.utils.Bunch(
            site=site,
            session=zoom.utils.Bunch(),
            remote_user=None
        )
        self.assertRaises(Exception, set_current_user, request)

    def test_set_current_user_guest(self):
        site = zoom.sites.Site()
        request = zoom.utils.Bunch(
            site=site,
            session=zoom.utils.Bunch(),
            remote_user=None,
            user=None,
            profiler=set(),
        )
        set_current_user(request)
        self.assertEqual(request.user.username, 'guest')

    def test_set_current_user_known(self):
        site = zoom.sites.Site()
        request = zoom.utils.Bunch(
            site=site,
            session=zoom.utils.Bunch(),
            remote_user='user',
            profiler=set(),
        )
        set_current_user(request)
        self.assertEqual(request.user.username, 'user')

    def test_set_current_user_unknown(self):
        zoom.system.site = site = zoom.sites.Site()
        request = zoom.utils.Bunch(
            site=site,
            session=zoom.utils.Bunch(),
            remote_user='newuser',
            profiler=set(),
        )
        # If the user is authenticated but not known to the system
        # the user should be added to the users table.
        self.assertFalse(site.users.first(username='newuser'))
        set_current_user(request)
        self.assertEqual(request.user.username, 'newuser')
        self.assertTrue(site.users.first(username='newuser'))
        site.users.delete(username='newuser')
        self.assertFalse(site.users.first(username='newuser'))

    def test_user_groups(self):
        user = self.users.first(username='admin')
        self.assertEqual(user.groups, [
            'administrators',
            'everyone',
            'managers',
            'users'
        ])
        user = self.users.first(username='user')
        self.assertEqual(user.groups, ['everyone', 'users'])
        self.assertEqual(sorted(user.groups_ids), [2, 4])

    def test_user_login(self):
        request = zoom.request.build('http://localhost')
        request.site = zoom.sites.Site()
        admin = request.site.users.first(username='admin')
        request.user = admin
        request.session = zoom.utils.Bunch()
        admin.login(request, 'admin')
        self.assertEqual(request.session.username, 'admin')

    def test_user_initialize(self):
        user = self.users.first(username='admin')
        self.assertFalse(user.is_admin)
        request = zoom.request.build('http://localhost')
        request.site = zoom.sites.Site()
        request.user = user
        user.initialize(request)
        self.assertTrue(user.is_admin)

    def test_user_is_member(self):
        user = self.users.first(username='admin')
        self.assertTrue(user.is_member('administrators'))
        self.assertTrue(user.is_member('users'))
        self.assertFalse(user.is_member('notagroup'))
        user = self.users.first(username='user')
        self.assertTrue(user.is_member('users'))
        self.assertFalse(user.is_member('administrators'))
        self.assertFalse(user.is_member('notagroup'))

    def test_user_link(self):
        user = self.users.first(username='user')
        self.assertEqual(user._id, 2)
        logging.debug('user id is %r', user._id)
        zoom.system.user = zoom.utils.Bunch(is_admin=False)
        zoom.system.site = zoom.utils.Bunch(url='mysite.com/app')
        self.assertEqual(user.link, 'user')
        zoom.system.user = zoom.utils.Bunch(is_admin=True)
        self.assertEqual(
            user.link,
            '<a href="mysite.com/app/admin/users/user" name="link-to-user">user</a>'
        )

    def test_user_user_id(self):
        user = self.users.first(username='user')
        self.assertEqual(user._id, 2)
        self.assertEqual(user.user_id, 2)

    def test_user_nt_user_id(self):
        user = self.users.first(username='user')
        user.username = 'domain\\user'
        self.assertEqual(user.key, 'domain-user')

    def test_user_email_user_id(self):
        user = self.users.first(username='user')
        user.username = 'user@testco.com'
        self.assertEqual(user.key, 'user-at-testco.com')

    def test_user_activate(self):
        user = self.users.first(username='user')
        self.assertEqual(user.status, 'A')
        self.assertTrue(user.is_active)
        user.deactivate()
        self.assertFalse(user.is_active)
        self.assertNotEqual(user.status, 'A')

        user = self.users.first(username='user')
        self.assertFalse(user.is_active)
        self.assertEqual(user.status, 'I')
        user.activate()
        self.assertTrue(user.is_active)

        user = self.users.first(username='user')
        self.assertTrue(user.is_active)
        self.assertEqual(user.status, 'A')

    def test_user_can(self):
        class MyObject(object):
            def allows(self, user, action):
                return action == 'read' or user.username == 'admin'
        obj = MyObject()

        user = self.users.first(username='user')
        self.assertTrue(user.can('read', obj))
        self.assertFalse(user.can('edit', obj))

        user = self.users.first(username='admin')
        self.assertTrue(user.can('read', obj))
        self.assertTrue(user.can('edit', obj))

    def test_user_authorize(self):
        class MyObject(object):
            def allows(self, user, action):
                return action == 'read' or user.username == 'admin'
        obj = MyObject()

        user = self.users.first(username='user')
        user.authorize('read', obj)
        with self.assertRaises(UnauthorizedException):
            user.authorize('edit', obj)

        user = self.users.first(username='admin')
        user.authorize('read', obj)
        user.authorize('edit', obj)

    def test_set_password(self):
        class MyObject(object):
            def allows(self, user, action):
                return action == 'read' or user.username == 'admin'
        obj = MyObject()

        user = self.users.first(username='user')
        old_password = user.password
        new_password = 'helloworld'
        user.set_password(new_password)

        user2 = self.users.first(username='user')
        self.assertNotEqual(user2.password, old_password)
        self.assertEqual(user2.authenticate(new_password), True)

    def test_user_store(self):
        user = self.users.first(username='guest')
        self.assertListEqual(
            user.get_groups()[-4:],
            ['a_passreset', 'a_signup', 'everyone', 'guests']
        )

        # setup to trigger accessing the store
        user = self.users.first(username='user')
        del user['__store']
        self.assertRaises(KeyError, user.get_groups)

    def test_last_seen(self):
        guest = self.users.first(username='guest')
        self.assertIsNone(guest.last_seen)
        admin = self.users.first(username='admin')
        self.assertIsNone(admin.last_seen)

        # trigger the last seen attribute being set
        admin.update_last_seen()

        guest = self.users.first(username='guest')
        self.assertIsNone(guest.last_seen)
        admin = self.users.first(username='admin')
        self.assertIsNotNone(admin.last_seen)
        self.assertIsInstance(admin.last_seen, datetime.datetime)

    def test_get_user_no_params(self):
        user = get_user()
        self.assertEqual(user.username, 'admin')

    def test_get_user_with_id(self):
        user_id = get_users().first(username='user').user_id
        user = get_user(user_id)
        self.assertEqual(user.username, 'user')

    def test_get_user_with_username(self):
        user = get_user('user')
        self.assertEqual(user.username, 'user')
