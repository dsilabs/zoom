
# -*- coding: utf-8 -*-

"""
    zoom.tests.selenium.test_admin

    test admin app functions
"""

import logging
import unittest

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options

target_cache = {}

class WebdriverTestCase(unittest.TestCase):
    """A Set of Webdriver Tests"""

    url = 'http://localhost'
    headless = True
    size = (1024, 768)
    logger = logging.getLogger(__name__)
    path = '.'

    def setUp(self):
        if self.headless:
            self.logger.info('running headless')
            self.display = Display(visible=0, size=self.size)
            self.display.start()
        else:
            self.logger.info('not running headless')

        self.driver = self.get_driver()
        self.driver.set_window_size(*self.size)
        self.driver.implicitly_wait(10)

    def tearDown(self):
        if self.headless:
            self.display.stop()

        self.driver.quit()

    def check_for_errors(self, text):
        pass

    def get_driver(self):
        chrome_options = Options()
        chrome_options.add_experimental_option('prefs', {
            'credentials_enable_service': False,
            'profile': {
                'password_manager_enabled': False
            }
        })
        driver = webdriver.Chrome(chrome_options=chrome_options)
        return driver

    def get(self, url):
        self.driver.get(self.url + url)

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
        self.find(target).click()

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
                    found = True
                    break
            if found:
                chosen.find_element_by_css_selector('input').click()
                result.click()


class SystemTests(WebdriverTestCase):
    """MyApp system tests"""

    # headless = False
    url = 'http://localhost:8000'

    def login(self, username, password):
        self.get('/login')
        self.type('username', username)
        self.type('password', password)
        self.click('login_button')

    def logout(self):
        self.get('/logout')

    def add_user(self, first_name, last_name, email, username):
        self.get('/admin')
        self.get('/admin/users')
        self.get('/admin/users/new')
        self.fill(
            dict(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username,
            )
        )
        self.chosen('groups', ['managers'])
        self.click('create_button')

    def delete_user(self, username):
        self.get('/admin')
        self.get('/admin/users')
        self.click_link(username)
        self.click('id=delete-action')
        self.click('name=delete_button')

    def test_admin_login_logout(self):
        self.login('admin', 'admin')
        self.logout()

    def test_admin_add_remove_user(self):
        self.login('admin', 'admin')
        self.add_user('Sally', 'Jones', 'sally@testco.com', 'sally')
        self.delete_user('sally')
        self.logout()
