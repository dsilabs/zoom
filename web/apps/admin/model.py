"""
    admin model
"""

import logging

import zoom
from zoom.context import context
from zoom.tools import today
from zoom.users import Users
from zoom.models import Groups


def get_user_group_options(site):
    groups = Groups(site.db)
    user_groups = list(sorted(
        (group.link, group.key)
        for group in groups.find(**{'type': 'U'})
    ))
    return user_groups


def get_subgroups(db, groups):
    """get subgroups for a list of groups
    """

    def get_memberships(group, memberships, depth=0):
        """get group memberships"""
        result = set([group])
        if depth < 10:
            for grp, sgrp in memberships:
                if group == sgrp and grp not in result:
                    result |= get_memberships(grp, memberships, depth+1)
        return result

    all_subgroups = list(db(
        'SELECT group_id, subgroup_id FROM subgroups ORDER BY subgroup_id'
    ))

    memberships = set([])
    for group in groups:
        memberships |= get_memberships(group, all_subgroups)

    return memberships


def get_supergroups(db, groups):
    """get supergroups for a list of groups
    """

    def get_memberships(group, memberships, depth=0):
        """get group memberships"""
        result = set([group])
        if depth < 10:
            for grp, sgrp in memberships:
                if group == grp and sgrp not in result:
                    result |= get_memberships(sgrp, memberships, depth+1)
        return result

    all_subgroups = list(db(
        'SELECT group_id, subgroup_id FROM subgroups ORDER BY subgroup_id'
    ))

    memberships = set([])
    for group in groups:
        memberships |= get_memberships(group, all_subgroups)

    return memberships


def named_groups(db, group_ids):
    """Returns names for a list of group ids"""
    result = []
    for _id, name in db('SELECT id, name FROM groups'):
        if _id in group_ids:
            result.append(name)
    return result


def get_subgroup_options(db, group_id):
    cmd = """
    select name, id
    from groups
    where id <> %s and left(groups.name, 2) <> 'a_'
    """
    return list(
        (name, str(id))
        for name, id in db(cmd, group_id)
    )


def get_role_options(db, group_id):
    cmd = """
    select name, id
    from groups
    where id <> %s and left(groups.name, 2) <> 'a_'
    """
    return list(
        (name, str(id))
        for name, id in db(cmd, group_id)
    )


class AdminModel(object):

    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.groups = Groups(db)

    def log(self, message, *args):
        self.logger.debug(message, *args)

    def get_user_options(self):
        return sorted(
            (user.link, user._id) for user in Users(self.db)
        )

    def get_subgroup_options(self, group_id):
        return sorted(
            (group.link, group._id)
            for group in self.groups.find(**{'type': 'U'})
            if group._id != group_id
        )

    def get_role_options(self, group_id):
        return sorted(
            (group.link, group._id)
            for group in self.groups.find(**{'type': 'U'})
            if group._id != group_id
        )

    def get_app_options(self, group_id):
        app_titles = {app.name: app.title for app in context.site.apps}
        return sorted([
            (app_titles.get(app.name[2:], app.name[2:]), app._id)
            for app in self.groups.find(type="A")
            if app.name[2:] in app_titles
        ])

    def update_group_users(self, record):
        """Post updated group users"""

        record_id = int(record['_id'])

        updated_users = set(int(id) for id in record['users'])
        self.log('updated members: %r', updated_users)

        cmd = 'select user_id from members where group_id=%s'
        existing_users = set(
            user_id for user_id, in
            self.db(cmd, record_id)
        )
        self.log('existing members: %r', existing_users)

        if updated_users != existing_users:
            if existing_users - updated_users:
                self.log('deleting members: %r', existing_users - updated_users)
                cmd = 'delete from members where group_id=%s and user_id in %s'
                self.db(cmd, record_id, existing_users - updated_users)
            if updated_users - existing_users:
                self.log('inserting members: %r', updated_users - existing_users)
                cmd = 'insert into members (group_id, user_id) values (%s, %s)'
                values = updated_users - existing_users
                sequence = zip([record_id] * len(values), values)
                self.db.execute_many(cmd, sequence)
        else:
            self.log('users unchanged')

    def update_group_subgroups(self, record):
        """Post updated group subgroups"""

        record_id = int(record['_id'])

        updated_subgroups = set(int(id) for id in record['subgroups'])
        self.log('updated subgroups: %r', updated_subgroups)

        cmd = 'select subgroup_id from subgroups where group_id=%s'
        existing_subgroups = set(
            subgroup_id for subgroup_id, in
            self.db(cmd, record_id)
        )
        self.log('existing subgroups: %r', existing_subgroups)

        if updated_subgroups != existing_subgroups:
            if existing_subgroups - updated_subgroups:
                self.log('deleting: %r', existing_subgroups - updated_subgroups)
                cmd = 'delete from subgroups where group_id=%s and subgroup_id in %s'
                self.db(cmd, record_id, existing_subgroups - updated_subgroups)
            if updated_subgroups - existing_subgroups:
                self.log('inserting: %r', updated_subgroups - existing_subgroups)
                cmd = 'insert into subgroups (group_id, subgroup_id) values (%s, %s)'
                values = updated_subgroups - existing_subgroups
                sequence = zip([record_id] * len(values), values)
                self.db.execute_many(cmd, sequence)
        else:
            self.log('subgroups unchanged')

    def update_group_roles(self, record):
        """Post updated group roles"""

        record_id = int(record['_id'])
        group = context.site.groups.get(record_id)
        assert group

        updated_roles = set(int(user) for user in record['roles'])
        self.log('updated roles: %r', updated_roles)

        existing_roles = group.roles
        self.log('existing roles: %r', existing_roles)

        if updated_roles != existing_roles:
            if existing_roles - updated_roles:
                self.log('deleting: %r', existing_roles - updated_roles)
                cmd = 'delete from subgroups where subgroup_id=%s and group_id in %s'
                self.db(cmd, record_id, existing_roles - updated_roles)
            if updated_roles - existing_roles:
                self.log('inserting: %r', updated_roles - existing_roles)
                cmd = 'insert into subgroups (subgroup_id, group_id) values (%s, %s)'
                values = updated_roles - existing_roles
                sequence = zip([record_id] * len(values), values)
                self.db.execute_many(cmd, sequence)
        else:
            self.log('roles unchanged')

    def update_group_apps(self, record):
        """Post updated group apps"""

        record_id = int(record['_id'])
        group = context.site.groups.get(record_id)
        assert group

        updated_apps = set(int(user) for user in record['apps'])
        self.log('updated apps: %r', updated_apps)

        existing_apps = group.apps
        self.log('existing apps: %r', existing_apps)

        if updated_apps != existing_apps:
            if existing_apps - updated_apps:
                self.log('deleting: %r', existing_apps - updated_apps)
                cmd = 'delete from subgroups where subgroup_id=%s and group_id in %s'
                self.db(cmd, record_id, existing_apps - updated_apps)
            if updated_apps - existing_apps:
                self.log('inserting: %r', updated_apps - existing_apps)
                cmd = 'insert into subgroups (subgroup_id, group_id) values (%s, %s)'
                values = updated_apps - existing_apps
                sequence = zip([record_id] * len(values), values)
                self.db.execute_many(cmd, sequence)
        else:
            self.log('apps unchanged')

    def update_group_relationships(self, record):
        self.update_group_users(record)
        self.update_group_subgroups(record)
        self.update_group_roles(record)
        self.update_group_apps(record)


