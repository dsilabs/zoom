"""
    test tools
"""

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# It's reasonable in this case.

import unittest

import zoom


class TestFill(unittest.TestCase):
    """test the fill function"""

    def test_load_template(self):
        zoom.system.request = zoom.utils.Bunch(site=zoom.sites.Site())
        load = zoom.tools.load_template
        template = load('default')
        self.assertTrue('<html>' in template)

    def test_load_template_source_note_name(self):
        zoom.system.request = zoom.utils.Bunch(site=zoom.sites.Site())
        load = zoom.tools.load_template
        template = load('default')
        self.assertTrue('source: default' in template)

    def test_load_template_source_note_path(self):
        site=zoom.sites.Site()
        site.theme_comments = 'path'
        zoom.system.request = zoom.utils.Bunch(site=site)
        load = zoom.tools.load_template
        template = load('default')
        self.assertFalse('source: default' in template)
        self.assertTrue('source:' in template)
        self.assertTrue('themes/default/default.html' in template)

    def test_load_template_source_none(self):
        site=zoom.sites.Site()
        site.theme_comments = 'none'
        zoom.system.request = zoom.utils.Bunch(site=site)
        load = zoom.tools.load_template
        template = load('default')
        self.assertFalse('source: default' in template)
        self.assertFalse('source:' in template)
        self.assertFalse('themes/default/default.html' in template)

    def test_load_template_mixed_case(self):
        zoom.system.request = zoom.utils.Bunch(site=zoom.sites.Site())
        load = zoom.tools.load_template
        template = load('Default')
        self.assertTrue('<html>' in template)

    def test_load_template_missing(self):
        zoom.system.request = zoom.utils.Bunch(site=zoom.sites.Site())
        load = zoom.tools.load_template
        template = load('notthere')
        self.assertEqual('<!-- template missing -->', template)

    def test_load_template_invalid_path(self):
        zoom.system.request = zoom.utils.Bunch(site=zoom.sites.Site())
        load = zoom.tools.load_template
        self.assertRaises(
            Exception,
            load, '/default'
        )

    def test_load_content(self):
        zoom.system.site = zoom.sites.Site()
        content = zoom.tools.load_content(zoom.tools.zoompath('README'))
        self.assertTrue('<h1 id="zoom">Zoom</h1>' in content)

    def test_load_content_missing(self):
        zoom.system.site = zoom.sites.Site()
        load = zoom.tools.load_content
        self.assertRaises(FileNotFoundError, load, 'noREADME')

    def test_load_template_missing_and_default(self):
        zoom.system.request = zoom.utils.Bunch(site=zoom.sites.Site())
        load = zoom.tools.load_template
        template = load('notthere', 'missing')
        self.assertEqual('missing', template)

    def test_get_template(self):
        zoom.system.site = zoom.sites.Site()
        template = zoom.tools.get_template('default')
        self.assertTrue('<html>' in template)

    def test_get_template_missing(self):
        zoom.system.site = zoom.sites.Site()
        template = zoom.tools.get_template('notthere')
        self.assertTrue('<html>' in template)

    def test_get_default_template_missing(self):
        zoom.system.site = zoom.sites.Site()
        self.assertRaises(
            zoom.exceptions.ThemeTemplateMissingException,
            zoom.tools.get_template, 'default', 'notheme'
        )
