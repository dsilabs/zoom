# -*- coding: utf-8 -*-

"""
    Test the jsonz module
"""

import unittest
import datetime
from decimal import Decimal

from zoom.jsonz import loads, dumps

class TestConvert(unittest.TestCase):

    def test_string(self):
        t = 'This is a test'
        tj = dumps(t)
        t2 = loads(tj)
        self.assertEqual(t, t2)

    def test_datetime(self):
        d = datetime.datetime.now()
        dj = dumps(d)
        d2 = loads(dj)
        self.assertEqual(d, d2)

    def test_date(self):
        d = datetime.date.today()
        dj = dumps(d)
        d2 = loads(dj)
        self.assertEqual(d, d2)

    def test_float(self):
        d = [22.32, '22.32']
        dj = dumps(d)
        d2 = loads(dj)
        self.assertEqual(d, d2)

    def test_decimal(self):
        d = [Decimal('22.32'), Decimal(22.32)]
        dj = dumps(d)
        d2 = loads(dj)
        self.assertEqual(d, d2)

    def test_obj(self):
        """test object literal decode - pass/fallthrough of object_hook of loads"""
        d = [Decimal('22.32'), dict(status='this is a test')]
        dj = dumps(d)
        d2 = loads(dj)
        self.assertListEqual(d, d2)

    def test_error(self):
        d = [Decimal('22.32'), self]
        self.assertRaises(TypeError, dumps, d)
