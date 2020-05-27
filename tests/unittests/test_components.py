"""
    components tests
"""


import unittest

import zoom
from zoom.component import Component


def parts():
    return zoom.system.parts.parts


class TestRender(unittest.TestCase):

    def setUp(self):
        zoom.system.parts = Component()

    def test_html(self):
        self.assertEqual(
            Component('hey').render(),
            'hey'
        )

    def test_html_many(self):
        self.assertEqual(
            Component('hey', 'you').render(),
            'heyyou'
        )

    def test_html_many_with_none(self):
        self.assertEqual(
            Component(None, 'hey', None, 'you', None).render(),
            'heyyou'
        )

    def test_css(self):
        Component(css='testcss').render()
        self.assertEqual(
            parts()['css'],
            ['testcss']
        )

    def test_css_many(self):
        Component(
            Component(css='test1css'),
            Component(css='test2css'),
            Component(css='test3css'),
        ).render()
        self.assertEqual(
            parts()['css'],
            ['test1css', 'test2css', 'test3css']
        )

    def test_css_many_with_none(self):
        Component(
            Component(css='test1css'),
            Component(css=None),
            None,
            Component(css='test3css'),
        ).render()
        self.assertEqual(
            parts()['css'],
            ['test1css', 'test3css']
        )

    def test_js(self):
        Component(js='testjs').render()
        self.assertEqual(
            parts()['js'],
            ['testjs']
        )

    def test_js_many(self):
        Component(
            Component(js='test1js'),
            Component(js='test2js'),
            Component(js='test3js'),
        ).render()
        self.assertEqual(
            parts()['js'],
            ['test1js', 'test2js', 'test3js']
        )

    def test_js_many_with_none(self):
        Component(
            Component(js='test1js'),
            Component(js=None),
            None,
            Component(js='test3js'),
        ).render()
        self.assertEqual(
            parts()['js'],
            ['test1js', 'test3js']        )

    def test_undefined(self):
        Component(other='othertext').render()
        self.assertEqual(
            parts()['other'],
            ['othertext']
        )

    def test_undefined_many(self):
        Component(
            Component(other='test1other'),
            Component(other='test2other'),
            Component(other='test3other'),
        ).render()
        self.assertEqual(
            parts()['other'],
            ['test1other', 'test2other', 'test3other']
        )

    def test_undefined_many_with_none(self):
        Component(
            Component(other='test1other'),
            Component(other=None),
            None,
            Component(other='test3other'),
        ).render()
        self.assertEqual(
            parts()['other'],
            ['test1other', 'test3other']
        )

    def test_mixed(self):
        html = Component(
            Component('test', css='css1', other='test1other'),
            Component(
                'one',
                Component('two', css='css2'),
                other=None,
                css=None
            ),
            None,
            Component('Hey', None, js='testjs'),
        ).render()
        self.assertEqual(
            html, 'testonetwoHey'
        )
        self.assertEqual(
            parts()['css'],
            ['css1', 'css2']
        )
        self.assertEqual(
            parts()['js'],
            ['testjs']
        )
        self.assertEqual(
            parts()['other'],
            ['test1other']
        )

