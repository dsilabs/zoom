"""
    Test the validators module

"""
# pylint: disable=missing-docstring
# method names are more useful for testing

import base64
import decimal
import unittest

import zoom

from .utils import create_fieldstorage


class TestValidators(unittest.TestCase):
    """test field validators"""

    def test_cleaner(self):
        Cleaner = zoom.validators.Cleaner
        self.assertEqual(Cleaner(str.lower).clean('Test'), 'test')

        dec = Cleaner(decimal.Decimal)
        self.assertEqual(dec.clean('10'), decimal.Decimal('10'))
        self.assertEqual(dec('10'), dec.clean('10'))

    def test_latitude(self):
        valid = zoom.validators.latitude_valid
        self.assertTrue(valid(45))
        self.assertTrue(valid(''))
        self.assertFalse(valid(100))
        self.assertFalse(valid('x'))
        self.assertRaises(TypeError, valid, None)

    def test_longitude(self):
        valid = zoom.validators.longitude_valid
        self.assertTrue(valid(145))
        self.assertTrue(valid(''))
        self.assertFalse(valid(200))
        self.assertFalse(valid('x'))
        self.assertRaises(TypeError, valid, None)

    def test_mime_type(self):
        gif = base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
        valid = zoom.validators.image_mime_type_valid

        self.assertTrue(valid(gif))
        self.assertTrue(valid(create_fieldstorage('application/pdf', gif)))  # validator only looks at the data
        self.assertFalse(valid(create_fieldstorage('application/pdf', b'123')))
        self.assertFalse(valid(b'x'))
