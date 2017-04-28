"""
    system users
"""

from zoom.components import success, error
from zoom.collect import Collection, CollectionController
from zoom.forms import Form
from zoom.users import User, Users
from zoom.tools import now
import zoom.validators as v
import zoom.fields as f

from fields import UserGroupsField
from model import update_members

#
# def not_registered(request):
#     db = request.site.db
#     user_id = len(request.route) > 2 and request.route[2] or None
#     def email_unknown_test(email):
#         print(user_id)
#         cmd = 'select * from users where id<>%s and email=%s'
#         return not bool(db(cmd, user_id, email))
#     return v.Validator('already registered', email_unknown_test)
#
#
# def username_available(request):
#     db = request.site.db
#     user_id = len(request.route) > 2 and request.route[2] or None
#     def username_available_test(username):
#         cmd = 'select * from users where id<>%s and username=%s'
#         return not bool(db(cmd, user_id, username))
#     return v.Validator('taken', username_available_test)
#

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
        UserGroupsField('Groups', options=request.site.user_groups)
    ])

    return f.Fields(personal_fields, account_fields, security_fields)


class UserCollectionController(CollectionController):

    def before_update(self, record):
        record['status'] = 'A'
        record['updated'] = now()
        record['updated_by'] = self.collection.user._id
        update_members(record)


def main(route, request):
    db = request.site.db
    users = Users(db)
    fields = user_fields(request)
    columns = 'link', 'username', 'phone', 'email', 'username', 'status', 'updated', 'updated_by'
    return Collection(
        fields,
        model=User,
        controller=UserCollectionController,
        store=users,
        item_name='user',
        columns=columns,
        url='/admin/users'
    )(route, request)
