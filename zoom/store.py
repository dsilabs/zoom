"""
    zoom.store

    key value store
"""

import datetime
import decimal

import zoom.utils
import zoom.exceptions
import zoom.jsonz
from zoom.database import setup_test


Record = Entity = zoom.utils.Record
EntityList = zoom.utils.RecordList


def entify(rs, storage):
    """
    converts query result into an EntityList
    """
    klass = storage.klass
    entities = {}

    if hasattr(rs, 'data'):  # maintain backward compatibility with
        rs = rs.data         # legacy database module

    for _, _, row_id, attribute, datatype, value in rs:

        if datatype == 'str':
            pass

        elif datatype == 'unicode' and isinstance(value, str):
            pass

        elif datatype == 'unicode':
            value = value.decode('utf8')

        elif datatype == "int":
            value = int(value)

        elif datatype == 'float':
            value = float(value)

        elif datatype == 'decimal.Decimal':
            value = decimal.Decimal(value)

        elif datatype == "datetime.date":
            y = int(value[:4])
            m = int(value[5:7])
            d = int(value[8:10])
            value = datetime.date(y, m, d)

        elif datatype == "datetime.datetime":
            y = int(value[:4])
            m = int(value[5:7])
            d = int(value[8:10])
            hr = int(value[11:13])
            mn = int(value[14:16])
            sc = int(value[17:19])
            value = datetime.datetime(y, m, d, hr, mn, sc)

        elif datatype == 'bool':
            value = (value == '1' or value == 'True')

        elif datatype == 'NoneType':
            value = None

        elif datatype == 'instance':
            value = int(rec.id)

        elif datatype in ['list', 'tuple']:
            value = zoom.jsonz.loads(value)

        else:
            msg = 'unsupported data type: ' + repr(datatype)
            raise zoom.exceptions.TypeException(msg)

        entities.setdefault(row_id, klass(_id=row_id, __store=storage))[attribute] = value

    return EntityList(entities.values())


class Store(object):

    def before_update(self, record):
        pass

    def after_update(self, record):
        pass

    def before_insert(self, record):
        pass

    def after_insert(self, record):
        pass

    def before_delete(self, ids):
        pass

    def after_delete(self, ids):
        pass


