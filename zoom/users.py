"""
    zoom.users
"""

import logging
import string

import zoom
from zoom.auditing import audit
from zoom.context import context
from zoom.exceptions import UnauthorizedException
from zoom.records import Record, RecordStore
from zoom.helpers import link_to, url_for
from zoom.auth import validate_password, hash_password
from zoom.impersonation import get_impersonated_username

chars = ''.join(map(chr, range(256)))
keep_these = string.ascii_letters + string.digits + '.-_ '
delete_these = chars.translate(str.maketrans(chars, chars, keep_these))
allowed = str.maketrans(keep_these, keep_these, delete_these)


def key_for(username):
    """
    Calculates a valid HTML tag id given an arbitrary string.

        >>> key_for('Test 123')
        'test-123'
        >>> key_for('New Record')
        'new-record'
        >>> key_for('New "special" Record')
        'new-special-record'
        >>> key_for("hi test")
        'hi-test'
        >>> key_for("hi-test")
        'hi-test'
        >>> key_for(1234)
        '1234'
        >>> key_for('this %$&#@^is##-$&*!it')
        'this--at-is-it'
        >>> key_for('test-this')
        'test-this'
        >>> key_for('test.this')
        'test.this'
        >>> key_for('test\\\\this')
        'test-this'
        >>> key_for('test@this.com')
        'test-at-this.com'

    """
    def _key_for(text):
        return str(text).strip().translate(allowed).lower().replace(' ', '-')

    if '\\' in str(username):
        username = username.replace('\\', '-')
    if '@' in str(username):
        username = username.replace('@', '-at-')

    return _key_for(username)


def link_to_user(username):
    return link_to(username, '/admin/users/{}'.format(key_for(username)))


def get_current_username(request):
    """get current user username"""
    site = request.site
    return (
        getattr(request, 'username', None) or
        site.config.get('users', 'override', '') or
        get_impersonated_username() or
        getattr(request.session, 'username', None) or
        request.remote_user or
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

    def get_memberships(group, memberships, depth=0):
        """get group memberships"""
        result = {group}
        if depth < 10:
            for grp, sgrp in memberships:
                if group == sgrp and grp not in result and grp in all_groups:
                    result |= get_memberships(grp, memberships, depth+1)
        return result

    all_groups = dict(db('select id, name from `groups`'))

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

    groups = set()
    for group in my_groups:
        groups |= get_memberships(group, subgroups)

    named_groups = sorted(all_groups[g] for g in set(groups))

    return named_groups


class User(Record):
    """Zoom User"""

    # key = property(lambda a: id_for(a.username))
    @property
    def key(self):
        return key_for(self.username)

    def __init__(self, *args, **kwargs):
        Record.__init__(self, *args, **kwargs)
        self.is_admin = self.is_administrator = False
        self.is_developer = False
        self.is_authenticated = False
        self.__groups = None
        self.__user_groups = None
        self.__user_group_ids = None
        self.__apps = None
        self.__memberships = None
        self.request = None

    @property
    def user_id(self):
        """Return user record id"""
        return self.get('_id')

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
            self.id == request.user.id
        )
        logger.debug(
            'user %r is_authenticated: %r',
            self.username, self.is_authenticated
        )

        self.is_admin = self.is_member(site.administrators_group)
        self.is_administrator = self.is_admin
        self.is_developer = self.is_member(site.developers_group)

        if self.is_developer:
            logger.debug('user is a developer')
        if self.is_admin:
            logger.debug('user is an administrator')

        logger.debug('%r is a member of %s groups', self.username, len(self.groups))

        if self.is_active:
            logger.debug('%r can access %s apps', self.username, len(self.apps))
        else:
            logger.debug('%r is deactivated', self.username)

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
        if zoom.system.user and zoom.system.user.is_admin:
            return link_to(self.username, self.url)
        else:
            return self.username

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
            match, _ = validate_password(password, self.password)
            return match

    def update_last_seen(self):
        """Record the latest activity time for the user

            avoid the record store put so as not to update the updated timestamp
        """
        self.last_seen = zoom.tools.now()
        self.get('__store').db('update users set last_seen=%s where id=%s', self.last_seen, self._id)

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
            logger.debug('cannot logout %r', self.username)

    @property
    def default_app(self):
        """returns the default app for the user"""
        return '/home'

    def deactivate(self):
        """Deactivate the user"""
        audit('deactivate user', self.username)
        self.status = 'I'
        self.updated_by = zoom.system.user.user_id
        self.updated = zoom.tools.now()
        self.save()

    def activate(self):
        """Activate the user"""
        audit('activate user', self.username)
        self.status = 'A'
        self.updated_by = zoom.system.user.user_id
        self.updated = zoom.tools.now()
        self.save()

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

    def get_memberships(self):
        db = zoom.system.site.db
        return set(
            group_id for group_id, in
            db('select group_id from members where user_id=%s', self.user_id)
        )

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
            if len(groups):
                db = self.get('__store').db
                slots = ', '.join(['%s'] * len(groups))
                cmd = 'select id from `groups` where name in (%s)' % slots
                self.__user_group_ids = [i[0] for i in db(cmd, *groups)]
            else:
                self.__user_group_ids = []
        return self.__user_group_ids

    @property
    def apps(self):
        """Returns the names of the apps the user can access"""
        if self.__apps is None:
            self.__apps = [g[2:] for g in self.get_groups() if g.startswith('a_')]
        return self.__apps

    def can_run(self, app):
        """test if user can run an app"""
        return app and self.is_active and (app.name in self.apps or app.in_development and (self.is_developer or self.is_admin))

    def can(self, action, thing):
        """test to see if user can action a thing object.

        Object thing must provide allows(user, action) method.
        """
        return self.is_active and bool(thing and thing.allows(self, action))

    def authorize(self, action, thing):
        """authorize a user to perform an action on thing

        If user is not allowed to perform the action an exception is raised.
        Object thing must provide allows(user, action) method.
        """
        if not (self.is_active and thing.allows(self, action)):
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

    @property
    def status_text(self):
        """Return status as human friendly text"""
        status = self.get('status')
        label = {
            'A': 'active',
            'I': 'deactivated',
            'S': 'security',
            'D': 'deleted',
        }.get(status, status)
        return label

    @property
    def when_updated(self):
        """Human friendly updated timestamp"""
        now = getattr(self, 'now', None) or zoom.tools.now()
        return zoom.tools.how_long_ago(self.get('updated'), since=now)

    @property
    def updated_by_link(self):
        """Human friendly user account"""
        user_id = self.get('updated_by')
        if user_id:
            users = self.get('__store')
            if users:
                user = users.get(user_id)
                if user:
                    return user.link
        return user_id

    @property
    def when_last_seen(self):
        return zoom.helpers.when(self.last_seen)

    @property
    def memberships(self):
        if not self.__memberships:
            self.__memberships = self.get_memberships()
        return self.__memberships


