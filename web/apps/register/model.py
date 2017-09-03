"""
    register.model
"""

import zoom
import zoom.fields as f
import zoom.validators as v


def get_fields():
    return f.Fields([
        f.Section('First, the basics',[
            f.TextField(
                'First Name',
                v.required,
                v.valid_name,
                maxlength=40,
                placeholder='First Name'
            ),
            f.TextField(
                'Last Name',
                v.required,
                maxlength=40,
                placeholder="Last Name"
            ),
            f.EmailField(
                'Email',
                v.required,
                v.valid_email,
                maxlength=60,
                placeholder='Email'
            ),
        ]),
        f.Section('Next, choose a username and password',[
            f.TextField(
                'Username',
                v.required,
                v.valid_username,
                # v.name_available,
                maxlength=50,
                size=30
            ),
            f.PasswordField(
                'Password',
                v.required,
                v.valid_password,
                maxlength=16,
                size=20
            ),
            f.PasswordField(
                'Confirm',
                v.required,
                maxlength=16,
                size=20
            ),
        ]),
    ])

def submit_registration(fields):
    return True
