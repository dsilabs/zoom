"""
    login page
"""

import logging

import zoom
from zoom.mvc import DynamicView, Controller, View
from zoom.page import page
from zoom.users import Users
from zoom.tools import redirect_to, load_content
from zoom.components import error
import zoom.html as html


class LoginForm(DynamicView):

    @property
    def registration_link(self):
        if self.user.is_member('a_register'):
            return html.a('New User?', href='/register')
        return ''

    @property
    def forgot_password(self):
        if 'forgot' in self.user.apps:
            return load_content('views/forgot_password.html')
        return ''

    @property
    def remember_me_checkbox(self):
        remember_me = zoom.system.site.config.get('site', 'remember_me', True)
        if remember_me in zoom.utils.POSITIVE:
            return load_content('views/remember_me.html')
        return ''


class LoginView(View):

    def index(self, *a, **k):
        username = k.get('username', '')
        user = self.model.user
        referrer_url = k.get('referrer')
        if referrer_url:
            referrer = html.hidden(
                id="referrer",
                name="referrer",
                value=referrer_url,
            )
        else:
            referrer = ''
        form = LoginForm(username=username, user=user, referrer=referrer)
        return page(form)


class LoginController(Controller):

    def login_button(self, **data):
        logger = logging.getLogger(__name__)
        logger.debug('login_button called')
        site = self.model.site
        username = data.get('username')
        password = data.get('password')
        remember_me = bool(data.get('remember_me'))
        if username and password:
            print(remember_me)
            users = Users(site.db)
            user = users.first(username=username, status='A')
            if user:
                if user.login(self.model, password, remember_me):
                    logger.info('user {!r} sucesfully logged in'.format(username))
                    return redirect_to(user.default_app)
            logger.debug('failed login attempt for user {!r}'.format(username))
            error('incorrect username or password')
        elif username:
            error('password missing')
        else:
            error('username missing')


def main(route, request):
    return (
        LoginController(request)(*route, **request.data) or
        LoginView(request)(*route, **request.data)
    )
