"""
    zoom.queues

    message queues
"""

import uuid
import time
import datetime
import platform
import logging

from zoom.store import Record, EntityStore
import zoom.jsonz as json

__all__ = [
    'Queues',
    'Topic',
    'EmptyException',
    'WaitException',
    'StopListening',
    'StopHandling',
    'StopProcessing',
    ]

DEFAULT_DELAY = 0.1
DEFAULT_TIMEOUT = 15

now = datetime.datetime.now


class EmptyException(Exception):
    pass


class WaitException(Exception):
    pass


class StopListening(Exception):
    pass


class StopHandling(Exception):
    pass


class StopProcessing(Exception):
    pass


class SystemMessage(Record):
    pass


Message = SystemMessage


def response_topic_name(topic, id):
    """calculate the name of the reponse topic for a topic"""
    return '%s.response.%s' % (topic, id)


def setup_test():
    from zoom.database import setup_test
    db = setup_test()
    return Queues(db)


class TopicIterator(object):

    def __init__(self, topic, newest=None):
        self.topic = topic

    def __iter__(self):
        return self

    def __next__(self):
        try:
            message = self.topic.poll()
        except EmptyException:
            raise StopIteration
        else:
            return message


class Topic(object):
    """
    message topic
    """

    def __init__(self, name, newest=None, db=None):
        self.name = name
        self.db = db
        self.messages = EntityStore(db, Message)
        self.newest = newest is not None and newest or self.last() or -1

    def last(self):
        """get row_id of the last (newest) message in the topic"""
        if self.name:
            cmd = """
                select max(row_id) n
                from attributes
                where kind=%s and attribute="topic" and value=%s
                """
            rec = self.db(cmd, self.messages.kind, self.name)
        else:
            cmd = 'select max(row_id) n from attributes where kind=%s'
            rec = self.db(cmd, self.messages.kind)
        if type(rec) == int:
            return 0
        row_id = rec.first()[0]
        return row_id or 0


    def put(self, message):
        """put a message in the topic"""
        return self.messages.put(
                Message(
                    topic = self.name,
                    timestamp = now(),
                    node = platform.node(),
                    body = json.dumps(message),
                    )
                )

    def clear(self):
        """clear the topic

        >>> messages = setup_test()
        >>> t = messages.get('test_topic')
        >>> t.send('hey!', 'you!')
        [1, 2]
        >>> len(t)
        2
        >>> t.clear()
        >>> len(t)
        0
        """
        if self.name:
            self.messages.delete(topic=self.name)
        else:
            self.messages.zap()

    def send(self, *messages):
        """send list of messages

            >>> messages = setup_test()
            >>> t = messages.get('test_topic')
            >>> t.send('hey!', 'you!')
            [1, 2]
            >>> t.peek()
            'hey!'
            >>> t.peek()
            'hey!'
        """
        return [self.put(message) for message in messages]

    def _peek(self, newest=None):
        def decoded(value):
            if type(value) is bytes:
                return value.decode('utf8')
            return value
        top_one = newest is not None and newest or self.newest or 0
        db = self.db
        if self.last() > self.newest:
            if self.name:
                cmd = """
                    select min(row_id) as row_id
                    from attributes
                    where
                        kind=%s and
                        attribute="topic" and
                        value=%s and
                        row_id > %s
                    """
                rec = db(cmd, self.messages.kind, self.name, top_one)
            else:
                cmd = """
                    select min(row_id) as row_id
                    from attributes where kind=%s and row_id > %s
                    """
                rec = db(cmd, self.messages.kind, top_one)
            if type(rec) == int:
                row_id = 0
            else:
                row_id = rec.first()[0]
            if row_id:
                message = self.messages.get(row_id)
                if message:
                    return row_id, decoded(message.topic), json.loads(decoded(message.body))
        raise EmptyException

    def peek(self, newest=None):
        """
        return the next message but don't remove it

            >>> messages = setup_test()
            >>> t = messages.get('test_topic')
            >>> t.peek()
            >>> t.put('hey!')
            1
            >>> t.put('you!')
            2
            >>> t.peek()
            'hey!'
            >>> t.peek()
            'hey!'
        """
        try:
            return self._peek(newest)[2]
        except EmptyException:
            return None


    def _poll(self, newest=None):
        r = self._peek(newest)
        self.newest = r[0]
        return r


    def poll(self, newest=None):
        """
        peek at the next message and increment internal pointer

            >>> messages = setup_test()
            >>> t = messages.get('test_topic')
            >>> t.put('hey!')
            1
            >>> t.put('you!')
            2
            >>> t.newest
            -1
            >>> t.poll()
            'hey!'
            >>> t.newest
            1
            >>> t.poll()
            'you!'

            >>> raised = False
            >>> try:
            ...     t.poll()
            ... except EmptyException:
            ...     raised = True
            >>> raised
            True

            >>> t.newest = -1
            >>> t.poll()
            'hey!'
        """
        return self._poll(newest)[2]

    def _pop(self):
        r = self._peek()
        row_id = r[0]
        self.messages.delete(row_id)
        if self.messages.db.rowcount > 0:
            self.newest = row_id
            return r
        else:
            # If we were unable to delete it then soneone else
            # has already deleted it between the time that
            # we saw it and the time we attempted to delete it.
            raise EmptyException

    def pop(self):
        """
        read next message and remove it from the topic

            >>> messages = setup_test()
            >>> t = messages.get('test_topic')
            >>> t.put('hey!')
            1
            >>> t.put('you!')
            2
            >>> t.len()
            2
            >>> t._peek()
            (1, 'test_topic', 'hey!')
            >>> t.pop()
            'hey!'
            >>> t.len()
            1
            >>> t.pop()
            'you!'
            >>> t.len()
            0
            >>> t.pop()
            >>> t.newest = -1
            >>> raised = False
            >>> try:
            ...     t._pop()
            ... except EmptyException:
            ...     raised = True
            >>> raised
            True
        """
        try:
            return self._pop()[2]
        except EmptyException:
            return None


    def len(self, newest=None):
        """
        return the number of messages in the topic

            >>> messages = setup_test()
            >>> t = messages.get('test_topic')
            >>> t.put('hey!')
            1
            >>> t.put('you!')
            2
            >>> t.len()
            2
        """
        if self.last() > self.newest:
            if self.name:
                cmd = """
                    select count(row_id) as n
                    from attributes
                    where kind=%s and attribute="topic" and value=%s and row_id>%s
                    """
                t = self.db(cmd, self.messages.kind, self.name, self.newest)
            else:
                cmd = """select count(row_id) as n
                    from attributes
                    where kind=%s and row_id>%s
                    """
                t = self.db(cmd, self.messages.kind, self.newest)
            n = t.first()[0] or 0
            return n
        return 0


    def __len__(self):
        """
        return the number of messages in a topic as an int
        (note: for large number of messages use t.len()

            >>> messages = setup_test()
            >>> t = messages.get('test_topic')
            >>> t.put('hey!')
            1
            >>> t.put('you!')
            2
            >>> len(t)
            2
        """
        return self.len()


    def __iter__(self):
        """
        iterate through a topic

            >>> messages = setup_test()
            >>> t = messages.get('test_topic')
            >>> t.put('hey!')
            1
            >>> t.put('you!')
            2
            >>> for m in t: print(m)
            hey!
            you!
        """
        return TopicIterator(self, self.newest)


    def wait(self, delay=DEFAULT_DELAY, timeout=DEFAULT_TIMEOUT):
        """
        wait for a message to arrive and return it

            >>> messages = setup_test()
            >>> t = messages.get('test_topic')
            >>> t.put('hey!')
            1
            >>> t.put('you!')
            2
            >>> t.wait()
            'hey!'
            >>> t.wait()
            'you!'
        """
        deadline = time.time() + timeout
        while True:
            msg = self.pop()
            if msg:
               return msg
            time.sleep(delay)
            if time.time() > deadline:
                raise WaitException


    def listen(self, f, delay=DEFAULT_DELAY, meta=False):
        """
        observe but don't consume messages

            >>> messages = setup_test()
            >>> t = messages.get('test_topic')
            >>> t.put('hey!')
            1
            >>> t.put('you!')
            2
            >>> def echo(m):
            ...     print(m)
            ...     return m == 'you!'
            >>> t.listen(echo)
            hey!
            you!
            2

            >>> t1 = messages.topic('test_topic1')
            >>> t2 = messages.topic('test_topic2')
            >>> t3 = messages.topic(None)

            >>> t1.put('hey!')
            3
            >>> t2.put('you!')
            4
            >>> def echo(m):
            ...     print(m)
            ...     return m == 'you!'
            >>> t3.listen(echo)
            hey!
            you!
            2

        """
        n = 0
        done = False
        while not done:
            try:
                more_to_do = True
                while more_to_do:
                    try:
                        p = self._poll()
                    except EmptyException:
                        more_to_do = False
                    else:
                        if meta:
                            done = f(p)
                        else:
                            done = f(p[2])
                        n += 1
            except StopListening:
                return n
            else:
                time.sleep(delay)
        return n


    def join(self, jobs):
        """wait for responses from consumers"""
        return [
                Topic(
                    response_topic_name(self.name, job),
                    newest=job,
                    db=self.db,
                    ).wait() for job in jobs
                ]


    def call(self, *messages):
        """send messages and wait for responses"""
        return self.join(self.send(*messages))


    def handle(self, f, timeout=0, delay=DEFAULT_DELAY, one_pass=False):
        """respond to and consume messages

            >>> messages = setup_test()
            >>> t = messages.get('test_topic')
            >>> def echo(m):
            ...     if m == 'quit': raise StopHandling
            ...     print('got', repr(m))
            >>> t.put('hey!')
            1
            >>> t.put('you!')
            2
            >>> t.put('quit')
            3
            >>> t.handle(echo)
            got 'hey!'
            got 'you!'
            2
        """
        deadline = timeout and time.time() + timeout
        done = False
        n = 0
        while not done:
            try:
                try:
                    more_to_do = True
                    while more_to_do:
                        try:
                            row, topic, message = self._pop()
                            result = f(message)
                            t = Topic(
                                response_topic_name(topic, row),
                                None,
                                self.db
                            )
                            t.send(result)
                            deadline = timeout and time.time() + timeout
                            n += 1
                        except EmptyException:
                            more_to_do = False
                        time.sleep(0)
                except StopHandling:
                    done = True
                else:
                    time.sleep(delay)
            except KeyboardInterrupt:
                done = True
            if timeout and time.time() > deadline:
                done = True
        return n

    def process(self, f):
        """respond to and consume current messages

            >>> messages = setup_test()
            >>> t = messages.get('test_topic')
            >>> def echo(m):
            ...     if m == 'quit': raise StopProcessing
            ...     print('got', repr(m))
            >>> t.put('hey!')
            1
            >>> t.put('you!')
            2
            >>> t.put('quit')
            3
            >>> t.process(echo)
            got 'hey!'
            got 'you!'
            2
            >>> t.process(echo)
            0
        """
        n = 0
        more_to_do = True
        while more_to_do:
            try:
                row, topic, message = self._pop()
                if message is None:
                    result = f()
                else:
                    result = f(message)
                response_topic = response_topic_name(topic, row)
                t = Topic(response_topic, None, self.db)
                t.put(result)
                n += 1
            except StopProcessing:
                more_to_do = False
            except EmptyException:
                more_to_do = False
            time.sleep(0)
        return n


