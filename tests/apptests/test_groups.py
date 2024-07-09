"""
    test groups
"""

import zoom
from zoom.models import Group
from zoom.testing.apptest import AppTestCase

TEST_GROUPS = [
    ('testgroup1', 'U', 1),
    ('testgroup2', 'U', 1),
    ('testgroup3', 'U', 1),
    ('testgroup4', 'U', 1),
    ('testgroup5', 'U', 1),
    ('testgroup6', 'U', 1),
    ('testgroup7', 'U', 1),
]

class TestData(AppTestCase):

    def setup_data(self):
        self.teardown_data()
        site = zoom.get_site()
        for group in TEST_GROUPS:
            name, _type, admin_id = group
            site.groups.put(
                Group(name=name, type=_type, admin_group_id=admin_id)
            )

        groups = zoom.get_site().groups

        def add_subgroups(group_name, subgroup_names):
            for subgroup_name in subgroup_names:
                groups.first(name=group_name).add_subgroup(
                    groups.first(name=subgroup_name))

        add_subgroups('testgroup1', ['testgroup2', 'testgroup3'])
        add_subgroups('testgroup2', ['testgroup4', 'testgroup5'])
        add_subgroups('testgroup4', ['testgroup7'])
        add_subgroups('testgroup5', ['testgroup6'])

    def teardown_data(self):

        groups = zoom.get_site().groups
        for group in TEST_GROUPS:
            name = group[0]
            groups.delete(name=name)

        zoom.get_db()("""
            DELETE FROM subgroups
            WHERE group_id NOT IN (SELECT id FROM `groups`)
            OR subgroup_id NOT IN (SELECT id FROM `groups`)
        """)

    def setUp(self):
        super().setUp()
        self.setup_data()

    def tearDown(self):
        self.teardown_data()
        super().tearDown()


class TestGroup(TestData):

    def test_get_subgroup_ids_1(self):

        groups = zoom.get_site().groups
        testgroup1 = groups.first(name='testgroup1')

        subgroup_ids = set()
        for group in TEST_GROUPS[1:]:
            name = group[0]
            if name in ['testgroup2', 'testgroup3', 'testgroup4',
                        'testgroup5', 'testgroup6', 'testgroup7']:
                subgroup_ids.add(groups.first(name=name).group_id)

        result_ids = testgroup1.get_subgroup_ids()
        self.assertEqual(result_ids, subgroup_ids)

    def test_get_subgroup_ids_2(self):

        groups = zoom.get_site().groups
        testgroup5 = groups.first(name='testgroup5')

        subgroup_ids = set()
        for group in TEST_GROUPS[1:]:
            name = group[0]
            if name in ['testgroup6']:
                subgroup_ids.add(groups.first(name=name).group_id)

        result_ids = testgroup5.get_subgroup_ids()
        self.assertEqual(result_ids, subgroup_ids)

    def test_get_supergroup_ids(self):

        groups = zoom.get_site().groups
        testgroup = groups.first(name='testgroup6')

        supergroup_ids = set(
            groups.first(name=f'testgroup{n}').group_id
            for n in [5, 2, 1]
        )

        result_ids = testgroup.get_supergroup_ids(max_depth=10)
        self.assertEqual(result_ids, supergroup_ids)

    def test_get_supergroup_with_depth_specified(self):

        groups = zoom.get_site().groups
        testgroup = groups.first(name='testgroup6')

        supergroup_ids = set(
            groups.first(name=f'testgroup{n}').group_id
            for n in [5, 2]
        )

        result_ids = testgroup.get_supergroup_ids(max_depth=2)
        self.assertEqual(result_ids, supergroup_ids)
