"""
    test tools
"""

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# It's reasonable in this case.

import unittest

import zoom


class TestTools(unittest.TestCase):
    """test the tools module"""

    def setUp(self):
        zoom.system.site = zoom.sites.Site()
        zoom.system.request = zoom.utils.Bunch(
            site=zoom.system.site,
            app=zoom.utils.Bunch(templates_paths=[])
        )

    def test_load_template(self):
        load = zoom.tools.load_template
        template = load('default')
        self.assertTrue('<html>' in template)

    def test_load_template_source_note_name(self):
        load = zoom.tools.load_template
        template = load('default')
        self.assertTrue('source: default' in template)

    def test_load_template_source_note_path(self):
        site = zoom.system.request.site
        site.theme_comments = 'path'
        load = zoom.tools.load_template
        template = load('default')
        self.assertFalse('source: default' in template)
        self.assertTrue('source:' in template)
        self.assertTrue('themes/default/default.html' in template)

    def test_load_template_source_none(self):
        site = zoom.system.request.site
        site.theme_comments = 'none'
        load = zoom.tools.load_template
        template = load('default')
        self.assertFalse('source: default' in template)
        self.assertFalse('source:' in template)
        self.assertFalse('themes/default/default.html' in template)

    def test_load_template_mixed_case(self):
        load = zoom.tools.load_template
        template = load('Default')
        self.assertTrue('<html>' in template)

    def test_load_template_missing(self):
        load = zoom.tools.load_template
        template = load('notthere')
        self.assertEqual('<!-- template missing \'notthere.html\' -->', template)

    def test_load_template_invalid_path(self):
        load = zoom.tools.load_template
        self.assertRaises(
            Exception,
            load, '/default'
        )

    def test_load_content(self):
        content = zoom.tools.load_content(zoom.tools.zoompath('README'))
        self.assertTrue('<h1 id="zoom">Zoom</h1>' in content)

    def test_load_content_missing(self):
        load = zoom.tools.load_content
        self.assertRaises(FileNotFoundError, load, 'noREADME')

    def test_load_template_missing_and_default(self):
        load = zoom.tools.load_template
        template = load('notthere', 'missing')
        self.assertEqual('missing', template)

    def test_get_template(self):
        template = zoom.tools.get_template('default')
        self.assertTrue('<html>' in template)

    def test_get_template_missing(self):
        template = zoom.tools.get_template('notthere')
        self.assertTrue('<html>' in template)

    def test_get_default_template_missing(self):
        self.assertRaises(
            zoom.exceptions.ThemeTemplateMissingException,
            zoom.tools.get_template, 'default', 'notheme'
        )
