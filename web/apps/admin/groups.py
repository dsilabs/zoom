"""
    system users
"""

from zoom.components import success, error
from zoom.collect import Collection, CollectionController
from zoom.forms import Form
from zoom.utils import Record
# from zoom.users import User, Users
from zoom.helpers import link_to, url_for
from zoom.records import RecordStore
from zoom.tools import now
import zoom.validators as v
import zoom.fields as f


class Group(Record):

    @property
    def key(self):
        return self._id

    @property
    def url(self):
        """user view url"""
        return url_for('/admin/groups/{}'.format(self.key))

    @property
    def link(self):
        """user as link"""
        return link_to(self.name, self.url)

class Groups(RecordStore):

    def __init__(self, db, entity=Group):
        RecordStore.__init__(
            self,
            db,
            entity,
            name='groups',
            key='id'
            )



def group_fields(request):

    db = request.site.db
    group_options = db('select id, name from groups where type="U"')

    fields = f.Fields([
        f.TextField('Name', v.required, v.valid_name),
        f.RadioField('Type', v.required, options=[('A', 'Application'), ('U', 'User Group')]),
        f.MemoField('Description', v.required),
        f.NumberField('Administrators', options=group_options),
    ])
    return fields


class GroupCollectionController(CollectionController):

    def before_update(self, record):
        pass


def main(route, request):
    db = request.site.db
    users = Groups(db)
    fields = group_fields(request)
    return Collection(
        fields,
        model=Group,
        controller=GroupCollectionController,
        store=users,
        item_name='group',
        url='/admin/groups',
    )(route, request)
