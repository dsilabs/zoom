"""
    admin model
"""

from zoom.tools import today


def search_all(text):
    users = Users()

def get_index_metrics(db):
    # db = site.db

    # print(db('describe groups'))
    def count(where, *args):
        return list(db('select count(*) from ' + where, *args))[0][0]

    num_users = count('users where status="A"')
    num_groups = count('groups where type="U"')
    num_requests = count('log where status="C" and timestamp>=%s', today())
    num_errors = count('log where status="E" and timestamp>=%s', today())

    metrics = [
        ('Users', '/admin/users', num_users),
        ('Groups', '/admin/groups', num_groups),
        ('Requests Today', '/admin/requests', num_requests),
        ('Errors Today', '/admin/errors', num_errors),
    ]
    return metrics
