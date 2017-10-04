"""
    zoom.users
"""

import logging

import zoom
from zoom.context import context
from zoom.exceptions import UnauthorizedException
from zoom.records import Record, RecordStore
from zoom.helpers import link_to, url_for
from zoom.auth import validate_password, hash_password
from zoom.utils import id_for


def get_current_username(request):
    """get current user username"""
    site = request.site
    return (
        site.config.get('users', 'override', '') or
        getattr(request.session, 'username', None) or
        request.env.get('REMOTE_USER', None) or
        site.guest or
        None
    )


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
    False
    >>> 'managers' in groups
    True
    >>> 'administrators' in groups
    True
    """
    logger = logging.getLogger(__name__)

    def get_memberships(group, memberships, depth=0):
        """get group memberships"""
        # result = [group]
        result = {group}
        if depth < 10:
            for grp, sgrp in memberships:
                if group == sgrp and grp not in result and grp in all_groups:
                    verb = all_groups[grp].startswith('a_') and 'can' or 'are'
                    logger.debug(
                        '%s %s %s',
                        all_groups[sgrp],
                        verb,
                        all_groups[grp],
                    )
                    result |= get_memberships(grp, memberships, depth+1)
        return result

    all_groups = dict(db('select id, name from groups'))

    my_groups = [
        rec[0]
        for rec in db(
            'SELECT group_id FROM members WHERE user_id=%s',
            user._id
        )
        if rec[0] in all_groups
    ]

    subgroups = list(db(
        'SELECT group_id, subgroup_id FROM subgroups ORDER BY subgroup_id'
    ))

    # memberships = []
    groups = set()
    for group in my_groups:
        # memberships += get_memberships(group, subgroups)
        groups |= get_memberships(group, subgroups)

    # groups = my_groups + memberships

    named_groups = sorted(all_groups[g] for g in set(groups))

    logger.debug('%s has groups %s', user.username, named_groups)
    return named_groups


class User(Record):
    """Zoom User"""

    # key = property(lambda a: id_for(a.username))
    @property
    def key(self):
        if '\\' in self.username:
            username = self.username.replace('\\','-')
        else:
            username = self.username
        return id_for(username)

    def __init__(self, *args, **kwargs):
        Record.__init__(self, *args, **kwargs)
        self.is_admin = False
        self.is_developer = False
        self.is_authenticated = False
        self.__groups = None
        self.__user_groups = None
        self.__user_group_ids = None
        self.__apps = None
        self.request = None

    def allows(self, user, action):
        return action != 'delete' or self.username != 'admin'

    def initialize(self, request):
        """Initialize user based on a request"""
        logger = logging.getLogger(__name__)
        logger.debug('initializing user %r', self.username)

        self.request = request
        site = request.site

        self.is_authenticated = (
            self.username != site.guest and
            self.username == get_current_username(request)
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
        return ' '.join(filter(bool, [self.first_name, self.last_name])) or 'New User'

    @property
    def name(self):
        """user full name"""
        return self.full_name

    @property
    def url(self):
        """user view url"""
        return url_for('/admin/users/{}'.format(self.key))

    @property
    def link(self):
        """user as link"""
        return link_to(self.username, self.url)

    def set_password(self, password):
        """set the user password"""
        hashed = hash_password(password)
        logger = logging.getLogger(__name__)
        logger.debug('set password for %s to %r', self.username, hashed)
        self['password'] = hashed
        self.save()

    def authenticate(self, password):
        """authenticate user credentials"""
        if self.is_active:
            match, phash = validate_password(password, self.password)
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
                if remember_me:
                    two_weeks = 14 * 24 * 60 * 60
                    request.session.lifetime = two_weeks
                return True
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
        """returns the default app for the user"""
        return '/home'

    def deactivate(self):
        """Deactivate the user

        Note: does not save.
        """
        self.status = 'I'

    def activate(self):
        """Activate the user

        Note: does not save.
        """
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
        ['a_admin', 'a_apps']
        """
        if self.__groups is None:
            store = self.get('__store')
            self.__groups = get_groups(store.db, self)
        return self.__groups

    @property
    def groups(self):
        """Returns the groups the user belongs to"""
        if self.__user_groups is None:
            self.__user_groups = [g for g in self.get_groups() if not g.startswith('a_')]
        return self.__user_groups

    @property
    def groups_ids(self):
        """Returns the IDs for the groups the user belongs to"""
        if self.__user_group_ids is None:
            # if we have groups then we have a store so avoid another check here
            groups = self.groups
            cmd = 'select id from groups where name in (%s)' % (', '.join(['%s'] * len(groups)))
            self.__user_group_ids = [i[0] for i in self.get('__store').db(cmd, *groups)]  # list of group id's
        return self.__user_group_ids

    @property
    def apps(self):
        """Returns the names of the apps the user can access"""
        if self.__apps is None:
            self.__apps = [g[2:] for g in self.get_groups() if g.startswith('a_')]
        return self.__apps

    def can_run(self, app):
        """test if user can run an app"""
        return app and (app.name in self.apps or app.in_development and (self.is_developer or self.is_admin))

    def can(self, action, thing):
        """test to see if user can action a thing object.

        Object thing must provide allows(user, action) method.
        """
        return bool(thing and thing.allows(self, action))

    def authorize(self, action, thing):
        """authorize a user to perform an action on thing

        If user is not allowed to perform the action an exception is raised.
        Object thing must provide allows(user, action) method.
        """
        if not thing.allows(self, action):
            raise UnauthorizedException('Unauthorized')

    def helpers(self):
        """provide user helpers"""
        return dict(
            username=self.username,
            user_full_name=self.full_name,
            user_first_name=self.first_name,
            user_last_name=self.last_name,
        )

    def add_group(self, group):
        """Make user a member of the group"""
        logger = logging.getLogger(__name__)
        group = context.site.groups.locate(group)
        if group:
            group.add_user(self)
            logger.debug('added %s to group %s', self.username, group.name)
        else:
            logger.warning('unable to add %s to group %s',
                self.username, group.name)

    def remove_groups(self):
        """Remove user membership in the group"""
        assert self._id
        zoom.system.site.db('delete from members where user_id=%s', self._id)


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
      name ................: 'Guest User'
      first_name ..........: 'Guest'
      last_name ...........: 'User'
      url .................: '/admin/users/guest'
      apps ................: ['content', 'forgot', 'login', 'passreset', 'signup']
      link ................: '<a href="/admin/users/guest">guest</a>'
      email ...............: 'guest@datazoomer.com'
      phone ...............: ''
      groups ..............: ['everyone', 'guests']
      status ..............: 'A'
      created .............: datetime.datetime(2017, 3, 30, 17, 23, 43)
      request .............: None
      updated .............: datetime.datetime(2017, 3, 30, 17, 23, 43)
      is_admin ............: False
      password ............: ''
      username ............: 'guest'
      full_name ...........: 'Guest User'
      is_active ...........: True
      created_by ..........: 1
      groups_ids ..........: [4, 3]
      updated_by ..........: 1
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

    def before_insert(self, user):
        """Things to do just before inserting a new User record"""
        user.update(status='A')
        user.created = user.updated = zoom.tools.now()

    def before_update(self, user):
        """Things to do just before updating a User record"""
        user.updated = zoom.tools.now()

    def after_insert(self, user):
        """Things to do right after inserting a new user"""
        user.remove_groups()  # avoid accidental authourizations
        user.add_group('users')

    def before_delete(self, user):
        """Things to do right before deleting a user"""
        user.remove_groups()

    def locate(self, key):
        users = context.site.users
        user = users.first(username=key)
        if user:
            return user
        alternate_key = key.replace('-', '\\')
        user = users.first(username=alternate_key)
        if user:
            return user


