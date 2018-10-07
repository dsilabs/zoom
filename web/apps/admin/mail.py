"""
    admin.mail

    mail queue viewer
"""

import uuid

import zoom
from zoom.context import context
from zoom.mvc import View, Controller
from zoom.mail import get_mail_store, send, Attachment
from zoom.browse import browse
import zoom.fields as f
from zoom.forms import Form
from zoom.components import success
from zoom.tools import home
from zoom.alerts import success

mail_form = Form([
    f.TextField('Recipient', size=60, maxlength=60, default=(context.user.email)),
    f.TextField('Subject', default='a subject ' + uuid.uuid4().hex),
    f.MemoField('Message', value='this is the message body\n' + uuid.uuid4().hex),
    # f.FileField('Attachment'),
    f.ButtonField('Send'),
    ])


class MyView(View):

    def index(self):
        actions = ['Compose']
        site = zoom.system.request.site
        mail_settings = '&nbsp;&nbsp;'.join([
            '%s: %s' % (k, v) for k, v in dict(
                host=site.smtp_host,
                user=site.smtp_user,
                port=site.smtp_port,
                passwd=('*' * (len(site.smtp_passwd) - 2)) + site.smtp_passwd[-2:],
            ).items() if v
        ])
        content = mail_settings + '<h2>Waiting</h2>' + browse(get_mail_store(context.site))
        return zoom.page(content, title='Mail', actions=actions)

    def compose(self):
        site = zoom.system.request.site
        return zoom.page(content='Send mail as "{} &lt;{}&gt;"<br><br>{}'.format(
            site.mail_from_name,
            site.mail_from_addr,
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
                success('message sent with attachment')
            else:
                send(input['recipient'], input['subject'], input['message'])
                success('message sent')

            return home('mail')

view = MyView()
controller = MyController()
