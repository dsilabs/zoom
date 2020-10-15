"""
    profile index
"""

import zoom

import model


class Layout(zoom.DynamicComponent):
    """Profile Layout"""


class ProfileController(zoom.Controller):
    """Profile Controller"""

    def index(self, *args, **kwargs):

        user = zoom.get_user()
        form = zoom.Form(
            model.profile_fields(),
            zoom.fields.ButtonField('Update Profile')
        )
        form.update(user)

        layout = Layout()

        actions = [
            'Change Password'
        ]

        return zoom.page(
            layout.format(form=form.show()),
            title='Profile',
            # actions=actions
        )

    def change_password(self, **_):
        """Change Password Form"""

        form = zoom.Form(
            model.change_password_fields(),
            zoom.fields.ButtonField('Change Password', cancel='/profile')
        )

        return zoom.page(
            form.edit(),
            title='Change Password'
        )

    def change_photo(self, **_):
        """Change Photo"""

        form = zoom.Form(
            model.change_photo_fields(),
            zoom.fields.ButtonField('Change Photo', cancel='/profile')
        )

        return zoom.page(
            form.edit(),
            title='Change Photo'
        )


main = zoom.dispatch(ProfileController)