def authorize(*roles):
    """Decorator that authorizes (or not) the current user

    Raises an exception if the current user does not have at least
    one of the listed roles.
    """
    user = zoom.system.request.user
    def wrapper(func):
        """wraps the protected function"""
        def authorize_and_call(*args, **kwargs):
            """checks authorization and calls function if authorized"""
            if user.is_administrator:
                return func(*args, **kwargs)
            for role in roles:
                if role in user.groups:
                    return func(*args, **kwargs)
            raise zoom.exceptions.UnauthorizedException('Unauthorized')
        return authorize_and_call
    return wrapper


def set_current_user(request):
    """Set current user

    Set the current user based on the current username.
    """
    logger = logging.getLogger(__name__)

    username = get_current_username(request)
    if not username:
        raise Exception('No user information available')

    users = Users(request.site.db)
    user = users.first(username=username, status='A')
    if not user:
        logger.debug('no active user record for %s', username)

        user = users.first(username=username)
        if not user:
            # We have identified a valid user but we don't have them
            # in our database.  This happens when authentication is handled
            # by another layer before us.  What we need to do in this case
            # is register a new user record so we can keep track of them like
            # any other user but we will likely never be asked to authenticate
            # this user.
            logger.debug('adding new user record for %s', username)
            user = User(username=username)
            users.put(user)
            user = users.first(username=username, status='A')
            msg = 'new user record added for unregistered user %r'
            logger.info(msg, username)

    if user:
        user.initialize(request)
        zoom.system.user = request.user = user
        logger.debug('user loaded: %s (%r)', user.full_name, user.username)
        request.profiler.add('user initialized')
    else:
        raise Exception('Unable to initialize user')


def handler(request, next_handler, *rest):
    """handle user"""
    set_current_user(request)
    return next_handler(request, *rest)
