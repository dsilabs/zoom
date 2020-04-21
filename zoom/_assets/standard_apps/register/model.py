"""
    register.model
"""

import datetime
import logging
import time
import uuid

import zoom
import zoom.mail
import zoom.fields as f
import zoom.validators as v


REGISTRATION_TIMEOUT = 3600 # one hour


def load(filename, **kwargs):
    values = dict(
        site_name=zoom.system.site.title,
    )
    values.update(kwargs)
    return zoom.tools.load_content(filename, **values)


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
        logger.debug('no email sent to test account')
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

            zoom.mail.send(recipient, subject, body)
            logger.debug(
                'registration %r',
                dict(
                    recipient=recipient,
                    subject=subject,
                    body=body,
                )
            )

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


def email_registered(email):
    return bool(zoom.system.site.users.find(email=email))


def username_available(username):
    return not bool(zoom.system.site.users.find(username=username))


def register_user(data):

    columns = (
        'username', 'password',
        'first_name', 'last_name', 'email', 'phone'
    )

    data = {k: v for k, v in data.items() if k in columns}

    user = zoom.users.User(**data)
    user.created_by = user.updated_by = zoom.system.request.user._id

    users = zoom.system.site.users
    new_id = users.put(user)

    logger = logging.getLogger(__name__)
    logger.debug(
        'new user %r registration complete',
        new_id,
    )
    return new_id


def confirm_registration(token):
    registration = get_registrations().first(token=token)
    delete_registration(token)
    if registration:
        if registration.expiry < time.time():
            # happens if the user waits too long to validate
            content = load('expired.md')
            fills = dict(register_link=zoom.helpers.url_for('/register'))
            result = zoom.page(content, fills)

        elif email_registered(registration.email):
            # can happen if someone registers using the same email address
            # between the time that we issue the token and when the user gets
            # around to confirming.
            result = zoom.page(load('already_registered.md'))

        elif not username_available(registration.username):
            # can happen if someone registers using the same username
            # between the time that we issue the token and when the user gets
            # around to confirming.
            result = zoom.page(
                load('name_taken.md', username=registration.username)
            )

        else:
            # good to go
            register_user(registration)
            result = zoom.home('thank-you')

        if zoom.system.request.user.is_admin:
            msg = 'registration activated for {}'.format(registration.username)
            zoom.alerts.success(msg)

        return result


def delete_registration(token):
    """Delete a registration record"""
    get_registrations().delete(token=token)
