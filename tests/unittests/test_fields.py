# -*- coding: utf-8 -*-

"""
    test the fields module
"""

import unittest
import logging

from zoom.fields import *
from zoom.tools import unisafe

logger = logging.getLogger('zoom.fields')


class TextTests(object):

    def setUp(self, field_type):
        self.field_type = field_type
        self.show_css_class = self.css_class = self.field_type.css_class
        self.basic_text = 'test text'
        self.encoded_text = 'A “special character” & quote test.'
        self.edit_template = '{widget}'
        self.display_template = '{text}'

    def compare(self, expected, got):
        def strify(text):
            if type(text) is str:
                return text.encode('utf8')
            return text
        logger.debug('expected:\n%s\n', strify(expected))
        logger.debug('.....got:\n%s\n', strify(got))
        self.assertEqual(strify(expected), strify(got))

    def test_widget(self):
        f = self.field_type('Field1')
        f.initialize({'field1': self.basic_text})
        t = self.widget_template.format(self=self, text=self.basic_text)
        self.compare(t, f.widget())

    def test_widget_with_unicode(self):
        f = self.field_type('Field1')
        f.initialize({'field1': self.encoded_text})
        t = self.widget_template.format(self=self, text=htmlquote(self.encoded_text))
        self.compare(t, f.widget())

    def test_display_value(self):
        f = self.field_type('Field1')
        f.initialize({'field1': self.basic_text})
        t = self.display_template.format(self=self, text=self.basic_text)
        self.compare(t, f.display_value())

    def test_display_value_with_unicode(self):
        f = self.field_type('Field1')
        f.initialize({'field1': self.encoded_text})
        t = self.display_template.format(self=self, text=htmlquote(self.encoded_text))
        self.compare(t, f.display_value())


class TestField(unittest.TestCase):

    def test_initialize(self):
        f = zoom.fields.Field('Test')
        f.initialize({'test': 'one'})
        self.assertEqual(f.value, 'one')
        self.assertEqual(f.display_value(), 'one')
        f.initialize()
        self.assertEqual(f.value, 'one')
        self.assertEqual(f.widget(), 'one')


class TestMarkdownText(unittest.TestCase):

    def test_evaluate(self):
        f = zoom.fields.MarkdownText('Test')
        self.assertEqual(f.evaluate(), {})


class TestMemoField(unittest.TestCase, TextTests):

    def setUp(self, *a, **k):
        TextTests.setUp(self, MemoField)
        self.show_css_class = 'textarea'
        self.widget_template = (
            '<textarea class="{self.css_class}" cols="60" id="field1" '
            'name="field1" rows="6" size="10">{text}</textarea>'
        )

    def test_nohint(self):
        f = zoom.fields.MemoField('Notes', value='some notes')
        self.assertTrue('some notes' in f.edit())

class TestMarkdownField(unittest.TestCase, TextTests):

    def setUp(self, *a, **k):
        TextTests.setUp(self, MarkdownField)
        self.show_css_class = 'textarea'
        self.display_template = '<p>{text}</p>'
        self.widget_template = (
            '<textarea class="{self.css_class}" cols="60" id="field1" '
            'name="field1" rows="6" '
            'size="10">{text}</textarea>'
        )
        self.widget_template = (
            '<textarea class="{self.css_class}" cols="60" id="field1" '
            'name="field1" rows="6" size="10">{text}</textarea>'
        )


class TestEditField(unittest.TestCase, TextTests):

    def setUp(self, *a, **k):
        TextTests.setUp(self, EditField)
        self.show_css_class = 'textarea'
        self.widget_template = (
            '<textarea class="{self.css_class}" height="6" '
            'id="field1" name="field1" size="10">{text}</textarea>'
        )

    def test_edit_value(self):
        f = zoom.fields.EditField('memo')
        f.initialize({'memo': 'test data'})
        assert 'test data' in f.edit()

