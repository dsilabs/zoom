"""
    zoom.session
"""

import logging
import pickle
import time
import uuid

from zoom.database import DatabaseException
from zoom.records import Record, RecordStore


SESSION_LIFE = 60  # in minutes


class Sessions(Record):
    pass


class Session(object):

    def __init__(self, request):

        logger = logging.getLogger(__name__)
        logger.debug('session token: {}'.format(request.session_token))

        db = request.site.db
        self._request = request
        token = request.session_token
        # sessions = RecordStore(db, Sessions)
        self.ip_address = request.ip_address

        if not token:
            token = self.new(db)
            request.session_token = token
            logger.info('new user')
            logger.debug('created session: %r', token)
        else:
            if self.load(db, token):
                logger.debug('loaded session: %r', token)
            else:
                old_token = token
                token = self.new(db)
                logger.debug('expired session: replaced %r with %r', old_token, token)
        self._token = token

    @property
    def token(self):
        """return the token"""
        return self._token

    def destroy(self):
        """destroy the session"""
        logger = logging.getLogger(__name__)
        db = self._request.site.db
        old_token = self._token
        cmd = 'delete from sessions where id=%s'
        db(cmd, self._token)
        self._token = token = self.new(db)
        logger.debug('destroyed session: replaced %r with %r', old_token, token)

    def new(self, db, timeout=SESSION_LIFE):
        """create a new session"""

        def purge(db):
            """purge old sessions"""
            now = time.time()
            db('delete from sessions where (expiry<%s) or (status="D")', now)

        def try_sid(sid, expiry):
            """create and test the availability of a session id"""
            cmd = "insert into sessions values (%s, %s, 'A', '')"

            try:
                db(cmd, sid, expiry)
                return True
            except DatabaseException as s:
                logger.warning('wow, it happened')
                if 'Duplicate' in str(s):
                    return False
                raise

        def make_session_id():
            """make a new session id"""
            return uuid.uuid4().hex

        logger = logging.getLogger(__name__)

        purge(db)

        crazyloop = 10
        expiry = time.time() + timeout * 60
        newsid = make_session_id()
        success = try_sid(newsid, expiry)

        # Try again in the unlikely event that the generated
        # session id is being used
        while not success and crazyloop > 0:
            newsid = make_session_id()
            success = try_sid(newsid, expiry)
            crazyloop -= 1

        if success:
            # self.token = newsid
            self.ip_address = self.ip_address
            return newsid
        else:
            raise Exception('Crazy session error')

    def save(self, db, timeout=SESSION_LIFE):
        """save a session"""
        logger = logging.getLogger(__name__)

        if self._token:
            # using __dict__ method because getattr is overridden
            timeout_in_seconds = self.__dict__.get('lifetime', timeout * 60)

            expiry = time.time() + timeout_in_seconds

            values = {}
            for key in self.__dict__.keys():
                if key[0] != '_':
                    values[key] = self.__dict__[key]

            value = pickle.dumps(values)

            cmd = 'update sessions set expiry=%s, value=%s where id=%s'
            db(cmd, expiry, value, self._token)
            logger.debug('saved session %r expires %s', self._token, time.strftime('%c', time.localtime(expiry)))
            logger.debug('session values saved: {}'.format(values))
            return timeout_in_seconds

    def load(self, db, token):
        """load a session"""

        def load_existing(token):
            """load an existing session"""
            now = time.time()
            cmd = (
                'select value from sessions '
                'where id=%s and expiry>%s and status="A"'
            )
            result = db(cmd, token, now)
            if len(result):
                data = list(result)[0][0]
                # print(data)
                values = (
                    data and
                    pickle.loads(data) or
                    {}
                )
                return values
            else:
                cmd = (
                    'select status, expiry from sessions '
                    'where id=%s'
                )
                result = db(cmd, token)
                if len(result):
                    status, expiry = list(result)[0]
                    if expiry <= now:
                        logger.warning('session expired')
                    elif status != 'A':
                        logger.warning('session not active')
                    else:
                        logger.warning('session invalid')
                else:
                    logger.warning('session record missing')

        logger = logging.getLogger(__name__)
        logger.debug('loading session: {}'.format(token))

        token_is_valid = token and len(token) == 32 and token.isalnum()
        if token_is_valid:
            values = load_existing(token)
            if values:
                logger.debug('session values loaded: {}'.format(values))
                if values.get('ip_address', None) == self._request.ip_address:
                    logger.debug('session ip_address matches')
                    self.__dict__.update(values)
                    return True
                else:
                    msg = 'session ip_address mismatch, exiting session load'
                    logger.warning(msg)
            elif values == {}:
                logger.warning('session values missing')
            else:
                logger.warning('session not loaded')


def handler(request, next_handler, *rest):
    """session handler"""
    session = request.session = Session(request)
    request.session_token = session.token
    response = next_handler(request, *rest)
    request.session_timeout = request.profiler.time(
        'save session', request.session.save, request.site.db
    )
    return response
