"""
    zoom.models

    common models
"""

import zoom
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

    >>> zoom.system.site = site = zoom.sites.Site()
    >>> zoom.system.request = zoom.utils.Bunch(route=[])
    >>> class MyModel(Model):
    ...     pass
    >>> thing = MyModel(name='Pat Smith')

    >>> thing.name
    'Pat Smith'

    >>> thing.key
    'pat-smith'

    >>> url_for_item('pat-smith')
    '/pat-smith'

    >>> thing.url
    '/pat-smith'

    >>> thing.link
    '<a href="/pat-smith">Pat Smith</a>'

    >>> thing.allows('user', 'edit')
    False
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
    """Get users of a Group

    Gets the users that are members of a group from a given database.

    >>> site = zoom.sites.Site()
    >>> users_group = Groups(site.db).first(name='users')
    >>> get_users(site.db, users_group)
    {2}
    """
    my_users = {
        user_id
        for user_id, in db("""
        select distinct
            users.id
            from users, members
            where
                users.id = members.user_id
                and group_id = %s
        """,
        group._id)
    }
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
    """Zoom Users Group

    >>> zoom.system.site = site = zoom.sites.Site()
    >>> groups = Groups(site.db)
    >>> group = groups.first(name='users')

    >>> user = site.users.first(username='admin')
    >>> group.allows(user, 'edit')
    True

    >>> group.key
    '2'

    >>> group.url
    '/admin/groups/2'

    >>> group.link
    '<a href="/admin/groups/2">users</a>'

    >>> group.roles
    {4}

    >>> zoom.utils.pp(group.apps)
    {
      10,
      12,
      20,
      28,
      29
    }

    >>> groups.first(name='everyone').subroups

    """

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
        return self.name not in system_groups or action != 'delete'

    def get_users(self):
        return get_users(self['__store'].db, self)

    @property
    def users(self):
        """Return list of users that are part of this group"""
        return self.get_users()

    def add_user(self, user):
        store = self.get('__store')
        members = Members(store.db)
        membership = members.first(group_id=self._id, user_id=user._id)
        if not membership:
            members.put(Member(group_id=self._id, user_id=user._id))

    @property
    def roles(self):
        db = self['__store'].db
        my_roles = {
            group_id
            for group_id, in db("""
            select distinct
                groups.id
                from groups, subgroups
                where
                    groups.id = subgroups.group_id
                    and subgroup_id = %s
                    and groups.type = 'U'
            """,
            self._id)
        }
        return my_roles

    @property
    def apps(self):
        """Return set of apps that group can access"""
        db = self['__store'].db
        my_apps = {
            group_id
            for group_id, in db("""
            select distinct
                group_id
                from subgroups, groups
                where
                    groups.id = subgroups.group_id
                    and subgroup_id = %s
                    and groups.type = 'A'
            """,
            self._id)
        }
        return my_apps

    @property
    def subgroups(self):
        """Return set of subgroups that are part of this group"""
        db = self['__store'].db
        my_apps = {
            group_id
            for group_id, in db("""
            select distinct
                subgroup_id
                from subgroups, groups
                where
                    id = group_id
                    and group_id = %s
                    and groups.type = 'U'
            """,
            self._id)
        }
        return my_apps


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


class SystemAttachment(Record):
    pass


Attachment = SystemAttachment


def handler(request, handler, *rest):
    request.site.groups = Groups(request.site.db)
    request.site.users = Users(request.site.db)
    return handler(request, *rest)
