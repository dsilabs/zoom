"""
    zoom.mail

    email services
"""

import os
import json
import logging
from smtplib import SMTP
from mimetypes import guess_type
from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

import zoom
from zoom.context import context
from zoom.store import EntityStore
from zoom.tools import ensure_listy, now
from zoom.utils import Record
from zoom.tools import get_template


__all__ = (
    'send',
    'send_as',
    'deliver',
    'Attachment',
)


class AttachmentDataException(Exception):
    """raised when asked to deliver data in background process"""
    pass


class SystemMail(Record):
    """system message"""
    pass


class Attachment(object):
    """Email attachment

    provide either a pathname, or a filename and a pathname, or if sending
    directly a filename and a file-like object.

    """
    # pylint: disable=too-few-public-methods
    def __init__(self, pathname, data=None, mime_type=None):
        self.pathname = pathname
        self.data = data
        self.mimetype = mime_type
        self.filename = os.path.split(pathname)[1]

    def as_tuple(self):
        """partilars required for delivery"""
        if hasattr(self.data, 'read'):
            msg = 'Unable to deliver data directly, use physical file instead'
            raise AttachmentDataException(msg)
        return self.pathname, self.data, self.mimetype

    @property
    def read(self):
        """provides a reader for the data

        if the data is not open, it will be because the user provided only a
        pathanme so we open the file at the pathname and return it"""
        if not self.data:
            self.data = open(self.pathname)
        elif isinstance(self.data, str):
            self.data = open(self.data)
        return self.data.read


def get_mail_store(site):
    """returns the mail store"""
    return EntityStore(site.db, SystemMail)


def format_as_html(text, logo_url):
    template = get_template('email_template')
    return template.format(logo_url=logo_url, message=text)


def display_email_address(email):
    """Make a formatted address (eg: "User Name <username@somewhere.net>"),
       from a tuple (Display name, email address) or a list of tuples.
       If the parameter is a string, it is returned.

       >>> recipients = [('Joe','joe@smith.com'),'sally@smith.com']
       >>> display_email_address(recipients)
       'Joe <joe@smith.com>;sally@smith.com'

    """
    if isinstance(email, (list, tuple)):
        result = []
        for item in email:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                result.append(formataddr(item))
            else:
                result.append(item)
        return ';'.join(result)
    return email


def get_plain_from_html(html):
    """extract plain text from html

    >>> test_html = "<div><h1>Hey<h1><p>This is some text</p></div>"
    >>> get_plain_from_html(test_html)
    'Hey\\nThis is some text'

    """
    # import here to avoid high startup cost
    from html.parser import HTMLParser

    class MyHTMLParser(HTMLParser):
        """custom HTML parser"""
        def __init__(self):
            HTMLParser.__init__(self)
            self.lines = []
        def handle_data(self, data):
            self.lines.append(data)
        def value(self):
            return '\n'.join(self.lines)

    parser = MyHTMLParser()
    parser.feed(html)
    parser.close()
    return parser.value()