class Users(RecordStore):
    """Zoom Users

    >>> import datetime
    >>> from zoom.database import setup_test
    >>> db = setup_test()
    >>> users = Users(db)
    >>> user = users.first(username='guest')
    >>> user.created = datetime.datetime(2017, 3, 30, 17, 23, 43)
    >>> user.updated = datetime.datetime(2017, 3, 30, 17, 23, 43)
    >>> user.now = datetime.datetime(2017, 4, 30, 17, 23, 43)
    >>> import zoom
    >>> zoom.system.site = zoom.sites.Site()
    >>> print(user)
    User
      user_id .............: 3
      key .................: 'guest'
      name ................: 'Guest User'
      first_name ..........: 'Guest'
      last_name ...........: 'User'
      now .................: datetime.datetime(2017, 4, 30, 17, 23, 43)
      url .................: '/admin/users/guest'
      apps ................: ['content', 'forgot', 'login', 'passreset', 'signup']
      link ................: 'guest'
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
      memberships .........: {3}
      status_text .........: 'active'
      is_developer ........: False
      when_updated ........: 'over a month ago'
      when_last_seen ......: 'never'
      updated_by_link .....: 'admin'
      is_administrator ....: False
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

    def add(
            self,
            username,
            first_name,
            last_name,
            email,
            phone='',
        ):
        """Add user record to the database"""

        def validate(value, validator):
            """validate a value"""
            if not validator(value):
                raise Exception(validator.msg)

        def username_not_taken(username):
            return self.first(username=username) is None

        v = zoom.validators
        username_available = v.Validator('username taken', username_not_taken)
        rules = (
            (username, v.valid_username),
            (first_name, v.valid_name),
            (last_name, v.valid_name),
            (email, v.valid_email),
            (phone, v.valid_phone),
            (username, username_available),
        )

        for value, rule in rules:
            validate(value, rule)

        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
        )

        self.put(user)

        return user

    def before_insert(self, user):
        """Things to do just before inserting a new User record"""
        user.update(status='A')
        user.created = user.updated = zoom.tools.now()

    def before_update(self, user):
        """Things to do just before updating a User record"""
        user.updated = zoom.tools.now()

    def after_update(self, user):
        """Things to do immediately after a user update"""
        audit('update user', user.username)

    def after_insert(self, user):
        """Things to do immediately after inserting a new user"""
        user.remove_groups()  # avoid accidental authourizations
        user.add_group('users')
        audit('create user', user.username)

    def before_delete(self, user):
        """Things to do immediately before deleting a user"""
        user.remove_groups()
        audit('delete user', user.username)

    def locate(self, key):
        """Locate a user by username or user_id"""
        user = key and (
            self.first(username=key) or
            self.first(username=key.replace('-', '\\')) or
            self.first(username=key.replace('-at-', '@'))
        )
        if user and user.key == key:
            return user


def authorize(*roles):
    """Decorator that authorizes (or not) the current user

    Raises an exception if the current user does not have at least
    one of the listed roles.
    """
    def wrapper(func):
        """wraps the protected function"""
        def authorize_and_call(*args, **kwargs):
            """checks authorization and calls function if authorized"""
            user = context.request.user
            if user.is_active:
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
            # We have an authenticated user but we don't have them
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
        zoom.system.user = request.user = user
        user.initialize(request)
        user.update_last_seen()  # avoid updating the 'updated' timestamp
        logger.debug('user loaded: %s (%r)', user.full_name, user.username)
        request.profiler.add('user initialized')
    else:
        raise Exception('Unable to initialize user')


def get_user(key=None):
    """Return the currrent user or a specified user"""
    if key is None:
        return zoom.system.request.user
    users = zoom.get_site().users
    return users.get(key) or users.locate(key)


def handler(request, next_handler, *rest):
    """handle user"""
    set_current_user(request)
    return next_handler(request, *rest)
