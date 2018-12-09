"""
    system users
"""

import zoom
from zoom.audit import audit
from zoom.components import success
from zoom.collect import Collection, CollectionView, CollectionController, RawSearch
from zoom.context import context
from zoom.forms import Form
from zoom.users import User, Users
from zoom.tools import home, now
import zoom.validators as v
import zoom.fields as f

from fields import UserGroupsField
import model

def user_fields(request):
    # username_available = Validator('taken', valid_username(db))
    # not_registered = Validator('already registered', email_unknown_test)

    personal_fields = f.Section('Personal', [
        f.TextField('First Name', v.required, v.valid_name),
        f.TextField('Last Name', v.required, v.valid_name),
        # f.TextField('Email', v.required, v.valid_email, not_registered(request)),
        f.EmailField('Email', v.required, v.valid_email),
        f.PhoneField('Phone', v.valid_phone, hint='optional'),
        ])

    account_fields = f.Section('Account', [
        # f.TextField('Username', v.required, v.valid_username, username_available(request)),
        f.TextField('Username', v.required, v.valid_username),
        ])

    security_fields = f.Section('Security', [
        UserGroupsField(
            'Groups',
            name='memberships',
            default=[2],
            options=model.get_user_group_options(request.site)
        )
    ])

    return f.Fields(personal_fields, account_fields, security_fields)


def get_reset_password_form(key):
    reset_password_form = Form(
        f.TextField('New Password', v.required),
        f.ButtonField('Save Password', cancel='/admin/users/' + key)
    )
    return reset_password_form


def user_activity_logs(user, weeks=12):
    """gathers log information for the user

    The activity logs are comprised of both the user
    activities within the system and the authorization
    activities related to the user as captured in the
    audit logs.

    Note that the system log entries are host specific
    so this app displays the activities for the host
    it is on.  However, audit logs are not host specific
    as hosts sometimes share authozation databases and
    thus changes in authorizations affect all hosts
    using that database.
    """
    recent_weeks = weeks
    max_len = 50
    websafe = zoom.tools.websafe
    today = zoom.tools.today()
    one_week = zoom.tools.one_week
    db = zoom.system.site.db
    when = zoom.helpers.when
    who = zoom.helpers.who

    recently = today - recent_weeks * one_week

    auth_data = db("""
    select *
    from audit_log
    where
        (subject1=%s or subject2=%s) and
        timestamp>=%s
    order by timestamp desc
    limit 20
    """, user.username, user.username, recently)
    labels = 'App', 'User', 'Activity', 'Subject1', 'Subject2', 'When'
    auth_activity = zoom.browse([
        (a[1],who(a[2]),a[3],a[4],a[5],when(a[6])
    ) for a in auth_data], labels=labels)

    activity_data = db("""
        select
            id, timestamp, path, status, address, elapsed, message
        from log
        where
            user_id=%s
            and server=%s
            and timestamp>=%s
        order by timestamp desc
        limit 50
    """,
        user.user_id,
        zoom.system.request.host,
        recently
    )
    labels = (
        'id', 'Path', 'Status', 'Address',
        'When', 'Elapsed', 'Message'
    )
    activity = zoom.browse([
        (
            zoom.helpers.link_to_page(a[0], 'entry', a[0]),
            a[2],
            a[3],
            a[4],
            zoom.helpers.when(a[1]),
            a[5],
            a[6] if a[3] == 'A' else websafe(a[6][:max_len])
    ) for a in activity_data], labels=labels)

    return """
    <h2>Recent Authorizations Activity</h2>
    %s
    <h2>Recent User Activity</h2>
    %s
    """ % (auth_activity, activity)

class UserCollectionView(CollectionView):

    def show(self, key):
        """Show user"""
        user = context.site.users.locate(key)
        if user:
            page = CollectionView.show(self, key)
            page.content += user_activity_logs(user)
            page.actions.insert(0, 'Reset Password')
            if user.is_active:
                page.actions.insert(0, 'Deactivate')
            else:
                page.actions.insert(0, 'Activate')
            return page

    def reset_password(self, key, **kwargs):
        """Show resset password form"""
        user = context.site.users.locate(key)
        if user:
            msg = 'Reset password for %s (%s)<br><br>' % (user.full_name, user.username)
            form = get_reset_password_form(key)
            form.validate(kwargs)
            content = msg + form.edit()
        else:
            content = 'Error locating user %r' % key
        return zoom.page(content, title='Reset Password')

    def _get_recent(self, number):
        c = self.collection
        cmd = """
            select id
            from users
            order by updated desc
            limit %s
        """
        ids = [id for id, in c.store.db(cmd, number)]
        return c.store.get(ids)


class UserCollectionController(CollectionController):

    def before_update(self, record):
        record['status'] = 'A'

    def after_update(self, record):
        model.update_user_groups(record)

    def before_insert(self, record):
        record['status'] = 'A'

    def after_insert(self, record):
        model.update_user_groups(record)

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
        user = zoom.system.site.users.first(username=key)
        if user:
            user.activate()
        return home('users/' + key)

    def deactivate(self, key):
        user = zoom.system.site.users.first(username=key)
        if user:
            user.deactivate()
        return home('users/' + key)

def get_users_collection(request):
    db = request.site.db
    users = Users(db)
    fields = user_fields(request)
    columns = 'link', 'phone', 'email', 'status_text', 'when_updated', 'when_last_seen'
    labels = 'Username', 'Phone', 'Email', 'Status', 'Updated', 'Last Seen'
    return model.AdminCollection(
        fields,
        model=User,
        view=UserCollectionView,
        controller=UserCollectionController,
        store=users,
        item_name='user',
        columns=columns,
        labels=labels,
        url='/admin/users',
        key_name='id',
        search_engine=RawSearch
    )

def main(route, request):
    return get_users_collection(request)(route, request)