class EntityStore(Store):
    """stores entities

        >>> db = setup_test()

        >>> stuff = EntityStore(db)
        >>> stuff.put(dict(name='Joe', age=14))
        1
        >>> stuff.put(dict(name='Sally', age=34))
        2
        >>> stuff.put(dict(name='Sam', age=34))
        3
        >>> print(zoom.utils.RecordList(stuff.find(name='Joe')))
        dict
        _id name age
        --- ---- ---
          1 Joe   14
        1 dict records
        >>> s = stuff.find(age=34)
        >>> print(s)
        dict
        _id name  age
        --- ----- ---
          2 Sally  34
          3 Sam    34
        2 dict records

        >>> db = setup_test()
        >>> class Person(Entity): pass
        >>> class People(EntityStore): pass
        >>> people = People(db, Person)
        >>> people.kind
        'person'
        >>> joe = Person(name='Joe', age=20, birthdate=datetime.date(1992,5,5))
        >>> joe
        <Person {'name': 'Joe', 'age': 20, 'birthdate': datetime.date(1992, 5, 5)}>
        >>> people.put(joe)
        1
        >>> person = people.get(1)
        >>> person
        <Person {'name': 'Joe', 'age': 20, 'birthdate': datetime.date(1992, 5, 5)}>
        >>> sally = Person(name='Sally', kids=0, birthdate=datetime.date(1992,5,5))
        >>> people.put(sally)
        2
        >>> sally = people.find(name='Sally')
        >>> sally
        [<Person {'name': 'Sally', 'kids': 0, 'birthdate': datetime.date(1992, 5, 5)}>]
        >>> sally = people.first(name='Sally')
        >>> sally
        <Person {'name': 'Sally', 'kids': 0, 'birthdate': datetime.date(1992, 5, 5)}>
        >>> sally.kids += 1
        >>> people.put(sally)
        2
        >>> people.first(name='Sally')
        <Person {'name': 'Sally', 'kids': 1, 'birthdate': datetime.date(1992, 5, 5)}>
        >>> sally = people.first(name='Sally')
        >>> sally.kids += 1
        >>> people.put(sally)
        2
        >>> people.first(name='Sally')
        <Person {'name': 'Sally', 'kids': 2, 'birthdate': datetime.date(1992, 5, 5)}>
        >>> sally = people.first(name='Sally')
        >>> sally.kids += 1
        >>> people.put(sally)
        2
        >>> people.first(name='Sally')
        <Person {'name': 'Sally', 'kids': 3, 'birthdate': datetime.date(1992, 5, 5)}>

        >>> class Misc(EntityStore): pass
        >>> misc = Misc(db, dict)
        >>> config_info = dict(host='database', name='somename')
        >>> id = misc.put(config_info)
        >>> x = misc.put(dict(other='this', stuff='that'))
        >>> my_info = misc.get(id)
        >>> Record(my_info)
        <Record {'name': 'somename', 'host': 'database'}>
        >>> Record(misc.get(x))
        <Record {'other': 'this', 'stuff': 'that'}>

        >>> people = EntityStore(db, 'person')
        >>> people.klass
        <class 'dict'>
        >>> people.kind
        'person'
        >>> print(sorted(people.first(name='Sally').items()))
        [('__store', <EntityStore(dict)>), ('_id', 2), ('birthdate', datetime.date(1992, 5, 5)), ('kids', 3), ('name', 'Sally')]
        >>> print(Person(people.first(name='Sally')))
        Person
          name ................: 'Sally'
          kids ................: 3
          birthdate ...........: datetime.date(1992, 5, 5)
        >>> EntityStore(db, 'person').first(name='Joe')['age']
        20
        >>>
        >>> name = 'somename'
        >>> id = misc.put(dict(host='database', name=name))
        >>> my_info = misc.get(id)
        >>> assert type(my_info['name'])==type(name)

    """

    def __init__(self, db, klass=dict, kind=None):
        self.db = db
        self.klass = type(klass) == str and dict or klass
        self.kind = kind or type(klass) == str and klass or zoom.utils.kind(klass())
        self.key = 'id'
        self.id_name = '_id'

    def put(self, entity):
        """
        stores an entity

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> sally = Person(name='Sally', age=25)
            >>> sally
            <Person {'name': 'Sally', 'age': 25}>
            >>> id = people.put(Person(name='Sally', age=25))
            >>> id
            1
            >>> sally
            <Person {'name': 'Sally', 'age': 25}>
            >>> sally = people.get(id)
            >>> sally
            <Person {'name': 'Sally', 'age': 25}>
            >>> sally.age = 35
            >>> people.put(sally)
            1
            >>> person = people.get(id)
            >>> person
            <Person {'name': 'Sally', 'age': 35}>
            >>> id = people.put({'name':'James', 'age':15})
            >>> id
            2
            >>> people.get(id)
            <Person {'name': 'James', 'age': 15}>
            >>> classes = ['one', 'Not this one']
            >>> grades = (('one', 'A'), ('Not this one', 'C+'), )
            >>> id = people.put({'name':'James', 'classes':classes, 'grades': grades})
            >>> assert classes == people.get(id).classes
            >>> assert len(people.get(id).grades) == 2  # json dump/load will bring back all tuples as lists
            >>> db.close()

        """
        def fixval(d):
            if type(d) == datetime.datetime:
                # avoids mysqldb reliance on strftime that lacks support
                # for dates before 1900
                return "%02d-%02d-%02d %02d:%02d:%02d" % (
                    d.year,
                    d.month,
                    d.day,
                    d.hour,
                    d.minute,
                    d.second
                    )
            if type(d) == decimal.Decimal:
                return str(d)
            if isinstance(d, (list, tuple)):
                return zoom.jsonz.dumps(d)
            return d

        def get_type_str(v):
            t = repr(type(v))
            if 'type' in t:
                return t.strip('<type >').strip("'")
            elif 'class' in t:
                return t.strip('<class >').strip("'")
            else:
                return t

        db = self.db

        updating = '_id' in entity
        if updating:
            self.before_update(entity)
        else:
            self.before_insert(entity)

        keys = [k for k in list(entity.keys()) if k not in ('_id', '__store')]
        values = [entity[k] for k in keys]
        datatypes = [get_type_str(v) for v in values]
        values = [fixval(i) for i in values]  # same fix as above
        valid_types = [
            'str', 'unicode', 'int', 'float', 'decimal.Decimal',
            'datetime.date', 'datetime.datetime', 'bool', 'NoneType',
            'list', 'tuple'
            ]

        for n, atype in enumerate(datatypes):
            if atype not in valid_types:
                msg = 'unsupported type <type %s> in value %r'
                raise zoom.exceptions.TypeException(msg % (atype, keys[n]))

        if updating:
            id = entity['_id']
            db('delete from attributes where row_id=%s', id)
        else:
            db('insert into entities (kind) values (%s)', self.kind)
            id = entity['_id'] = db.lastrowid
            entity['__store'] = self

        n = len(keys)
        lkeys = [k.lower() for k in keys]
        param_list = list(zip([self.kind]*n, [id]*n, lkeys, datatypes, values))
        cmd = (
            'insert into attributes ('
            '    kind, row_id, attribute, datatype, value'
            ') values (%s,%s,%s,%s,%s)'
            )
        db.execute_many(cmd, param_list)

        if updating:
            self.after_update(entity)
        else:
            self.after_insert(entity)

        return id

    def get(self, keys):
        """
        retrives entities

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(**{'name': 'Sam', 'age':15,
            ...     'salary': decimal.Decimal('100.00')}))
            >>> sam = people.get(id)
            >>> sam
            <Person {'name': 'Sam', 'age': 15, 'salary': Decimal('100.00')}>
            >>> people.put(Person(name='Jim', age=21,
            ...    salary=decimal.Decimal('50')))
            2
            >>> people.put(Person(name='Alice', age=29))
            3
            >>> print(people)
            person
            _id name  age salary
            --- ----- --- ------
              1 Sam    15 100.00
              2 Jim    21 50
              3 Alice  29 None
            3 person records

            >>> print(people.get([1, '3']))
            person
            _id name  age salary
            --- ----- --- ------
              1 Sam    15 100.00
              3 Alice  29 None
            2 person records

            >>> db.close()
        """
        if keys is None:
            return None

        if not isinstance(keys, (list, tuple)):
            keys = (keys,)
            as_list = 0
        else:
            as_list = 1
        keys = [int(key) for key in keys]

        if not keys:
            if as_list:
                return []
            else:
                return None

        cmd = 'select * from attributes where kind=%s and row_id in (%s)' % (
            '%s', ','.join(['%s']*len(keys))
            )
        rs = self.db(cmd, self.kind, *keys)

        result = entify(rs, self)

        if as_list:
            return result
        if result:
            return result[0]

    def get_attributes(self):
        """
        get complete set of attributes for the entity type

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> sam = Person(**{'name': 'Sam', 'age':15})
            >>> sorted(sam.keys())
            ['age', 'name']
            >>> id = people.put(sam)
            >>> sorted(people.get_attributes())
            ['age', 'name']
            >>> db.close()

        """
        # order by id desc so that newly introduced attributes appear at
        # the end of the keys list
        cmd = (
            'select distinct attribute, id '
            'from attributes '
            'where kind=%s order by id desc'
        )
        rs = self.db(cmd, self.kind)
        values = [rec[0] for rec in rs]
        return values

    def _delete(self, ids):
        if ids:
            self.before_delete(ids)
            spots = ','.join('%s' for _ in ids)
            cmd = 'delete from attributes where row_id in ({})'.format(spots)
            self.db(cmd, *ids)
            cmd = 'delete from entities where id in ({})'.format(spots)
            self.db(cmd, *ids)
            self.after_delete(ids)
            return ids

    def delete(self, *args, **kwargs):
        """
        delete entities

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sally', age=25))
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Joe', age=25))
            >>> joe = people.get(id)
            >>> id
            3
            >>> bool(joe)
            True
            >>> joe
            <Person {'name': 'Joe', 'age': 25}>
            >>> people.delete(id)
            [3]
            >>> joe = people.get(id)
            >>> joe
            >>> bool(joe)
            False

            >>> bool(people.find(name='Sally'))
            True
            >>> people.delete(name='Sallie')
            >>> bool(people.find(name='Sally'))
            True
            >>> people.delete()
            >>> people.delete(name='Sally')
            [1]
            >>> bool(people.find(name='Sally'))
            False

            >>> db.close()

        """
        ids = []
        for key in args:
            if hasattr(key, 'get'):
                key = key['_id']
            ids.append(key)
        if kwargs:
            ids.extend(self._find(**kwargs))
        return self._delete(ids)

    def exists(self, keys=None):
        """
        tests for existence of an entity

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sally', age=25))
            >>> sally = people.get(id)
            >>> sally
            <Person {'name': 'Sally', 'age': 25}>
            >>> people.exists(1)
            True
            >>> people.exists(2)
            False
            >>> people.exists([1, 2])
            [True, False]
            >>> id = people.put(Person(name='Sam', age=25))
            >>> people.exists([1, 2])
            [True, True]
            >>> db.close()

        """
        if not isinstance(keys, (list, tuple)):
            keys = (keys,)
        slots = (','.join(['%s']*len(keys)))
        cmd = (
            'select distinct row_id '
            'from attributes '
            'where row_id in (%s)'
            ) % slots
        rs = self.db(cmd, *keys)

        found_keys = [rec[0] for rec in rs]
        if len(keys) > 1:
            result = [(key in found_keys) for key in keys]
        else:
            result = keys[0] in found_keys
        return result

    def all(self):
        """
        Retrieves all entities

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sally', age=25))
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Joe', age=25))
            >>> people.all()
            [<Person {'name': 'Sally', 'age': 25}>, <Person {'name': 'Sam', 'age': 25}>, <Person {'name': 'Joe', 'age': 25}>]
            >>> db.close()

        """
        cmd = 'select * from attributes where kind="%s"' % (self.kind)
        return entify(self.db(cmd), self)

    def zap(self):
        """
        deletes all entities of the given kind

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sally', age=25))
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Joe', age=25))
            >>> people.all()
            [<Person {'name': 'Sally', 'age': 25}>, <Person {'name': 'Sam', 'age': 25}>, <Person {'name': 'Joe', 'age': 25}>]
            >>> people.zap()
            >>> people.all()
            []
            >>> db.close()

        """
        cmd = 'delete from attributes where kind=%s'
        self.db(cmd, self.kind)
        cmd = 'delete from entities where kind=%s'
        self.db(cmd, self.kind)

    def __len__(self):
        """
        returns number of entities

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> len(people)
            0
            >>> id = people.put(Person(name='Sam', age=15))
            >>> id = people.put(Person(name='Sally', age=25))
            >>> len(people)
            2
            >>> db.close()

        """
        cmd = ('select count(*) n from '
               '(select distinct row_id from attributes where kind=%s) a')
        r = self.db(cmd, self.kind)
        return int(list(r)[0][0])

    def _find(self, **kv):
        """
        Find keys that meet search critieria
        """
        db = self.db
        all_keys = []
        for field_name in kv.keys():
            value = kv[field_name]
            if value is not None:
                if not isinstance(value, (list, tuple)):
                    wc = 'value=%s'
                    v = (value,)
                else:
                    wc = 'value in ('+','.join(['%s']*len(value))+')'
                    v = value
                cmd = 'select distinct row_id from attributes where kind=%s and attribute=%s and '+wc
                rs = db(cmd, self.kind, field_name.lower(), *v)
                all_keys.append([rec[0] for rec in rs])
        answer = all_keys and set(all_keys[0]) or set()
        for keys in all_keys[1:]:
            answer = set(keys) & answer
        if answer:
            return list(answer)
        else:
            return []

    def find(self, **kv):
        """
        finds entities that meet search criteria

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Sally', age=55))
            >>> id = people.put(Person(name='Bob', age=25))

            >>> print(people.find(age=25))
            person
            _id name age
            --- ---- ---
              1 Sam   25
              3 Bob   25
            2 person records

            >>> len(people.find(name='Sam'))
            1

            >>> db.close()

        """
        return self.get(self._find(**kv))

    def first(self, **kv):
        """
        finds the first entity that meet search criteria

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Sally', age=55))
            >>> id = people.put(Person(name='Bob', age=25))
            >>> people.first(age=5)
            >>> people.first(age=25)
            <Person {'name': 'Sam', 'age': 25}>
            >>> db.close()

        """
        for item in self.find(**kv):
            return item

    def last(self, **kv):
        """
        finds the last entity that meet search criteria

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Sally', age=55))
            >>> id = people.put(Person(name='Bob', age=25))
            >>> people.last(age=5)
            >>> people.last(age=25)
            <Person {'name': 'Bob', 'age': 25}>
            >>> db.close()

        """
        rows = self._find(**kv)
        if rows:
            return self.get(rows[-1])
        return None

    def search(self, text):
        """
        search for entities that match text

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Sally', age=55))
            >>> id = people.put(Person(name='Bob', age=25))

            >>> list(people.search('bob'))
            [<Person {'name': 'Bob', 'age': 25}>]

            >>> for r in list(people.search(25)): print(r)
            Person
              name ................: 'Sam'
              age .................: 25
            Person
              name ................: 'Bob'
              age .................: 25

            >>> list(people.search('Bill'))
            []
            >>> db.close()

        """
        t = str(text).lower()
        for rec in self:
            if t in repr(list(rec.values())).lower():
                yield rec

    def __iter__(self):
        """
        interates through records

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Sally', age=55))
            >>> id = people.put(Person(name='Bob', age=25))
            >>> for rec in people: print(rec)
            Person
              name ................: 'Sam'
              age .................: 25
            Person
              name ................: 'Sally'
              age .................: 55
            Person
              name ................: 'Bob'
              age .................: 25
            >>> sum(person.age for person in people)
            105

        """
        return self.all()

    def __getitem__(self, key):
        """
        return entities or slices of entities by position

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Sally', age=55))
            >>> id = people.put(Person(name='Bob', age=25))

            >>> people[0]
            <Person {'name': 'Sam', 'age': 25}>

            >>> people[1]
            <Person {'name': 'Sally', 'age': 55}>

            >>> people[-1]
            <Person {'name': 'Bob', 'age': 25}>

            >>> people[0:2]
            [<Person {'name': 'Sam', 'age': 25}>, <Person {'name': 'Sally', 'age': 55}>]

            >>> people[::2]
            [<Person {'name': 'Sam', 'age': 25}>, <Person {'name': 'Bob', 'age': 25}>]

            >>> people[::-2]
            [<Person {'name': 'Bob', 'age': 25}>, <Person {'name': 'Sam', 'age': 25}>]

            >>> people[1:-1]
            [<Person {'name': 'Sally', 'age': 55}>]

            >>> try:
            ...     people[3]
            ... except IndexError as e:
            ...     print(e)
            Index (3) out of range

            >>> db.close()

        """
        n = len(self)
        if isinstance(key, slice):
            # get the start, stop, and step from the slice
            start, stop, step = key.indices(n)
            return [self[ii] for ii in range(start, stop, step)]
        elif isinstance(key, int):
            if key < 0:
                key += n
            elif key >= n:
                raise IndexError('Index ({}) out of range'.format(key))
            cmd = (
                'select distinct row_id '
                'from attributes '
                'where kind="%s" '
                'limit %s,1'
                ) % (self.kind, key)
            rs = self.db(cmd)
            if rs:
                return self.get(list(rs)[0][0])
            else:
                return 'no records'
        else:
            raise TypeError('Invalid argument type')

    def __str__(self):
        """
        format for humans

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Sally', age=55))
            >>> id = people.put(Person(name='Bob', age=25))
            >>> print(people)
            person
            _id name  age
            --- ----- ---
              1 Sam    25
              2 Sally  55
              3 Bob    25
            3 person records

            >>> people.zap()
            >>> print(people)
            Empty list

        """
        return str(self.all())

    def __repr__(self):
        """
        unabiguous representation

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Sally', age=55))
            >>> id = people.put(Person(name='Bob', age=25))
            >>> repr(people)
            '<EntityStore(Person)>'
            >>> len(people)
            3
            >>> people.zap()
            >>> people
            <EntityStore(Person)>
            >>> len(people)
            0

        """
        return '<EntityStore({})>'.format(self.klass.__name__)
