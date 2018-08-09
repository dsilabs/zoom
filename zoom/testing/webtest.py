
# -*- coding: utf-8 -*-

"""
    web tests

    Common functions and classes for WebDriver based system tests

    Note:
        Requires Python packages that are not included in the
        main requiremen.txt file.  To run these types of tests
        you'll need to install the packages listed in
        zoom/tests/requirements.txt

"""

import logging
import os
import time
import unittest
import warnings

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.remote_connection import LOGGER

LOGGER.setLevel(logging.WARNING)

target_cache = {}

class WebdriverTestPrimitives(unittest.TestCase):
    """Webdriver Test Primitives"""

    url = 'http://localhost'
    headless = True
    size = (1024, 768)
    logger = logging.getLogger(__name__)
    path = '.'

    driver_name = os.environ.get('ZOOM_TEST_DRIVER', 'chrome')

    def setUp(self):
        if self.headless:
            self.logger.info('running headless')
            self.display = Display(visible=0, size=self.size)
            self.display.start()
        else:
            self.logger.info('not running headless')

        self.driver = self.get_driver()

    def tearDown(self):
        if self.headless:
            self.display.stop()

        if self.driver_name == 'phantomjs':
            del self.driver
        else:
            self.driver.quit()
            del self.driver

    def check_for_errors(self, text):
        pass

    def get_driver(self):

        driver_name = self.driver_name

        if driver_name == 'chrome':
            chrome_options = Options()
            chrome_options.add_experimental_option('prefs', {
                'credentials_enable_service': False,
                'profile': {
                    'password_manager_enabled': False
                }
            })
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_window_size(*self.size)
            driver.implicitly_wait(10)

        elif driver_name == 'firefox':
            driver = webdriver.Firefox()
            driver.set_window_size(*self.size)
            driver.implicitly_wait(10)

        elif driver_name == 'phantomjs':
            driver = webdriver.PhantomJS()

        return driver

    def get(self, url):
        target = self.url + url
        logger = logging.getLogger(__name__)
        logger.debug('getting: %r', target)
        self.driver.get(target)

    def find(self, target):
        """find an element in the page"""

        def try_method(method, target):
            try:
                logger.debug('trying method %s(%r)', method.__name__, target)
                result = method(target)
                if result:
                    logger.debug('method %s worked!', method.__name__)
                    return result
            except NoSuchElementException:
                return False

        driver = self.driver

        logger = logging.getLogger(__name__)
        logger.debug('finding element: %r', target)

        if target in target_cache:
            target = target_cache[target]

        if target.startswith('link='):
            try:
                result = driver.find_element_by_link_text(target[5:])
                logger.debug('going with %r: %r', target, result)
                return result
            except NoSuchElementException:
                # try lowercase version of link, to work around text-transform bug
                result = driver.find_element_by_link_text(target[5:].lower())
                target_cache[target] = 'link=' + target[5:].lower()
                msg = '   label %s is being cached as %s'
                logger.info(msg, target, target_cache[target])
                return result

        elif target.startswith('//'):
            return driver.find_element_by_xpath(target)

        elif target.startswith('xpath='):
            return driver.find_element_by_xpath(target[6:])

        elif target.startswith('css='):
            return driver.find_element_by_css_selector(target[4:])

        elif target.startswith('id='):
            return driver.find_element_by_id(target[3:])

        elif target.startswith('name='):
            return driver.find_element_by_name(target[5:])

        direct = (
            try_method(driver.find_element_by_name, target)
            or try_method(driver.find_element_by_id, target)
            or try_method(driver.find_element_by_link_text, target)
            or try_method(driver.find_element_by_link_text, target.lower())
        )

        if direct:
            logger.debug('found %r: %r', target, direct)
            return direct

        test_name = unittest.TestCase.id(self)
        driver.save_screenshot('%s-error_screen.png' % test_name)
        raise Exception('Don\'t know how to find %s' % target)

    def type(self, target, text):
        element = self.find(target)
        element.click()
        element.clear()
        element.send_keys(text)

    def fill(self, values):
        for name, value in values.items():
            self.type(name, value)

    def click(self, target):
        try:
            self.find(target).click()
        except WebDriverException:
            test_name = unittest.TestCase.id(self)
            self.driver.save_screenshot('%s-click_error_screen.png' % test_name)
            raise

    def click_and_wait(self, target):
        self.find(target).click()

    def click_link(self, target):
        self.find('link=' + target).click()

    def chosen(self, chosen_field, values):
        logger = logging.getLogger(__name__)
        logger.debug('called chosen: %r %r', chosen_field, values)

        chosen = self.driver.find_element_by_id(chosen_field + '_chosen')
        chosen.click() # populates the results list
        logger.debug('chosen object: %r', chosen)
        results = chosen.find_elements_by_css_selector(".chosen-results li")

        logger.debug('chosen results: %r', results)

        for value in values:
            logger.debug('possible value: %r', value)
            found = False
            for result in results:
                logger.debug('possible result: %r', result.text)
                if result.text == value:
                    logger.debug('matched: %r', result.text)
                    found = True
                    break
            if found:
                chosen.find_element_by_css_selector('input').click()
                result.click()

    def contains(self, text):
        return text in self.driver.page_source

    def assertContains(self, text):
        if not self.contains(text):
            test_name = unittest.TestCase.id(self)
            self.driver.save_screenshot('%s-error_screen.png' % test_name)
            raise Exception('page does not contain {!r})'.format(
                text
            ))

    @property
    def page_source(self):
        return self.driver.page_source


class WebdriverTestCase(WebdriverTestPrimitives):
    """Webdriver Test Base Class"""

    headless = os.environ.get('ZOOM_TEST_HEADLESS', True) != 'False'
    url = os.environ.get('ZOOM_TEST_URL', 'http://localhost:8000')
    credentials = {
        'admin': 'admin',
        'user': 'user',
    }

    def login(self, username, password):
        self.get('/login')
        self.type('username', username)
        self.type('password', password)
        self.click('login_button')

    def logout(self):
        self.get('/logout')

    def as_user(self, username):
        if username in self.credentials:
            self.logout()
            self.login(username, self.credentials[username])
        else:
            raise Exception('test username {!r} unknown'.format(username))


class AdminTestCase(WebdriverTestCase):
    """Webdriver Test Base Classe that runs tests as admin"""

    def setUp(self):
        WebdriverTestCase.setUp(self)
        self.as_user('admin')

    def tearDown(self):
        self.logout()
        WebdriverTestCase.tearDown(self)
