"""
    settings model
"""

import os

import zoom
import zoom.html as h
import zoom.fields as f
import zoom.validators as v


def get_mail_settings_form():
    """Creates, initializes and returns the mail settings form"""
    form = zoom.forms.Form(
        f.Section('Mail', [
            f.TextField('SMTP Host'),
            f.IntegerField('SMTP Port', size=4, default=3309),
            f.TextField('SMTP User'),
            f.TextField('SMTP Password', name='smtp_password'),
            f.URLField('Logo'),
            f.EmailField('From Address', name='from_addr'),
            f.TextField('From Name', name='from_name'),
            f.PulldownField('Delivery', options=['immediate', 'background'])
        ]),
        f.ButtonField('Save')
    )
    form.update(zoom.system.site.settings.mail)
    return form


def save_mail_settings(data):
    site = zoom.system.site
    site.settings.update('mail', data)
    site.settings.save()
