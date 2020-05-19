"""
    test utils
"""

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# It's reasonable in this case.

import unittest

import zoom


class TestUtils(unittest.TestCase):
    """test the Storage class"""

    def test_storage_delattr(self):
        o = zoom.utils.Storage(a=1)
        self.assertRaises(AttributeError, o.__delattr__, 'b')


class TestRecord(unittest.TestCase):
    """Test the Record class"""

    def test_getitem_class_attribute(self):

        class Thing(zoom.utils.Record):
            name = 'whatsit'

        thing = Thing()

        self.assertEqual(thing.name, 'whatsit')
        self.assertEqual(thing['name'], 'whatsit')

    def test_getitem_class_property(self):

        class Thing(zoom.utils.Record):
            name = property(lambda a: 'whatsit')

        thing = Thing()

        self.assertEqual(thing.name, 'whatsit')
        self.assertEqual(thing['name'], 'whatsit')
