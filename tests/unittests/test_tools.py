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

    def test_load_template_missing(self):
        zoom.system.request = zoom.utils.Bunch(site=zoom.sites.Site())
        load = zoom.tools.load_template
        template = load('notthere')
        self.assertEqual('<!-- template missing -->', template)

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
