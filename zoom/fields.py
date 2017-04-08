"""
    zoom.Fields
"""

import os
import types
from decimal import Decimal

from zoom.render import render
from zoom.utils import name_for
from zoom.tools import (
    htmlquote,
    websafe,
    markdown,
)
import zoom.html as html
from zoom.validators import (
    valid_phone,
    valid_email,
    valid_postal_code,
    valid_url,
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
    return render(**locals())


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
        content = render(
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
