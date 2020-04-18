"""
    system users
"""

import zoom
from zoom.collect import CollectionController, RawSearch
from zoom.models import Group, Groups
from zoom.tools import ensure_listy, is_listy
import zoom.validators as v
import zoom.fields as f

import model


no_app_groups = v.Validator(
    'group names cannot start with a_',
    lambda a: not a.startswith('a_')
)


class SelectionField(f.ChosenMultiselectField):
    """Selects things related to groups"""

    select_layout = '<select data-placeholder="{}" multiple="multiple" style="width: 400px" class="{}" name="{}" id="{}">\n'

    def __init__(self, *args, **kwargs):
        f.ChosenMultiselectField.__init__(self, width=60, *args, **kwargs)

    def _scan(self, t, func):
        if t:
            t = [str(i) for i in ensure_listy(t)]
            result = []
            for option in self.options:
                if len(option) == 2 and is_listy(option):
                    label, value = option
                    if label in t or str(value) in t:
                        result.append(func(option))
                elif option in t:
                    result.append(option)
            return result
        return []

    def display_value(self):
        return ', '.join(self._scan(self.value, lambda a: a[0]))


def group_fields(request):

    user_groups = model.get_user_group_options(request.site)

    fields = f.Fields([
        f.TextField('Name', v.required, v.valid_name, no_app_groups),
        f.TextField('Description', maxlength=60),
        f.PulldownField(
            'Administrators',
            default='administrators',
            name='admin_group_id',
            options=user_groups
        ),
    ])

    db = request.site.db
    admin = model.AdminModel(db)

    if len(request.route) > 2 and request.route[2] not in ['new', 'clear', 'reindex']:
        group_id = int(request.route[2])
    else:
        group_id = None

    include_fields = f.Section('Includes',[
        SelectionField('Subgroups', options=admin.get_subgroup_options(group_id)),
        SelectionField('Users', options=admin.get_user_options()),
    ])

    access_fields = f.Section('Accesses',[
        SelectionField('Roles', options=admin.get_role_options(group_id)),
        SelectionField('Apps', options=admin.get_app_options()),
    ])

    return f.Fields(fields, include_fields, access_fields)

def group_activity_log(group):
    """gathers log information for the group

    Authorization activity related to groups is captured
    by zoom and retreived from the audit_log table.

    Note that system log entries are host specific,
    however, audit logs are not host specific
    as hosts sometimes share authozation databases and
    thus changes in authorizations affect all hosts
    using that database.
    """
    query = """
        select
            app,
            user_id,
            activity,
            subject1,
            subject2,
            timestamp
        from audit_log
        where subject2=%s
        union select
            app,
            user_id,
            activity,
            subject1,
            subject2,
            timestamp
        from audit_log
        where
            activity in (
                "add group",
                "remove group",
                "create group",
                "remove subgroup",
                "add subgroup",
                "delete group",
                "add member",
                "remove member"
            )
            and subject1=%s
        order by timestamp desc
        limit 20
    """
    db = zoom.system.site.db
    items = [
        (
            app,
            zoom.helpers.who(user_id),
            activity,
            subject1,
            subject2,
            timestamp,
            zoom.helpers.when(timestamp)
        ) for app, user_id, activity, subject1, subject2, timestamp in db(query, group.name, group.name)
    ]
    labels = [
        'App',
        'User',
        'Activity',
        'Subject1',
        'Subject2',
        'Timestamp',
        'When'
    ]
    auth_activity = zoom.browse(items, labels=labels)
    return """
    <h2>Recent Authorizations Activity<h2>
    {}
    """.format(auth_activity)

class GroupCollectionView(zoom.collect.CollectionView):

    def index(self, q='', *args, **kwargs):
        """collection landing page"""

        c = self.collection
        user = c.user

        if c.request.route[-1:] == ['index']:
            return zoom.redirect_to('/'+'/'.join(c.request.route[:-1]), **kwargs)

        actions = user.can('create', c) and ['New'] or []

        if q:
            title = 'Selected ' + c.title
            records = c.search(q)
        else:
            title = c.title
            records = c.store.find(type='U')

        authorized = (i for i in records if user.can('read', i))
        items = sorted(authorized, key=c.order)
        num_items = len(items)

        if num_items != 1:
            footer_name = c.title.lower()
        else:
            footer_name = c.item_title.lower()

        if q:
            footer = '{:,} {} found in search of {:,} {}'.format(
                num_items,
                footer_name,
                len(c.store),
                c.title.lower(),
            )
        else:
            footer = '%s %s' % (len(items), footer_name)

        admin_ids = [item.admin_group_id for item in items]
        admin_lookup = {
            group.group_id: zoom.link_to(group.name, 'groups', group.group_id)
            for group in zoom.system.site.groups
            if group.group_id in admin_ids
        }

        for item in items:
            item.administrators = admin_lookup.get(item.admin_group_id, '')

        content = zoom.browse(
            [c.model(i) for i in items],
            labels=c.get_labels(),
            columns=c.get_columns(),
            footer=footer
        )

        return zoom.page(content, title=title, actions=actions, search=q)


    def show(self, key):
        page = super().show(key)
        group = zoom.system.site.groups.get(key)
        if group:
            page.content += group_activity_log(group)
        return page

class GroupCollectionController(CollectionController):

    def before_insert(self, record):
        record['type'] = 'U'

    def after_insert(self, record):
        model.update_group_relationships(record)

    def before_update(self, record):
        record['type'] = 'U'
        model.update_group_relationships(record)


def get_groups_collection(request):

    def user_group(group):
        return group.type == 'U' and not group.name.startswith('a_')

    def get_fields():
        return group_fields(request)

    db = request.site.db
    users = Groups(db)
    labels = 'Name', 'Description', 'Administrators'
    columns = 'link', 'description', 'administrators'
    return model.GroupsCollection(
        get_fields,
        model=Group,
        controller=GroupCollectionController,
        view=GroupCollectionView,
        store=users,
        item_name='group',
        url='/admin/groups',
        filter=user_group,
        columns=columns,
        labels=labels,
        key_name='id',
        search_engine=RawSearch
    )


def main(route, request):
    return get_groups_collection(request)(route, request)
