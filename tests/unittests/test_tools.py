"""
    test tools
"""

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# It's reasonable in this case.

import unittest

import zoom
import zoom.request


class TestTools(unittest.TestCase):
    """test the tools module"""

    def setUp(self):
        zoom.system.site = zoom.sites.Site()
        zoom.system.request = zoom.utils.Bunch(
            site=zoom.system.site,
            app=zoom.utils.Bunch(templates_paths=[], url='/app1')
        )
        zoom.system.providers = [{}]

    def test_load_template(self):
        load = zoom.tools.load_template
        template = load('default.pug')
        self.assertIn('!!! 5', template)

    def test_load_template_no_app(self):
        del zoom.system.request.app
        load = zoom.tools.load_template
        template = load('default.pug')
        self.assertIn('!!! 5', template)

    @unittest.skip
    def test_load_template_source_note_name(self):
        load = zoom.tools.load_template
        template = load('default')
        self.assertIn('source: default', template)

    @unittest.skip
    def test_load_template_source_note_path(self):
        site = zoom.system.request.site
        site.theme_comments = 'path'
        load = zoom.tools.load_template
        template = load('default')
        self.assertFalse('source: default' in template)
        self.assertTrue('source:' in template)
        self.assertTrue('themes/default/default.html' in template)

    @unittest.skip
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
        template = load('Default.pug')
        self.assertIn('!!! 5', template)

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
        self.assertTrue('README' in content)

    def test_load_content_missing(self):
        load = zoom.tools.load_content
        self.assertRaises(FileNotFoundError, load, 'noREADME')

    def test_load_template_missing_and_default(self):
        load = zoom.tools.load_template
        template = load('notthere', 'missing')
        self.assertEqual('missing', template)

    def test_get_template(self):
        template = zoom.tools.get_template('default')
        self.assertIn('html>', template)

    def test_get_template_missing(self):
        template = zoom.tools.get_template('notthere')
        self.assertIn('html>', template)

    @unittest.skip
    def test_get_default_template_missing(self):
        self.assertRaises(
            zoom.exceptions.ThemeTemplateMissingException,
            zoom.tools.get_template, 'default', 'notheme'
        )

    def test_raw_helpers(self):
        content = "this is a [[raw!site_name-raw]] helper"
        self.assertEqual(
            zoom.tools.restore_helpers(content),
            'this is a {{site_name}} helper'
        )

    def test_websafe(self):
        content = "send a message to <info@{{site_name}}> for assistance"
        self.assertEqual(
            zoom.tools.websafe(content),
            'send a message to &lt;info@[[raw!site_name-raw]]&gt; for assistance'
        )

        content = "<script>alert('nasty code')</script>"
        self.assertEqual(
            zoom.tools.websafe(content),
            '&lt;script&gt;alert(&#39;nasty code&#39;)&lt;/script&gt;'
        )

    def test_htmlquote_as_rendered(self):
        content = "send a message to <info@{{site_name}}> for assistance"
        self.assertEqual(
            zoom.tools.restore_helpers(zoom.tools.htmlquote(content)),
            'send a message to &lt;info@{{site_name}}&gt; for assistance'
        )

    def test_redirect_nowhere(self):
        zoom.system.providers = [{}]
        request = zoom.request.Request({})
        response = zoom.redirect_to().render(request)
        self.assertEqual(
            response.headers['Location'],
            '<dz:abs_site_url><dz:request_path>'
        )

    def test_redirect_path(self):
        request = zoom.request.Request({})
        response = zoom.redirect_to('/test').render(request)
        self.assertEqual(
            response.headers['Location'],
            '<dz:abs_site_url>/test'
        )

    def test_redirect_params(self):
        request = zoom.request.Request({})
        response = zoom.redirect_to(one=1, two=2).render(request)
        self.assertEqual(
            response.headers['Location'],
            '<dz:abs_site_url><dz:request_path>/?one=1&two=2'
        )

    def test_redirect_path_and_params(self):
        request = zoom.request.Request({})
        response = zoom.redirect_to('/test', one=1, two=2).render(request)
        self.assertEqual(
            response.headers['Location'],
            '<dz:abs_site_url>/test?one=1&two=2'
        )

    def test_redirect_root(self):
        request = zoom.request.Request({})
        response = zoom.redirect_to('/').render(request)
        self.assertEqual(
            response.headers['Location'],
            '<dz:abs_site_url>'
        )

    def test_redirect_root_with_params(self):
        request = zoom.request.Request({})
        response = zoom.redirect_to('/', one=1, two=2).render(request)
        self.assertEqual(
            response.headers['Location'],
            '<dz:abs_site_url>/?one=1&two=2'
        )

    def test_home(self):
        request = zoom.request.build('http://localhost/app1')

        self.assertEqual(zoom.system.site.url, '')
        self.assertEqual(request.path, '/app1')
        self.assertEqual(zoom.system.request.app.url, '/app1')

        response = zoom.home().render(request)
        self.assertEqual(
            response.headers['Location'],
            '<dz:abs_site_url>/app1'
        )

        response = zoom.home('page1').render(request)
        self.assertEqual(
            response.headers['Location'],
            '<dz:abs_site_url>/app1/page1'
        )

    def test_home_default(self):
        request = zoom.request.build('http://localhost/test')
        zoom.system.request.app.url = '/'

        self.assertEqual(zoom.system.site.url, '')
        self.assertEqual(request.path, '/test')

        response = zoom.home().render(request)
        self.assertEqual(
            response.headers['Location'],
            '<dz:abs_site_url>'
        )

        response = zoom.home('page1').render(request)
        self.assertEqual(
            response.headers['Location'],
            '<dz:abs_site_url>/page1'
        )

    def test_now(self):
        utc_date = zoom.tools.now()
        self.assertEqual(utc_date.tzinfo, None)
