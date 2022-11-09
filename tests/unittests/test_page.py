"""
    test page module
"""

import unittest

import zoom


class TestPage(unittest.TestCase):

    def test_page_status_not_provided(self):
        page = zoom.Page('test')
        self.assertEqual(page.status, '200 OK')

    def test_page_status_provided(self):
        page = zoom.Page('page missing', status='404 Not Found')
        self.assertEqual(page.status, '404 Not Found')

        page = zoom.Page('Moved temporarily', status='302 Found')
        self.assertEqual(page.status, '302 Found')

    def test_search_appears_when_empty(self):
        page = zoom.Page('some content', search='')
        self.assertIsNotNone(
            page.header()
        )
