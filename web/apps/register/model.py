"""
    register.model
"""

import datetime
import logging
import time
import uuid

import zoom
import zoom.fields as f
import zoom.validators as v


REGISTRATION_TIMEOUT = 3600 # one hour


class Registration(zoom.utils.Record):
    """Registration Record"""

    def __init__(self, *args, **kwargs):
        self.token = None
        self.expiry = None
        self.password = None
        zoom.utils.Record.__init__(self, *args, **kwargs)

    @property
    def action(self):
        """Actions that can be performed on a registration record"""
        link_to = zoom.helpers.link_to
        app = zoom.system.request.app
        activate_link = link_to('activate', app.url, self.token, 'confirm')
        delete_link = link_to('delete', app.url, self.token, 'delete')
        return activate_link + ' ' + delete_link

    @property
    def expires(self):
        """Text describing when the registration form expires"""
        diff = self.expiry - time.time()
        if diff > 0:
            suffix = 'from now'
        else:
            suffix = 'ago'
            diff = -diff
        now = datetime.datetime.now()
        then = datetime.datetime.now() + datetime.timedelta(seconds=diff)
        return '{} {}'.format(zoom.tools.how_long(now, then), suffix)


def get_registrations():
    """Return a registration store"""
    return zoom.store.EntityStore(zoom.system.site.db, Registration)


def is_test_account(data):
    """Return True if email is a test email account"""
    email = data.email
    return 'test' in email and (
        email.endswith('@testco.com')
    )


def get_fields():
    """Return registration form fields"""
    return f.Fields([
        f.Section('First, the basics', [
            f.TextField(
                'First Name',
                v.required,
                v.valid_name,
                maxlength=40,
                placeholder='First Name'
            ),
            f.TextField(
                'Last Name',
                v.required,
                maxlength=40,
                placeholder="Last Name"
            ),
            f.EmailField(
                'Email',
                v.required,
                v.valid_email,
                maxlength=60,
                placeholder='Email'
            ),
        ]),
        f.Section('Next, choose a username and password', [
            f.TextField(
                'Username',
                v.required,
                v.valid_username,
                # v.name_available,
                maxlength=50,
                size=30
            ),
            f.PasswordField(
                'Password',
                v.required,
                v.valid_password,
                maxlength=16,
                size=20
            ),
            f.PasswordField(
                'Confirm',
                v.required,
                maxlength=16,
                size=20
            ),
        ]),
    ])


def submit_registration(data):
    """Save registration information"""
    password = zoom.auth.hash_password(data.pop('password'))
    del data['confirm']

    rec = Registration(**data)
    rec.token = token = uuid.uuid4().hex
    rec.expiry = time.time() + REGISTRATION_TIMEOUT
    rec.password = password

    logger = logging.getLogger(__name__)

    if is_test_account(rec):
        logger.warning('no email sent to test account')
        zoom.alerts.warning(
            'test account - registration email will not be sent'
        )
        rec.token = '1234'

    else:
        try:
            abs_url_for = zoom.helpers.abs_url_for
            # site_name = zoom.helpers.site_name
            recipient = rec.email
            template = zoom.tools.load('activate.html')

            body = zoom.render.render(
                template,
                link=abs_url_for('/register/confirm', token),
                site_name=zoom.system.site.title,
            )

            subject = zoom.system.site.title + ' registration'

            # zoom.mail.send(recipient, subject, body)
            logger.debug(
                'registration %r',
                dict(
                    recipient=recipient,
                    subject=subject,
                    body=body,
                )
            )
            print(body)

            logger.info(
                'registration sent to %s with token %s',
                recipient,
                token
            )
        except:
            logger.error(
                'Registration error sending %s to %s',
                token,
                recipient
            )
            raise

    get_registrations().put(rec)

    return True
