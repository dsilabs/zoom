# -*- coding: utf-8 -*-

"""
    zoom.Fields
"""

import locale
import logging
import os
import types
import datetime
from decimal import Decimal

import zoom
from zoom.component import component
from zoom.utils import name_for
from zoom.tools import (
    htmlquote,
    websafe,
    markdown,
    is_listy,
    ensure_listy,
    load_content,
)
import zoom.html as html
from zoom.validators import (
    valid_phone,
    valid_email,
    valid_postal_code,
    valid_url,
    valid_date,
)


def locate_view(name):
    return os.path.join(os.path.dirname(__file__), 'views', name + '.html')


def layout_field(label, content, edit=True):
    """
        Layout a field (usually as part of a form).

        >>> print(
        ...     layout_field(
        ...         'Name',
        ...         '<input type=text value="John Doe">',
        ...         True
        ...     )
        ... )
        <div class="field">
          <div class="field_label">Name</div>
          <div class="field_edit"><input type=text value="John Doe"></div>
        </div>
        <BLANKLINE>

        >>> print(layout_field('Name', 'John Doe', False))
        <div class="field">
          <div class="field_label">Name</div>
          <div class="field_show">John Doe</div>
        </div>
        <BLANKLINE>
    """
    pathname = os.path.join(os.path.dirname(__file__), 'views', 'field.html')
    mode = bool(edit) and 'edit' or 'show'
    return load_content(**locals())


def args_to_dict(values=None, **kwargs):
    """convert args to a dict

    Allows developers to pass field values to fields either
    as a dict or as a set of keyword arguments, whichever
    makes the most sense for their code.

    This is currently only used for clean() but could potentially
    be used in a number of other places in this modudle where the
    same pattern shows up.  Erring on the side of caution for now.

    >>> args_to_dict()
    {}

    >>> args_to_dict({})
    {}

    >>> args_to_dict({'name': 'Pat'})
    {'name': 'Pat'}

    >>> from zoom.utils import pp
    >>> pp(args_to_dict(**{'name': 'Pat', 'age': 10}))
    {
      "age": 10,
      "name": "Pat"
    }

    >>> try:
    ...    args_to_dict({'name': 'Pat'}, 'bad value', age=10)
    ... except TypeError as e:
    ...    expected = 'args_to_dict() takes' in str(e)
    >>> expected
    True

    """
    return values or kwargs


class Field(object):
    """Field base class
    """
    js_init = ''
    js = ''
    css = ''
    value = ''
    options = []
    label = ''
    hint = ''
    addon = ''
    default = ''
    placeholder = None
    msg = ''
    required = False
    visible = True
    validators = []
    style = ''
    wrap = ' nowrap'
    browse = True

    def __init__(self, label='', *validators, **keywords):
        self.label = label
        self.validators = list(validators) + self.validators
        self.id = self.name
        self.__dict__.update(keywords)
        if 'value' in keywords:
            self.assign(keywords['value'])

    def show(self):
        """show the field"""
        return (
            self.visible and
            (bool(self.value) or bool(self.default)) and
            layout_field(self.label, self.display_value(), edit=False) or ''
        )

    def widget(self):
        """returns the field widget"""
        return self.display_value()

    def edit(self):
        """edit the field"""
        content = load_content(
            locate_view('hint'),
            widget=self.widget(),
            hints=self.render_msg() + self.render_hint(),
            wrap=self.wrap,
        )
        return layout_field(self.label, content)

    def __getattr__(self, name):
        if name == 'name' and hasattr(self, 'label'):
            return name_for(self.label)
        raise AttributeError

    def initialize(self, *a, **k):
        """
        Initialize field value.

            Set field value according to value passed in as parameter
            or if there is not value for this field, set it to the
            default value for the field.

            >>> f = Field('test', default='zero')

            >>> f.initialize(test='one')
            >>> f.value
            'one'

            >>> r = dict(test='two')
            >>> f.initialize(r)
            >>> f.value
            'two'

            >>> r = dict(not_test='two')
            >>> f.initialize(r)
            >>> f.value
            'zero'
        """
        if a:
            values = a[0]
        elif k:
            values = k
        else:
            values = None
        if values:
            self._initialize(values)

    def _initialize(self, values):
        """initialize field"""
        self.assign(values.get(self.name.lower(), self.default))

    def update(self, **values):
        """Update field.

        >>> name_field = Field('Name', value='Sam')
        >>> name_field.value
        'Sam'
        >>> name_field.update(city='Vancouver')
        >>> name_field.value
        'Sam'
        >>> name_field.update(name='Joe')
        >>> name_field.value
        'Joe'
        >>> name_field.update(NaMe='Adam')
        >>> name_field.value
        'Adam'
        """
        for value in values:
            if value.lower() == self.name.lower():
                self.assign(values[value])

    def assign(self, value):
        """assign a value to the field"""
        self.value = value

    def evaluate(self):
        """Evaluate field value.

        Return the value of the field expressed as key value pair (dict)
        ususally to be combined with other fields in the native type where
        the value is the native data type for the field type.
        """
        return {self.name: self.value or self.default}

    def as_dict(self):
        return {self.name: self}

    def __repr__(self):
        """return a representation of the field

        >>> name_field = Field('Name', value='test')
        >>> print(name_field)
        <Field name='name' value='test'>
        """
        return '<Field name=%r value=%r>' % (self.name, self.value)

    def display_value(self):
        """Display field value.

        >>> name_field = Field('Name', default='default test')
        >>> name_field.display_value()
        'default test'

        >>> name_field = Field('Name', value='test')
        >>> name_field.display_value()
        'test'

        >>> name_field = Field('Name', value='こんにちは')
        >>> name_field.display_value()
        '\u3053\u3093\u306b\u3061\u306f'

        >>> name_field.visible = False
        >>> name_field.display_value()
        ''
        """
        return self.visible and websafe(self.value) or self.default or ''

    def as_searchable(self):
        """Return searchable parts of field

        >>> name_field = Field('Name', default='default test')
        >>> name_field.as_searchable()
        {'default test'}

        >>> name_field = Field('Name', value='test')
        >>> name_field.as_searchable()
        {'test'}

        >>> name_field = Field('Age', value=10)
        >>> name_field.as_searchable()
        {'10'}

        >>> name_field = Field('Name', value='こんにちは')
        >>> name_field.as_searchable()
        {'\u3053\u3093\u306b\u3061\u306f'}

        >>> name_field.visible = False
        >>> name_field.as_searchable()
        set()

        >>> EmailField('Email', value='test@testco.com').as_searchable()
        {'test@testco.com'}
        """
        return (
            self.visible and
            set([str(self.value) or str(self.default)],) or
            set()
        )


    def render_hint(self):
        """Render hint.

        >>> name_field = Field('Name', hint='Full name')
        >>> name_field.render_hint()
        '<span class="hint">Full name</span>'
        """
        if self.hint:
            return '<span class="hint">%s</span>' % self.hint
        else:
            return ''

    def render_msg(self):
        """Render validation error message.

        >>> from zoom.validators import required
        >>> name_field = Field('Name', required)
        >>> name_field.update(NAME='')
        >>> name_field.valid()
        False
        >>> name_field.render_msg()
        '<span class="wrong">required</span>'
        """
        if self.msg:
            return '<span class="wrong">%s</span>' % self.msg
        else:
            return ''

    def valid(self):
        """Validate field value.

        >>> from zoom.validators import required
        >>> name_field = Field('Name',required)
        >>> name_field.update(NAME='Fred')
        >>> name_field.valid()
        True

        >>> name_field.update(NAME='')
        >>> name_field.valid()
        False
        >>> name_field.msg
        'required'
        """
        for v in self.validators:
            if not v.valid(self.value):
                self.msg = v.msg
                return False
        return True

    def validate(self, *a, **k):
        """Update and validate a field.

        >>> from zoom.validators import required
        >>> name_field = Field('Name',required)
        >>> name_field.validate(city='Vancouver')
        False

        >>> name_field.validate(name='Fred')
        True
        >>> name_field.value
        'Fred'
        """
        self.update(*a, **k)
        return self.valid()

    def clean(self, *args, **kwargs):
        """Update (sometimes ammended values) and validate a field.

        >>> from zoom.validators import Cleaner, required
        >>> upper = Cleaner(str.upper)
        >>> name_field = Field('Name', upper, required)
        >>> name_field.clean(city='Vancouver')
        False

        >>> name_field.validate(name='Vancouver')
        True
        >>> name_field.value
        'Vancouver'

        >>> name_field.clean(name='Vancouver')
        True
        >>> name_field.value
        'VANCOUVER'
        """
        self.update(**args_to_dict(*args, **kwargs))
        value = self.value
        for validator in self.validators:
            value = validator.clean(value)
            if not validator.valid(value):
                self.msg = validator.msg
                return False
        self.assign(value)
        return True

    def requires_multipart_form(self):
        """return True if a multipart form is required for this field
        """
        return False


class MarkdownText(object):
    """a markdown text object that can be placed in a form like a field

    >>> f = MarkdownText('One **bold** statement')
    >>> f.edit()
    '<p>One <strong>bold</strong> statement</p>'
    """
    def __init__(self, text):
        self.value = text

    def edit(self):
        """display the markdown as text, even in edit mode
        """
        return markdown('%s\n' % self.value)

    def evaluate(self):
        """return the value

        Not a field so doesn't return a value
        """
        return {}


