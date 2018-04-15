# -*- coding: utf-8 -*-

"""
    test the fields module
"""

import unittest
import logging

from zoom.fields import *
from zoom.tools import unisafe
import zoom.validators as v

logger = logging.getLogger('zoom.fields')


class TextTests(object):
    # pylint: disable=E1101

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


class TestButton(unittest.TestCase):

    def test_display_value(self):
        f = zoom.fields.Button('Save')
        self.assertEqual(f.display_value(), '')

    def test_as_searchable(self):
        f = zoom.fields.Button('Save')
        self.assertEqual(f.as_searchable(), set())


class TestMarkdownText(unittest.TestCase):

    def test_evaluate(self):
        f = zoom.fields.MarkdownText('Test')
        self.assertEqual(f.evaluate(), {})


class TestMarkdownEditField(unittest.TestCase):

    def test_evaluate(self):
        content = """
        Heading
        ====
        Paragraph text.
        """
        f = zoom.fields.MarkdownEditField('Test', value=content)
        self.assertEqual(
            f.display_value(),
            '<h1 id="heading">Heading</h1>\n<p>Paragraph text.</p>'
        )


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

class TestEmailField(unittest.TestCase, TextTests):

    def setUp(self, *a, **k):
        TextTests.setUp(self, MemoField)
        self.show_css_class = 'textarea'
        self.widget_template = (
            '<textarea class="{self.css_class}" cols="60" id="field1" '
            'name="field1" rows="6" size="10">{text}</textarea>'
        )

    def test_antispam(self):
        f = zoom.fields.EmailField('Notes', value='a@b.com')
        self.assertEqual(
            f.display_value(),
            '<a href="&#109;&#97;&#105;&#108;&#116;&#111;&#58;&#97;&#64;&#98;&#46;&#99;&#111;&#109;">&#97;&#64;&#98;&#46;&#99;&#111;&#109;</a>'
        )

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

    def test_as_list_nested(self):
        f1, f2, f3, f4, f5 = (
            TextField('Name'),
            DecimalField('Height', units='cm', default=''),
            DateField('Birthdate'),
            NumberField('Latitude', value=10),
            NumberField('Longitude', value=20)
        )
        fields = Fields(f1, f2, f3, Fields(f4, f5))
        for f in fields.as_list():
            print(f)

        self.assertEqual(
            fields.as_list(),
            [f1, f2, f3, f4, f5]
        )

    def test_clean(self):
        to_upper = zoom.validators.Cleaner(str.upper)
        f1, f2, f3 = (
            TextField('Name', to_upper),
            DecimalField('Height', units='cm', default=''),
            DateField('Birthdate'),
        )
        fields = Fields(f1, f2, f3)
        fields.initialize(name='joe')
        fields.clean()
        self.assertEqual(
            fields.evaluate(),
            {'birthdate': None, 'height': None, 'name': 'JOE'}
        )


class TestFieldSet(TestFields):
    def setUp(self):
        self.fields = zoom.fields.Fieldset('Section 1', [
            TextField('Name'),
            DecimalField('Height', units='cm', default=''),
            DateField('Birthdate'),
        ])

    def test_hint(self):
        self.assertEqual(self.fields.render_hint(), '')
        self.fields.hint = 'here is a hint'
        self.assertEqual(
            self.fields.render_hint(),
            '<span class="hint">here is a hint</span>'
            )

    def test_show(self):
        print(self.fields.show())
        assert '<fieldset>' not in self.fields.show()

        self.fields.initialize(
            {
                'name': 'Joe',
                'height': Decimal('220'),
                'birthdate': 'Aug 20, 2017',
                'extra_field': 2
            }
        )
        print(self.fields.show())
        assert '<fieldset>' in self.fields.show()

    def test_edit(self):
        assert '<fieldset>' in self.fields.edit()

