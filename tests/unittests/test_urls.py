"""
    test url tools
"""

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# It's reasonable in this case.

import unittest

from zoom.helpers import url_for, link_to
from zoom.context import context

class TestFill(unittest.TestCase):
    """test the fill function"""

    # pylint: disable=too-many-public-methods
    # It's reasonable in this case.
    def setUp(self):
        context.site = lambda: None
        context.site.url = ''

    def test_basic(self):
        self.assertEqual(url_for(), '')
        self.assertEqual(url_for(''), '')
        # self.assertEqual(url_for('/'), '/')
        self.assertEqual(url_for('/', 'home'), '/home')
        self.assertEqual(url_for('/home'), '/home')
        self.assertEqual(url_for('home'), 'home')
        self.assertEqual(url_for('/user', 1234), '/user/1234')

    def test_site_specified_urls(self):
        context.site.url = 'mysite.com/app'
        self.assertEqual(url_for(), '')
        self.assertEqual(url_for(''), '')
        # self.assertEqual(url_for('/'), '/')
        self.assertEqual(url_for('/', 'home'), 'mysite.com/app/home')
        self.assertEqual(url_for('/home'), 'mysite.com/app/home')
        self.assertEqual(url_for('home'), 'home')
        self.assertEqual(url_for('/user', 1234), 'mysite.com/app/user/1234')

    # '<dz:site_url>/home'
    #
    # >>> url_for('/home')
    # '<dz:site_url>/home'
    #
    # >>> url_for('home')
    # 'home'
    #
    # >>> url_for('/user', 1234)
    # '<dz:site_url>/user/1234'
    #
    # >>> url_for('/user', 1234, q='test one', age=15)
    # '<dz:site_url>/user/1234?age=15&q=test+one'
    #
    # >>> url_for('/user', q='test one', age=15)
    # '<dz:site_url>/user?age=15&q=test+one'
    #
    # >>> url_for('/', q='test one', age=15)
    # '<dz:site_url>?age=15&q=test+one'
    #
    # >>> url_for(q='test one', age=15)
    # '?age=15&q=test+one'
    #
    # >>> url_for('https://google.com', q='test one')
    # 'https://google.com?q=test+one'
