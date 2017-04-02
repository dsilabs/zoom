"""
    zoom.Fields
"""

import os

from zoom.render import render
from zoom.utils import name_for
from zoom.tools import (
    htmlquote,
    websafe,
    markdown,
)
import zoom.html as html


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
            'hint',
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
                html.tag('textarea', self.display_value(), Class='textarea'),
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
