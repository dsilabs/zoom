"""
    zoom.validators
"""

import re
import imghdr
import cgi
import datetime

PHONE_RE = r'^\(?([2-9][0-8][0-9])\)?[-. ]?([2-9][0-9]{2})[-. ]?([0-9]{4})$'
USERNAME_RE = r'^[a-zA-Z0-9.@\\]+$'


class Validator(object):
    """A content validator.

    >>> is_true = Validator('not true', bool)
    >>> is_true.valid(1)
    True

    >>> is_true.valid([])
    False

    >>> is_true.msg
    'not true'

    >>> is_true.clean({})
    {}

    """

    def __init__(self, msg, test):
        self.msg = msg
        self.test = test

    def clean(self, value):
        """cleans up a value"""  # pylint: disable=no-self-use
        return value

    def valid(self, value):
        """tests validity of a value"""
        return self.test(value)

    def __call__(self, value):
        return self.valid(value)


class Cleaner(object):
    """A content cleaner.

    >>> Cleaner(str.lower).clean('Test')
    'test'

    >>> import decimal
    >>> Cleaner(decimal.Decimal).clean('10')
    Decimal('10')
    """

    def __init__(self, transformer):
        self.transform = transformer

    def clean(self, value):
        """cleans up a value"""
        return self.transform(value)

    def valid(self, value):
        """tests validity of a value"""
        # pylint: disable=no-self-use, unused-argument
        return True

    def __call__(self, value):
        return self.clean(value)


class RegexValidator(Validator):
    """
    A regular expression validator

        >>> validator = RegexValidator('invalid input', r'^[a-zA-Z0-9]+$')
        >>> validator.valid('1')
        True

        >>> validator = RegexValidator('invalid input', r'^[a-zA-Z0-9]+$')
        >>> validator.valid('')
        True

        >>> is_valid = RegexValidator('invalid input', r'^[a-zA-Z0-9]+$')
        >>> is_valid('')
        True
        >>> is_valid('*')
        False

        >>> validator = RegexValidator('invalid input', r'^[a-zA-Z0-9]+$')
        >>> validator.valid('-')
        False
        >>> validator.msg
        'invalid input'
    """

    def __init__(self, msg, regex, options=0):
        Validator.__init__(self, msg, None)
        self.regex = regex
        self.options = options

    def valid(self, value):
        # compile regex on first use only
        self.test = self.test or re.compile(self.regex, self.options).match
        # only test if value exists
        return not value or bool(self.test(value))


class URLValidator(RegexValidator):
    """
    A URL Validator

        >>> validator = URLValidator()
        >>> validator.valid('http://google.com')
        True

        >>> validator = URLValidator()
        >>> validator.valid('test123')
        False

    """

    def __init__(self):
        RegexValidator.__init__(
            self,
            'Enter a valid URL',
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)'
            r'+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
            r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$',
            re.IGNORECASE
        )


class PostalCodeValidator(RegexValidator):
    """A Postal Code Validator

    >>> validator = PostalCodeValidator()
    >>> validator.valid('V8X 1G1')
    True

    >>> validator = PostalCodeValidator()
    >>> validator.valid('V8X1G1')
    True

    >>> validator = PostalCodeValidator()
    >>> validator.valid('V8X XG1')
    False

    >>> validator = PostalCodeValidator()
    >>> validator.valid('8X XG1')
    False

    >>> validator = PostalCodeValidator()
    >>> validator.valid('V8X 1g1')
    True
    """
    def __init__(self):
        e = r'^[A-Za-z][0-9][A-Za-z]\s*[0-9][A-Za-z][0-9]$'
        RegexValidator.__init__(self, 'enter a valid postal code', e)


class DateValidator(Validator):
    """Date validator

    >>> v = DateValidator()
    >>> v.valid('asdf')
    False
    >>> v.msg
    'enter valid date in "Jan 31, 2016" format'

    >>> v.valid('Jan 1, 2016')
    True

    >>> v.valid('Jan 41, 2016')
    False

    >>> v.valid('2016-01-14')
    True

    >>> v.valid('2016-01-41')
    False
    """
    def __init__(self, date_format='%b %d, %Y'):
        strftime = datetime.datetime.strftime
        strptime = datetime.datetime.strptime

        def test(date):
            """test for valid date value"""
            if not date:
                return True
            try:
                strptime(date, date_format)
            except ValueError:
                try:
                    strptime(date, '%Y-%m-%d')
                except ValueError:
                    return False
                else:
                    return True
            else:
                return True

        msg = 'enter valid date in "{}" format'.format(strftime(
            datetime.date(2016, 1, 31),
            date_format,
        ))
        Validator.__init__(self, msg, test)


class MinimumLength(Validator):
    """A minimum length validator

    >>> v = MinimumLength(2)
    >>> v.test('')
    False
    >>> v.test(' ')
    False
    >>> v.test('  ')
    False
    >>> v.test('t')
    False
    >>> v.msg
    'minimum length 2'
    >>> v.test('te')
    True

    >>> v = MinimumLength(2, True)
    >>> v.test('')
    True
    >>> v.test(' ')
    True
    >>> v.test('  ')
    True
    >>> v.test('t')
    False
    >>> v.test('te')
    True
    """

    def __init__(self, min_length, empty_allowed=False):

        def test(value):
            """test value meets minimum length"""
            return (
                empty_allowed and value.strip() == ''
                or not len(value.strip()) < min_length
            )
        msg = 'minimum length %s' % min_length

        Validator.__init__(self, msg, test)
        self.min_length = min_length
        self.empty_allowed = empty_allowed