def compose(sender, reply_to, recipients, subject, body, attachments, style, logo_url):
    """compose an email message"""

    email = MIMEMultipart()
    email['Subject'] = subject
    email['From'] = formataddr(sender)
    email['To'] = display_email_address(recipients)
    if sender != reply_to:
        email['Reply-To'] = formataddr(reply_to)
    email.preamble = (
        'This message is in MIME format. '
        'You will not see this in a MIME-aware mail reader.\n'
    )
    email.epilogue = ''  # To guarantee the message ends with a newline

    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they
    # want to display.
    msg_alternative = MIMEMultipart('alternative')
    email.attach(msg_alternative)

    # if isinstance(body, str):
    #     body = body.encode('utf8')
    #
    # simple encoding test, we will leave as ascii if possible (readable)
    _char = 'us-ascii'
    try:
        body.encode('ascii')
    except UnicodeDecodeError:
        _char = 'utf8'
    except AttributeError:
        _char = 'utf8'

    # attach a plain text version of the html email
    if style == 'html':
        msg_alternative.attach(
            MIMEText(get_plain_from_html(body), 'plain', _char)
        )
        body = format_as_html(body, logo_url)
    body = MIMEText(body.encode('utf8'), style, _char)
    msg_alternative.attach(body)

    for attachment in attachments or []:
        # Guess the content type based on the file's extension.  Encoding
        # will be ignored, although we should check for simple things like
        # gzip'd or compressed files.

        ctype, encoding = guess_type(attachment.filename)
        if ctype is None or encoding is not None:
            # No guess could be made, or the file is encoded (compressed),
            # so use a generic bag-of-bits type.
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)

        if maintype == 'text' or (
                ctype is not None and
                attachment.filename[-4:].lower() == '.ini'
            ):
            # Note: we should handle calculating the charset
            msg = MIMEText(attachment.read(), _subtype=subtype)
        elif maintype == 'image':
            msg = MIMEImage(attachment.read(), _subtype=subtype)
        elif maintype == 'audio':
            msg = MIMEAudio(attachment.read(), _subtype=subtype)
        else:
            msg = MIMEBase(maintype, subtype)
            msg.set_payload(attachment.read())
            # Encode the payload using Base64
            encoders.encode_base64(msg)

        # Set the filename parameter
        msg.add_header(
            'Content-Disposition',
            'attachment',
            filename=attachment.filename
        )
        email.attach(msg)

    return email.as_string()


def connect(site, get_server, debug=False):
    """connect to the mail server"""
    if site.smtp_host and site.smtp_port:
        server = get_server(site.smtp_host, site.smtp_port)
        if debug:
            server.set_debuglevel(1)
        if site.smtp_user and site.smtp_passwd:
            server.login(site.smtp_user, site.smtp_passwd)

        return server


def disconnect(server):
    """disconnect from the mail server"""
    if server:
        server.quit()


def deliver():
    """deliver mail"""
    # spylint: disable=too-many-locals

    count = 0
    server = connect(context.site, SMTP)
    try:
        mail_store = get_mail_store(context.site)
        mails = mail_store.find(status='waiting')
        for mail in mails:

            sender = json.loads(mail.sender)
            reply_to = json.loads(mail.reply_to) if mail.reply_to else sender
            recipients = json.loads(mail.recipients)
            attachments = [
                Attachment(name, data, mimetype)
                for name, data, mimetype
                in json.loads(mail.attachments) or []
            ]

            email = compose(
                sender,
                reply_to,
                recipients,
                mail.subject,
                mail.body,
                attachments,
                mail.style,
                context.site.mail_logo,
            )

            try:
                sender_address = sender[1]
            except IndexError:
                sender_address = sender

            try:
                server.sendmail(
                    sender_address,
                    [r[1] for r in recipients],
                    email
                )
                mail.status = 'sent'
                count += 1
            except Exception:
                mail.status = 'error'
                raise
            finally:
                mail_store.put(mail)
    finally:
        disconnect(server)

    return count


def expedite(site, sender, recipients, subject, body,
             attachments=None, style='plain'):
    """deliver this email now"""
    logger = logging.getLogger(__name__)

    email = compose(
        get_default_sender(site),
        sender,
        recipients,
        subject,
        body,
        attachments or [],
        style,
        site.mail_logo,
    )

    sender_address = formataddr(sender)

    server = connect(site, SMTP)
    if server:
        try:
            result = server.sendmail(
                sender_address,
                [r[1] for r in recipients],
                email
            )
            if result:
                msg = 'Unable to send email. Please contact administrator.'
                logger.error('Unable to send email: {}'.format(result))
                raise Exception(msg)
            else:
                logger.debug('mail sent successfully')
        finally:
            disconnect(server)
    else:
        logger.error('unable to connect to mail server')