class TextField(Field):
    """Text Field

    >>> print(TextField('Name', value="John Doe").show())
    <div class="field">
      <div class="field_label">Name</div>
      <div class="field_show">John Doe</div>
    </div>
    <BLANKLINE>

    >>> print(TextField('Name',value='John Doe').widget())
    <input class="text_field" id="name" maxlength="40" name="name" size="40" type="text" value="John Doe" />

    >>> print(TextField('Name',value="Dan").show())
    <div class="field">
      <div class="field_label">Name</div>
      <div class="field_show">Dan</div>
    </div>
    <BLANKLINE>

    >>> print(TextField('Name',default="Dan").show())
    <div class="field">
      <div class="field_label">Name</div>
      <div class="field_show">Dan</div>
    </div>
    <BLANKLINE>

    >>> TextField('Name', hint="required").widget()
    '<input class="text_field" id="name" maxlength="40" name="name" size="40" type="text" value="" />'

    >>> TextField('Name', placeholder="Jack").widget()
    '<input class="text_field" id="name" maxlength="40" name="name" placeholder="Jack" size="40" type="text" value="" />'

    >>> f = TextField('Title')
    >>> f.update(**{"TITLE": "Joe's Pool Hall"})
    >>> f.value
    "Joe's Pool Hall"
    >>> f.evaluate()
    {'title': "Joe's Pool Hall"}

    """

    size = maxlength = 40
    _type = 'text'
    css_class = 'text_field'

    def widget(self):

        value = self.value or self.default
        try:
            value = htmlquote(value)
        except AttributeError:
            value = value

        valid_attributes = (
            'id', 'size', 'maxlength',
            'placeholder', 'title'
        )

        attributes = dict(
            (k, getattr(self, k))
            for k in (list(self.__dict__.keys()) + list(self.__class__.__dict__.keys()))
            if k in valid_attributes
        )

        return html.input(
            type=self._type,
            Class=self.css_class,
            name=self.name,
            value=value,
            **attributes
        )


class Hidden(Field):
    """Hidden field.

    >>> Hidden('Hide Me').show()
    ''

    >>> Hidden('Hide Me', value='test').edit()
    '<input type="hidden" id="hide_me" name="hide_me" value="test" />'

    """
    visible = False

    def edit(self):
        return html.tag(
            'input',
            name=self.name,
            id=self.id,
            value=self.value or self.default,
            Type='hidden'
        )


class PasswordField(TextField):
    """Password Field

    >>> PasswordField('Password').show()
    ''

    >>> PasswordField('Password').widget()
    '<input class="text_field" id="password" maxlength="40" name="password" size="40" type="password" value="" />'
    """

    size = maxlength = 40
    _type = 'password'

    def show(self):
        return ''


class MemoField(Field):
    """Edit a paragraph of text.

    >>> print(MemoField('Notes').widget())
    <textarea class="memo_field" cols="60" id="notes" name="notes" rows="6" size="10"></textarea>
    """
    value = ''
    height = 6
    size = 10
    rows = 6
    cols = 60
    css_class = 'memo_field'

    def widget(self):
        return html.tag(
            'textarea',
            content=htmlquote(self.value),
            name=self.name,
            id=self.id,
            size=self.size,
            cols=self.cols,
            rows=self.rows,
            Class=self.css_class,
        )

    def edit(self):
        widget = self.widget()
        if self.hint or self.msg:
            table_start = (
                '<table class="transparent" width="100%">'
                '<tr><td width=10%>'
            )
            table_middle = '</td><td>'
            table_end = '</td></tr></table>'
            return layout_field(
                self.label,
                ''.join([
                    table_start,
                    widget,
                    table_middle,
                    self.render_msg(),
                    self.render_hint(),
                    table_end
                ])
            )
        else:
            return layout_field(self.label, widget)

    def show(self):
        return (
            self.visible and
            (bool(self.value) or bool(self.default)) and
            layout_field(
                self.label,
                html.tag('div', self.display_value(), Class='textarea'),
                edit=False
            ) or ''
        )


class MarkdownField(MemoField):
    """MarkdownField

    >>> f = MarkdownField('Notes', value='test **one** 23')
    >>> f.display_value()
    '<p>test <strong>one</strong> 23</p>'

    """
    def display_value(self):
        return markdown(self.value)


class EditField(MemoField):
    """Large textedit.

    >>> EditField('Notes').widget()
    '<textarea class="edit_field" height="6" id="notes" name="notes" size="10"></textarea>'
    """
    value = ''
    height = 6
    size = 10
    css_class = 'edit_field'

    def widget(self):
        return html.tag(
            'textarea',
            content=htmlquote(self.value),
            name=self.name,
            id=self.id,
            size=self.size,
            height=self.height,
            Class=self.css_class,
        )

    def edit(self):
        return layout_field(self.label, self.widget())


class MarkdownEditField(EditField):
    """Large markdown edit field

    >>> MarkdownEditField('Notes').widget()
    '<textarea class="edit_field" height="6" id="notes" name="notes" size="10"></textarea>'
    """
    def display_value(self):
        return markdown(self.value)


class PhoneField(TextField):
    """Phone field

    >>> PhoneField('Phone').widget()
    '<input class="text_field" id="phone" name="phone" size="20" type="text" value="" />'

    """
    size=20
    validators = [valid_phone]


class FieldIterator(object):

    def __init__(self, fields):
        self.field_list = [(n.lower(), v) for n, v in fields.evaluate().items()]
        self.current = 0
        self.high = len(self.field_list)

    def __next__(self):
        if self.current < self.high:
            self.current += 1
            return self.field_list[self.current - 1]
        else:
            raise StopIteration


class Fields(object):
    """A collection of field objects.


    >>> fields = Fields(TextField('Name'), PhoneField('Phone'))
    >>> print(fields.edit())
    <div class="field">
      <div class="field_label">Name</div>
      <div class="field_edit"><table class="transparent">
        <tr>
            <td nowrap><input class="text_field" id="name" maxlength="40" name="name" size="40" type="text" value="" /></td>
            <td>
                <div class="hint"></div>
            </td>
        </tr>
    </table>
    </div>
    </div>
    <div class="field">
      <div class="field_label">Phone</div>
      <div class="field_edit"><table class="transparent">
        <tr>
            <td nowrap><input class="text_field" id="phone" name="phone" size="20" type="text" value="" /></td>
            <td>
                <div class="hint"></div>
            </td>
        </tr>
    </table>
    </div>
    </div>
    <BLANKLINE>

    >>> from zoom.utils import pp
    >>> fields = Fields(TextField('Name', value='Amy'), PhoneField('Phone', value='2234567890'))
    >>> pp(fields.as_dict())
    {
      'name' ...........: <Field name='name' value='Amy'>
      'phone' ..........: <Field name='phone' value='2234567890'>
    }

    >>> fields = Fields(TextField('Name'), MemoField('Notes'))
    >>> fields.validate({'name': 'Test'})
    True
    >>> d = fields.evaluate()
    >>> d['name']
    'Test'

    >>> len(d['notes'])
    0
    >>> fields.validate({'notes': 'here are some notes'})
    True
    >>> d = fields.evaluate()
    >>> len(d['notes'])
    19

    >>> pp(fields.as_dict())
    {
      'name' ...........: <Field name='name' value='Test'>
      'notes' ..........: <Field name='notes' value='here are some notes'>
    }

    >>> record = dict(name='Adam', notes='no text here')
    >>> pp(record)
    {
      "name": "Adam",
      "notes": "no text here"
    }

    >>> record.update(fields)
    >>> record['name']
    'Test'
    >>> len(record['notes'])
    19

    """

    def __init__(self, *args):
        if len(args) == 1 and type(args[0]) in [list, tuple]:
            self.fields = args[0]
        else:
            self.fields = list(args)

    def show(self):
        return ''.join([field.show() for field in self.fields])

    def edit(self):
        return ''.join([field.edit() for field in self.fields])

    def as_dict(self):
        result = {}
        for field in self.fields:
            result = dict(result, **field.as_dict())
        return result

    def __getitem__(self, name):
        """access a contained field

        >>> fields = Fields(
        ...     TextField('Name', value='Amy'),
        ...     PhoneField('Phone', value='2234567890'),
        ... )
        >>> fields['name'].label
        'Name'

        >>> hint = 'xxx.xxx.xxxx'
        >>> fields = Fields(
        ...     Section('Personal', [
        ...         TextField('Name', value='Amy'),
        ...         PhoneField('Phone', value='2234567890', hint=hint),
        ...     ]),
        ... )
        >>> fields['personal'].name
        'personal'
        >>> fields['personal']['phone'].hint
        'xxx.xxx.xxxx'
        """
        lookup = {f.name.lower(): f for f in self.fields}
        return lookup[name]

    def initialize(self, *a, **k):
        """Initialize Field values

        >>> from zoom.utils import pp
        >>> fields = Fields(TextField('Name', value='Amy'), PhoneField('Phone', value='2234567890'))
        >>> fields.initialize(phone='987654321')
        >>> pp(fields.as_dict())
        {
          'name' ...........: <Field name='name' value=''>
          'phone' ..........: <Field name='phone' value='987654321'>
        }
        """
        if a:
            values = a[0]
        elif k:
            values = k
        else:
            values = None
        if values:
            for field in self.fields:
                field.initialize(values)

    def update(self,*a,**k):
        """Update Field values

        >>> from zoom.utils import pp
        >>> fields = Fields(TextField('Name', value='Amy'), PhoneField('Phone', value='2234567890'))
        >>> fields.update(phone='987654321')
        >>> pp(fields.as_dict())
        {
          'name' ...........: <Field name='name' value='Amy'>
          'phone' ..........: <Field name='phone' value='987654321'>
        }
        """
        if a:
            values = a[0]
        elif k:
            values = k
        else:
            values = None
        if values:
            for field in self.fields:
                field.update(**values)

    def display_value(self):
        """
        >>> from zoom.utils import pp
        >>> fields = Fields(TextField('Name', value='Amy'), PhoneField('Phone', value='2234567890'))
        >>> pp(fields.display_value())
        {
          "name": "Amy",
          "phone": "2234567890"
        }
        """
        result = {}
        for field in self.fields:
            if hasattr(field, 'name'):
                result = dict(result, **{field.name: field.display_value()})
            else:
                result = dict(result, **field.display_value())
        return result

    def as_searchable(self):
        """Return fields as a set of searchable items

        >>> from zoom.utils import pp
        >>> fields = Fields(
        ...     TextField('Name', value='Amy'),
        ...     PhoneField('Phone', value='2234567890'),
        ...     DateField('Birthdate', value=datetime.date(1980,1,1)),
        ...     MultiselectField(
        ...         'Type',
        ...         value=['One','dos'],
        ...         options=[('One','uno'),('Two','dos')]
        ...     )
        ... )

        >>> pp(sorted(map(str, fields.as_searchable())))
        [
          "1980-01-01 01-01-1980 Tuesday January 1 1980",
          "2234567890",
          "Amy",
          "One",
          "Two"
        ]

        """
        result = set()
        for field in self.fields:
            result |= field.as_searchable()
        return result

    def as_list(self):
        """
            >>> fields = Fields(TextField('Name', value='Amy'), PhoneField('Phone', value='2234567890'))
            >>> fields.as_list()
            [<Field name='name' value='Amy'>, <Field name='phone' value='2234567890'>]
        """
        result = []
        for field in self.fields:
            if hasattr(field, 'name'):
                result.append(field)
            else:
                result.extend(field._fields())
        return result

    def _fields(self):
        result = []
        for field in self.fields:
            if hasattr(field, 'name'):
                result.append(field)
            else:
                result.extend(field._fields())
        return result

    def evaluate(self):
        """
        >>> from zoom.utils import pp
        >>> fields = Fields(TextField('Name', value='Amy'), PhoneField('Phone', value='2234567890'))
        >>> pp(fields.evaluate())
        {
          "name": "Amy",
          "phone": "2234567890"
        }
        """
        result = {}
        for field in self.fields:
            result = dict(result,**field.evaluate())
        return result

    def __iter__(self):
        return FieldIterator(self)

    def __repr__(self):
        return '\n'.join([repr(field) for field in self.fields if field.evaluate()])

    def valid(self):
        errors = 0
        for field in self.fields:
            if not field.valid():
                errors += 1
        return not errors

    def validate(self, *a, **k):
        self.update(*a, **k)
        return self.valid()

    def clean(self, *args, **kwargs):
        errors = 0
        for field in self.fields:
            if not field.clean(*args, **kwargs):
                errors += 1
        return not errors

    def requires_multipart_form(self):
        for field in self.fields:
            if field.requires_multipart_form():
                return True


