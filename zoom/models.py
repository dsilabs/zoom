"""
    zoom.models

    common models
"""

import logging


import zoom
from zoom.helpers import link_to, url_for_item, url_for
from zoom.utils import Record
from zoom.records import RecordStore
from zoom.users import Users
from zoom.audit import audit


class Model(zoom.utils.DefaultRecord):
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

    >>> from zoom.utils import Bunch
    >>> zoom.system.site = site = zoom.sites.Site()
    >>> zoom.system.user = zoom.system.site.users.get(1)
    >>> zoom.system.request = Bunch(route=[], app=Bunch(name=__name__))
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
    '<a href="/pat-smith" name="link-to-pat-smith">Pat Smith</a>'

    >>> thing.allows('user', 'edit')
    False
    """

    @property
    def key(self):
        """Return the key"""
        return zoom.utils.id_for(self.name)

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
        group.group_id)
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


class Subgroup(Record):
    pass


class Subgroups(RecordStore):

    def __init__(self, db, entity=Subgroup):
        RecordStore.__init__(
            self,
            db,
            entity,
            name='subgroups',
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
    '<a href="/admin/groups/2" name="link-to-users">users</a>'

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

    >>> groups.first(name='everyone').subgroups
    {2, 3}

    >>> groups.first(name='users').user_ids
    [2]
    >>> {u.username for u in site.users.get(groups.first(name='users').user_ids)}
    {'user'}

    """

    @property
    def group_id(self):
        """Return the group ID"""
        return self._id

    @property
    def key(self):
        """Return the group key"""
        return str(self._id)

    @property
    def url(self):
        """return the group URL"""
        return url_for('/admin/groups/{}'.format(self.key))

    @property
    def link(self):
        """user as link"""
        return link_to(self.name, self.url)

    def allows(self, user, action):
        """access policy"""
        system_groups = ['administrators', 'everyone', 'guests', 'managers', 'users']
        return self.name not in system_groups or action != 'delete'

    def get_users(self):
        """return set of IDs for users that are a member of this group"""
        return get_users(self['__store'].db, self)

    @property
    def users(self):
        """Return list of IDs of users that are part of this group"""
        # TODO:
        # Ideally, this should have returned users as it advertises.  Instead
        # it returns user IDs.  We're introducing the user_ids property below
        # to take the place of this property prior to switching this it
        # over to fixing it so clients from this point forward have a property
        # that returns value consistent with its name.  Plan to do a scan of
        # existing systems before switching this over so we don't break things.
        return self.get_users()

    @property
    def user_ids(self):
        """Return list of user IDs of users that are in the group"""
        return list(self.get_users())

    def add_user(self, user):
        """Add a user to a group"""
        store = self.get('__store')
        members = Members(store.db)
        membership = members.first(group_id=self._id, user_id=user._id)
        if not membership:
            members.put(Member(group_id=self._id, user_id=user._id))

    @property
    def roles(self):
        """Return set of IDs of roles that group can assume"""
        db = self['__store'].db
        my_roles = {
            group_id
            for group_id, in db("""
            select distinct
                groups.id
                from `groups`, subgroups
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
        """Return set of IDs of apps that group can access"""
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
        """Return set of IDs of subgroups that are part of this group"""
        db = self['__store'].db
        my_subgroups = {
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
        return my_subgroups

    @property
    def administrators(self):
        """Returns the administrator group name"""
        store = self['__store']
        admin_group = store.get(self['admin_group_id'])
        if admin_group:
            return admin_group.name
        return 'nothing'

    def add_subgroup(self, subgroup):
        """add a subgroup"""
        db = self['__store'].db
        cmd = """
            insert into subgroups (
                group_id,
                subgroup_id
            ) values (
                %s, %s
            )
        """
        db(cmd, self.group_id, subgroup.group_id)
        audit(
            'add subgroup',
            self.name,
            subgroup.name,
        )

    def remove_subgroup(self, subgroup):
        """remove a subgroup"""
        db = self['__store'].db
        cmd = """
            delete from subgroups where
                group_id=%s and
                subgroup_id=%s
        """
        db(cmd, self.group_id, subgroup.group_id)
        audit(
            'remove subgroup',
            self.name,
            subgroup.name,
        )

    def update_subgroups_by_id(self, subgroup_ids):
        """Post updated group subgroups"""

        updated_subgroups = set(map(int, subgroup_ids))

        logger = logging.getLogger(__name__)
        debug = logger.debug

        debug('updating subgroups: %r', updated_subgroups)

        existing_subgroups = self.subgroups
        debug('existing subgroups: %r', existing_subgroups)

        if updated_subgroups != existing_subgroups:

            group_lookup = {
                group.group_id: group.name
                for group in zoom.system.site.groups
            }

            db = self['__store'].db

            to_remove = existing_subgroups - updated_subgroups
            if to_remove:
                debug('removing subgroups %r from %r', to_remove, self.name)
                cmd = 'delete from subgroups where group_id=%s and subgroup_id in %s'
                db(cmd, self.group_id, to_remove)

                for subgroup_id in to_remove:
                    audit(
                        'remove subgroup',
                        self.name,
                        group_lookup.get(
                            subgroup_id,
                            'unknown (%s)' % subgroup_id,
                        )
                    )

            to_add = updated_subgroups - existing_subgroups
            if to_add:
                debug('adding %r to %r', to_add, self.name)
                cmd = 'insert into subgroups (group_id, subgroup_id) values (%s, %s)'
                sequence = zip([self.group_id] * len(to_add), to_add)
                db.execute_many(cmd, sequence)

                for subgroup_id in to_add:
                    audit(
                        'add subgroup',
                        self.name,
                        group_lookup.get(
                            subgroup_id,
                            'unknown (%s)' % subgroup_id,
                        )
                    )

        else:
            debug('subgroups unchanged')

    def update_supergroups_by_id(self, group_ids, kind):
        """Post updated group supergroups"""

        updated = set(map(int, group_ids))

        logger = logging.getLogger(__name__)
        debug = logger.debug

        debug('updating %s: %r', kind, updated)

        # print(kind)
        existing = getattr(self, kind + 's')
        debug('existing %s: %r', kind, updated)
        # print(updated, existing)

        if updated != existing:

            group_lookup = {
                group.group_id: group.name
                for group in zoom.system.site.groups
            }

            db = self['__store'].db

            to_remove = existing - updated
            if to_remove:
                debug('removing %s %r from %r', kind, to_remove, self.name)
                cmd = 'delete from subgroups where subgroup_id=%s and group_id in %s'
                db(cmd, self.group_id, to_remove)

                for group_id in to_remove:
                    audit(
                        'remove %s' % kind,
                        group_lookup.get(
                            group_id,
                            'unknown (%s)' % group_id,
                        ),
                        self.name
                    )

            to_add = updated - existing
            if to_add:
                debug('adding %s %r to %r', kind, to_add, self.name)
                cmd = 'insert into subgroups (group_id, subgroup_id) values (%s, %s)'
                sequence = zip(to_add, [self.group_id] * len(to_add))
                db.execute_many(cmd, sequence)

                for subgroup_id in to_add:
                    audit(
                        'add %s' % kind,
                        group_lookup.get(
                            subgroup_id,
                            'unknown (%s)' % subgroup_id,
                        ),
                        self.name
                    )

        else:
            debug('%s unchanged', kind)

    def update_apps_by_id(self, app_ids):
        return self.update_supergroups_by_id(app_ids, 'app')

    def update_roles_by_id(self, role_ids):
        return self.update_supergroups_by_id(role_ids, 'role')

    def update_members_by_id(self, user_ids):
        """Post updated group memberships"""

        updated = set(int(id) for id in user_ids)

        logger = logging.getLogger(__name__)
        debug = logger.debug

        db = self['__store'].db

        debug('updating members: %r', updated)

        cmd = 'select user_id from members where group_id=%s'
        existing = set(
            user_id for user_id, in
            db(cmd, self.group_id)
        )
        debug('existing members: %r', existing)

        if updated != existing:

            user_lookup = {
                user.user_id: user.username
                for user in zoom.system.site.users
            }

            to_remove = existing - updated
            if to_remove:
                debug('removing members: %r', to_remove)
                cmd = 'delete from members where group_id=%s and user_id in %s'
                db(cmd, self.group_id, to_remove)

                for user_id in to_remove:
                    audit('remove member', self.name, \
                            user_lookup.get(user_id, 'unknown'))

            to_add = updated - existing
            if to_add:
                debug('adding members: %r', to_add)
                cmd = 'insert into members (group_id, user_id) values (%s, %s)'
                sequence = zip([self.group_id] * len(to_add), to_add)
                db.execute_many(cmd, sequence)

                for user_id in to_add:
                    audit('add member', self.name, \
                            user_lookup.get(user_id, 'unknown'))

        else:
            debug('memberships unchanged')

    def add_apps(self, app_names):
        """Add apps to the group"""
        logger = logging.getLogger(__name__)
        debug = logger.debug
        site = zoom.system.site

        for name in app_names:
            if not site.groups.first(name='a_' + name):
                debug('adding group for app %r', name)
                site.groups.add(name='a_' + name, type='A')
                audit('add app', name)
            supergroup = site.groups.first(name='a_' + name)
            supergroup.add_subgroup(self)

    def remove_apps(self, app_names):
        """Remove apps from the group"""
        site = zoom.system.site
        for name in app_names:
            supergroup = site.groups.first(name='a_' + name)
            if supergroup:
                supergroup.remove_subgroup(self)


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
            isinstance(locator, int) and self.get(locator) or
            isinstance(locator, str) and self.first(name=locator)
        )

    def add(self, name, group_type, description=''):
        """Add a group"""
        debug = logging.getLogger(__name__).debug
        group_id = self.put(
            Group(
                name=name,
                type=group_type,
                description=description,
            )
        )
        debug('created new group %r (%r)', name, group_id)
        audit('create group', name)
        return group_id


class SystemAttachment(Record):
    pass


Attachment = SystemAttachment


def handler(request, handler, *rest):
    request.site.groups = Groups(request.site.db)
    request.site.users = Users(request.site.db)
    return handler(request, *rest)
