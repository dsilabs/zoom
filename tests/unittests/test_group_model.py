"""
    test the group model from zoom.models
"""
import unittest

from zoom.database import setup_test
from zoom.models import Group, Groups


class TestGroup(unittest.TestCase):
    """Test the Zoom Group and Groups models"""

    def setUp(self):
        self.db = setup_test()
        self.groups = Groups(self.db)

    def tearDown(self):
        self.db.close()

    def test_get_group(self):
        group = self.groups.get(1)
        self.assertEqual(group._id, 1)
        self.assertEqual(group.name, 'administrators')
        self.assertEqual(group.type, 'U')
        self.assertEqual(group.admin_group_id, 1)
        group = self.groups.get(3)
        self.assertEqual(group._id, 3)

    def test_get_group_users(self):
        group = self.groups.first(name='users')
        self.assertSetEqual(group.users, group.get_users())
        self.assertTrue(group.users)

    def test_group_record_store(self):
        group = self.groups.first(name='users')
        self.assertTrue(group['__store'])
        self.assertIsInstance(group['__store'], Groups)

        del group['__store']
        self.assertRaises(KeyError, lambda: group.apps, )
        self.assertRaises(KeyError, lambda: group.roles, )
        self.assertRaises(KeyError, lambda: group.subgroups, )