class Section(Fields):
    """A collection of field objects with an associated label.

    >>> print(Section('Personal',[TextField('Name',value='Joe')]).show())
    <h2>Personal</h2>
    <div class="field">
      <div class="field_label">Name</div>
      <div class="field_show">Joe</div>
    </div>
    <BLANKLINE>
    """

    def __init__(self, label, fields, hint=''):
        Fields.__init__(self, fields)
        self.label = label
        self.hint = hint

    @property
    def name(self):
        return self.label and name_for(self.label)

    def render_hint(self):
        if self.hint:
            return '<span class="hint">%s</span>' % self.hint
        else:
            return ''

    def show(self):
        value = Fields.show(self)
        return bool(value) and ('<h2>%s</h2>\n%s' % (self.label, value)) or ''

    def edit(self):
        return '<H2>%s</H2>%s\n%s' % (
            self.label,
            self.render_hint(),
            Fields.edit(self)
        )


class Fieldset(Fields):
    """A collection of field objects with an associated label.

    >>> print(Section('Personal',[TextField('Name',value='Joe')]).show())
    <h2>Personal</h2>
    <div class="field">
      <div class="field_label">Name</div>
      <div class="field_show">Joe</div>
    </div>
    <BLANKLINE>
    """

    def __init__(self, label, fields, hint=''):
        Fields.__init__(self, fields)
        self.label = label
        self.hint = hint

    def render_hint(self):
        if self.hint:
            return '<span class="hint">%s</span>' % self.hint
        else:
            return ''

    def show(self):
        value = Fields.show(self)
        tpl = '<fieldset><legend>%s</legend>\n%s</fieldset>'
        return (
            bool(value) and
            (tpl % (self.label, value)) or ''
        )

    def edit(self):
        tpl = '<fieldset><legend>%s</legend>%s\n%s</fieldset>'
        return tpl % (self.label, self.render_hint(), Fields.edit(self))


class Button(Field):
    """Button field.

    >>> Button('Save').show()
    ''

    >>> Button('Save').edit()
    '<input class="button" type="submit" id="save_button" name="save_button" style="" value="Save" />'

    >>> Button('Save', cancel='/app/cancel').edit()
    '<input class="button" type="submit" id="save_button" name="save_button" style="" value="Save" />&nbsp;<a href="/app/cancel">cancel</a>'
    """
    def __init__(self, caption='Save', **keywords):
        Field.__init__(self, caption+' Button', **keywords)
        self.caption = caption

    def show(self):
        return ""

    def edit(self):
        if hasattr(self, 'cancel'):
            cancel_link = '&nbsp;' + \
                html.tag('a', 'cancel', href=getattr(self, 'cancel'))
        else:
            cancel_link = ''
        return html.tag(
            'input',
            Type='submit',
            Class='button',
            name=self.name,
            style=self.style,
            id=self.id,
            value=self.caption
            ) + cancel_link

    def evaluate(self):
        return {}

    def __repr__(self):
        return ''

    def as_searchable(self):
        return set()


class Buttons(Field):
    """Buttons

    >>> Buttons(['Save','Publish','Delete']).show()
    ''

    >>> Buttons(['Save','Publish']).widget()
    '<input class="button" type="submit" id="save_button" name="save_button" value="Save" />&nbsp;<input class="button" type="submit" id="publish_button" name="publish_button" value="Publish" />'

    >>> Buttons(['Save'],cancel='/app/id').widget()
    '<input class="button" type="submit" id="save_button" name="save_button" value="Save" />&nbsp;<a href="/app/id">cancel</a>'
    """

    def __init__(self, captions=['Save'], **keywords):
        Field.__init__(self, **keywords)
        self.captions = captions

    def show(self):
        return ""

    def edit(self):
        return self.widget()

    def widget(self):
        buttons = [
            html.tag(
                'input',
                Type='submit',
                Class='button',
                name=name_for(caption + ' button'),
                id=name_for(caption + ' button'),
                value=caption
            ) for caption in self.captions
        ]
        if hasattr(self, 'cancel'):
            buttons.append(
                html.tag('a', 'cancel', href=getattr(self, 'cancel', 'cancel'))
            )
        return '&nbsp;'.join(buttons)

    def evaluate(self):
        return {}

    def as_searchable(self):
        return set()

    def __repr__(self):
        return ''


class ButtonsField(Buttons):
    """Buttons field.

    >>> ButtonsField('Save').show()
    ''

    >>> print(ButtonsField(['Save','Publish']).edit())
    <div class="field">
      <div class="field_label">&nbsp;</div>
      <div class="field_edit"><input class="button" type="submit" id="save_button" name="save_button" value="Save" />&nbsp;<input class="button" type="submit" id="publish_button" name="publish_button" value="Publish" /></div>
    </div>
    <BLANKLINE>

    """

    def edit(self):
        return layout_field('&nbsp;', self.widget())


class ButtonField(Button):
    """Button field.

    >>> ButtonField('Save').show()
    ''

    >>> print(ButtonField('Save').edit())
    <div class="field">
      <div class="field_label">&nbsp;</div>
      <div class="field_edit"><input class="button" type="submit" id="save_button" name="save_button" style="" value="Save" /></div>
    </div>
    <BLANKLINE>

    """

    def edit(self):
        return layout_field('&nbsp;', Button.edit(self))

    def evaluate(self):
        return {}

    def __repr__(self):
        return ''


class EmailField(TextField):
    """Email field

    >>> EmailField('Email').widget()
    '<input class="text_field" id="email" name="email" type="text" value="" />'
    """

    def __init__(self, label, *validators, **keywords):
        TextField.__init__(self, label, valid_email, *validators, **keywords)

    def display_value(self):
        def antispam_format(address):
            t = markdown('<%s>' % address)
            if t.startswith('<p>') and t.endswith('</p>'):
                return t[3:-4]
            return t
        address = htmlquote(self.value or self.default)
        return self.visible and address and antispam_format(address) or ''


class PostalCodeField(TextField):
    """Postal code field

    >>> PostalCodeField('Postal Code').widget()
    '<input class="text_field" id="postal_code" maxlength="7" name="postal_code" size="7" type="text" value="" />'
    """

    size = maxlength = 7

    def __init__(self, label='Postal Code', *validators, **keywords):
        TextField.__init__(self, label, valid_postal_code, *validators, **keywords)


class URLField(TextField):
    """URL Field

    >>> URLField('Website', default='www.google.com').display_value()
    '<a target="_window" href="http://www.google.com">http://www.google.com</a>'

    >>> f = URLField('Website', default='www.google.com')
    >>> f.assign('www.dsilabs.ca')
    >>> f.display_value()
    '<a target="_window" href="http://www.dsilabs.ca">http://www.dsilabs.ca</a>'

    >>> f = URLField('Website', default='www.google.com')
    >>> f.assign('http://www.dsilabs.ca')
    >>> f.display_value()
    '<a target="_window" href="http://www.dsilabs.ca">http://www.dsilabs.ca</a>'

    >>> f = URLField('Website', default='www.google.com', trim=True)
    >>> f.assign('http://www.dsilabs.ca/')
    >>> f.display_value()
    '<a target="_window" href="http://www.dsilabs.ca">www.dsilabs.ca</a>'

    >>> f = URLField('Website', default='www.google.com')
    >>> f.assign('https://www.dsilabs.ca/')
    >>> f.display_value()
    '<a target="_window" href="https://www.dsilabs.ca/">https://www.dsilabs.ca/</a>'

    >>> f = URLField('Website', default='www.google.com', trim=True)
    >>> f.assign('https://www.dsilabs.ca/')
    >>> f.display_value()
    '<a target="_window" href="https://www.dsilabs.ca">www.dsilabs.ca</a>'

    """

    size = 60
    maxlength = 120
    trim = False

    def __init__(self, label, *validators, **keywords):
        TextField.__init__(self, label, valid_url, *validators, **keywords)

    def display_value(self):
        url = text = websafe(self.value) or self.default
        if url:
            if not (url.startswith('http') or url.startswith('ftp:')):
                url = 'http://' + url
                if not self.trim:
                    text = 'http://' + text
        if self.trim and text.startswith('http://'):
            text = text[7:]
        if self.trim and text.startswith('https://'):
            text = text[8:]
        if self.trim and text.endswith('/'):
            text = text[:-1]
            url = url[:-1]
        return self.visible and url and ('<a target="_window" href="%s">%s</a>' % (url, text)) or ''

    def assign(self, value):
        self.value = value


