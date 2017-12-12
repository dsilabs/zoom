"""
    admin.mail

    mail queue viewer
"""

import uuid

from zoom.context import context
from zoom.mvc import View, Controller
from zoom.page import page
from zoom.mail import get_mail_store, send
from zoom.browse import browse
import zoom.fields as f
from zoom.forms import Form
from zoom.components import success
from zoom.tools import home

mail_form = Form([
    f.TextField('Recipient', size=60, maxlength=60, default=(context.user.email or 'herb@dynamic-solutions.com')),
    f.TextField('Subject', default='a subject ' + uuid.uuid4().hex),
    f.MemoField('Message', value='this is the message body\n' + uuid.uuid4().hex),
    # f.FileField('Attachment'),
    f.ButtonField('Send'),
    ])


class MyView(View):

    def index(self):
        actions = ['Compose']
        content = '<h2>Waiting</h2>' + browse(get_mail_store(context.site))
        return page(content, title='Mail', actions=actions)

    def compose(self):
        # print(context.site)
        return page(content='Send mail as "{} &lt;{}&gt;"<br><br>{}'.format(
            context.site.mail_from_name,
            context.site.mail_from_addr,
            mail_form.edit(),
        ), title='Send Mail')


class MyController(Controller):

    def send_button(self, *args, **input):

        if mail_form.validate(input):

            if False and 'attachment' in input and hasattr(input['attachment'], 'filename'):
                send(
                    input['recipient'],
                    input['subject'],
                    input['message'],
                    [Attachment(
                        input['attachment'].filename,
                        input['attachment'].file,
                    )],
                )
                message('message sent with attachment')
            else:
                send(input['recipient'], input['subject'], input['message'])
                success('message sent')

            # return page('done')
            return home('mail')

view = MyView()
controller = MyController()