class MinimumValue(Validator):
    """Minimum value validator

    >>> v = MinimumValue(100)
    >>> v.valid(50)
    False
    >>> v.valid(120)
    True
    """
    def __init__(self, min_value, empty_allowed=True):
        def test(value):
            """Test the value"""
            return (
                empty_allowed and value == '' or
                not value < min_value
            )
        msg = 'value must be at least %s' % min_value
        Validator.__init__(self, msg, test)


class MaximumValue(Validator):
    """Maximum value validator

    >>> v = MaximumValue(100)
    >>> v.valid(50)
    True
    >>> v.valid(120)
    False

    >>> from datetime import date
    >>> v = MaximumValue(date(2015,1,1))
    >>> v.valid(date(2015,1,1))
    True
    >>> v.valid(date(2015,1,2))
    False
    >>> v.msg
    'value must be at most 2015-01-01'
    """
    def __init__(self, max_value, empty_allowed=True):
        def test(value):
            """Test the value"""
            return (
                empty_allowed and value == '' or
                not value > max_value
            )
        msg = 'value must be at most %s' % max_value
        Validator.__init__(self, msg, test)


def email_valid(email):
    """test for valid email address

    >>> email_valid('test@testco.com')
    True

    >>> email_valid('test@@testco.com')
    False

    >>> email_valid('test@testco')
    False
    """
    if email == '':
        return True
    email_re = re.compile(
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+"
        r"(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|'
        r'\\[\001-011\013\014\016-\177])*"'  # quoted-string
        r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)'
        r'+[A-Z]{2,6}\.?$', re.IGNORECASE)  # domain
    return bool(email_re.match(email))


def image_mime_type_valid(data):
    """check data against the more commonly browser supported mime types
    """
    accept = ['gif', 'jpeg', 'png', 'xbm', 'bmp']
    if isinstance(data, cgi.FieldStorage) and data.file:
        return imghdr.what('a', data.file.read()) in accept
    if (
            not data or isinstance(data, (str, bytes)) and
            imghdr.what('a', data) in accept
    ):
        return True
    return False


def number_valid(value):
    """Test for valid number

    >>> number_valid(0)
    True
    >>> number_valid(-1)
    True
    >>> number_valid(1.12039123)
    True
    >>> number_valid('1.12039123')
    True
    >>> number_valid('x1.12039123')
    False
    >>> number_valid('t')
    False
    >>> number_valid('')
    True
    >>> number_valid(False) # not sure if this is what's we want
    True
    """
    if value == '':
        return True
    try:
        float(value)
        return True
    except ValueError:
        return False


def latitude_valid(value):
    """test for valid latitude

    >>> latitude_valid(45)
    True

    >>> latitude_valid(100)
    False

    >>> latitude_valid('x')
    False
    """
    if value == '':
        return True
    try:
        v = float(value)
        if v >= -90 and v <= 90:
            return True
        else:
            return False
    except ValueError:
        return False


def longitude_valid(value):
    """test for valid longitude

    >>> longitude_valid(145)
    True

    >>> longitude_valid(200)
    False

    >>> longitude_valid('x')
    False
    """
    if value == '':
        return True
    try:
        v = float(value)
        if v >= -180 and v <= 180:
            return True
        else:
            return False
    except ValueError:
        return False


def empty(value):
    """test if a value is empty

    >>> empty('')
    True

    >>> empty(' ')
    True

    >>> empty('\\n')
    True

    >>> empty('x')
    False

    >>> empty(1)
    False
    """
    try:
        return not value or value.isspace()
    except AttributeError:
        return False

    # return hasattr(value, 'isspace') and value.isspace()


def is_present(value):
    """test if a value is present

    >>> is_present('')
    False

    >>> is_present('x')
    True
    """
    return bool(value) and not empty(value)


# Common Validators
# ----------------------------
# Error messages should suggest what the user needs to do for the value
# to be considered value (i.e. "enter a numeric value").
notnull = Validator("required", bool)
required = Validator("required", is_present)
valid_name = MinimumLength(2)
valid_email = Validator('enter a valid email address', email_valid)
valid_phone = RegexValidator('enter valid phone number', PHONE_RE)
valid_username = RegexValidator('letters and numbers only', USERNAME_RE)
valid_password = MinimumLength(6)
valid_new_password = MinimumLength(8)
valid_url = URLValidator()
valid_postal_code = PostalCodeValidator()
valid_date = DateValidator()
image_mime_type = Validator(
    "provide image in a supported format (gif, jpeg, png)",
    image_mime_type_valid
)
valid_number = Validator("enter a numeric value", number_valid)
valid_latitude = Validator("enter a number between -90 and 90", latitude_valid)
valid_longitude = Validator(
    "enter a number between -180 and 180", longitude_valid
)