class TwitterField(TextField):
    """Twitter field

    >>> TwitterField('Twitter').widget()
    '<input class="text_field" id="twitter" name="twitter" type="text" value="" />'

    >>> TwitterField('Twitter', value='dsilabs').display_value()
    '<a target="_window" href="http://www.twitter.com/dsilabs">@dsilabs</a>'
    """
    def display_value(self):
        twitter_id = (
            self.value or
            self.default).strip().strip('@')
        return self.visible and twitter_id and '<a target="_window" href="http://www.twitter.com/%(twitter_id)s">@%(twitter_id)s</a>' % locals() or ''


class NumberField(TextField):
    """Number Field

    >>> NumberField('Size', value=2).display_value()
    '2'

    >>> NumberField('Size').widget()
    '<input class="number_field" type="text" id="size" maxlength="10" name="size" size="10" value="" />'

    >>> n = NumberField('Size')
    >>> n.assign('2')
    >>> n.value
    2

    >>> n = NumberField('Size', units='units')
    >>> n.assign('2,123')
    >>> n.value
    2123
    >>> n.evaluate()
    {'size': 2123}
    >>> n.display_value()
    '2,123 units'

    >>> n.assign(None)
    >>> n.value == None
    True
    >>> n.display_value()
    ''

    """

    size = maxlength = 10
    css_class = 'number_field'
    units = ''
    converter = int

    def assign(self, value):
        try:
            if type(value) == str:
                value = ''.join(c for c in value if c in '0123456789.-')
            self.value = self.converter(value)
        except:
            self.value = None

    def widget(self):
        w = html.tag(
            'input',
            name=self.name,
            id=self.id,
            size=self.size,
            maxlength=self.maxlength,
            value=self.value or self.default,
            Type=self._type,
            Class=self.css_class,
        )

        if self.units:
            return """
            <div class="input-group">
              {w}
              <span class="input-group-addon">{u}</span>
            </div>
            """.format(w=w, u=self.units)
        else:
            return w

    def display_value(self):
        units = self.units and (' ' + self.units) or ''
        value = self.value and ('{:,}{}'.format(self.value, units)) or ''
        return websafe(value)

    def evaluate(self):
        return {self.name: self.value}

    def as_searchable(self):
        return set(str(self.value))


class IntegerField(TextField):
    """Integer Field

    >>> IntegerField('Count', value=2).display_value()
    '2'

    >>> IntegerField('Count').widget()
    '<input class="number_field" id="count" maxlength="10" name="count" size="10" type="text" value="" />'

    >>> n = IntegerField('Size')
    >>> n.assign('2')
    >>> n.value
    2
    >>> n.evaluate()
    {'size': 2}

    >>> n = IntegerField('Size', units='meters')
    >>> n.assign('22234')
    >>> n.value
    22234
    >>> n.display_value()
    '22,234 meters'

    >>> n.assign('')
    >>> n.evaluate()
    {'size': ''}
    """

    size = maxlength = 10
    css_class = 'number_field'
    value = 0
    units = ''

    def assign(self, value):
        try:
            self.value = int(value)
        except:
            self.value = self.default

    def display_value(self):
        units = self.units and (' ' + self.units) or ''
        value = self.value and ('{:,}{}'.format(self.value, units)) or ''
        return websafe(value)

    def as_searchable(self):
        return set(str(self.value))


class FloatField(NumberField):
    """Float Field

    >>> FloatField('Count', value=2.1).display_value()
    '2.1'

    >>> FloatField('Count').widget()
    '<input class="float_field" type="text" id="count" maxlength="10" name="count" size="10" value="" />'

    >>> n = FloatField('Size')
    >>> n.assign(2.1)
    >>> n.value
    2.1

    >>> n.assign(0)
    >>> n.value
    0.0

    >>> n.assign('0')
    >>> n.value
    0.0

    >>> n.assign('2.1')
    >>> n.value
    2.1

    >>> n.assign('')
    >>> n.evaluate()
    {'size': None}
    """

    size = maxlength = 10
    css_class = 'float_field'
    value = 0
    converter = float

    def evaluate(self):
        return {self.name: self.value}


class DecimalField(NumberField):
    """
    Decimal Field

        >>> DecimalField('Count',value="2.1").display_value()
        '2.1'

        >>> DecimalField('Count', value=Decimal('10.24')).widget()
        '<input class="decimal_field" type="text" id="count" maxlength="10" name="count" size="10" value="10.24" />'

        >>> DecimalField('Count').widget()
        '<input class="decimal_field" type="text" id="count" maxlength="10" name="count" size="10" value="" />'

        >>> n = DecimalField('Size')
        >>> n.assign('2.1')
        >>> n.value
        Decimal('2.1')

        >>> n.assign(0)
        >>> n.value
        Decimal('0')

        >>> n.assign('0')
        >>> n.value
        Decimal('0')

        >>> n.assign('2.1')
        >>> n.value
        Decimal('2.1')

        >>> n.assign('')
        >>> n.evaluate()
        {'size': None}

        >>> DecimalField('Hours').evaluate()
        {'hours': 0}
    """

    size = maxlength = 10
    css_class = 'decimal_field'
    value = 0
    converter = Decimal


class MoneyField(DecimalField):
    """Money Field

    >>> f = MoneyField("Amount")
    >>> f.widget()
    '<div class="input-group"><span class="input-group-addon">$</span><input class="decimal_field" type="text" id="amount" maxlength="10" name="amount" size="10" value="" /></div>'
    >>> f.display_value()
    '$0.00'
    >>> f.assign(Decimal(1000))
    >>> f.display_value()
    '$1,000.00'

    >>> from platform import system
    >>> l = system()=='Windows' and 'eng' or 'en_GB.utf8'
    >>> f = MoneyField("Amount", locale=l)
    >>> f.display_value()
    '\\xa30.00'

    >>> f.assign(Decimal(1000))
    >>> f.display_value()
    '\\xa31,000.00'
    >>> print(f.show())
    <div class="field">
      <div class="field_label">Amount</div>
      <div class="field_show">£1,000.00</div>
    </div>
    <BLANKLINE>

    >>> f.widget()
    '<div class="input-group"><span class="input-group-addon">£</span><input class="decimal_field" type="text" id="amount" maxlength="10" name="amount" size="10" value="1000" /></div>'
    >>> f.units = 'per month'
    >>> f.display_value()
    '\\xa31,000.00 per month'
    >>> f.units = ''
    >>> f.display_value()
    '\\xa31,000.00'
    >>> f.assign('')
    >>> f.display_value()
    ''
    >>> f.assign('0')
    >>> f.display_value()
    '\\xa30.00'
    >>> f.assign(' ')
    >>> f.display_value()
    ''

    >>> f = MoneyField("Amount", placeholder='0')
    >>> f.widget()
    '<div class="input-group"><span class="input-group-addon">$</span><input class="decimal_field" type="text" id="amount" maxlength="10" name="amount" placeholder="0" size="10" value="" /></div>'

    >>> f = MoneyField("Amount", symbol='£', value=1)
    >>> f.widget()
    '<div class="input-group"><span class="input-group-addon">£</span><input class="decimal_field" type="text" id="amount" maxlength="10" name="amount" size="10" value="1" /></div>'

    """

    locale = None
    symbol = '$'

    def widget(self):
        if self.locale:
            locale.setlocale(locale.LC_ALL, self.locale)
            self.symbol = locale.localeconv()['currency_symbol']

        t = '<div class="input-group"><span class="input-group-addon">{}</span>{}{}</div>'
        tu = '<span class="input-group-addon">{}</span>'

        if self.placeholder is not None:
            result = t.format(
                self.symbol,
                html.tag(
                    'input',
                    name=self.name,
                    id=self.id,
                    size=self.size,
                    placeholder=self.placeholder,
                    maxlength=self.maxlength,
                    value=self.value or self.default,
                    Type=self._type,
                    Class=self.css_class,
                    ),
                self.units and tu.format(self.units) or '',
                )
        else:
            result = t.format(
                self.symbol,
                html.tag(
                    'input',
                    name=self.name,
                    id=self.id,
                    size=self.size,
                    maxlength=self.maxlength,
                    value=self.value or self.default,
                    Type=self._type,
                    Class=self.css_class,
                    ),
                self.units and tu.format(self.units) or '',
                )
        return result

    def display_value(self):
        if self.value is None:
            return ''
        if self.locale:
            locale.setlocale(locale.LC_ALL, self.locale)
            v = locale.currency(self.value, grouping=True)
        else:
            v = self.symbol + ('{:20,.2f}'.format(self.value)).strip()
        if self.units and self.value is not None:
            v += ' ' + self.units
        return v


