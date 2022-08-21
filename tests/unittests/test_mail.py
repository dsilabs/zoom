"""
    test_mail
"""
import datetime
import unittest
from unittest import mock

import zoom
from zoom.request import Request
from zoom.site import Site
import zoom.mail as mail


def mocked_time():
    """return a mocked time"""
    return datetime.datetime(2017, 10, 27, 22, 54, 56, 566179)


class TestMail(unittest.TestCase):

    def test_make_recipients_list(self):
        self.assertEqual(
            mail.make_recipients_list('joe@testco.com'),
            [('joe@testco.com', 'joe@testco.com')]
        )

        self.assertEqual(
            mail.make_recipients_list(['joe@testco.com']),
            [('joe@testco.com', 'joe@testco.com')]
        )

        self.assertEqual(
            mail.make_recipients_list('joe@testco.com;sally@testco.com'),
            [
                ('joe@testco.com', 'joe@testco.com'),
                ('sally@testco.com', 'sally@testco.com'),
            ]
        )

        self.assertEqual(
            mail.make_recipients_list([
                'joe@testco.com',
                ('Sally', 'sally@testco.com'),
            ]), [
                ('joe@testco.com', 'joe@testco.com'),
                ('Sally', 'sally@testco.com'),
            ]
        )

        self.assertEqual(
            mail.make_recipients_list(
                'joe@testco.com;jim@testco.com;sally@testco.com'
            ), [
                ('joe@testco.com', 'joe@testco.com'),
                ('jim@testco.com', 'jim@testco.com'),
                ('sally@testco.com', 'sally@testco.com'),
            ]
        )

    def test_get_default_sender(self):
        site = zoom.sites.Site()
        self.assertEqual(
            mail.get_default_sender(site),
            ('ZOOM Support', 'alerts@testco.com')
        )

    @mock.patch('zoom.mail.now', side_effect=mocked_time)
    def test_post(self, _):
        site = Site(Request({}))
        site.name = 'Testco'
        data = []
        self.assertEqual(
            mail.post(
                data.append,
                ('Testco', 'sender@testco.com'),
                'sally@testco.com',
                'The Subject',
                'The Body'
            ),
            None
        )
        self.assertEqual(
            data,
            [
                {
                    'attachments': "[]",
                    'body': 'The Body',
                    'created': mocked_time(),
                    'style': 'plain',
                    'status': 'waiting',
                    'subject': 'The Subject',
                    'recipients': '"sally@testco.com"',
                    'sender': '["Testco", "sender@testco.com"]'
                }
            ]
        )

    def test_display_email_address(self):
        self.assertEqual(
            mail.display_email_address('joe@smith.com'),
            'joe@smith.com'
        )
        self.assertEqual(
            mail.display_email_address([('Joe', 'joe@smith.com')]),
            'Joe <joe@smith.com>'
        )
        self.assertEqual(
            mail.display_email_address([('Joe', 'joe@smith.com'), 'sally@smith.com']),
            'Joe <joe@smith.com>;sally@smith.com'
        )
        self.assertEqual(
            mail.display_email_address([('joe@smith.com'), 'sally@smith.com']),
            'joe@smith.com;sally@smith.com'
        )


    def test_get_plain_from_html(self):
        test_html = "<div><h1>Hey<h1><p>This is some text</p></div>"
        self.assertEqual(
            mail.get_plain_from_html(test_html),
            'Hey\nThis is some text',
        )

    def test_compose_plain(self):
        #  just make sure it composes without an error
        t = mail.compose(
                ['Testco', 'sender@testco.com'],
                ['Testco', 'sender@testco.com'],
                'sally@testco.com',
                'The Subject',
                'The Body',
                [],
                'plain',
                'https://testco.com/logo.png'
            )
        print(t)
        assert t
        assert 'MIME-Version: 1.0' in t
        assert 'Subject: The Subject' in t
        assert 'From: Testco <sender@testco.com>' in t
        assert 'To: sally@testco.com' in t
        assert 'https://testco.com/logo.png' not in t

    def test_compose_html(self):
        #  just make sure it composes without an error
        t = mail.compose(
                ['Testco', 'sender@testco.com'],
                ['Testco', 'sender@testco.com'],
                'sally@testco.com',
                'The Subject',
                'The Body',
                [],
                'html',
                'https://testco.com/logo.png'
            )
        print(t)
        assert t
        assert 'MIME-Version: 1.0' in t
        assert 'Subject: The Subject' in t
        assert 'From: Testco <sender@testco.com>' in t
        assert 'To: sally@testco.com' in t
        assert 'https://testco.com/logo.png' in t

    def test_compose_reply_to_html(self):
        #  just make sure it composes without an error
        t = mail.compose(
                ['Testco', 'sender@testco.com'],
                ['Testco User', 'user@testco.com'],
                'sally@testco.com',
                'The Subject',
                'The Body',
                [],
                'html',
                'https://testco.com/logo.png'
            )
        print(t)
        assert t
        assert 'MIME-Version: 1.0' in t
        assert 'Subject: The Subject' in t
        assert 'From: Testco <sender@testco.com>' in t
        assert 'To: sally@testco.com' in t
        assert 'Reply-To: Testco User <user@testco.com>' in t
        assert 'https://testco.com/logo.png' in t

    def test_expedite(self):
        pass

    def test_deliver(self):
        pass

    def test_format_as_html(self):
        pass

    def test_attachment(self):
        pass