def post(put, sender, recipients, subject,
         body, attachments=None, style='plain'):
    """post an email message for delivery"""
    # pylint: disable=too-many-arguments

    dumps = json.dumps
    mail = SystemMail(
        sender=dumps(sender),
        recipients=dumps(recipients),
        subject=subject,
        body=body,
        attachments=dumps([a.as_tuple() for a in attachments or []]),
        style=style,
        status='waiting',
        created=now(),
    )
    put(mail)


def make_recipients_list(recipients):
    """build a well formed list of recipients

    >>> make_recipients_list('joe@testco.com')
    [('joe@testco.com', 'joe@testco.com')]

    >>> v = make_recipients_list('joe@testco.com;sally@testco.com')
    >>> v == [
    ...     ('joe@testco.com', 'joe@testco.com'),
    ...     ('sally@testco.com', 'sally@testco.com')
    ... ]
    True

    >>> make_recipients_list(['joe@testco.com'])
    [('joe@testco.com', 'joe@testco.com')]

    >>> v = make_recipients_list(
    ...     [
    ...         'joe@testco.com',
    ...         ('Sally', 'sally@testco.com')
    ... ])
    >>> v == [
    ...     ('joe@testco.com', 'joe@testco.com'),
    ...     ('Sally', 'sally@testco.com')
    ... ]
    True

    """
    if isinstance(recipients, str):
        if ';' in recipients:
            recipients = list(zip(recipients.split(';'), recipients.split(';')))
        else:
            recipients = (recipients, recipients)

    recipients = isinstance(recipients, list) and recipients or [recipients]
    # if it's a list we interpret it as a list of addresses since
    # (name, address) pairs are always tuples.

    recipients = ensure_listy(recipients)

    recipients = [isinstance(x, str) and (x, x) or x for x in recipients]
    return recipients


def as_sender_tuple(sender):
    """build a sender tuple

    >>> as_sender_tuple('joe@testco.com')
    ('joe@testco.com', 'joe@testco.com')

    >>> as_sender_tuple(('joe@testco.com', 'joe@testco.com'))
    ('joe@testco.com', 'joe@testco.com')

    >>> as_sender_tuple(['joe@testco.com', 'joe@testco.com'])
    ('joe@testco.com', 'joe@testco.com')
    """
    if isinstance(sender, str):
        return sender, sender
    return tuple(sender)


def send_as(sender, recipients, subject, message, attachments=None):
    """send an email as a specific sender

    >>> zoom.system.site = zoom.sites.Site()
    >>> send_as('a-user@testco.com', 'joe@testco.com', "test", "This is a test")

    This function compares the sender to the default send_from information
    configured for the site, and if they differ it includes a Reply-To header
    in the email message.

    NOTE: Some email providers may flag emails sent using the reply-to header
    as spam or phishing emails.  To send email reliably when the domains of the
    site send_from address differ from the reply-to address domain the system
    must be configured properly.  There is much written on this topic so we
    don't try to cover it here, however here is a useful place to start:

    * https://blog.codinghorror.com/so-youd-like-to-send-some-email-through-code/

    """

    site = context.site
    sender = as_sender_tuple(sender)
    recipients = make_recipients_list(recipients)

    if site.mail_delivery != 'background':
        expedite(site, sender, recipients, subject, message, attachments, 'html')
    else:
        raise Exception('background email processing not yet implemented')
        # put = get_mail_store(site).put
        # post(put, sender, recipients, subject, message, attachments, 'html')


def get_default_sender(site):
    """get default sender (name, address) tuple"""
    sender = (site.mail_from_name, site.mail_from_addr)
    return sender


def send(recipients, subject, message, attachments=None):
    """send an email

    >>> zoom.system.site = zoom.sites.Site()
    >>> send('joe@testco.com', "test", "This is a test")
    """
    sender = get_default_sender(context.site)
    send_as(sender, recipients, subject, message, attachments)
