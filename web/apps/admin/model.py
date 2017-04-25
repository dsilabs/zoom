"""
    admin model
"""


def search_all(text):
    users = Users()

def get_index_metrics(db):
    # db = site.db

    # print(db('describe groups'))

    num_users = list(db('select count(*) from users'))[0][0]
    num_groups = list(db('select count(*) from groups where type="U"'))[0][0]

    metrics = [
        ('Users', '/admin/users', num_users),
        ('Groups', '/admin/groups', num_groups),
    ]
    return metrics