class DateField(Field):
    """Date Field

    DatField values can be either actual dates (datetime.date) or string
    representations of dates.  Values coming from databases or from code
    will typically be dates, while dates coming in from forms will
    typically be strings.

    DateFields always evaluate to date types and always display as string
    representations of those dates formatted according to the specified
    format.

    >>> DateField("Start Date").widget()
    '<input class="date_field" type="text" id="start_date" maxlength="12" name="start_date" value="" />'

    >>> from datetime import date, datetime

    >>> f = DateField("Start Date")
    >>> f.display_value()
    ''
    >>> f.assign('')
    >>> f.display_value()
    ''

    >>> f = DateField("Start Date", value=date(2015,1,1))
    >>> f.value
    datetime.date(2015, 1, 1)

    >>> f = DateField("Start Date", value=datetime(2015,1,1))
    >>> f.value
    datetime.datetime(2015, 1, 1, 0, 0)
    >>> f.evaluate()
    {'start_date': datetime.date(2015, 1, 1)}

    >>> f.assign('Jan 01, 2015') # forms assign with strings
    >>> f.display_value()
    'Jan 01, 2015'
    >>> f.evaluate()
    {'start_date': datetime.date(2015, 1, 1)}

    >>> f.assign('2015-12-31') # forms assign with strings
    >>> f.display_value()
    'Dec 31, 2015'
    >>> f.evaluate()
    {'start_date': datetime.date(2015, 12, 31)}

    >>> f.assign(date(2015,1,31))
    >>> f.display_value()
    'Jan 31, 2015'

    >>> f.assign('TTT 01, 2015')
    >>> f.display_value()
    'TTT 01, 2015'
    >>> failed = False
    >>> try:
    ...     f.evaluate()
    ... except ValueError:
    ...     failed = True
    >>> failed
    True

    >>> DateField("Start Date", value=date(2015,1,1)).widget()
    '<input class="date_field" type="text" id="start_date" maxlength="12" name="start_date" value="Jan 01, 2015" />'

    """

    value = default = None
    size = maxlength = 12
    input_format = '%b %d, %Y'
    alt_input_format = '%Y-%m-%d'
    format = '%b %d, %Y'
    _type = 'date'
    css_class = 'date_field'
    validators = [valid_date]
    min = max = None

    def display_value(self, alt_format=None):
        format = alt_format or self.format
        if self.value:
            strftime = datetime.datetime.strftime
            try:
                result = strftime(self.evaluate()[self.name], format)
            except ValueError:
                result = self.value
        else:
            result = self.default and self.default.strftime(format) or ''
        return result

    def widget(self):
        value = self.display_value(self.input_format)
        parameters = dict(
            name=self.name,
            id=self.id,
            maxlength=self.maxlength,
            value=value,
            Type='text',
            Class=self.css_class,
        )
        js = []
        if self.min != None:
            js.append("""
            $(function(){
                $('#%s').datepicker('option', 'minDate', '%s');
            });
            """ % (self.id, self.min.strftime(self.input_format)))

        if self.max != None:
            js.append("""
            $(function(){
                $('#%s').datepicker('option', 'maxDate', '%s');
            });
            """ % (self.id, self.max.strftime(self.input_format)))
        return html.tag('input', **parameters)

    def show(self):
        return self.visible and bool(self.value) and layout_field(self.label,self.display_value()) or ''

    def evaluate(self):
        if self.value:
            if type(self.value) == datetime.datetime:
                value = self.value.date()
            elif type(self.value) == datetime.date:
                value = self.value
            else:
                strptime = datetime.datetime.strptime
                try:
                    value = strptime(self.value, self.input_format).date()
                except ValueError:
                    value = strptime(self.value, self.alt_input_format).date()
            return {self.name: value or self.default}
        return {self.name: self.default}

    def as_searchable(self):
        """Return searchable parts of field

        >>> from datetime import date, datetime
        >>> f = DateField("Start Date")

        >>> f.assign(date(2015,1,31))
        >>> f.display_value()
        'Jan 31, 2015'
        >>> f.as_searchable()
        {'2015-01-31 01-31-2015 Saturday January 31 2015'}

        """
        def get_formatted_value():
            value = self.evaluate()[self.name]
            if value:
                return set([fmt.format(value)])
            return set()

        fmt = '{:%Y-%m-%d %m-%d-%Y %A %B %-d %Y}'
        return self.visible and get_formatted_value()


class BirthdateField(DateField):
    size = maxlength = 12
    css_class = 'birthdate_field'


class CheckboxesField(Field):
    """Checkboxes field.

    >>> cb = CheckboxesField('Select', value='One', values=['One','Two','Three'], hint='test hint')
    >>> print(cb.widget())
    <ul class="checkbox_field">
    <li><input checked class="checkbox_field" type="checkbox" id="select" name="select" value="One" /><div>One</div></li>
    <li><input class="checkbox_field" type="checkbox" id="select" name="select" value="Two" /><div>Two</div></li>
    <li><input class="checkbox_field" type="checkbox" id="select" name="select" value="Three" /><div>Three</div></li>
    </ul>
    """

    def widget(self):
        result = []
        for value in self.values:
            checked = value in self.value and 'checked' or ''
            tag = html.tag(
                'input',
                checked,
                name=self.name,
                id=self.id,
                Type='checkbox',
                Class='checkbox_field',
                value=value,
                )
            result.append('<li>%s<div>%s</div></li>\n' % (tag, value))
        result = '<ul class="checkbox_field">\n%s</ul>' % (''.join(result))
        return result

    def show(self):
        return layout_field(self.label, ', '.join(ensure_listy(self.value)))


class CheckboxField(TextField):
    """
    Checkbox Field

        >>> CheckboxField('Done').display_value()
        'no'

        >>> CheckboxField('Done', value=True).display_value()
        'yes'

        >>> CheckboxField('Done').widget()
        '<input class="checkbox_field" type="checkbox" id="done" name="done" />'

        >>> f = CheckboxField('Done', value=True)
        >>> f.widget()
        '<input checked class="checkbox_field" type="checkbox" id="done" name="done" />'
        >>> f.validate(**{'DONE': 'on'})
        True
        >>> f.evaluate()
        {'done': True}

        >>> f = CheckboxField('Done')
        >>> f.widget()
        '<input class="checkbox_field" type="checkbox" id="done" name="done" />'
        >>> f.evaluate()
        {'done': None}
        >>> f.validate(**{})
        True
        >>> f.evaluate()
        {'done': None}

        >>> f = CheckboxField('Done')
        >>> f.widget()
        '<input class="checkbox_field" type="checkbox" id="done" name="done" />'
        >>> f.evaluate()
        {'done': None}
        >>> f.validate(**{'DONE': 'on'})
        True
        >>> f.evaluate()
        {'done': True}

        >>> f = CheckboxField('Done', options=['yes','no'], value=False)
        >>> f
        <Field name='done' value=False>
        >>> f.validate(**{'done': True})
        True
        >>> f
        <Field name='done' value=True>
        >>> f.validate(**{'DoNE': False})
        True
        >>> f
        <Field name='done' value=False>
        >>> f.validate(**{'done': 'on'})
        True
        >>> f
        <Field name='done' value='on'>
        >>> f.display_value()
        'yes'
        >>> f.evaluate()
        {'done': True}

        >>> f = CheckboxField('Done', options=['yep','nope'], default=True)
        >>> f.evaluate()
        {'done': True}
        >>> f.widget()
        '<input checked class="checkbox_field" type="checkbox" id="done" name="done" />'

        >>> f.update(other='test')
        >>> f.widget()
        '<input class="checkbox_field" type="checkbox" id="done" name="done" />'

        >>> f = CheckboxField('Done', options=['yep','nope'])
        >>> f.evaluate()
        {'done': None}
        >>> f.validate(**{'OTHERDATA': 'some value'})
        True
        >>> f.evaluate()
        {'done': False}

        >>> CheckboxField('Done', options=['yep','nope']).display_value()
        'nope'

        >>> CheckboxField('Done', options=['yep','nope'], default=False).display_value()
        'nope'

        >>> CheckboxField('Done', options=['yep','nope'], default=True).display_value()
        'nope'

        >>> CheckboxField('Done', options=['yep','nope'], default=True).evaluate()
        {'done': True}

        >>> CheckboxField('Done', options=['yep','nope'], default=True, value=False).display_value()
        'nope'

        >>> CheckboxField('Done', options=['yep','nope'], value=True).display_value()
        'yep'

        >>> CheckboxField('Done', options=['yep','nope'], value=False).evaluate()
        {'done': False}

        >>> CheckboxField('Done', options=['yep','nope'], value='True').value
        'True'

    """
    options = ['yes','no']
    truthy = [True,'True','yes','on']
    default = None
    value = None

    def assign(self, value):
        self.value = value in self.truthy and value or False

    def widget(self):
        value = self.value is None and self.default or self.value
        checked = value and 'checked' or ''
        tag = html.tag(
            'input',
            checked,
            name = self.name,
            id = self.id,
            Type='checkbox',
            Class='checkbox_field',
            )
        return tag

    def display_value(self):
        return self.value in self.truthy and self.options[0] or self.options[1] or ''

    def show(self):
        return layout_field(self.label, self.display_value(), False)

    def update(self,**values):
        for value in values:
            if value.lower() == self.name.lower():
                self.assign(values[value])
                return
        if values:
            self.assign(False)

    def evaluate(self):
        if self.value in self.truthy:
            v = True
        elif self.value in [False]:
            v = False
        else:
            v = self.default
        return {self.name: v}


class RadioField(TextField):
    """Radio Field

    >>> RadioField('Choice', value='One', values=['One','Two']).display_value()
    'One'

    >>> print(RadioField('Choice', value='One', values=['One','Two']).widget())
    <span class="radio"><input checked class="radio" name="choice" type="radio" value="One" />One</span>
    <span class="radio"><input class="radio" name="choice" type="radio" value="Two" />Two</span>
    <BLANKLINE>

    >>> r = RadioField('Choice',value='1',values=[('One','1'),('Two','2')])
    >>> print(r.widget())
    <span class="radio"><input checked class="radio" name="choice" type="radio" value="1" />One</span>
    <span class="radio"><input class="radio" name="choice" type="radio" value="2" />Two</span>
    <BLANKLINE>


    >>> r.assign('1')
    >>> r.evaluate()
    {'choice': '1'}
    >>> r.display_value()
    'One'

    >>> r.assign('2')
    >>> r.evaluate()
    {'choice': '2'}
    >>> r.display_value()
    'Two'

    """
    values = []

    def widget(self):
        current_value = self.value #self.display_value()
        result = []
        name = self.name
        for option in self.values:
            if type(option) in (list, tuple) and len(option) == 2:
                text, value = option
            else:
                text = value = option
            label = self.label
            checked = (value == current_value) and 'checked' or ''
            result.append(
                html.span(
                    html.input(
                        checked,
                        type='radio',
                        name=name,
                        value=value,
                        Class='radio'
                    ) + text,
                    Class='radio',
                ) + '\n'
            )
        return ''.join(result)

    def display_value(self):
        t = self.value
        if t:
            for option in self.values:
                if isinstance(option, (list, tuple)) and len(option) == 2:
                    label, value = option
                    if t == value:
                        return label
        return t or ''

