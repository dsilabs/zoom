"""
    admin model
"""

import logging

from zoom.context import context
from zoom.tools import today
from zoom.records import Record, RecordStore


def search_all(text):
    users = Users()

def get_index_metrics(db):

    def count(where, *args):
        return '{:,}'.format((list(db('select count(*) from ' + where, *args))[0][0]))

    def avg(metric, where, *args):
        return '{:,.1f}'.format((list(db('select avg({}) from {}'.format(metric, where), *args))[0][0]))

    num_users = count('users where status="A"')
    num_groups = count('groups where type="U"')
    num_requests = count('log where status="C" and timestamp>=%s', today())
    num_errors = count('log where status="E" and timestamp>=%s', today())
    avg_speed = avg('elapsed', 'log where status="C" and timestamp>=%s and path<>"/login"', today())

    metrics = [
        ('Users', '/admin/users', num_users),
        ('Groups', '/admin/groups', num_groups),
        ('Requests Today', '/admin/requests', num_requests),
        ('Errors Today', '/admin/errors', num_errors),
        ('Performance (ms)', '/admin/requests', avg_speed),
    ]
    return metrics


def update_user_groups(record):
    logger = logging.getLogger(__name__)
    db = context.site.db

    logger.debug(str(db('select group_id, user_id from members')))

    current_members = list(
        db('select group_id, user_id from members where user_id=%s', record['_id'])
    )

    logger.debug('current_members: {!r}'.format(current_members))

    updated_members = [(
        (int(group), int(record['_id']))
    ) for group in record['groups']]
    logger.debug('updated_members: {!r}'.format(updated_members))

    for member in current_members:
        if member not in updated_members:
            group_id, user_id = member
            logger.debug('deleting %r', member)
            db('delete from members where group_id=%s and user_id=%s', group_id, user_id)

    for member in updated_members:
        if member not in current_members:
            group_id, user_id = member
            logger.debug('inserting %r', member)
            db('insert into members (group_id, user_id) values (%s, %s)', group_id, user_id)


def update_group_members(record):
    logger = logging.getLogger(__name__)
    db = context.site.db

    logger.debug(str(db('select group_id, user_id from members')))

    current_members = list(
        db('select group_id, user_id from members where group_id=%s', record['_id'])
    )

    logger.debug('current_members: {!r}'.format(current_members))

    print(current_members)
    print(record)

    updated_members = [(
        (int(record['_id']), int(user))
    ) for user in record['users']]
    logger.debug('updated_members: {!r}'.format(updated_members))

    # raise Exception('stopped')

    for member in current_members:
        if member not in updated_members:
            group_id, user_id = member
            logger.debug('deleting %r', member)
            db('delete from members where group_id=%s and user_id=%s', group_id, user_id)

    for member in updated_members:
        if member not in current_members:
            group_id, user_id = member
            logger.debug('inserting %r', member)
            db('insert into members (group_id, user_id) values (%s, %s)', group_id, user_id)
