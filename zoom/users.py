"""
    zoom.users
"""

from zoom.records import Record, RecordStore
from zoom.helpers import link_to, url_for


class User(Record):
    key = property(lambda a: a.username)
    is_authenticated = False

    @property
    def full_name(self):
        return ' '.join(filter(bool, [self.first_name, self.last_name]))

    @property
    def url(self):
        return url_for('/users/{}'.format(self.username))

    @property
    def link(self):
        return link_to(self.username, self.url)

    def logout(self):
        if self.is_authenticated:
            self.is_authenticated = False
            self.request.session.destroy()

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
      url .................: '<dz:site_url>/users/guest'
      link ................: '<a href="<dz:site_url>/users/guest">guest</a>'
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
