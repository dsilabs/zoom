"""
    login page
"""

import logging

from zoom.mvc import DynamicView, Controller, View
from zoom.page import page
from zoom.render import render
from zoom.users import Users
from zoom.tools import redirect_to
import zoom.html as html

logger = logging.getLogger(__name__)

class LoginForm(DynamicView):

    @property
    def registration_link(self):
        if self.user.can('register'):
            return html.a('New User?', href='/register')
        return ''

    @property
    def forgot_password(self):
        if self.user.can('forgot'):
            return render('views/forgot_password.html')
        return ''


class LoginView(View):

    def index(self, *a, **k):
        logger.debug('view called')
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
        site = self.model.site
        username = data.get('username')
        password = data.get('password')
        if username and password:
            users = Users(site.db)
            user = users.first(username=username)
            if user:
                if user.login(self.model, password):
                    return redirect_to(user.default_app)


def main(route, request):
    return (
        LoginController(request)(*route, **request.data) or
        LoginView(request)(*route, **request.data)
    )