class TestTextField(unittest.TestCase, TextTests):

    def setUp(self, *a, **k):
        TextTests.setUp(self, TextField)
        self.widget_template = (
            '<input class="{self.css_class}" id="field1" '
            'maxlength="40" name="field1" size="40" '
            'type="text" value="{text}" />'
        )

    def test_non_text_value(self):
        f = zoom.fields.TextField('Age')
        f.value = 20
        self.assertEqual(f.widget(), (
            '<input class="text_field" id="age" '
            'maxlength="40" name="age" size="40" '
            'type="text" value="20" />'
            )
        )




class DateTests(object):

    def setUp(self, field_type):
        self.field_type = field_type
        self.css_class = self.field_type.css_class
        self.basic_text = 'Aug 20, 2017'
        self.alt_text = '2017-08-20'
        self.widget_template = (
            '<input class="{self.css_class}" type="text" '
            'id="field1" maxlength="12" name="field1" '
            'value="{text}" />'
        )
        self.display_template = '{text}'

    def compare(self, expected, got):
        def strify(text):
            if type(text) is str:
                return text.encode('utf8')
            return text
        logger.debug('expected:\n%s\n', strify(expected))
        logger.debug('.....got:\n%s\n', strify(got))
        self.assertEqual(strify(expected), strify(got))

    def test_widget(self):
        f = self.field_type('Field1')
        f.initialize({'field1': self.basic_text})
        t = self.widget_template.format(self=self, text=self.basic_text)
        self.compare(t, f.widget())

    def test_display_value(self):
        f = self.field_type('Field1')
        f.initialize({'field1': self.basic_text})
        t = self.display_template.format(self=self, text=self.basic_text)
        self.compare(t, f.display_value())

    def test_evaluate(self):
        f = self.field_type('Field1')
        f.initialize({'field1': self.basic_text})
        self.assertEqual(f.evaluate(), {'field1': datetime.date(2017, 8, 20)})


class TestDateField(unittest.TestCase, DateTests):

    def setUp(self, *a, **k):
        DateTests.setUp(self, DateField)


class TestFields(unittest.TestCase):

    def setUp(self):
        self.fields = Fields(
            TextField('Name'),
            DecimalField('Height', units='cm', default=''),
            DateField('Birthdate'),
        )

    def test_evaluate_empty(self):
        self.assertEqual(
            self.fields.evaluate(),
            {'name': '', 'height': 0, 'birthdate': None}
        )

    def test_evaluate_initialized(self):
        self.fields.initialize(
            {
                'name': 'Joe',
                'height': Decimal('220'),
                'birthdate': 'Aug 20, 2017',
                'extra_field': 2
            }
        )
        self.assertEqual(
            self.fields.evaluate(),
            {
                'name': 'Joe',
                'height': Decimal('220'),
                'birthdate': datetime.date(2017, 8, 20),
            }
        )
        self.fields.initialize() # should have no effect
        self.assertEqual(
            self.fields.evaluate(),
            {
                'name': 'Joe',
                'height': Decimal('220'),
                'birthdate': datetime.date(2017, 8, 20),
            }
        )

    def test_evaluate_update(self):
        self.fields.initialize(
            {
                'name': 'Joe',
                'height': Decimal('220'),
                'birthdate': 'Aug 20, 2017',
                'extra_field': 2
            }
        )
        self.assertEqual(
            self.fields.evaluate(),
            {
                'name': 'Joe',
                'height': Decimal('220'),
                'birthdate': datetime.date(2017, 8, 20),
            }
        )
        self.fields.update() # should have no effect
        self.assertEqual(
            self.fields.evaluate(),
            {
                'name': 'Joe',
                'height': Decimal('220'),
                'birthdate': datetime.date(2017, 8, 20),
            }
        )

    def test_as_list(self):
        f1, f2, f3 = (
            TextField('Name'),
            DecimalField('Height', units='cm', default=''),
            DateField('Birthdate'),
        )
        fields = Fields(f1, f2, f3)

        self.assertEqual(
            fields.as_list(),
            [f1, f2, f3]
        )