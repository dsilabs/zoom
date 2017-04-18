
# -*- coding: utf-8 -*-

"""
    system_test

    MyApp system tests
"""

from os.path import join, dirname

from selenium import webdriver
from siderunner import SeleniumTests


class SystemTests(SeleniumTests):
    """MyApp system tests"""

    headless = True
    path = join(dirname(__file__), 'scripts')
    url = 'http://localhost:8000'

    def get_driver(self):
        return webdriver.Chrome()

    def test_overview(self):
        self.run_suite('overview-suite')