class PulldownField(TextField):
    """Pulldown Field

    >>> from zoom.component import composition, Component
    >>> composition.parts = Component()
    >>> PulldownField('Type',value='One',options=['One','Two']).display_value()
    'One'

    >>> print(PulldownField('Type',value='One',options=['One','Two']).widget())
    <select class="pulldown" name="type" id="type">
    <option value="One" selected>One</option>
    <option value="Two">Two</option>
    </select>

    >>> print(PulldownField('Type',options=['One','Two']).widget())
    <select class="pulldown" name="type" id="type">
    <option value=""></option>
    <option value="One">One</option>
    <option value="Two">Two</option>
    </select>

    >>> f = PulldownField('Type', options=[('',''),('One',1),('Two',2)])
    >>> print(f.widget())
    <select class="pulldown" name="type" id="type">
    <option value="" selected></option>
    <option value="1">One</option>
    <option value="2">Two</option>
    </select>

    >>> f.assign(2)
    >>> print(f.widget())
    <select class="pulldown" name="type" id="type">
    <option value=""></option>
    <option value="1">One</option>
    <option value="2" selected>Two</option>
    </select>

    >>> f.assign('2')
    >>> print(f.widget())
    <select class="pulldown" name="type" id="type">
    <option value=""></option>
    <option value="1">One</option>
    <option value="2" selected>Two</option>
    </select>

    >>> f = PulldownField('Type', options=[('',''),('One','1'),('Two','2')])
    >>> print(f.widget())
    <select class="pulldown" name="type" id="type">
    <option value="" selected></option>
    <option value="1">One</option>
    <option value="2">Two</option>
    </select>

    >>> f.assign(2)
    >>> print(f.widget())
    <select class="pulldown" name="type" id="type">
    <option value=""></option>
    <option value="1">One</option>
    <option value="2" selected>Two</option>
    </select>

    >>> f.assign('2')
    >>> print(f.widget())
    <select class="pulldown" name="type" id="type">
    <option value=""></option>
    <option value="1">One</option>
    <option value="2" selected>Two</option>
    </select>

    >>> f = PulldownField('Type',value='One',options=[('One','uno'),('Two','dos')])
    >>> print(f.widget())
    <select class="pulldown" name="type" id="type">
    <option value="uno" selected>One</option>
    <option value="dos">Two</option>
    </select>

    >>> f.value
    'uno'
    >>> f.evaluate()
    {'type': 'uno'}
    >>> f.value = 'One'
    >>> f.value
    'One'
    >>> f.evaluate()
    {'type': 'uno'}
    >>> f.update(**{'tYpe':'dos'})
    >>> f.value
    'dos'
    >>> f.evaluate()
    {'type': 'dos'}

    >>> f = PulldownField('Type',value='uno',options=[('One','uno'),('Two','dos')])
    >>> f.display_value()
    'One'

    >>> f = PulldownField('Type',default='uno',options=[('One','uno'),('Two','dos')])
    >>> f.display_value()
    'One'
    >>> f.evaluate()
    {'type': 'uno'}

    >>> p = PulldownField('Date', name='TO_DATE', options=[('JAN','jan'), ('FEB','feb'),], default='feb')
    >>> p.evaluate()
    {'TO_DATE': 'feb'}
    >>> p.display_value()
    'FEB'
    """

    value = None
    css_class = 'pulldown'
    select_layout = '<select class="{classed}" name="{name}" id="{name}">\n'
    libs = []
    styles = []

    def __init__(self, *a, **k):
        TextField.__init__(self, *a, **k)
        if 'placeholder' not in k:
            self.placeholder = 'Select ' + self.label

    def evaluate(self):
        for option in self.options:
            if type(option) in (list, tuple) and len(option) == 2:
                label, value = option
                if self.value == label:
                    return {self.name: value}
        return {self.name: self.value is None and self.default or self.value}

    def display_value(self):
        t = self.value is None and self.default or self.value
        if t:
            for option in self.options:
                if type(option) in (list, tuple) and len(option)==2:
                    label, value = option
                    if t == value:
                        return label
        return t

    def assign(self,new_value):
        self.value = new_value
        for option in self.options:
            if type(option) in (list, tuple) and len(option)==2:
                label, value = option
                if new_value == label:
                    self.value = value

    def widget(self):
        current_value = str(self.value or self.default) or ''
        result = []
        name = self.name
        found = False
        result.append(self.select_layout.format(**dict(place=self.placeholder, classed=self.css_class, name=name)))
        for option in self.options:
            if type(option) in (list, tuple) and len(option)==2:
                label, value = option
            else:
                label, value = option, option
            if str(value) == current_value:
                result.append('<option value="%s" selected>%s</option>\n' % (value,label))
                found = True
            else:
                result.append('<option value="%s">%s</option>\n' % (value,label))
        if not found and not current_value:
            blank_option = '<option value=""></option>\n'
            result.insert(1, blank_option)
        result.append('</select>')
        return component(result, libs=self.libs, styles=self.styles)


class ChosenSelectField(PulldownField):
    css_class = 'chosen'
    libs = ['/static/zoom/chosen/chosen.jquery.js']
    styles = ['/static/zoom/chosen/chosen.css']
    select_layout = '<select data-placeholder="{place}" class="{classed}" name="{name}" id="{name}">\n'


class MultiselectField(TextField):
    """Multiselect Field

    >>> MultiselectField('Type',value='One',options=['One','Two']).display_value()
    'One'

    >>> f = MultiselectField('Type', default='One', options=['One','Two'])
    >>> f.evaluate()
    {'type': []}
    >>> f.display_value()
    ''
    >>> print(f.widget())
    <select multiple="multiple" class="multiselect" name="type" id="type">
    <option value="One" selected>One</option>
    <option value="Two">Two</option>
    </select>

    >>> f.value
    >>> f.assign([])
    >>> f.value
    []
    >>> f.evaluate()
    {'type': []}
    >>> print(f.widget())
    <select multiple="multiple" class="multiselect" name="type" id="type">
    <option value="One">One</option>
    <option value="Two">Two</option>
    </select>

    >>> f= MultiselectField('Type',value='One',options=['One','Two'])
    >>> print(f.widget())
    <select multiple="multiple" class="multiselect" name="type" id="type">
    <option value="One" selected>One</option>
    <option value="Two">Two</option>
    </select>

    >>> f = MultiselectField('Type',value=['One','Three'],options=['One','Two','Three'])
    >>> print(f.widget())
    <select multiple="multiple" class="multiselect" name="type" id="type">
    <option value="One" selected>One</option>
    <option value="Two">Two</option>
    <option value="Three" selected>Three</option>
    </select>

    >>> f = MultiselectField('Type',default=['One'],options=['One','Two','Three'])
    >>> print(f.widget())
    <select multiple="multiple" class="multiselect" name="type" id="type">
    <option value="One" selected>One</option>
    <option value="Two">Two</option>
    <option value="Three">Three</option>
    </select>

    >>> f = MultiselectField('Type',default=['One','Two'],options=['One','Two','Three'])
    >>> print(f.widget())
    <select multiple="multiple" class="multiselect" name="type" id="type">
    <option value="One" selected>One</option>
    <option value="Two" selected>Two</option>
    <option value="Three">Three</option>
    </select>

    >>> f = MultiselectField('Type',value='One',options=[('One','uno'),('Two','dos')])
    >>> print(f.widget())
    <select multiple="multiple" class="multiselect" name="type" id="type">
    <option value="uno" selected>One</option>
    <option value="dos">Two</option>
    </select>
    >>> f.value
    ['uno']
    >>> f.evaluate()
    {'type': ['uno']}
    >>> f.value = ['One']
    >>> f.value
    ['One']
    >>> f.evaluate()
    {'type': ['uno']}
    >>> f.update(**{'type':['dos']})
    >>> f.value
    ['dos']
    >>> f.evaluate()
    {'type': ['dos']}

    >>> f = MultiselectField('Type',value='uno',options=[('One','uno'),('Two','dos')])
    >>> f.display_value()
    'One'

    >>> f = MultiselectField('Type',value='uno',options=[('One','uno'),('One','dos')])
    >>> f.display_value()
    'One'
    >>> print(f.widget())
    <select multiple="multiple" class="multiselect" name="type" id="type">
    <option value="uno" selected>One</option>
    <option value="dos">One</option>
    </select>

    >>> f = MultiselectField('Type',value=['One','dos'],options=[('One','uno'),('Two','dos')])
    >>> f.display_value()
    'One; Two'
    >>> f.evaluate()
    {'type': ['uno', 'dos']}
    >>> sorted(f.as_searchable())
    ['One', 'Two']

    >>> f = MultiselectField('Type',value=['One'],options=[('One','uno'),('Two','dos')])
    >>> f.display_value()
    'One'
    >>> f.evaluate()
    {'type': ['uno']}

    >>> f = MultiselectField('Type', options=[('One','uno'),('Two','dos')])
    >>> f.initialize({'type': 'One'})
    >>> f.evaluate()
    {'type': ['uno']}

    >>> f = MultiselectField('Type',value=['uno','dos'],options=[('One','uno'),('Two','dos')])
    >>> f.display_value()
    'One; Two'
    >>> f.evaluate()
    {'type': ['uno', 'dos']}
    >>> f.option_style('zero','nada')
    ''

    >>> s = lambda label, value: value.startswith('d') and 's1' or 's0'
    >>> f = MultiselectField('Type',value=['uno','dos'],options=[('One','uno'),('Two','dos')], styler=s)
    >>> print(f.widget())
    <select multiple="multiple" class="multiselect" name="type" id="type">
    <option class="s0" value="uno" selected>One</option>
    <option class="s1" value="dos" selected>Two</option>
    </select>

    >>> f.styler('test','dos')
    's1'
    >>> f.option_style('zero','nada')
    'class="s0" '

    # test for iterating over a string vs. a sequence type (iteration protocol)
    >>> m1 = MultiselectField('Type', default='11', options=[('One','1'),('Two','2'),('Elves','11'),]).widget()
    >>> m2 = MultiselectField('Type', default=('11',), options=[('One','1'),('Two','2'),('Elves','11'),]).widget()
    >>> assert m1 == m2

    """

    value = None
    default = []
    css_class = 'multiselect'
    styler = None

    def _scan(self, t, f):
        if t:
            t = list(map(str, ensure_listy(t)))
            result = []
            for option in self.options:
                if len(option) == 2 and is_listy(option):
                    label, value = option
                    if label in t or str(value) in t:
                        result.append(f(option))
                elif option in t:
                    result.append(option)
            return result
        return []

    def evaluate(self):
        return {self.name: self._scan(self.value, lambda a: a[1])}

    def display_value(self):
        return '; '.join(self._scan(self.value, lambda a: a[0]))

    def as_searchable(self):
        return set(self._scan(self.value, lambda a: a[0]))

    def assign(self, new_value):
        self.value = self._scan(new_value, lambda a: a[1])

    def update(self, **values):
        for value in values:
            if value.lower() == self.name.lower():
                self.assign(values[value])
                return
        self.assign([])

    def option_style(self, label, value):
        if self.styler is not None:
            return 'class="{}" '.format(self.styler(label, value))
        return ''

    def widget(self):
        if self.value is None:
            current_values = self.default
        else:
            current_values = self.value
        current_values = ensure_listy(current_values)
        current_values = list(map(str, ensure_listy(current_values)))
        result = []
        name = self.name
        tpl = '<select multiple="multiple" class="%s" name="%s" id="%s">\n'
        result.append(tpl%(self.css_class, name, name))
        for option in self.options:
            if is_listy(option) and len(option) == 2:
                label, value = option
            else:
                label, value = option, option
            style = self.option_style(label, value)
            if str(value) in current_values:
                result.append('<option %svalue="%s" selected>%s</option>\n' % (style, value, label))
            else:
                result.append('<option %svalue="%s">%s</option>\n' % (style, value, label))
        result.append('</select>')
        return ''.join(result)


