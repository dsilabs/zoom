"""
    login page
"""

import logging

import zoom
from zoom.tools import load_content
from zoom.alerts import error
import zoom.html as html


class LoginForm(zoom.DynamicView):

    @property
    def registration_link(self):
        """returns registration link for new users"""
        if 'register' in self.user.apps:
            return html.a('New User?', href='/register')
        return ''

    @property
    def forgot_password(self):
        """returns link to password recovery app"""
        if 'forgot' in self.user.apps:
            return load_content('views/forgot_password.pug')
        return ''

    @property
    def remember_me_checkbox(self):
        """return Remember Me checkbox"""
        remember_me = zoom.system.site.config.get('site', 'remember_me', True)
        if remember_me in zoom.utils.POSITIVE:
            return load_content('views/remember_me.pug')
        return ''


class LoginView(zoom.View):
    """Login View"""

    def index(self, *args, **kwargs):
        """return index page"""
        username = kwargs.get('username', '')
        user = zoom.get_user()

        referrer_url = kwargs.get('referrer')
        if referrer_url:
            referrer = html.hidden(
                id="referrer",
                name="referrer",
                value=referrer_url,
            )
        else:
            referrer = ''

        original_url = kwargs.get('original_url')
        if original_url:
            origin = html.hidden(
                id="original-url",
                name="original_url",
                value=original_url,
            )
        else:
            origin = ''

        form = LoginForm(
            username=username,
            user=user,
            referrer=referrer,
            origin=origin,
        )

        return zoom.page(form, template='login')


class LoginController(zoom.Controller):
    """Login Controller"""

    def login_button(self, **data):
        """login button control"""
        logger = logging.getLogger(__name__)
        logger.debug('login_button called')

        site = zoom.system.request.site

        username = data.get('username')
        password = data.get('password')
        remember_me = bool(data.get('remember_me'))

        if username and password:
            user = site.users.first(username=username, status='A')
            if user:
                if user.login(zoom.system.request, password, remember_me):
                    logger.info('user %s sucesfully logged in', username)
                    logger.debug(data)
                    if 'original_url' in data:
                        logger.debug('redirecting to %r', data['original_url'])
                        return zoom.redirect_to(data['original_url'])
                    return zoom.redirect_to('/')

            logger.debug('failed login attempt for user %s', username)
            error('incorrect username or password')

        elif username:
            error('password missing')

        else:
            error('username missing')


main = zoom.dispatch(LoginController, LoginView)
