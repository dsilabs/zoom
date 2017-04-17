"""
    zoom.tools
"""

import datetime

from markdown import Markdown
from zoom.response import RedirectResponse
from zoom.helpers import abs_url_for, url_for_page
from zoom.utils import trim
from zoom.render import apply_helpers

one_day = datetime.timedelta(1)
one_week = one_day * 7
one_hour = datetime.timedelta(hours=1)
one_minute = datetime.timedelta(minutes=1)


def now():
    """Return the current datetime"""
    return datetime.datetime.now()


def today():
    """Return the current date"""
    return datetime.date.today()


def yesterday(any_date=None):
    """Return date for yesterday"""
    return (any_date or today()) - one_day


def tomorrow(any_date=None):
    """Return date for tomorrow"""
    return (any_date or today()) + one_day


def first_day_of_the_month(any_date):
    """returns the first day of the month for any date"""
    return datetime.date(any_date.year, any_date.month, 1)


def last_day_of_the_month(any_date):
    """returns the last day of the month for any date"""
    next_month = any_date.replace(day=28) + datetime.timedelta(days=4)
    return next_month - datetime.timedelta(days=next_month.day)


def first_day_of_next_month(any_date):
    """returns the first day of next month for any date"""
    return last_day_of_the_month(any_date) + one_day


def last_day_of_next_month(any_date):
    """returns the last day of next month for any date"""
    return last_day_of_the_month(first_day_of_next_month(any_date))


def first_day_of_last_month(any_date):
    """Returns the first day of last month for any date"""
    return first_day_of_the_month(last_day_of_last_month(any_date))


def last_day_of_last_month(any_date):
    """Returns the first day of last month for any date"""
    return first_day_of_the_month(any_date) - one_day


def this_month(any_date):
    """Returns date range for last month for any date"""
    return (first_day_of_the_month(any_date), last_day_of_the_month(any_date))


def next_month(any_date):
    """Returns date range for next month for any date"""
    return (first_day_of_next_month(any_date), last_day_of_next_month(any_date))


def last_month(any_date):
    """Returns date range for last month for any date"""
    return (first_day_of_last_month(any_date), last_day_of_last_month(any_date))


def how_long(time1, time2):
    """Returns a string that describes the difference between two times.

    >>> now = now()

    >>> how_long(now, now + 2 * one_day)
    '2 days'

    >>> how_long(now, now + 15 * one_day)
    '2 weeks'

    >>> how_long(now, now + 35 * one_day)
    'over a month'

    >>> how_long(now, now + 361 * one_day)
    'almost a year'

    >>> how_long(now, now + 20 * one_minute)
    '20 minutes'

    """
    #pylint: disable=R0912

    def as_datetime(anytime):
        """Convert value to datetime"""
        if type(anytime) == datetime.datetime:
            return anytime
        elif type(anytime) == datetime.date:
            return datetime.datetime(anytime.year, anytime.month, anytime.day)
        elif anytime == None:
            return None
        else:
            return datetime.datetime.fromtimestamp(anytime)

    diff = as_datetime(time2) - as_datetime(time1)

    if diff.days > 365*2:
        result = 'over %d years' % (diff.days / 365)
    elif diff.days > 365*1.75:
        result = 'almost two years'
    elif diff.days > 365:
        result = 'over a year'
    elif diff.days > 360:
        result = 'almost a year'
    elif diff.days > 60:
        result = 'over %d months' % (diff.days / 30)
    elif diff.days > 30:
        result = 'over a month'
    elif diff.days > 14:
        result = '%d weeks' % (diff.days / 7)
    elif diff.days > 1:
        result = '%d days' % diff.days
    elif diff.days == 1:
        result = '1 day'
    elif diff.seconds > 3600:
        result = '%d hours' % int(diff.seconds / 3600)
    elif diff.seconds > 60:
        result = '%d minutes' % int(diff.seconds / 60)
    elif diff.seconds > 0:
        result = '%d seconds' % int(diff.seconds)
    else:
        result = 'a moment'
    return result

