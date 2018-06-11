"""
    system users
"""

from zoom.collect import Collection, CollectionController
from zoom.models import Group, Groups
from zoom.tools import now, ensure_listy, is_listy
import zoom.validators as v
import zoom.fields as f


# from model import update_group_members
import model


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
        f.TextField('Name', v.required, v.valid_name),
        f.MemoField('Description'),
        f.PulldownField(
            'Administrators',
            default='administrators',
            options=user_groups
        ),
    ])

    db = request.site.db
    admin = model.AdminModel(db)

    if len(request.route) > 2 and request.route[2] != 'new':
        group_id = int(request.route[2])
    else:
        group_id = None

    include_fields = f.Section('Includes',[
        SelectionField('Subgroups', options=admin.get_subgroup_options(group_id)),
        SelectionField('Users', options=admin.get_user_options()),
    ])

    access_fields = f.Section('Accesses',[
        SelectionField('Roles', options=admin.get_role_options(group_id)),
        SelectionField('Apps', options=admin.get_app_options(group_id)),
    ])

    return f.Fields(fields, include_fields, access_fields)


class GroupCollectionController(CollectionController):

    def before_insert(self, record):
        record['type'] = 'U'

    def after_insert(self, record):
        model.update_group_relationships(record)

    def before_update(self, record):
        record['type'] = 'U'
        model.update_group_relationships(record)


def main(route, request):

    def user_group(group):
        return group.type == 'U' and not group.name.startswith('a_')

    db = request.site.db
    users = Groups(db)
    fields = group_fields(request)
    columns = 'link', 'description', 'administrators'
    return model.AdminCollection(
        fields,
        model=Group,
        controller=GroupCollectionController,
        store=users,
        item_name='group',
        url='/admin/groups',
        filter=user_group,
        columns=columns,
        key_name='id',
    )(route, request)
