"""
    zoom test_snippets
"""

import unittest

import zoom

from zoom.snippets import *
from zoom.database import Database

# dbhost  = 'database'
# dbname  = 'test'
# dbuser  = 'testuser'
# dbpass  = 'password'

class TestSnippets(unittest.TestCase):

    def setUp(self):
        site = zoom.system.site = zoom.sites.Site()
        snippets = self.snippets = zoom.snippets.get_snippets(site.db)
        snippets.zap()

    def tearDown(self):
        # snippets.zap()
        pass

    def test_updates(self):

        snippets = self.snippets

        snippets.put(Snippet(name='address', variant='', body='my addr'))
        snippets.put(Snippet(name='phone', variant='', body='my phone'))
        snippets.put(Snippet(name='twitter', variant='', body='my twitter'))
        snippets.put(Snippet(name='notice', variant='', body='my notice'))

        assert(len(snippets.all())==4)

        self.assertEqual(snippet('name'), '')
        self.assertEqual(snippet('address'), 'my addr')
        self.assertEqual(snippet('address'), 'my addr')
        self.assertEqual(snippet('address'), 'my addr')
        self.assertEqual(snippet('address'), 'my addr')
        self.assertEqual(snippet('address'), 'my addr')
        self.assertEqual(snippet('twitter'), 'my twitter')
        self.assertEqual(snippet('twitter'), 'my twitter')
        self.assertEqual(snippet('twitter'), 'my twitter')
        self.assertEqual(snippet('twitter'), 'my twitter')

        s = snippets.first(name='address')
        print(s)
        self.assertEqual(s.impressions, 5)

        s = snippets.first(name='twitter')
        print(s)
        self.assertEqual(s.impressions, 4)

        s = snippets.first(name='name')
        self.assertEqual(s, None)

    def test_many_updates(self):
        snippets = self.snippets
        for name in ['one','two','three','four','five']:
            for variant in ['a','b','c','d','e','f','g']:
                snippets.put(Snippet(
                    name=name,
                    variant=variant,
                    body='my '+name))

        t = len(snippets.all())
        print(snippets.all())

        c = 10
        for n in range(c):
            for name in sorted(['one','two','three','four'], reverse=True):
                for variant in ['a','b','c','d','e','f','g']:
                    self.assertEqual(
                        snippet(
                            name,
                            variant=variant
                        ),
                        'my '+name
                    )

        print(snippets.all())

        s = snippets.first(name='three')
        self.assertEqual(s.impressions, c)

        self.assertEqual(t, len(snippets.all()))


    def test_render(self):

        snippets = self.snippets
        snippets.put(Snippet(name='phone', variant='', body='my phone'))

        template = """

        {{snippet phone}}

        """

        zoom.system.providers = [
            zoom.helpers.__dict__,
        ]
        content = zoom.render.render(template)

        self.assertIn('my phone', content)