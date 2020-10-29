
# -*- coding: utf-8 -*-

"""
    web tests

    Common functions and classes for WebDriver based system tests

    Note:
        Requires Python packages that are not included in the
        main requirements.txt file.  To run these types of tests
        you'll need to install the packages listed in
        zoom/tests/requirements.txt

"""
# pragma: no cover

import logging
import os
import unittest

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.support.ui import Select

from zoom.testing.common import get_output_path


LOGGER.setLevel(logging.WARNING)

target_cache = {}

class WebdriverTestPrimitives(unittest.TestCase):
    """Webdriver Test Primitives"""

    url = 'http://localhost'
    headless = True
    size = (1024, 768)
    logger = logging.getLogger(__name__)
    path = '.'
    wait_time = 4

    driver_name = os.environ.get('ZOOM_TEST_DRIVER', 'chrome')

    def setUp(self):
        easyprocess_logger = logging.getLogger('easyprocess')
        easyprocess_logger.setLevel(logging.WARNING)
        urllib3_logger = logging.getLogger('urllib3')
        urllib3_logger.setLevel(logging.WARNING)

        self.driver = self.get_driver()

    def tearDown(self):
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
            if self.headless:
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
            chrome_options.add_experimental_option('prefs', {
                'credentials_enable_service': False,
                'profile': {
                    'password_manager_enabled': False
                }
            })
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_window_size(*self.size)
            driver.implicitly_wait(self.wait_time)

        elif driver_name == 'firefox':
            firefox_options = FirefoxOptions()
            if self.headless:
                firefox_options.headless = True
            driver = webdriver.Firefox(options=firefox_options)
            driver.set_window_size(*self.size)
            driver.implicitly_wait(self.wait_time)

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

        self.save_artifacts()
        raise Exception('Don\'t know how to find %s' % target)

    def type(self, target, text):
        try:
            element = self.find(target)
            element.click()
            element.clear()
            element.send_keys(text)
        except:
            self.save_artifacts()
            raise

    def select(self, target, value):
        try:
            element = self.find(target)
            select = Select(element)
            select.select_by_value(value)
        except:
            self.save_artifacts()
            raise

    def fill(self, values):
        for name, value in values.items():
            element = self.find(name)
            if element.tag_name == 'select':
                self.select(name, value)
            else:
                self.type(name, value)

    def click(self, target):
        try:
            self.find(target).click()
        except WebDriverException:
            self.save_artifacts()
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
            self.save_artifacts()
            msg = 'page does not contain {!r}'.format(text)
            raise self.failureException(msg)

    def assertNotContains(self, text):
        if self.contains(text):
            self.save_artifacts()
            msg = 'page contains {!r}'.format(text)
            raise self.failureException(msg)

    def assertDoesNotContain(self, text):
        return self.assertNotContains(text)

    @property
    def page_source(self):
        return self.driver.page_source

    def save_artifacts(self):
        """Save artifacts of current state"""
        self.save_content()
        self.save_screenshot()

    def save_content(self, filename=None):
        """Save page content to a file

        If filename is provided, the page content will be saved to that
        location.  If not the content will be saved to the artifacts
        directory in a filename starting with the test name, and ending
        with "-content.html".

        This function can be called anytime you wish to save the content
        of the current page.  It is called automatically whenever a
        test fails due to missing content.
        """
        if filename is None:

            join = os.path.join
            test_output_directory = get_output_path()
            if not os.path.isdir(test_output_directory):
                os.mkdir(test_output_directory)

            test_name = unittest.TestCase.id(self)
            filename = join(
                test_output_directory,
                '%s-content.html' % test_name
            )

        print('saving content to %s' % filename)
        with open(filename, 'w') as f:
            f.write(self.driver.page_source)

    def save_screenshot(self, filename=None):
        """Save screenshot image to a file

        If filename is provided, the screenshot will be saved to that
        location.  If not the screenshot will be saved to the artifacts
        directory in a filename starting with the test name, and ending
        with "-screenshot.png".

        This function can be called anytime to save a screenshot
        of the current page.  It is called automatically whenever a
        test fails due to missing content.
        """
        if filename is None:

            join = os.path.join
            test_output_directory = get_output_path()
            if not os.path.isdir(test_output_directory):
                os.mkdir(test_output_directory)

            test_name = unittest.TestCase.id(self)
            filename = join(
                test_output_directory,
                '%s-screenshot.png' % test_name
            )

        print('saving screenshot to %s' % filename)
        self.driver.save_screenshot(filename)


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