class TestBasicImageField(unittest.TestCase):
    def setUp(self):
        self.field = BasicImageField('Photo', hint='click to select')

    def test_hint(self):
        self.assertIn('click to select', self.field.edit())

    def test_edit(self):
        target = '<input class="image-field" id="photo" name="photo" type="file" />'
        self.assertIn(target, self.field.edit())

    def test_display_value(self):
        self.field.initialize({'photo': b'fake image'})
        self.assertIn('<img', self.field.display_value())

    def test_assign_object(self):
        field = self.field
        fake_image = zoom.utils.Bunch(value=b'fake image')
        field.assign(fake_image)
        self.assertEqual(b'fake image', field.value)
        self.assertEqual({'photo': b'fake image'}, field.evaluate())

    def test_assign_value(self):
        field = self.field
        field.assign(b'fake image')
        self.assertEqual(b'fake image', field.value)
        self.assertEqual({'photo': b'fake image'}, field.evaluate())

    def test_initialize(self):
        person = zoom.utils.Record(name='Joe', photo=b'fake photo', url='/people/joe')
        self.field._initialize(person)
        self.assertEqual(b'fake photo', self.field.value)
        self.assertIn('alt="Joe"', self.field.display_value())
        self.assertEqual({'photo': b'fake photo'}, self.field.evaluate())

        person = zoom.utils.Record(title='DSI', photo=b'fake photo', url='/company/dsi')
        self.field._initialize(person)
        self.assertEqual(b'fake photo', self.field.value)
        self.assertIn('alt="Photo"', self.field.display_value())
        self.assertEqual({'photo': b'fake photo'}, self.field.evaluate())

    def test_alt_override(self):
        person = zoom.utils.Record(title='DSI', photo=b'fake photo', url='/company/dsi')
        self.field._initialize(person)
        self.field.alt = 'DSI'
        self.assertEqual(b'fake photo', self.field.value)
        self.assertIn('alt="DSI"', self.field.display_value())
        self.assertEqual({'photo': b'fake photo'}, self.field.evaluate())

    def test_multipart(self):
        self.assertTrue(self.field.requires_multipart_form())

    def test_create_record_validation_fail_and_retry(self):
        # Test the case where a user specifies an
        # image in the ImageField but some other
        # field fails validation.   We want this field
        # to reset since at this point there is no
        # way for this simiple field type to save to
        # keep the image that was specified at this
        # point.  Next, the user fixes the field that failed
        # and re-specifies the image, and the validation
        # should pass.
        fields = Fields(
            TextField('Title', v.MinimumLength(10)),
            ImageField('Photo'),
            URLField('Site'),
        )
        form_data = dict(
            title='DSI',
            photo=zoom.utils.Bunch(value=b'fake photo'),
            site='http://localhost',
            url='/clients/dsi'
        )
        self.assertFalse(fields.validate(form_data))

        # The record has been rejected because
        # of the title length.  The image field has not had
        # the chance to save anything so there is nothing to
        # show.  With this simple field it's not smart enough
        # to save the image anywhere so it goes back to being
        # empty.
        self.assertEqual('minimum length 10', fields['title'].msg)
        self.assertEqual(None, fields['photo'].value)
        # self.assertEqual(b'fake photo', fields['photo'].value)
        photo = fields['photo']
        target = (
            '<input '
                'class="image-field" '
                'id="photo" '
                'name="photo" '
                'type="file" '
            '/>'
        )
        self.assertEqual(target, fields['photo'].widget())

        # The form is now re-submitted with a valid title
        # and it should pass validation, and the re-specified
        # image will be saved as well.
        form_data['title'] = 'Dynamic Solutions'
        form_data['photo'] = zoom.utils.Bunch(value=b'fake photo')
        self.assertTrue(fields.validate(form_data))
        self.assertEqual({'photo': b'fake photo'}, fields['photo'].evaluate())

    def test_create_record_validation_fail(self):
        # User is creating a new record.
        # Test the case where a user specifies an
        # image in the ImageField but some other
        # field fails validation.   We want this field
        # to reset since at this point there is no
        # way for this simiple field type to save to
        # keep the image that was specified at this
        # point.  Next, the user fixes the field that failed
        # and does not re-specify the image, and the validation
        # should pass but there is no image.
        fields = Fields(
            TextField('Title', v.MinimumLength(10)),
            ImageField('Photo'),
            URLField('Site'),
        )
        form_data = dict(
            title='DSI',
            photo=zoom.utils.Bunch(value=b'fake photo'),
            site='http://localhost',
            url='/clients/dsi'
        )
        self.assertFalse(fields.validate(form_data))

        # The record has been rejected because
        # of the title length.  The image field has not had
        # the chance to save anything so there is nothing to
        # show.  With this simple field it's not smart enough
        # to save the image anywhere so it goes back to being
        # empty.
        self.assertEqual('minimum length 10', fields['title'].msg)
        self.assertEqual(None, fields['photo'].value)
        target = (
            '<input '
                'class="image-field" '
                'id="photo" '
                'name="photo" '
                'type="file" '
            '/>'
        )
        self.assertEqual(target, fields['photo'].widget())

    def test_edit_record_validation_fail(self):
        # User is editing an existing a new record.
        # Test the case where a user specifies an
        # image in the ImageField but some other
        # field fails validation.   We want this field
        # to reset since at this point there is no
        # way for this simiple field type to save to
        # keep the image that was specified at this
        # point.  Next, the user fixes the field that failed
        # and does not re-specify the image, and the validation
        # should pass but there is no image.
        fields = Fields(
            TextField('Title', v.MinimumLength(10)),
            ImageField('Photo'),
            URLField('Site'),
        )
        client = zoom.utils.Record(
            title='Old Company Name',
            photo=b'old photo',
            site='http://localhost',
            url='/clients/dsi'
        )
        fields.initialize(client)
        self.assertTrue(fields.valid())

        form_data = dict(
            title='DSI',
            photo=b'new photo',
            site='http://localhost',
            url='/clients/dsi'
        )
        self.assertFalse(fields.validate(form_data))

        # The record has been rejected because
        # of the title length.  The image field has not had
        # the chance to save anything so there is nothing to
        # show.  With this simple field it's not smart enough
        # to save the image anywhere so it goes back to being
        # empty.
        self.assertEqual('minimum length 10', fields['title'].msg)
        self.assertEqual(b'old photo', fields['photo'].value)
        target = (
            '<input '
                'class="image-field" '
                'id="photo" '
                'name="photo" '
                'type="file" '
            '/>'
            '<div class="image-field-delete-link">'
                '<a href="delete-image?name=photo">delete photo</a>'
            '</div>'
            '<img '
                'alt="Photo" '
                'class="image-field-image" '
                'src="/clients/dsi/image?name=photo" '
            '/>'
        )
        self.assertEqual(target, fields['photo'].widget())


