"""
    zoom.users

    experimental

    intention is to eventually replace user.py module
"""

from zoom.records import Record, RecordStore


class User(Record):
    key = property(lambda a: a.username)

    @property
    def full_name(self):
        return ' '.join(filter(bool, [self.first_name, self.last_name]))

    def helpers(self):
        return dict(
            username=self.username,
        )


class Users(RecordStore):
    """Zoom Users

    >>> import datetime
    >>> from zoom.database import setup_test
    >>> db = setup_test()
    >>> users = Users(db)
    >>> user = users.first(username='guest')
    >>> user.created = datetime.datetime(2017, 3, 30, 17, 23, 43)
    >>> user.updated = datetime.datetime(2017, 3, 30, 17, 23, 43)
    >>> print(user)
    User
      key .................: 'guest'
      first_name ..........: 'Guest'
      last_name ...........: 'User'
      email ...............: 'guest@datazoomer.com'
      phone ...............: ''
      status ..............: 'A'
      created .............: datetime.datetime(2017, 3, 30, 17, 23, 43)
      updated .............: datetime.datetime(2017, 3, 30, 17, 23, 43)
      password ............: ''
      username ............: 'guest'
      full_name ...........: 'Guest User'
    
    """
    def __init__(self, db, entity=User):
        RecordStore.__init__(
            self,
            db,
            entity,
            name='users',
            key='id'
            )
