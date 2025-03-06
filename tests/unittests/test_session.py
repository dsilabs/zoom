"""
    Test the session module

    Copyright (c) 2005-2016 Dynamic Solutions Inc. (support@dynamic-solutions.com)

    This file is part of DataZoomer.
"""
# pylint: disable=missing-docstring

import unittest
import logging

from zoom.request import Request
from zoom.session import Session
from zoom.sites import Site
from zoom.database import setup_test


class TestRequest(unittest.TestCase):

    def setUp(self):
        env = {}
        self.request = Request(env)
        setup_test()
        self.request.site = Site()

    def tearDown(self):
        self.request.site.db.close()

    def test_session(self):
        logger = logging.getLogger(__name__)

        db = self.request.site.db

        # create session and and store some values
        session = Session(self.request)
        token = session.token
        logger.debug('created session %r', token)
        self.assertNotEqual(token, 'Session error')
        session.MyName = 'Test'
        session.Message = 'This is a test session'
        session.Number = 123

        session.save(db)
        try:
            cmd = 'select * from sessions where id=%s'
            q = db(cmd, token)
            self.assertEqual(len(list(q)), 1)

            # Create new session object
            session2 = Session(self.request)

            # Load previously created session
            self.request.session_token = token
            session2.load(db, token)
            self.assertEqual(session2.Number, 123)
            self.assertEqual(session2.MyName, 'Test')
            self.assertEqual(session2.Message, 'This is a test session')

        finally:
            session.destroy()

            logger.debug('attempting to destroy session %r', token)
            cmd = 'select * from sessions where id=%s'
            q = db(cmd, token)
            self.assertEqual(len(list(q)), 0)

    def test_unicode_value(self):
        logger = logging.getLogger(__name__)

        db = self.request.site.db

        # create session and and store a unicode value
        session = Session(self.request)
        token = session.token
        logger.debug('created session %r', token)
        self.assertNotEqual(token, 'Session error')
        session.content = 'こんにちは'
        session.save(db)

        try:
            cmd = 'select * from sessions where id=%s'
            q = db(cmd, token)
            self.assertEqual(len(list(q)), 1)

            # Create new session object
            session2 = Session(self.request)

            # Load previously created session
            self.request.session_token = token
            session2.load(db, token)
            self.assertEqual(session2.content, 'こんにちは')

        finally:
            session.destroy()

            logger.debug('attempting to destroy session %r', token)
            cmd = 'select * from sessions where id=%s'
            q = db(cmd, token)
            self.assertEqual(len(list(q)), 0)