def trim(text):
    return '\n'.join(filter(bool, (line.strip() for line in text.splitlines())))

class TestMultiselectField(unittest.TestCase):

    field_type = MultiselectField

    def test_multiselect_basic(self):
        user_options = ['Pat', 'Terry', 'Sam']
        f = self.field_type('Users', options=user_options)
        self.assertEqual(f.display_value(), '')

        t = trim("""
        <select multiple="multiple" class="multiselect" name="users" id="users">
        <option value="Pat">Pat</option>
        <option value="Terry">Terry</option>
        <option value="Sam">Sam</option>
        </select>
        """)
        self.assertEqual(str(f.widget()), t)

        f.validate(**dict(users='Pat'))
        self.assertEqual(f.display_value(), 'Pat')

        f.validate(**dict(users=['Pat', 'Terry']))
        self.assertEqual(f.display_value(), 'Pat; Terry')

        f.validate(**dict())
        self.assertEqual(f.display_value(), '')

    def test_multiselect_numeric_codes(self):
        membership_options = [
            ('admins', 1),
            ('users', 2),
            ('guests', 3),
        ]
        f = self.field_type('Memberships', options=membership_options)
        self.assertEqual(f.evaluate(), {'memberships': []})
        self.assertEqual(f.display_value(), '')

        f.initialize({'memberships': 1})
        self.assertEqual(f.evaluate(), {'memberships': [1]})
        self.assertEqual(f.display_value(), 'admins')

        f.initialize({'memberships': [1, 2]})
        self.assertEqual(f.evaluate(), {'memberships': [1, 2]})
        self.assertEqual(f.display_value(), 'admins; users')

        f.initialize({'memberships': [2, 1]})
        self.assertEqual(f.evaluate(), {'memberships': [1, 2]})
        self.assertEqual(f.display_value(), 'admins; users')

        f.initialize({'memberships': ['2', '1']})
        self.assertEqual(f.evaluate(), {'memberships': [1, 2]})
        self.assertEqual(f.display_value(), 'admins; users')

        f.initialize({'memberships': [3, '1']})
        self.assertEqual(f.evaluate(), {'memberships': [1, 3]})
        self.assertEqual(f.display_value(), 'admins; guests')

        f = self.field_type(
            'Memberships',
            default=[2],
            options=membership_options
        )
        self.assertEqual(f.evaluate(), {'memberships': []})
        self.assertEqual(f.display_value(), '')
        self.assertEqual(str(f.widget()),
        trim(
        """
        <select multiple="multiple" class="multiselect" name="memberships" id="memberships">
        <option value="1">admins</option>
        <option value="2" selected>users</option>
        <option value="3">guests</option>
        </select>
        """
        ))

        f = self.field_type(
            'Memberships',
            default=['2'],
            options=membership_options
        )
        self.assertEqual(f.evaluate(), {'memberships': []})
        self.assertEqual(f.display_value(), '')
        self.assertEqual(str(f.widget()),
        trim(
        """
        <select multiple="multiple" class="multiselect" name="memberships" id="memberships">
        <option value="1">admins</option>
        <option value="2" selected>users</option>
        <option value="3">guests</option>
        </select>
        """
        ))


