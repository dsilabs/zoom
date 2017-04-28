"""
    Test the session module

    Copyright (c) 2005-2016 Dynamic Solutions Inc. (support@dynamic-solutions.com)

    This file is part of DataZoomer.
"""

import os
import unittest
import time
import logging
import datetime

from zoom.request import Request
from zoom.session import Session
from zoom.site import Site
from zoom.database import setup_test

logger = logging.getLogger(__name__)

class TestRequest(unittest.TestCase):

    def setUp(self):
        env = {}
        self.request = Request(env)
        self.request.site = Site(self.request)
        self.request.site.db = setup_test()

    def tearDown(self):
        self.request.site.db.close()

    def test_session(self):
        db = self.request.site.db

        session = Session(self.request)

        #Create new session
        # id = session.new(db)
        id = session._token
        logger.debug('created session %r', id)
        # logger.debug('session._token is %r', session._token)
        self.assert_(id!='Session error')
        session.MyName = 'Test'
        session.Message = 'This is a test session'
        session.Number = 123

        session.save(db)
        try:
            cmd = 'select * from sessions where id=%s'
            q = db(cmd, id)
            self.assertEqual(len(list(q)), 1)

            # Create new session object
            session2 = Session(self.request)

            # Load previously created session
            self.request.session_token = id
            session2.load(db, id)
            self.assertEqual(session2.Number,123)
            self.assertEqual(session2.MyName,'Test')
            self.assertEqual(session2.Message,'This is a test session')

        finally:
            session.destroy()

            logger.debug('attempting to destroy session %r', id)
            cmd = 'select * from sessions where id=%s'
            q = db(cmd, id)
            self.assertEqual(len(list(q)), 0)
