
# -*- coding: utf-8 -*-

"""
    system_test

    MyApp system tests
"""

import os
from os.path import join, dirname

from selenium import webdriver
from siderunner import SeleniumTests


class SystemTests(SeleniumTests):
    """MyApp system tests"""

    headless = True
    path = join(dirname(__file__), 'scripts')
    url = 'http://localhost:8000'

    def get_driver(self):
        driver_name = os.environ.get('ZOOM_TEST_DRIVER', 'chrome')
        if driver_name == 'phantomjs':
            return webdriver.PhantomJS()
        elif driver_name == 'chrome':
            return webdriver.Chrome()
        return None

    def test_sample(self):
        self.run_suite('sample-suite')
