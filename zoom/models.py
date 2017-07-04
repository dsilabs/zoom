"""
    zoom.models

    common models
"""

from zoom.utils import DefaultRecord, id_for
from zoom.helpers import link_to, url_for_item, url_for
from zoom.utils import Record, id_for
from zoom.records import RecordStore
from zoom.users import Users


class Model(DefaultRecord):
    """Model Superclass

    Provide basic model properties and functions.

    Subclass this to create a Model that can be stored in
    a RecordStore, EntityStore or some other type of store.

    Assumes every record has an id attribute.  If not, you
    will need to provide one via an additional property
    defined in the subclass.

    The key can end up being just the str of the id, however
    it is provided separately to make it easy to provide human
    friendly keys typically used in REST style URLs.  If used
    this way the key should generated such that it is unique
    for each record.
    """

    @property
    def key(self):
        """Return the key"""
        return id_for(self.name)

    @property
    def url(self):
        """Return a valid URL"""
        return url_for_item(self.key)

    @property
    def link(self):
        """Return a link"""
        return link_to(self.name, self.url)

    def allows(self, user, action):
        return False


def get_users(db, group):
    my_users = [
        str(user_id)
        for user_id, in db("""
        select distinct
            users.id
            from users, members
            where
                users.id = members.user_id
                and group_id = %s
        """,
        group._id)
    ]
    return my_users


class Member(Record):
    pass


class Members(RecordStore):

    def __init__(self, db, entity=Member):
        RecordStore.__init__(
            self,
            db,
            entity,
            name='members',
            key='id'
            )


class Group(Record):

    @property
    def key(self):
        return str(self._id)

    @property
    def url(self):
        """user view url"""
        return url_for('/admin/groups/{}'.format(self.key))

    @property
    def link(self):
        """user as link"""
        return link_to(self.name, self.url)

    def allows(self, user, action):
        system_groups = ['administrators', 'everyone', 'guests', 'managers', 'users']
        return (
            self.name not in system_groups or action != 'delete'
        )

    def get_users(self):
        store = self.get('__store')
        if store:
            return get_users(store.db, self)
        return []

    @property
    def users(self):
        return self.get_users()

    def add_user(self, user):
        store = self.get('__store')
        members = Members(store.db)
        membership = members.first(group_id=self._id, user_id=user._id)
        if not membership:
            members.put(Member(group_id=self._id, user_id=user._id))


class Groups(RecordStore):

    def __init__(self, db, entity=Group):
        RecordStore.__init__(
            self,
            db,
            entity,
            name='groups',
            key='id'
            )

    def locate(self, locator):
        """locate a group whether it is referred to by reference, id or name"""
        return (
            isinstance(locator, Group) and locator or
            type(locator) == int and self.get(locator) or
            type(locator) == str and self.first(name=locator)
        )


def get_user_groups(site):
    return list(
        (name, str(id)) for name, id in
        site.db('select name, id from groups where type="U" order by name')
    )

def get_user_options(site):
    return list(
        (user.link, str(user._id)) for user in Users(site.db)
    )

def handler(request, handler, *rest):
    request.site.groups = Groups(request.site.db)
    request.site.users = Users(request.site.db)
    request.site.user_groups = get_user_groups(request.site)
    request.site.user_options = get_user_options(request.site)
    return handler(request, *rest)
