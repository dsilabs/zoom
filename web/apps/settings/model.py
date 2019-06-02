"""
    settings model
"""

import os

import zoom
import zoom.html as h
import zoom.fields as f
import zoom.validators as v

listdir = os.listdir


theme_comment_options = [
    'name',
    'path',
    'none',
]


def get_theme_options():
    return [''] + sorted(listdir(zoom.system.site.themes_path))


def get_site_settings_form():
    """Creates, initializes and returns the site settings form"""
    form = zoom.forms.Form(
        f.Section('Site', [
            f.TextField('Name', v.required),
            f.TextField('Owner Name'),
            f.EmailField('Owner Email'),
            f.URLField('Owner URL'),
            f.EmailField('Register Email'),
            f.EmailField('Support Email'),
        ]),
        f.ButtonField('Save')
    )
    form.update(zoom.system.site.settings.site)
    return form


def get_theme_settings_form():
    """Creates, initializes and returns the theme settings form"""
    form = zoom.forms.Form(
        f.Section('Theme',[
            f.PulldownField(
                'Name',
                name='theme_name',
                options=get_theme_options()
            ),
            # f.TextField('Template', name='theme_template'),
            f.PulldownField(
                'Comments',
                name='theme_comments',
                options=theme_comment_options
            )
        ]),
        f.ButtonField('Save')
    )
    form.update(zoom.system.site.settings.theme)
    return form


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


def save_site_settings(data):
    """Save site settings"""
    site = zoom.system.site
    site.settings.update('site', data)
    site.settings.save()


def save_theme_settings(data):
    """Save theme settings"""
    site = zoom.system.site
    site.settings.update('theme', data)
    site.settings.save()


def save_mail_settings(data):
    """Save mail settings"""
    site = zoom.system.site
    site.settings.update('mail', data)
    site.settings.save()