class Queues(object):
    """messages

        >>> messages = setup_test()
        >>> t = messages.get('test_topic')
        >>> t.put('hey!')
        1
        >>> t.put('you!')
        2
        >>> t.peek()
        'hey!'
    """

    def __init__(self, db=None):
        self.db = db

    def get(self, name, newest=None):
        return Topic(name, newest, self.db)

    def topic(self, name, newest=None):
        return Topic(name, newest, self.db)

    def topics(self):
        cmd = """
            select distinct value
            from attributes
            where kind=%s and attribute="topic"
            order by value
        """
        kind = EntityStore(self.db, Message).kind
        return [a for a, in self.db(cmd, kind)]

    def stats(self):
        cmd = """
            select value, count(*) as count
            from attributes
            where kind=%s and attribute="topic"
            group by value
        """
        kind = EntityStore(self.db, Message).kind
        return self.db(cmd, kind)

    def clear(self):
        return EntityStore(self.db, Message).zap()

    def __call__(self, name, newest=None):
        return Topic(name, newest, self.db)

    def __str__(self):
        return str(EntityStore(self.db, Message))


def handler(request, handler, *rest):
    """Connect a database to the site if specified"""
    site = request.site
    site.queues = Queues(site.db)
    logger = logging.getLogger(__name__)
    logger.debug('queues initialized for %s', site.name)
    result = handler(request, *rest)
    return result
