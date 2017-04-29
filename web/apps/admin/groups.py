"""
    system users
"""

from zoom.components import success, error
from zoom.collect import Collection, CollectionController
from zoom.forms import Form
from zoom.helpers import link_to, url_for
from zoom.models import Group, Groups
from zoom.tools import now
import zoom.validators as v
import zoom.fields as f


from model import update_group_members


def group_fields(request):

    fields = f.Fields([
        f.TextField('Name', v.required, v.valid_name),
        f.MemoField('Description'),
        f.PulldownField('Administrators', default='administrators', options=request.site.user_groups),
    ])
    personal_fields = f.Section('Includes',[
        # f.ChosenMultiselectField('Groups', options=request.site.user_groups),
        f.ChosenMultiselectField('Users', options=request.site.user_options),
    ])
    return f.Fields(fields, personal_fields)


class GroupCollectionController(CollectionController):

    def before_insert(self, record):
        record['type'] = 'U'
        update_group_members(record)

    def before_update(self, record):
        record['type'] = 'U'
        update_group_members(record)


def main(route, request):

    def user_group(group):
        return group.type == 'U' and not group.name.startswith('a_')

    db = request.site.db
    users = Groups(db)
    fields = group_fields(request)
    columns = 'link', 'description', 'administrators'
    return Collection(
        fields,
        model=Group,
        controller=GroupCollectionController,
        store=users,
        item_name='group',
        url='/admin/groups',
        filter=user_group,
        columns=columns,
    )(route, request)