def get_index_metrics(db):

    def count(where, *args):
        """Return the result of a count query"""
        return '{:,}'.format((list(db('select count(*) from ' + where, *args))[0][0]))

    def avg(metric, where, *args):
        """Return the result of a query that calculates an average"""
        return '{:,.1f}'.format((list(db('select avg({}) from {}'.format(metric, where), *args))[0][0]))

    the_day = today()

    num_users = count('users where status="A"')
    num_groups = count('groups where type="U"')
    num_requests = count('log where status="C" and timestamp>=%s', the_day)
    num_errors = count('log where status="E" and timestamp>=%s', the_day)
    avg_speed = avg('elapsed', 'log where status="C" and timestamp>=%s and path<>"/login"', the_day)
    num_authorizations = count('audit_log where timestamp>=%s', the_day)

    metrics = [
        ('Users', '/admin/users', num_users),
        ('Groups', '/admin/groups', num_groups),
        ('Requests Today', '/admin/requests', num_requests),
        ('Errors Today', '/admin/errors', num_errors),
        ('Performance (ms)', '/admin/requests', avg_speed),
        ('Authorizations Today', '/admin/audit', num_authorizations)
    ]
    return metrics


def update_user_groups(record):
    logger = logging.getLogger(__name__)
    db = context.site.db
    record_id = record['_id']

    existing_groups = set(
        group_id for group_id, in
        db('select group_id from members where user_id=%s', record_id)
    )
    logger.debug('existing_groups: %r', existing_groups)

    updated_groups = set(record['memberships'])
    logger.debug('updated_groups: %r', updated_groups)

    if updated_groups != existing_groups:
        if existing_groups - updated_groups:
            logger.debug('deleting: %r', existing_groups - updated_groups)
            cmd = 'delete from members where user_id=%s and group_id in %s'
            db(cmd, record_id, existing_groups - updated_groups)
        if updated_groups - existing_groups:
            logger.debug('inserting: %r', updated_groups - existing_groups)
            cmd = 'insert into members (user_id, group_id) values (%s, %s)'
            values = updated_groups - existing_groups
            sequence = zip([record_id] * len(values), values)
            db.execute_many(cmd, sequence)
    else:
        logger.debug('members unchanged')


def update_group_relationships(record):
    admin = AdminModel(context.site.db)
    admin.update_group_relationships(record)


def admin_crud_policy():
    """Authourization policy for Admin app collections
    """
    def _policy(item, user, action):
        """Policy rules for shared collection"""

        def can_crud(user):
            """Return True if user can crud this collection
            """
            return user.is_admin or user.is_member('authorizers')

        actions = {
            'create': can_crud,
            'read': can_crud,
            'update': can_crud,
            'delete': can_crud,
        }

        if action not in actions:
            raise Exception('action missing: {}'.format(action))

        return actions.get(action)(user)
    return _policy


class AdminCollection(zoom.collect.Collection):
    """Admin app Collection"""

    allows = admin_crud_policy()
