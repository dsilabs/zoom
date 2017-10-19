"""
    test the user module
"""
import unittest
import datetime
import logging

from zoom.database import setup_test
from zoom.users import User, Users, hash_password
from zoom.exceptions import UnauthorizedException

class TestUser(unittest.TestCase):

    def setUp(self):
        self.db = setup_test()
        self.users = Users(self.db)

    def tearDown(self):
        self.db.close()

    def test_get_user(self):
        user = self.users.get(1)
        self.assertEqual(user._id, 1)
        self.assertEqual(user.username, 'admin')
        self.assertEqual(user.first_name, 'Admin')
        self.assertEqual(user.last_name, 'User')
        user = self.users.get(3)
        self.assertEqual(user._id, 3)

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
        self.assertEqual(user.link, '<a href="mysite.com/app/admin/users/user">user</a>')

    def test_user_activate(self):
        user = self.users.first(username='user')
        self.assertEqual(user.status, 'A')
        self.assertTrue(user.is_active)
        user.deactivate()
        self.assertFalse(user.is_active)
        self.assertNotEqual(user.status, 'A')
        user.save()

        user = self.users.first(username='user')
        self.assertFalse(user.is_active)
        self.assertEqual(user.status, 'I')
        user.activate()
        self.assertTrue(user.is_active)
        user.save()

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
