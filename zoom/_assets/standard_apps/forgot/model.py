"""
    forgot model
"""

import logging
import time
import uuid

import zoom
from zoom.alerts import error
from zoom.context import context
from zoom.fill import dzfill
from zoom.mail import send
from zoom.page import page
from zoom.store import Entity, EntityStore
from zoom.tools import load, markdown, redirect_to, load_content, home
from zoom.validators import valid_new_password


class ForgotToken(Entity):

    @property
    def expired(self):
        return time.time() > self.expiry


def user_by_token(token):
    rec = get_tokens().first(token=token)
    if rec:
        return context.site.users.first(email=rec.email)


def get_tokens():
    return EntityStore(context.site.db, ForgotToken)


def valid_token(token):
    rec = get_tokens().first(token=token)
    return rec and not rec.expired


def make_message(token):
    """create a message to send to the user"""
    reset_link = redirect_to('/forgot/reset?token=%s' % token).render(context.request).headers['Location']
    filler = dict(
        site_name=context.site.title,
        reset_link=reset_link,
    ).get
    message = markdown(
        dzfill(
            load('activate.md'),
            filler,
        )
    )
    logger = logging.getLogger(__name__)
    logger.debug('password reset link: %s', reset_link)
    return message


def make_token(email):
    """creates a token and save it for future reference"""
    tokens = get_tokens()
    token = uuid.uuid4().hex
    expiry = time.time() + 3600
    tokens.put(ForgotToken(token=token, expiry=expiry, email=email))
    return token


def initiate_password_reset(email, fake=False):
    """creates and sends a token to the user"""
    token = make_token(email)
    message = make_message(token)
    if fake:
        return message
    if context.site.users.first(email=email, status='A'):
        send(email,'Password reset', message)


def process_reset_request(token, form):

    if not valid_token(token):
        return page(load_content('expired.md'))

    tokens = get_tokens()
    rec = tokens.first(token=token)
    if rec:
        user = context.site.users.first(email=rec.email)
        if user:
            filler = dict(
                username=user.username,
                first_name=user.first_name,
            )
            if context.user.is_admin:
                form.update(
                    dict(
                        new_password='somenewpassword',
                        confirm='somenewpassword',
                    )
                )
            content = load_content('reset.md', **filler) + form.edit()
            return page(content)
        else:
            # no user by that email!
            error('invalid request')
            return redirect_to('/')
    else:
        error('invalid reset request')
        return redirect_to('/')


def reset_password(token, password, confirm):
    """reset the user password"""
    if not valid_token(token):
        return page(load_content('expired.md'))
    if not valid_new_password(password):
        error('Invalid password ({})'.format(valid_new_password.msg))
    elif password != confirm:
        error('Passwords do not match')
    else:
        user = user_by_token(token)
        if user:
            user.set_password(password)
            get_tokens().delete(token=token)
            return home('complete')
        else:
            error('Invalid request')