class ChosenMultiselectField(MultiselectField):
    """
    Chosen Multiselect field.

    >>> from zoom.component import composition, Component
    >>> composition.parts = Component()
    >>> f = ChosenMultiselectField('Choose', options=['One','Two','Three'], hint='test hint')
    >>> print(f.widget())
    <select data-placeholder="Select Choose" multiple="multiple" class="chosen" name="choose" id="choose">
    <option value="One">One</option>
    <option value="Two">Two</option>
    <option value="Three">Three</option>
    </select>

    >>> f = ChosenMultiselectField('Choose', options=['One','Two','Three'], hint='test hint', placeholder='my placeholder')
    >>> print(f.widget())
    <select data-placeholder="my placeholder" multiple="multiple" class="chosen" name="choose" id="choose">
    <option value="One">One</option>
    <option value="Two">Two</option>
    <option value="Three">Three</option>
    </select>



    """
    css_class = 'chosen'
    select_layout = '<select data-placeholder="{}" multiple="multiple" class="{}" name="{}" id="{}">\n'

    def __init__(self, *a, **k):
        MultiselectField.__init__(self, *a, **k)
        if not 'placeholder' in k:
            self.placeholder = 'Select ' + self.label

    def widget(self):
        libs = ['/static/zoom/chosen/chosen.jquery.js']
        styles = ['/static/zoom/chosen/chosen.css']
        if self.value == None:
            current_values = self.default
        else:
            current_values = self.value
        # current_values = ensure_listy(current_values)
        current_values = list(map(str, ensure_listy(current_values)))
        current_labels = self._scan(current_values, lambda a: a[0])
        result = []
        name = self.name
        result.append(self.select_layout.format(self.placeholder, self.css_class, name, name))
        for option in self.options:
            if is_listy(option) and len(option)==2:
                label, value = option
            else:
                label, value = option, option
            style = self.option_style(label, value)
            if str(value) in current_values:
                result.append('<option %svalue="%s" selected>%s</option>\n' % (style, value,label))
            else:
                result.append('<option %svalue="%s">%s</option>\n' % (style,value,label))
        result.append('</select>')
        return component(result, libs=libs, styles=styles)


class RangeSliderField(IntegerField):
    """ jQuery UI Range Slider

    >>> r = RangeSliderField('Price', min=0, max=1500)
    >>> r.assign(0)
    >>> r.value
    (0, 1500)
    >>> r.assign((10, 20))
    >>> r.value
    (10, 20)
    >>> r.assign('10,20')
    >>> r.value
    (10, 20)
    >>> isinstance(r.widget(), zoom.Component)
    True
    >>> isinstance(r.display_value(), str)
    True
    """
    js_formatter = """var formatter = function(v) { return v;};"""
    js = """
        $( "#%(name)s" ).slider({
          range: true,
          min: %(tmin)s,
          max: %(tmax)s,
          values: [ %(minv)s, %(maxv)s ],
          change: function( event, ui ) {
            var v = ui.values,
                t = v[0] + ',' + v[1];
            $("input[name='%(name)s']").val(t);
            %(formatter)s
            $( "div[data-id='%(name)s'] span:nth-of-type(1)" ).html( formatter(ui.values[ 0 ]) );
            $( "div[data-id='%(name)s'] span:nth-of-type(2)" ).html( formatter(ui.values[ 1 ]) );
          },
          slide: function( event, ui ) {
            var v = ui.values;
            %(formatter)s
            $( "div[data-id='%(name)s'] span:nth-of-type(1)" ).html( formatter(ui.values[ 0 ]) );
            $( "div[data-id='%(name)s'] span:nth-of-type(2)" ).html( formatter(ui.values[ 1 ]) );
          }
        });
        $("#%(name)s").slider("values", $("#%(name)s").slider("values")); // set formatted label
    """
    min = 0
    max = 10
    show_labels = True
    css_class = 'range-slider'

    def assign(self, v):
        if v is None or not v or (isinstance(v, str) and v.strip()==','):
            self.value = (self.min, self.max)
        elif ',' in v:
            self.value = tuple(map(int, v.split(',')))
        else:
            self.value = (int(v[0]), int(v[1]))

    def widget(self):
        name = self.name
        tmin, tmax = self.min, self.max
        minv, maxv = self.value or (tmin, tmax)

        formatter = self.js_formatter
        js = self.js % locals()
        labels = """<div data-id="{}" class="{}"><span class="min pull-left">{}</span><span class="max pull-right">{}</span></div>""".format(
            name,
            not self.show_labels and "hidden" or "",
            minv, maxv
          )
        slider = '<div id="{}"><input type="hidden" name="{}" value="{}, {}"></div>'.format(name, name, minv, maxv)
        return component('<div class="{}">{}{}</div>'.format(self.css_class, slider, labels), js=js)

    def display_value(self):
        units = self.units and (' ' + self.units) or ''
        value1, value2 = self.value
        value = self.value and ('{:,} to {:,}{}'.format(value1, value2, units)) or ''
        return websafe(value)


