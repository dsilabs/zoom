"""
    profile app model
"""

import zoom.fields as f
import zoom.validators as v


def profile_fields():
    """Return Profile Fields"""
    return f.Fields([
        f.Section('Basic', [
            f.TextField('First Name', v.required),
            f.TextField('Last Name', v.required),
            f.TextField('Username', v.required, size=15),
            f.EmailField('Email'),
            f.PhoneField('Phone'),
            f.TextField('City', size=20),
            f.BasicImageField('Photo'),
        ]),
        f.Section('Locale', [
            f.TimezoneField('Timezone', default='Canada/Pacific'),
        ]),
        f.Section('Social', [
            f.TextField('Web'),
            f.TextField('Blog'),
            f.TextField('Twitter',size=20),
        ]),
        f.Section('Bio', [
            f.MemoField('About You', cols=40, name="about"),
        ]),
    ])


def change_password_fields():
    """Return Change Password Fields"""
    return f.Fields([
        f.PasswordField('Old Password', v.required),
        f.PasswordField('New Password', v.required),
        f.PasswordField('Confirm New Password', v.required),
    ])

def change_photo_fields():
    """Return Change Photo Fields"""
    return f.Fields([
        f.ImageField('Photo', v.required),
    ])