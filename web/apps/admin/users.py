"""
    system users
"""

from zoom.components import success, error
from zoom.collect import Collection, CollectionView, CollectionController
from zoom.context import context
from zoom.forms import Form
from zoom.page import page
from zoom.users import User, Users
from zoom.tools import now, home
import zoom.validators as v
import zoom.fields as f

from fields import UserGroupsField
from model import update_user_groups

def user_fields(request):
    # username_available = Validator('taken', valid_username(db))
    # not_registered = Validator('already registered', email_unknown_test)

    personal_fields = f.Section('Personal',[
        f.TextField('First Name', v.required, v.valid_name),
        f.TextField('Last Name', v.required, v.valid_name),
        # f.TextField('Email', v.required, v.valid_email, not_registered(request)),
        f.EmailField('Email', v.required, v.valid_email),
        f.PhoneField('Phone', v.valid_phone, hint='optional'),
        ])

    account_fields = f.Section('Account',[
        # f.TextField('Username', v.required, v.valid_username, username_available(request)),
        f.TextField('Username', v.required, v.valid_username),
        ])

    security_fields = f.Section('Security', [
        UserGroupsField('Groups', default=['2'], options=request.site.user_groups)
    ])

    return f.Fields(personal_fields, account_fields, security_fields)


def get_reset_password_form(key):
    reset_password_form = Form(
        f.TextField('New Password', v.required),
        f.ButtonField('Save Password', cancel='/admin/users/' + key)
    )
    return reset_password_form


class UserCollectionView(CollectionView):

    def show(self, key):
        page = CollectionView.show(self, key)
        page.actions.insert(0, 'Reset Password')
        user = context.site.users.first(username=key)
        if user.is_active:
            page.actions.insert(0, 'Deactivate')
        else:
            page.actions.insert(0, 'Activate')
        return page

    def reset_password(self, key, **kwargs):
        user = context.site.users.first(username=key)
        if user:
            msg = 'Reset password for %s (%s)<br><br>' % (user.full_name, user.username)
            form = get_reset_password_form(key)
            form.validate(kwargs)
            content = msg + form.edit()
        else:
            content = 'Error locating user %r' % key
        return page(content, title='Reset Password')


class UserCollectionController(CollectionController):

    def before_update(self, record):
        record['status'] = 'A'
        record['updated'] = now()
        record['updated_by'] = self.collection.user._id
        update_user_groups(record)

    def save_password_button(self, key, *args, **data):
        form = get_reset_password_form(key)
        if form.validate(data):
            user = context.site.users.first(username=key)
            if user:
                new_password = form.evaluate()['new_password']
                user.set_password(new_password)
                success('password updated')
                return home('users/' + key)

    def activate(self, key):
        user = context.site.users.first(username=key)
        user.activate()
        user.save()
        return home('users/' + key)

    def deactivate(self, key):
        user = context.site.users.first(username=key)
        user.deactivate()
        user.save()
        return home('users/' + key)


def main(route, request):
    db = request.site.db
    users = Users(db)
    fields = user_fields(request)
    columns = 'link', 'username', 'phone', 'email', 'status', 'updated', 'updated_by'
    return Collection(
        fields,
        model=User,
        view=UserCollectionView,
        controller=UserCollectionController,
        store=users,
        item_name='user',
        columns=columns,
        url='/admin/users'
    )(route, request)