class DataURIAttachmentsField(Field):  # pragma: no cover
    """An Attachments field - DEPRECATED

        this field stores the data within the database
        this field uses dropzone.js heavily
        the results are shown via a Data URI

        this field stores the data within the database
        this field uses dropzone.js heavily
        the results are shown via a Data URI
        multiple dropzones supported by assuming you will bind ONLY one to the form
            and the others to an element via the "selector" configuration option
        TODO: with multiple dropzones, support submit when the master/form is empty
        This field makes some assumptions about what you want todo:
            - this field uses dropzone.js
            - the field expects you want todo a native form submission (once vs. multiple ajax calls)
            - this field stores the data within the database
            - the results are shown via a Data URI which is not always optimal
            - it looks like dropzone.js only adds the form fields when dropzone is bound
                to a form (i.e. binding to dropzone within a form skips this - assumes xhr)
            -  due to assumption to mimic native form, the data makes round trips to/from server

    >>> icon = DataURIAttachmentsField('Icon')
    >>> icon.requires_multipart_form()
    True
    >>> icon.assign(None)
    >>> assert icon.value == icon.default
    >>> class PsuedoFile(object):
    ...     @property
    ...     def name(self):
    ...         return 'field_name'
    ...     @property
    ...     def filename(self):
    ...         return 'filename.png'
    ...     @property
    ...     def value(self):
    ...         return b''
    >>> icon.assign([PsuedoFile(), PsuedoFile()])
    >>> assert isinstance(icon.value, list)
    >>> icon.value
    [['field_name', ['filename.png', '']], ['field_name', ['filename.png', '']]]
     """
    default = []  # (filename, base64 data)
    classed = 'dropzone nojs'
    no_image_url = 'https://placehold.it/350x150'
    maximum_files = 5
    selector = "#zoom_form"  # select to attach the dropzone onto
    script = [
        """<script type="text/javascript" src="/static/zoom/dropzone/dropzone.min.js"></script>""",
        """<script type="text/javascript">Dropzone.autoDiscover = false;</script>""",
    ]
    css = """<link href="/static/zoom/dropzone/dropzone.min.css" rel="stylesheet" type="text/css" />"""

    @property
    def capitalize(self):
        """return the field id capitalized"""
        return self.id.capitalize()

    @property
    def configuration(self):
        """configure the Dropzone .js assets

            this field is designed to work within an existing/native form.  As such, we turn off
            the auto processing of the queue (AJAX push) to bulk send the form all at once.
        """
        return """
/* script type="text/javascript" */
/* var {self.id}Dropzone = new Dropzone("{self.selector}", {{ */
var {self.id}Dropzone = $("{self.selector}").dropzone({{
      url: $('form#zoom_form').attr("action") || '/think/of/some/default',
      paramName: "{self.id}",
      autoProcessQueue: false,
      uploadMultiple: true,
      parallelUploads: 5,
      maxFiles: {self.maximum_files},
      acceptedFiles: 'image/*',
      addRemoveLinks: true,
      clickable: ".dropzone.{self.id} .dz-clickable",
      method: "post",
      previewsContainer: "#{self.id}Preview",

      // The setting up of the dropzone
      init: function() {{
        var myDropzone = this;

        if (this.element.tagName === "FORM") {{
            // First change the button to actually tell Dropzone to process the queue.
            this.element.querySelector("input[type=submit],button[type=submit]").addEventListener("click", function(e) {{
              // Make sure that the form isn't actually being sent.
              if (myDropzone.getQueuedFiles().length > 0) {{
                e.preventDefault();
                e.stopPropagation();
                myDropzone.processQueue();
              }}
            }});
        }}

        // hook into master events for not FORM bindings
        if (this.element.tagName !== "FORM") {{
            // support for Master-Slave setup
            var masterDropzone = Dropzone.forElement("#zoom_form");
            masterDropzone.on("sendingmultiple", function(master_files, xhr, formData) {{
                // Gets triggered when the form is actually being sent.
                // Hide the success button or the complete form.

                // watch the Master Dropzone, when sending add the slave dropzones files
                console.log('sending multiple...')

                if (myDropzone.options.params) {{
                  _ref1 = myDropzone.options.params;
                  for (key in _ref1) {{
                    value = _ref1[key];
                    formData.append(key, value);
                  }}
                }}

                var files = myDropzone.files;  // just grab them all as this field type assumes a native form (i.e. ignore file.status)
                if (files.length > 0) {{
                    for (i = _m = 0, _ref5 = files.length - 1; 0 <= _ref5 ? _m <= _ref5 : _m >= _ref5; i = 0 <= _ref5 ? ++_m : --_m) {{
                        formData.append(myDropzone._getParamName(i), files[i], myDropzone._renameFilename(files[i].name));
                    }}
                }}

                console.log('sending multiple...done')
            }});

        }}

        // Listen to the sendingmultiple event. In this case, it's the sendingmultiple event instead
        // of the sending event because uploadMultiple is set to true.
        this.on("sendingmultiple", function(files, xhr, formData) {{
          // Gets triggered when the form is actually being sent.
          // Hide the success button or the complete form.
          /*
            console.log(formData);
            ignores = [];
            files.forEach(function(file) {{
                if (file.isMock) {{
                    console.log(file);
                    var tempFile = new File(["foo"], file.name, {{
                      type: "text/plain",
                    }});
                    formData.append(file.key, tempFile);

                    console.log(tempFile);
                }}
            }});
            console.log(formData);
            */
        }});
        this.on("successmultiple", function(files, response) {{
          // Gets triggered when the files have successfully been sent.
          // Redirect user or notify of success.
          document.open();
          document.write(response);
          document.close();
          // window.location.replace("/app/some/url");
        }});
        this.on("errormultiple", function(files, response) {{
          // Gets triggered when there was an error sending the files.
          // Maybe show form again, and notify user of error
          console.log('error');
          console.log(response);
        }});
        this.on("removedfile", function(file) {{
          // Called whenever a file is removed from the list.
          // Delete the file from the server if we want.
          if (file.accepted && file.status === "success") {{
            // TODO: using file.name as the key for now, expect this to change
            console.log(file.name);
          }}
        }});

        function dataURItoBlob(dataURI) {{
          // this was found via Stack Overflow
          // convert base64 to raw binary data held in a string
          // doesn't handle URLEncoded DataURIs - see SO answer #6850276 for code that does this
          var byteString = atob(dataURI.split(',')[1]);

          // separate out the mime component
          var mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0]

          // write the bytes of the string to an ArrayBuffer
          var ab = new ArrayBuffer(byteString.length);
          var ia = new Uint8Array(ab);
          for (var i = 0; i < byteString.length; i++) {{
              ia[i] = byteString.charCodeAt(i);
          }}

          // write the ArrayBuffer to a blob, and you're done
          var blob = new Blob([ab], {{type: mimeString}});
          return blob;
        }}

        function previewThumbailFromUrl(opts) {{
          var mockFile = {{
            isMock: true,
            key: opts.fieldName,
            name: opts.fileName,
            size: opts.fileSize,
            accepted: true,
            status: Dropzone.QUEUED,
            kind: 'image'
          }};
          //var tempFile = new File([dataURItoBlob(opts.imageURL)], opts.fileName, {{type: "text/plain",}});
          // File() not supported by Edge
          var tempFile = new Blob([dataURItoBlob(opts.imageURL)], {{
            type: "text/plain",
          }});
          tempFile.name = opts.fileName;
          mockFile = tempFile;
          mockFile.status = Dropzone.QUEUED;
          myDropzone.emit("addedfile", mockFile);
          myDropzone.files.push(mockFile);
          myDropzone.createThumbnailFromUrl(mockFile, opts.imageURL, function() {{
            myDropzone.emit("complete", mockFile);
            myDropzone.options.maxFiles = myDropzone.options.maxFiles - 1;
          }});
        }}

        // load the server side thumbnails
        {self.mockFile}

      }}

    }}
    );
/* /script */""".format(self=self)

    @property
    def mockFile(self):
        """return the saved file - this is a .js call and injected into the .js"""
        if self.value:
            thumbnails = []
            for name, image in self.value:
                filename, b64string = image
                if b64string:
                    opts = dict(
                        fieldName=name,
                        fileName=filename,
                        fileSize=((len(b64string) * 3) / 4 - b64string.count('=', -2)),
                        imageURL=self.datauri(b64string),
                    )
                    thumbnails.append("previewThumbailFromUrl({});".format(opts))
            if thumbnails:
                return '\n'.join(thumbnails)  # injected into .js file
        return ""

    def _initialize(self, values):
        """initialize field"""
        value = values.get(self.name.lower()) or self.default[:]  # ensure this is a copy
        self.assign(value)

    def update(self,**values):
        """update the field"""
        self._initialize(values)

    def assign(self, value={}):
        """assign a value to the field"""
        import base64

        self.value = self.default[:]  # reset to a base list, ensure it is a copy

        if value and isinstance(value, list) and not hasattr(value[0], 'name'):
            # from the database
            self.value = value
        elif value and isinstance(value, list):
            # multiple uploads from a form
            value = [[val.name, [val.filename, base64.b64encode(val.value).decode('ascii')]] for val in value]
            self.value.extend(value)
        elif value and hasattr(value, 'file'):
            # single upload from a form
            self.value.append([value.name, [value.filename, base64.b64encode(value.value).decode('ascii')]])

    def display_value(self):
        """web based display view of the field"""
        images = []
        for name, image in self.value:
            filename, image = image
            images.append("""<img class="img-rounded img-responsive" data-field="{}" alt="{}" src="{}"
        onerror="this.onerror=null;this.src='{}';">""".format(name, filename, self.datauri(image), self.no_image_url))
        return "".join(images)

    def datauri(self, image):
        """return the data URI string"""
        return "data:image/png;base64,{}".format(image)

    def requires_multipart_form(self):
        """return True if a multipart form is required for this field"""
        return True

    def widget(self):
        """return the dropzone widget"""
        previews = """<div class="{self.classed} {self.id} dz-clickable"><span class="btn btn-success fileinput-button">
            <i class="glyphicon glyphicon-plus"></i>
            <span>Add files...</span>
        </span><div id="{self.id}Preview" class="dropzone-previews"></div></div>"""
        fallback = """<div class="fallback"><input id="{}" name="{}" type="file" multiple /></div>"""
        return component(
            previews.format(self=self),
            fallback.format(self.id, self.name),
            self.render_msg(),
            tail=self.script,
            js=self.configuration,
            head=self.css,
        )

    def edit(self):
        return layout_field(self.label, self.widget())

    def as_searchable(self):
        return set()


class DataURIImageField(DataURIAttachmentsField):
    """An Attachments field making use of a Data URI where we limit to a single file"""
    maximum_files = 1


# alias
DataURIImagesField = DataURIAttachmentsField
ImageField = DataURIImageField


class BasicImageField(Field):
    """Image Field

    >>> f = BasicImageField('Photo')
    >>> f.initialize(None)
    >>> f.value
    >>> f.name
    'photo'

    >>> i = BasicImageField('Photo')
    >>> i.initialize({'photo':'data blob', 't':12})
    >>> i.value
    '<img class="image-field-image" alt="photo" src="image?name=photo">'
    """
    size = maxlength = 40
    _type = 'file'
    css_class = 'image_field'
    no_image_url = '/static/zoom/images/no_photo.png'
    binary_image_data = None
    value = None

    def _initialize(self, values):
        name = self.name.lower()
        alt = self.name
        if hasattr(values, name) and getattr(values, name):
            url = values.url + '/image?name=' + name
            alt = values.name
        elif isinstance(values, dict) and values.get(name):
            # we do not know the route when passed as a dict
            # we just see the data blob
            url = 'image?name=' + name
        else:
            url = self.no_image_url
            # self.value = None
        self.value = '<img class="image-field-image" alt="{}" src="{}">'.format(
            alt,
            url,
        )

    def display_value(self):
        return self.value

    def edit(self):

        tag = html.tag(
            'input',
            name=self.name,
            id=self.id,
            Type=self._type,
            Class=self.css_class,
        )

        delete_link = (
            '<div class="image-field-delete-link">'
            '<a href="delete-image?name=%s">delete %s</a>'
            '</div>' % (self.name.lower(), self.label.lower())
        )

        if self.value:
            tag += delete_link + self.display_value()
        return layout_field(
            self.label,
            ''.join([tag, self.render_msg(), self.render_hint()])
        )

    def requires_multipart_form(self):
        return True

    def assign(self, value):
        # print(f'{len(value)} bytes')
        # self.value = None
        try:
            try:
                self.binary_image_data = value.value
            except AttributeError:
                self.value = value
        except AttributeError:
            self.value = None

    def evaluate(self):
        value = self.binary_image_data
        return {self.name: value} if value else {}
