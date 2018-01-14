"""
    test_audit.py

    Test the audit module.
"""

import unittest

import zoom
from zoom.audit import audit

class TestAudit(unittest.TestCase):

    def setUp(self):
        bunch = zoom.utils.Bunch
        zoom.system.site = bunch(url='/')
        zoom.system.request = bunch(app=bunch(name='myapp'))
        self.db = zoom.system.site.db = zoom.database.setup_test()
        self.users = zoom.users.Users(self.db)
        zoom.system.user = self.users.first(username='user')

    def test_audit_with_user(self):
        result = self.db('select * from audit_log')
        self.assertEqual(len(result), 0)
        user = self.users.first(username='admin')
        audit('grant access', 'user1', 'user2', user)
        result = self.db('select * from audit_log')
        self.assertEqual(len(result), 1)
        data = list(result)[0][:-1]
        goal = (1, 'myapp', 1, 'grant access', 'user1', 'user2')
        self.assertEqual(data, goal)

    def test_audit_current_user(self):
        result = self.db('select * from audit_log')
        self.assertEqual(len(result), 0)
        audit('grant access', 'user1', 'user2')
        result = self.db('select * from audit_log')
        self.assertEqual(len(result), 1)
        data = list(result)[0][:-1]
        goal = (1, 'myapp', 2, 'grant access', 'user1', 'user2')
        self.assertEqual(data, goal)
