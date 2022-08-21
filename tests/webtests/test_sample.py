
# -*- coding: utf-8 -*-

"""
    zoom.tests.webdriver_tests.test_sample

    test sample app functions
"""


from zoom.testing.webtest import AdminTestCase


class SampleTests(AdminTestCase):
    """Sample App"""

    size = (1024, 2048)

    def assertText(self, element, value):
            element = self.find(element)
            self.assertEqual(element.text, value)

    def test_content(self):
        self.get('/sample')
        self.assertContains('<h1 id="sample">Sample</h1>')
        self.assertContains('<h2 id="paragraph-of-text">Paragraph of Text</h2>')
        self.assertContains('Site name: <strong>ZOOM</strong>')
        self.assertContains('{{user_full_name}} : <strong>Admin User</strong>')

    def test_fields_show(self):
        self.get('/sample/fields')
        self.assertContains('joey@dsilabs.ca')
        self.assertContains('Foreign Amount')
        self.assertContains('£121,232.43')
        self.assertEqual(
            self.find('link=joey@dsilabs.ca').text,
            'joey@dsilabs.ca'
        )

    def test_fields_edit(self):
        self.get('/sample/fields/edit')
        self.assertContains('joey@dsilabs.ca')
        self.assertContains('Foreign Amount')
        self.assertContains('121232.43')
        self.assertContains('show-action')
        self.assertContains('edit-action')
        self.assertContains('new-action')

        items = [
            ('id=phone', '2341231234'),
            ('id=email', 'joey@dsilabs.ca'),
            ('id=postal_code', 'V8X 2P2'),
            ('id=twitter', 'dsilabs'),
            ('id=web', 'https://www.dsilabs.ca'),
            ('id=number_of_things', '123'),
            ('id=size', '1.2345'),
            ('id=decimal', '1234132.234'),
            ('id=amount', '12341232.32432'),
            ('id=foreign_amount', '121232.432'),
            ('id=markdown', 'Heading\n====\nmarkdown content'),
        ]

        for locator, value in items:
            self.assertEqual(self.find(locator).get_attribute('value'), value)

    def test_collection(self):
        self.get('/sample/collection')
        self.click('id=new-action')

    def test_common_packages(self):
        self.get('/sample/components')
        self.assertContains('this text was updated by a common package')

    def test_missing(self):
        self.get('/sample/missing')
        self.assertContains('<h1>Page Not Found</h1>')

    def test_parts(self):
        self.get('/sample/parts')
        colors = [
            ('styles', 'pink'),
            ('css', 'green'),
            ('libs', 'chocolate'),
            ('js', 'magenta'),
            ('head', 'coral'),
            ('tail', 'tomato'),
        ]
        for kind, color in colors:
            element = self.find('css=div.component-%s' % color)
            self.assertEqual(
                element.text,
                'component %s makes this %s' % (kind, color)
            )

        colors = [
            ('styles', 'slategray'),
            ('css', 'red'),
            ('libs', 'purple'),
            ('js', 'cyan'),
            ('head', 'navy'),
            ('tail', 'olive'),
        ]
        for kind, color in colors:
            element = self.find('css=div.page-%s' % color)
            self.assertEqual(
                element.text,
                'page %s makes this %s' % (kind, color)
            )

    def test_tools(self):
        self.get('/sample/tools')
        element = self.find('id=time')
        self.assertEqual(element.text, 'Time')

    def test_alerts(self):
        self.get('/sample/alerts')
        self.click('link=Success')
        self.assertContains('that was great!')

        self.get('/sample/alerts')
        self.click('link=Warning')
        self.assertContains('that was close!')

        self.get('/sample/alerts')
        self.click('link=Error')
        self.assertContains('that was bad!')

        self.get('/sample/alerts')
        self.click('link=Stdout')
        self.assertContains('Here is some stdout output!')


class CollectionTests(AdminTestCase):
    """Collection Tests"""

    size = (1024, 2048)

    def assertText(self, element, value):
            element = self.find(element)
            self.assertEqual(element.text, value)

    def test_create_delete(self):
        self.get('/sample/collection')
        self.click('id=new-action')

        self.fill(
            {
                'id=name': 'Jill',
                'id=title': 'Manager',
                'id=date': 'May 1, 2017',
                'id=notes': 'Test for Jill'
            }
        )
        self.click('id=create_button')
        self.assertText('link=Jill', 'Jill')

        self.click('id=new-action')
        self.fill(
            {
                'id=name': 'Jack',
                'id=title': 'Brogrammer',
                'id=date': 'May 31, 2017',
                'id=notes': 'You don\'t know Jack.'
            }
        )
        self.click('id=create_button')
        self.assertText('link=Jack', 'Jack')

        self.assertText('css=div.footer', '2 contacts')

        self.fill(
            {'id=search-text': 'bro'}
        )
        self.click('css=input.search-button')

        self.assertText('css=div.footer', '1 contact found in search of 2 contacts')

        self.assertText('link=Jack', 'Jack')

        self.click('css=img')

        self.assertText('css=div.footer', '2 contacts')

        self.fill(
            {'id=search-text': 'Manager'}
        )
        self.click('css=input.search-button')

        self.assertText('link=Jill', 'Jill')

        self.click('css=img')

        self.fill(
            {'id=search-text': 'mAnaGer'}
        )
        self.click('css=input.search-button')

        self.assertText('link=Jill', 'Jill')
        self.assertText('css=div.footer', '1 contact found in search of 2 contacts')

        self.click('id=new-action')
        self.fill(
            {
                'id=name': 'Pat',
                'id=title': 'Contractor',
                'id=date': 'May 18, 2017',
                'id=notes': 'Nothing known about Pat.'
            }
        )
        self.click('id=create_button')

        self.click('link=Pat')
        self.click('id=edit-action')
        self.type('id=notes', 'Nothing much known about Pat.')
        self.click('id=save_button')
        self.assertText('css=div.textarea', 'Nothing much known about Pat.')

        self.get('/sample/collection')
        self.fill(
            {'id=search-text': 'Noth'}
        )
        self.click('css=input.search-button')
        self.assertText('link=Pat', 'Pat')
        self.assertText('css=div.footer', '1 contact found in search of 3 contacts')
        self.click('css=img')

        self.fill(
            {'id=search-text': 'Cont'}
        )
        self.click('css=input.search-button')
        self.click('link=Pat')
        self.assertText('css=div.field_show', 'Pat')

        self.click('id=delete-action')
        self.assertContains('Are you sure you want to delete')
        self.click('name=delete_button')
        self.assertText('css=div.footer', '2 contacts')

        self.fill(
            {'id=search-text': 'Wednesday'}
        )
        self.click('css=input.search-button')
        self.assertText('link=Jack', 'Jack')
        self.click('link=Jack')
        self.assertText('css=div.field_show', 'Jack')
        self.click('id=delete-action')
        self.assertContains('Are you sure you want to delete')
        self.click('name=delete_button')
        self.assertText('css=div.footer', '1 contact')

        self.click('link=Jill')
        self.assertText('css=div.field_show', 'Jill')
        self.click('id=delete-action')
        self.assertContains('Are you sure you want to delete')
        self.click('name=delete_button')
        self.assertText('css=td', 'None')
