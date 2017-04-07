"""
    zoom.users
"""

import logging

from zoom.records import Record, RecordStore
from zoom.helpers import link_to, url_for
from zoom.auth import validate_password, hash_password


def get_groups(db, user):
    """get groups for a user

    >>> from zoom.database import setup_test
    >>> db = setup_test()
    >>> users = Users(db)
    >>> guest = users.first(username='guest')
    >>> guest.username
    'guest'
    >>> guest._id
    3

    >>> groups = get_groups(db, guest)
    >>> len(groups)
    7
    >>> 'everyone' in groups
    True
    >>> 'a_login' in groups
    True
    >>> 'managers' in groups
    False
    >>> 'administrators' in groups
    False

    >>> admin = users.first(username='admin')
    >>> groups = get_groups(db, admin)
    >>> 'everyone' in groups
    True
    >>> 'a_login' in groups
    True
    >>> 'managers' in groups
    True
    >>> 'administrators' in groups
    True
    """
    # logger = logging.getLogger(__name__)
    # logger.debug(user)

    def get_memberships(group, memberships, depth=0):
        """get group memberships"""
        result = [group]
        if depth < 10:
            for grp, sgrp in memberships:
                if group == sgrp and grp not in result:
                    result += get_memberships(grp, memberships, depth+1)
        return result

    my_groups = [
        rec[0]
        for rec in db(
            'SELECT group_id FROM members WHERE user_id=%s',
            user._id
        )
    ]

    subgroups = list(db(
        'SELECT group_id, subgroup_id FROM subgroups ORDER BY subgroup_id'
    ))

    memberships = []
    for group in my_groups:
        memberships += get_memberships(group, subgroups)

    groups = my_groups + memberships

    named_groups = []
    for rec in db('SELECT id, name FROM groups'):
        groupid = rec[0]
        name = rec[1].strip()
        if groupid in groups:
            named_groups += [name]

    return named_groups


class User(Record):
    """Zoom User"""

    key = property(lambda a: a.username)

    def __init__(self, *args, **kwargs):
        Record.__init__(self, *args, **kwargs)
        self.is_admin = False
        self.is_developer = False
        self.is_authenticated = False

    def initialize(self, request):
        logger = logging.getLogger(__name__)
        logger.debug('initializing user %r', self.username)

        self.request = request
        site = request.site

        self.is_authenticated = (
            self.username != site.guest and
            self.username == request.session.username
        )
        logger.debug(
            'user %r is_authenticated: %r',
            self.username, self.is_authenticated
        )

        self.is_admin = self.is_member(site.administrators_group)
        self.is_admin = self.is_member(site.administrators_group)
        self.is_developer = self.is_member(site.developers_group)

        if self.is_developer:
            logger.debug('user is a developer')
        if self.is_admin:
            logger.debug('user is an administrator')

        logger.debug('groups: %r' % self.groups)
        logger.debug('apps: %r' % self.apps)

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

    def is_member(self, group):
        """determine if user is a member of a group"""
        return group in self.groups

    def login(self, request, password, remember_me=False):
        """log user in"""
        logger = logging.getLogger(__name__)
        site = request.site

        if self.is_active and self.username != site.guest:
            logger.debug('authenticating user %s with hash %r', self.username, self.password)
            if self.authenticate(password):
                request.user.logout()
                request.session.username = self.username
                request.user = self
                self.initialize(request)
                return True
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
            logger.debug('cannot logout %r' % self.username)

    @property
    def default_app(self):
        return '/home'

    def deactivate(self):
        self.status = 'D'

    def activate(self):
        self.status = 'A'

    def get_groups(self):
        """get groups this user belongs to

        >>> from zoom.database import setup_test
        >>> users = Users(setup_test())
        >>> user = users.first(username='guest')
        >>> user.get_groups()[-4:]
        ['a_passreset', 'a_signup', 'everyone', 'guests']

        >>> user = users.first(username='admin')
        >>> user.get_groups()[:2]
        ['administrators', 'a_apps']
        """
        store = self.get('__store')
        if store:
            return get_groups(store.db, self)
        return []

    @property
    def groups(self):
        return [g for g in self.get_groups() if not g.startswith('a_')]

    @property
    def apps(self):
        return [g[2:] for g in self.get_groups() if g.startswith('a_')]

    def can_run(self, app_name):
        """test if user can run an app"""
        return self.is_admin or self.is_developer or app_name in self.apps

    def can(self, action, object=None):
        """test if user can peform action on an object"""
        return True

    def helpers(self):
        """provide user helpers"""
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
      apps ................: ['content', 'forgot', 'login', 'passreset', 'signup']
      link ................: '<a href="<dz:site_url>/users/guest">guest</a>'
      email ...............: 'guest@datazoomer.com'
      phone ...............: ''
      groups ..............: ['everyone', 'guests']
      status ..............: 'A'
      created .............: datetime.datetime(2017, 3, 30, 17, 23, 43)
      updated .............: datetime.datetime(2017, 3, 30, 17, 23, 43)
      is_admin ............: False
      password ............: ''
      username ............: 'guest'
      full_name ...........: 'Guest User'
      is_active ...........: True
      default_app .........: '/home'
      is_developer ........: False
      is_authenticated ....: False

    """
    def __init__(self, db, entity=User):
        RecordStore.__init__(
            self,
            db,
            entity,
            name='users',
            key='id'
            )
