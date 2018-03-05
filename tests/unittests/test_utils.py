"""
    test utils
"""

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# It's reasonable in this case.

import unittest

import zoom


class TestUtils(unittest.TestCase):
    """test the fill function"""

    def test_storage_delattr(self):
        o = zoom.utils.Storage(a=1)
        self.assertRaises(AttributeError, o.__delattr__, 'b')