def how_long_ago(anytime):
    """
    Returns a string that describes the difference between any time and now.

    >>> now = now()

    >>> how_long_ago(now - datetime.timedelta(1) * 2)
    '2 days ago'

    >>> how_long_ago(now + 20 * one_minute)
    '19 minutes from now'

    >>> how_long_ago(now - 20 * one_minute)
    '20 minutes ago'

    """
    right_now = now()
    if anytime < right_now:
        return how_long(anytime, right_now) + ' ago'
    else:
        return how_long(right_now, anytime) + ' from now'


def is_listy(obj):
    """test to see if an object will iterate like a list

    >>> is_listy([1,2,3])
    True

    >>> is_listy(set([3,4,5]))
    True

    >>> is_listy((3,4,5))
    True

    >>> is_listy(dict(a=1, b=2))
    False

    >>> is_listy('123')
    False
    """
    return isinstance(obj, (list, tuple, set))


def ensure_listy(obj):
    """ensure object is wrapped in a list if it can't behave like one

    >>> ensure_listy('not listy')
    ['not listy']

    >>> ensure_listy(['already listy'])
    ['already listy']
    """
    return is_listy(obj) and obj or [obj]


def redirect_to(*args, **kwargs):
    """Return a redirect response for a URL."""
    abs_url = abs_url_for(*args, **kwargs)
    return RedirectResponse(abs_url)


def home(view=None):
    """Redirect to application home.

    >>> home().content
    ''
    >>> home('old').headers['Location']
    '<dz:abs_site_url><dz:request_path>/<dz:site_url>/<dz:app_name>/old'

    """
    if view:
        return redirect_to(url_for_page(view))
    return redirect_to(url_for_page())


def unisafe(val):
    """safely convert to unicode"""
    if val is None:
        return u''
    elif isinstance(val, bytes):
        try:
            val = val.decode('utf-8')
        except:
            val = val.decode('Latin-1')
    elif not isinstance(val, str):
        val = str(val)
    return val


def websafe(content):
    """Return htmlquoted version of content"""
    return htmlquote(unisafe(content))


def htmlquote(text):
    """
    Encodes `text` for raw use in HTML.

        >>> htmlquote(u"<'&\\">")
        '&lt;&#39;&amp;&quot;&gt;'

        >>> htmlquote("<'&\\">")
        '&lt;&#39;&amp;&quot;&gt;'
    """
    replacements = (
        ('&', '&amp;'),
        ('<', '&lt;'),
        ('>', '&gt;'),
        ("'", '&#39;'),
        ('"', '&quot;'),
    )
    for replacement in replacements:
        text = text.replace(*replacement)
    return text


def markdown(content):
    """Transform content with markdown
    """
    def make_page_name(text):
        result = []
        for c in text.lower():
            if c in 'abcdefghijklmnopqrstuvwxyz01234567890.-/':
                result.append(c)
            elif c == ' ':
                result.append('-')
        text = ''.join(result)
        if text.endswith('.html'):
            text = text[:-5]
        return text

    def url_builder(label, base, end):
        return make_page_name(label) + '.html'

    extras = ['tables', 'def_list', 'wikilinks', 'toc']
    configs = {'wikilinks': [('build_url', url_builder)]}
    converter = Markdown(extensions=extras, extension_configs=configs)
    return converter.convert(unisafe(trim(content)))


def load(pathname):
    """Load a file into memory"""
    with open(pathname) as reader:
        return reader.read()
    return ''


def load_content(pathname, *args, **kwargs):
    """Load a content file and use it to format parameters
    """
    template = load(pathname)
    if template:
        # content = template.format(*args, **kwargs)
        content = apply_helpers(template, None, [kwargs]).format(*args, **kwargs)
        if pathname.endswith('.md'):
            result = markdown(content)
        else:
            result = content
        return result
    return ''
