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


class TestIDFor(unittest.TestCase):

    def test_id_for_simple_strings(self):
        self.assertEqual(zoom.utils.id_for('Simple Test'), 'simple-test')
        self.assertEqual(zoom.utils.id_for('Another_Test'), 'another_test')

    def test_id_for_special_characters(self):
        self.assertEqual(zoom.utils.id_for('Test&*(@!#'), 'test')
        self.assertEqual(zoom.utils.id_for('Look at this: 100%'), 'look-at-this-100')

    def test_id_for_numerical_inputs(self):
        self.assertEqual(zoom.utils.id_for(1234), '1234')
        self.assertEqual(zoom.utils.id_for('1234'), '1234')

    def test_id_for_mixed_inputs(self):
        self.assertEqual(zoom.utils.id_for('Hi 123', 'bye 456'), 'hi-123~bye-456')
        self.assertEqual(zoom.utils.id_for('Spaces and_special chars'), 'spaces-and_special-chars')

    def test_id_for_empty_string(self):
        self.assertEqual(zoom.utils.id_for(''), '')

    def test_id_for_multiple_same_inputs(self):
        self.assertEqual(zoom.utils.id_for('test', 'test'), 'test~test')

    def test_id_for_non_string_non_integer_inputs(self):
        self.assertEqual(zoom.utils.id_for(True), 'true')
        self.assertEqual(zoom.utils.id_for(None), 'none')

    def test_id_for_consecutive_special_characters(self):
        self.assertEqual(zoom.utils.id_for('test&&&&&&'), 'test')

    def test_id_for_case_sensitivity(self):
        self.assertEqual(zoom.utils.id_for('TEST'), 'test')
        self.assertEqual(zoom.utils.id_for('Test'), 'test')

    def test_id_for_empty_string(self):
        self.assertEqual(zoom.utils.id_for(''), '')

    def test_id_for_large_input(self):
        self.assertEqual(zoom.utils.id_for('a'*1000), 'a'*1000)


class TestNameFor(unittest.TestCase):

    def test_name_for_simple_strings(self):
        self.assertEqual(zoom.utils.name_for('Simple Test'), 'simple_test')
        self.assertEqual(zoom.utils.name_for('Another-Test'), 'another_test')

    def test_name_for_special_characters(self):
        self.assertEqual(zoom.utils.name_for('Test&*(@!#'), 'test')
        self.assertEqual(zoom.utils.name_for('Look at this: 100%'), 'look_at_this_100')

    def test_name_for_numerical_inputs(self):
        self.assertEqual(zoom.utils.name_for(1234), '1234')
        self.assertEqual(zoom.utils.name_for('1234'), '1234')

    def test_name_for_mixed_inputs(self):
        self.assertEqual(zoom.utils.name_for('Hi 123 bye 456'), 'hi_123_bye_456')
        self.assertEqual(zoom.utils.name_for('Spaces and-special chars'), 'spaces_and_special_chars')

    def test_name_for_empty_string(self):
        self.assertEqual(zoom.utils.name_for(''), '')

    def test_name_for_multiple_same_inputs(self):
        self.assertEqual(zoom.utils.name_for('test test'), 'test_test')

    def test_name_for_non_string_non_integer_inputs(self):
        self.assertEqual(zoom.utils.name_for(True), 'true')
        self.assertEqual(zoom.utils.name_for(None), 'none')

    def test_name_for_consecutive_special_characters(self):
        self.assertEqual(zoom.utils.name_for('test&&&&&'), 'test')

    def test_name_for_case_sensitivity(self):
        self.assertEqual(zoom.utils.name_for('TEST'), 'test')
        self.assertEqual(zoom.utils.name_for('Test'), 'test')

    def test_name_for_large_input(self):
        self.assertEqual(zoom.utils.name_for('a'*1000), 'a'*1000)


class TestTrim(unittest.TestCase):

    def test_trim_normal_strings(self):
        self.assertEqual(zoom.utils.trim('   no leading space'), 'no leading space')
        self.assertEqual(zoom.utils.trim('trailing space    '), 'trailing space')
        self.assertEqual(zoom.utils.trim('   no trailing space    '), 'no trailing space')

    def test_trim_block_of_text(self):
        text = '   line 1\n     line 2\n  line 3\n     line 4'
        result = ' line 1\n   line 2\nline 3\n   line 4'
        self.assertEqual(zoom.utils.trim(text), result)

    def test_trim_block_with_empty_lines(self):
        text = '   \n   line 1\n   line 2\n   \n'
        result = '\nline 1\nline 2\n'
        self.assertEqual(zoom.utils.trim(text), result)

    def test_trim_block_without_change(self):
        text = 'line 1\nline 2'
        self.assertEqual(zoom.utils.trim(text), text)

    def test_trim_empty_string(self):
        self.assertEqual(zoom.utils.trim(''), '')