class TestChosenMultiselectField(unittest.TestCase):

    field_type = ChosenMultiselectField

    def test_multiselect_basic(self):
        user_options = ['Pat', 'Terry', 'Sam']
        f = self.field_type('Users', options=user_options)
        self.assertEqual(f.display_value(), '')

        t = trim("""
        <select data-placeholder="Select Users" multiple="multiple" class="chosen" name="users" id="users">
        <option value="Pat">Pat</option>
        <option value="Terry">Terry</option>
        <option value="Sam">Sam</option>
        </select>
        """)
        self.assertEqual(str(f.widget()), t)

        f.validate(**dict(users='Pat'))
        self.assertEqual(f.display_value(), 'Pat')

        f.validate(**dict(users=['Pat', 'Terry']))
        self.assertEqual(f.display_value(), 'Pat; Terry')

        f.validate(**dict())
        self.assertEqual(f.display_value(), '')

    def test_multiselect_numeric_codes(self):
        membership_options = [
            ('admins', 1),
            ('users', 2),
            ('guests', 3),
        ]
        f = self.field_type('Memberships', options=membership_options)
        self.assertEqual(f.evaluate(), {'memberships': []})
        self.assertEqual(f.display_value(), '')

        f.initialize({'memberships': 1})
        self.assertEqual(f.evaluate(), {'memberships': [1]})
        self.assertEqual(f.display_value(), 'admins')

        f.initialize({'memberships': [1, 2]})
        self.assertEqual(f.evaluate(), {'memberships': [1, 2]})
        self.assertEqual(f.display_value(), 'admins; users')

        f.initialize({'memberships': [2, 1]})
        self.assertEqual(f.evaluate(), {'memberships': [1, 2]})
        self.assertEqual(f.display_value(), 'admins; users')

        f.initialize({'memberships': ['2', '1']})
        self.assertEqual(f.evaluate(), {'memberships': [1, 2]})
        self.assertEqual(f.display_value(), 'admins; users')

        f.initialize({'memberships': [3, '1']})
        self.assertEqual(f.evaluate(), {'memberships': [1, 3]})
        self.assertEqual(f.display_value(), 'admins; guests')

        f = self.field_type(
            'Memberships',
            default=[2],
            options=membership_options
        )
        self.assertEqual(f.evaluate(), {'memberships': []})
        self.assertEqual(f.display_value(), '')
        self.assertEqual(str(f.widget()),
        zoom.utils.trim(
        """
<select data-placeholder="Select Memberships" multiple="multiple" class="chosen" name="memberships" id="memberships">
<option value="1">admins</option>
<option value="2" selected>users</option>
<option value="3">guests</option>
</select>
        """
        ))

        f = self.field_type(
            'Memberships',
            default=['2'],
            options=membership_options
        )
        self.assertEqual(f.evaluate(), {'memberships': []})
        self.assertEqual(f.display_value(), '')
        self.assertEqual(str(f.widget()),
        zoom.utils.trim(
        """
<select data-placeholder="Select Memberships" multiple="multiple" class="chosen" name="memberships" id="memberships">
<option value="1">admins</option>
<option value="2" selected>users</option>
<option value="3">guests</option>
</select>
        """
        ))
