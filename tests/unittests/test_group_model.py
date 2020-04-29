"""
    test the group model from zoom.models
"""
import unittest

import zoom
from zoom.database import setup_test
from zoom.models import Groups
from zoom.utils import Bunch

class TestGroup(unittest.TestCase):
    """Test the Zoom Group and Groups models"""

    def setUp(self):
        self.db = setup_test()
        self.groups = Groups(self.db)
        zoom.system.site = zoom.sites.Site()
        zoom.system.user = zoom.system.site.users.get(1)
        zoom.system.request = Bunch(app=Bunch(name=__name__))

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

    def test_add_remove_subgroup(self):
        users_group = self.groups.first(name='users')
        managers_group = self.groups.first(name='managers')
        self.assertEqual(managers_group.subgroups, {1})

        managers_group.add_subgroup(users_group)
        self.assertEqual(managers_group.subgroups, {1, users_group.group_id})

        managers_group.remove_subgroup(users_group)
        self.assertEqual(managers_group.subgroups, {1})

    def test_locate_group(self):
        groups = self.groups
        group = groups.first(name='users')
        group_id = group.group_id

        self.assertEqual(groups.locate(group).group_id, group_id)
        self.assertEqual(groups.locate(group_id).group_id, group_id)
        self.assertEqual(groups.locate(group.name).group_id, group_id)

    def test_groups_add_remove_app(self):
        groups = self.groups

        app_name = 'ping'

        self.assertNotIn(
            'a_' + app_name,
            set(g.name for g in groups)
        )

        groups.add_app(app_name)

        self.assertIn(
            'a_' + app_name,
            set(g.name for g in groups)
        )

        groups.remove_app(app_name)

        self.assertNotIn(
            'a_' + app_name,
            set(g.name for g in groups)
        )

    def test_groups_add_remove_app_idempotentcy(self):
        groups = self.groups

        app_name = 'ping'

        self.assertNotIn(
            'a_' + app_name,
            set(g.name for g in groups)
        )

        groups.add_app(app_name)
        groups.add_app(app_name)

        self.assertIn(
            'a_' + app_name,
            set(g.name for g in groups)
        )

        groups.remove_app(app_name)
        groups.remove_app(app_name)

        self.assertNotIn(
            'a_' + app_name,
            set(g.name for g in groups)
        )
