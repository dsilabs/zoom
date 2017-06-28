"""
    forgot index
"""

from zoom.mvc import View, Controller
from zoom.page import page
from zoom.context import context
from zoom.tools import load_content
from zoom.forms import Form
from zoom.fields import EmailField, ButtonField, PasswordField
from zoom.validators import required
from zoom.components import error
from zoom.tools import home

import model


form = Form(
    EmailField('Email', required, name='email', size=30),
    ButtonField('Request Password Reset', name='reset_button', cancel='/login')
)

reset_form = Form(
    PasswordField('New Password', required),
    PasswordField('Confirm', required),
    ButtonField('Reset My Password Now', name='reset_password_button', cancel='/login')
)


class MyView(View):

    def index(self, email=None, submit_button=None):

        if context.user.is_admin:
            form.update(dict(email='joe@testco.com'))

        content = load_content('index.md') + form.edit()
        return page(content)

    def step2(self):
        return page(load_content('step2.md'))

    def reset(self, token=None, **kwargs):
        return model.process_reset_request(token, reset_form)

    def expired(self):
        return page(load_content('expired.md'))

    def complete(self):
        return page(load_content('complete.md'))


class MyController(Controller):

    def reset_button(self, *args, **data):
        if form.validate(data):
            email = form.evaluate()['email']

            if 'testco' in email:
                if context.user.is_admin:
                    content = model.initiate_password_reset(email, fake=True)
                    msg = '<i>This message would be sent to user.</i><hr>'
                    return page(msg + content, title='Password Reset Message')
                else:
                    error('invalid email address')
                    return False

            err = model.initiate_password_reset(email)
            if err:
                error(err)
            else:
                return home('step2')

        error('please enter a valid email address')

    def reset_password_button(self, view, token, new_password="", confirm=""):
        print((view, token, new_password, confirm))
        if reset_form.validate(dict(new_password=new_password, confirm=confirm)):
            return model.reset_password(token, new_password, confirm)


view = MyView()
controller = MyController()
