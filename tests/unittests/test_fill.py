"""
    test the fill module
"""

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# It's reasonable in this case.

import datetime
import re
import unittest

from zoom.fill import parts_re, _fill, fill as viewfill

today = datetime.datetime.today()

def date():
    return today

def upper(text):
    return text.upper()

def concat(text1, text2):
    return text1 + text2

def link_to(label, url, *a, **k):
    args = ' '.join(['"%s"' % i for i in a])
    keywords = ' '.join(['%s="%s"' % (n, v) for n, v in k.items()])
    return '<a href="%s" %s %s>%s</a>' % (url, args, keywords, label)

def fill(text, callback):
    return _fill('<z:', '>', text, callback)

helpers = locals()

def filler(text, *args, **keywords):
    """A filler that raises an exception on unknown tag"""
    return helpers[text](*args, **keywords)

def filler2(text, *args, **keywords):
    """A filler that returns None on unknown tag"""
    if text in helpers:
        return helpers[text](*args, **keywords)

def defaultfiller(text, *args, **keywords):
    """A filler that fills a default value if provided on unknown tag"""
    if text in helpers:
        return filler(text, *args, **keywords)
    elif len(args) == 1:
        return str(args[0])

class TestFill(unittest.TestCase):
    """test the fill function"""

    # pylint: disable=too-many-public-methods
    # It's reasonable in this case.

    def test_basic(self):
        self.assertEqual(
            fill('foo bar <Z:Date> end', filler),
            'foo bar %s end' % today
        )

    def test_basic_with_extra_spaces(self):
        self.assertEqual(
            fill('foo bar <Z:Date > end', filler),
            'foo bar %s end' % today
        )
        self.assertEqual(
            fill('foo bar <Z:Date   > end', filler),
            'foo bar %s end' % today
        )

    def test_one_param(self):
        self.assertEqual(
            fill('foo bar <z:upper "Test"> end', filler),
            'foo bar TEST end'
        )

    def stest_complex(self):
        tpl = \
                """foo <z:link_to label="This is some text" """ + \
                """url="www.test.com" action="dothis"> bar"""
        self.assertEqual(
            fill(tpl, filler),
            'foo %s bar' % link_to(
                label='This is some text',
                url="www.test.com",
                action='dothis'
            )
        )
        tpl = 'foo <z:link_to "This is some text" action="dothis"> bar'
        self.assertEqual(
            fill(tpl, filler),
            'foo %s bar' % link_to('This is some text', 'x', action='dothis')
        )

    def test_no_quotes(self):
        def callback(tag, *args, **keywords):
            return '%s %s %s' % (tag, args, keywords)
        self.assertEqual(
            fill("""foo <z:test name=joe> bar""", callback),
            "foo test () {'name': 'joe'} bar"
        )

    def test_missing(self):
        self.assertRaises(
            Exception,
            filler,
            ('foo <z:missing> bar', filler)
        )

    def test_missing_with_default(self):
        self.assertEqual(
            viewfill('foo {{missing "nothing"}} bar', defaultfiller),
            "foo nothing bar"
        )

    def test_missing_with_default_single_quotes(self):
        self.assertEqual(
            viewfill("foo {{missing \'nothing\'}} bar", defaultfiller),
            "foo nothing bar"
        )

    def test_missing_quoted_with_nested_default_single_quotes(self):
        self.assertEqual(
            viewfill('foo "/{{missing \'nothing\'}}" bar', defaultfiller),
            "foo \"/nothing\" bar"
        )

    def test_missing_with_default_no_quotes(self):
        self.assertEqual(
            viewfill('foo {{missing nothing}} bar', defaultfiller),
            "foo nothing bar"
        )

    def test_partially_missing_double_quoted_defaults(self):
        template = """<a href="/{{action \"\"}}{{other \"\"}}">{{title ""}}</a>"""
        values = {'title': 'The Title'}
        self.assertEqual(
            viewfill(template, values.get),
            '<a href="/">The Title</a>'
        )

        values['action'] = 'one'
        self.assertEqual(
            viewfill(template, values.get),
            '<a href="/one">The Title</a>'
        )

        values['other'] = '/two'
        self.assertEqual(
            viewfill(template, values.get),
            '<a href="/one/two">The Title</a>'
        )

    def test_re(self):
        self.assertEqual(
            re.findall(parts_re, 'the name="test"'),
            [('', '', '', '', '', '', '', '', 'the'),
             ('name', 'test', '', '', '', '', '', '', '')]
        )

        self.assertEqual(
            re.findall(parts_re, "the name='test'"),
            [('', '', '', '', '', '', '', '', 'the'),
             ('', '', 'name', 'test', '', '', '', '', '')]
        )

        self.assertEqual(
            re.findall(parts_re, "the name=test"),
            [('', '', '', '', '', '', '', '', 'the'),
             ('', '', '', '', 'name', 'test', '', '', '')]
        )

        self.assertEqual(
            re.findall(parts_re, 'the "test"'),
            [('', '', '', '', '', '', '', '', 'the'),
             ('', '', '', '', '', '', 'test', '', '')]
        )

        self.assertEqual(
            re.findall(parts_re, 'the ""'),
            [('', '', '', '', '', '', '', '', 'the'),
             ('', '', '', '', '', '', '', '', '')]
        )

        self.assertEqual(
            re.findall(parts_re, "the ''"),
            [('', '', '', '', '', '', '', '', 'the'), ('', '', '', '', '', '', '', '', '')]
        )

        self.assertEqual(
            re.findall(parts_re, "the other"),
            [('', '', '', '', '', '', '', '', 'the'),
             ('', '', '', '', '', '', '', '', 'other')]
        )

    def test_partially_missing_single_quoted_defaults(self):
        template = r"""<a href="/{{action ''}}{{other ''}}">{{title ""}}</a>"""
        values = {'title': 'The Title'}
        self.assertEqual(
            viewfill(template, values.get),
            '<a href="/">The Title</a>'
        )

        values['action'] = 'one'
        self.assertEqual(
            viewfill(template, values.get),
            '<a href="/one">The Title</a>'
        )

        values['other'] = '/two'
        self.assertEqual(
            viewfill(template, values.get),
            '<a href="/one/two">The Title</a>'
        )

    def test_surrounded(self):
        self.assertEqual(
            viewfill('{{name}}', dict(name='Joe').get),
            'Joe'
        )
        self.assertEqual(
            viewfill('<p>{{name}}</p>', dict(name='Joe').get),
            '<p>Joe</p>'
        )
        self.assertEqual(
            viewfill('Test\n<p>{{name}}</p>\nother', dict(name='Joe').get),
            'Test\n<p>Joe</p>\nother'
        )

    def test_single_line_only(self):
        self.assertEqual(
            viewfill(
                'Test\n<p>{{name}}</p>\nother',
                dict(name='Joe').get
            ),
            'Test\n<p>Joe</p>\nother')
        self.assertEqual(
            viewfill(
                'Test\n<p>{{name}}</p>\n{{phone}}\nother',
                dict(name='Joe', phone='1234567').get
            ),
            'Test\n<p>Joe</p>\n1234567\nother'
        )
        self.assertEqual(
            viewfill(
                'Test\n{{name}}<br>{{name}}\n',
                dict(name='Joe', phone='1234567').get
            ),
            'Test\nJoe<br>Joe\n'
        )
        self.assertEqual(
            viewfill(
                '{{name}} > {{name}} > {{phone}}',
                dict(name='Joe', phone='1234567').get
            ),
            'Joe > Joe > 1234567'
        )
        self.assertEqual(
            viewfill(
                '{{name}}</p><br>{{name}}\n{{phone}}',
                dict(name='Joe', phone='1234567').get
            ),
            'Joe</p><br>Joe\n1234567'
        )
        self.assertEqual(
            viewfill(
                'Test\n<p>{{name}}</p><br>{{name}}\n{{phone}}\nother',
                dict(name='Joe', phone='1234567').get
            ),
            'Test\n<p>Joe</p><br>Joe\n1234567\nother'
        )

    def test_none(self):
        self.assertEqual(
            fill('foo <z:missing> bar', filler2),
            'foo <z:missing> bar'
        )

    def test_multiple(self):
        tpl1 = 'foo <!-- comm --> bar <Z:Date> and <z:link_to ' + \
                'Static1 "static.com" default="YourSite"> <!--c2--> end'
        t1 = fill(tpl1, filler)
        tpl2 = 'foo <!-- comm --> bar %s and %s <!--c2--> end'
        t2 = tpl2 % (
            date(),
            link_to('Static1', 'static.com', default='YourSite')
        )
        self.assertEqual(t1, t2)

    def test_comments(self):
        t1 = fill('foo <!-- comm --> bar <Z:Date> end', filler)
        t2 = 'foo <!-- comm --> bar %s end' % date()
        self.assertEqual(t1, t2)

    def test_nested_comments(self):
        tpl1 = 'foo <!-- comm <!-- test --> --> bar <Z:Date> comment'
        t1 = fill(tpl1, filler)
        tpl2 = 'foo <!-- comm <!-- test --> --> bar %s comment'
        t2 = tpl2 % filler('date')
        self.assertEqual(t1, t2)

    def test_multiple_comments(self):
        tpl1 = 'foo <!-- comm --> bar <Z:Date>  another <!-- test --> comment'
        t1 = fill(tpl1, filler)
        tpl2 = 'foo <!-- comm --> bar %s  another <!-- test --> comment'
        t2 = tpl2 % filler('date')
        self.assertEqual(t1, t2)
