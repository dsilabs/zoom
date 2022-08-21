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

    def test_getitem(self):

        car = zoom.Record(
            name='Car',
            model='Mini',
            brand='Austin',
            engine=zoom.Record(
                size=850,
                cylenders=4,
            )
        )

        self.assertEqual(car.engine.size, 850)

    def test_subrecord(self):

        class Car(zoom.Record):

            @property
            def cylender_size(self):
                return self.engine.size / self.engine.cylenders

            def start(self):
                return 'vrrooom'

        class Engine(zoom.Record):
            pass

        car = Car(
            name='Car',
            model='Mini',
            brand='Austin',
            engine=Engine(
                size=850,
                cylenders=4,
            )
        )

        self.assertEqual(car.name, 'Car')
        self.assertEqual(car.cylender_size, 212.5)
        self.assertEqual(car.start(), 'vrrooom')
