"""
    zoom.users
"""

import logging

from zoom.records import Record, RecordStore
from zoom.helpers import link_to, url_for
from zoom.auth import validate_password, hash_password


class User(Record):
    """Zoom User"""

    key = property(lambda a: a.username)

    def __init__(self, *args, **kwargs):
        Record.__init__(self, *args, **kwargs)
        self.is_authenticated = self.username != 'guest'

    @property
    def is_active(self):
        """get user active status"""
        return self.status == 'A'

    @property
    def full_name(self):
        """user full name"""
        return ' '.join(filter(bool, [self.first_name, self.last_name]))

    @property
    def url(self):
        """user view url"""
        return url_for('/users/{}'.format(self.username))

    @property
    def link(self):
        """user as link"""
        return link_to(self.username, self.url)

    def authenticate(self, password):
        """authenticate user credentials"""
        match, phash = validate_password(password, self.password, self.created)
        return match

    def login(self, request, password, remember_me=False):
        """log user in"""
        logger = logging.getLogger(__name__)
        if self.is_active and self.username != request.site.guest:
            logger.debug('authenticating user %s with hash %r', self.username, self.password)
            if self.authenticate(password):
                request.user.logout()
                request.session.username = self.username
                request.user = self
                self.is_authenticated = True
                logger.debug('user authenticated')
                # if remember_me:
                #     self.request.session.lifetime = TWO_WEEKS
            else:
                logger.debug('user authentication failed')

    def logout(self):
        """log user out"""
        logger = logging.getLogger(__name__)
        if self.is_authenticated:
            self.is_authenticated = False
            self.request.session.destroy()
            logger.debug('user authenticated')
        else:
            logger.debug('cannot logout')

    def helpers(self):
        """provide user helpers"""
        return dict(
            username=self.username,
        )

    def can(self, action, object=None):
        """test if user can peform action on an object"""
        return True


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
