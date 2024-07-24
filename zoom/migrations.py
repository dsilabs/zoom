"""
    zoom.migrations

    Work in progress - experimental
"""

import logging

import zoom


class SystemMigrationRecord(zoom.utils.Record):
    """Migration Record"""
    pass


class Migration(object):  # pragma: no cover
    """Migration

    Provies the methods to apply or revert transformations
    to get system to a desired state.
    """

    def __init__(self, db):
        self.db = db

    def apply(self):
        """apply changes to the database"""
        pass

    def revert(self):
        """Revert changes to the database"""
        pass

    @property
    def name(self):
        return self.__doc__.splitlines()[0]


class StartMigration(Migration):
    """Start Migration

    This is a starting state migration.  It serves as a starting point
    for the system before any migrations were applied and does not
    itself apply any data transformations.  This migration should be used
    as the first element of all migration sequences.

    In theory, migrating back to this state should put the database back
    into its original state.  By "in theory" we mean that assuming all
    of the applied migrations are completely revertable which may not
    be the case in all cases.
    """
    pass


class Migrations(object):
    """performs the migration steps needed to get to the target version

    Systems are migrated from one state to another by providing a sequence
    of steps typically subclassed from the Migration class.  Migrations
    should provide both an apply method to peform a transformation to take a
    system to a desired state and, where possible, a revert method to undo the
    transformation to transform the sytem back to its original state.

    As they are applied and reverted, the migrations are tracked in a
    data store including the name of the object peforming the migration (
    usually a subclass of Migration) the version of the system that was
    attained by applying or reverting the migration, the revision number
    of the migration (an integer representing the application or reversion
    of a transformation), the method used (apply or revert) and the timestamp
    of when the migration took place.

    >>> class AddFaxColumnToUser(Migration):
    ...     def apply(self):
    ...         self.db('alter table users add column fax char(30)')
    ...     def revert(self):
    ...         self.db('alter table users drop column fax')

    >>> steps = [
    ...     StartMigration,
    ...     AddFaxColumnToUser,
    ... ]

    >>> zoom.system.site = site = zoom.sites.Site()
    >>> site.db = zoom.database.setup_test()

    >>> print(site.db('describe users'))  # doctest: +SKIP
    Field      Type             Null Key Default Extra
    ---------- ---------------- ---- --- ------- --------------
    id         int(10) unsigned NO   PRI None    auto_increment
    username   char(50)         NO   UNI None
    password   varchar(125)     YES      None
    first_name char(40)         YES      None
    last_name  char(40)         YES      None
    email      char(60)         YES  MUL None
    phone      char(30)         YES      None
    created    datetime         YES      None
    updated    datetime         YES      None
    last_seen  datetime         YES  MUL None
    created_by int(10) unsigned YES      None
    updated_by int(10) unsigned YES      None
    status     char(1)          YES      None

    >>> migrations = Migrations(site.db, steps)
    >>> migrations.migrate()

    >>> print(site.db('describe users'))  # doctest: +SKIP
    Field      Type             Null Key Default Extra
    ---------- ---------------- ---- --- ------- --------------
    id         int(10) unsigned NO   PRI None    auto_increment
    username   char(50)         NO   UNI None
    password   varchar(125)     YES      None
    first_name char(40)         YES      None
    last_name  char(40)         YES      None
    email      char(60)         YES  MUL None
    phone      char(30)         YES      None
    created    datetime         YES      None
    updated    datetime         YES      None
    last_seen  datetime         YES  MUL None
    created_by int(10) unsigned YES      None
    updated_by int(10) unsigned YES      None
    status     char(1)          YES      None
    fax        char(30)         YES      None

    >>> migrations.migrate(0)
    >>> print(site.db('describe users'))  # doctest: +SKIP
    Field      Type             Null Key Default Extra
    ---------- ---------------- ---- --- ------- --------------
    id         int(10) unsigned NO   PRI None    auto_increment
    username   char(50)         NO   UNI None
    password   varchar(125)     YES      None
    first_name char(40)         YES      None
    last_name  char(40)         YES      None
    email      char(60)         YES  MUL None
    phone      char(30)         YES      None
    created    datetime         YES      None
    updated    datetime         YES      None
    last_seen  datetime         YES  MUL None
    created_by int(10) unsigned YES      None
    updated_by int(10) unsigned YES      None
    status     char(1)          YES      None

    >>> migrations.revisions.zap()

    """

    def __init__(self, db, steps):
        self.db = db
        self.steps = steps
        self.revisions = zoom.store_of(SystemMigrationRecord)

    def migrate(self, target=None):
        """migrate to a target version

        Target is the desired version.  If no target is supplied the
        migrations required to get to the most up to date version are
        applied.
        """
        logger = logging.getLogger(__name__)

        revisions = self.revisions
        target = target if target is not None else len(self.steps) - 1
        revision = max(m.revision for m in revisions) if revisions else -1
        current_version = revisions.first(revision=revision).version if revisions else -1

        if current_version < target:

            for i, migration in enumerate(self.steps):

                if i > current_version and i <= target:

                    migration(self.db).apply()
                    self.db.commit()

                    revision += 1
                    record = SystemMigrationRecord(
                        version=i,
                        revision=revision,
                        timestamp=zoom.tools.now(),
                        method='apply',
                        name=migration.__name__,
                    )
                    revisions.put(record)
                    self.db.commit()

                    logger.info(
                        'migration %s - %r applied', i, migration.__name__
                    )

                else:
                    logger.debug('skipping migration %s - %r', i, migration.__name__)

        elif current_version > target:

            for i, migration in reversed(list(enumerate(self.steps))):

                if i <= current_version and i > target:

                    migration(self.db).revert()
                    self.db.commit()

                    revision += 1
                    record = SystemMigrationRecord(
                        version=i-1,
                        revision=revision,
                        timestamp=zoom.tools.now(),
                        method='revert',
                        name=migration.__name__,
                    )
                    revisions.put(record)
                    self.db.commit()

                    logger.info(
                        'migration %s - %r reverted', i, migration.__name__
                    )

                else:
                    logger.debug('skipping migration %s - %r', i, migration.__name__)

    def replay(self, target=None):
        """replay the migrations from the beginning

        Replay all of the migrations from the beginning.  Reverts all
        migrations to this point, zaps the migration record as if it
        never happened and then runs the migrations from scratch.

        Often when developing a migration strategy it's desireable to
        rerun all of the migrations as if they had never been run before.
        This method makes that a simple call.  Once the migration
        strateigy is solidified this method would typically be
        replaced by the migrate method on it's own.

        >>> class AddFaxColumnToUser(Migration):
        ...     def apply(self):
        ...         self.db('alter table users add column fax char(30)')
        ...     def revert(self):
        ...         self.db('alter table users drop column fax')

        >>> class CombineNames(Migration):
        ...     def apply(self):
        ...         cmd = \"\"\"
        ...         alter table users
        ...            add column `name` char(80) after `password`,
        ...            drop column `first_name`,
        ...            drop column `last_name`
        ...         \"\"\"
        ...         self.db(cmd)
        ...     def revert(self):
        ...         cmd = \"\"\"
        ...         alter table users
        ...            add column `first_name` char(40) after `password`,
        ...            add column `last_name` char(40) after `first_name`,
        ...            drop column `name`
        ...         \"\"\"
        ...         self.db(cmd)

        >>> steps = [
        ...     StartMigration,
        ...     AddFaxColumnToUser,
        ...     CombineNames,
        ... ]

        >>> zoom.system.site = site = zoom.sites.Site()
        >>> site.db = zoom.database.setup_test()

        >>> print(site.db('describe users'))  # doctest: +SKIP
        Field      Type             Null Key Default Extra
        ---------- ---------------- ---- --- ------- --------------
        id         int(10) unsigned NO   PRI None    auto_increment
        username   char(50)         NO   UNI None
        password   varchar(125)     YES      None
        first_name char(40)         YES      None
        last_name  char(40)         YES      None
        email      char(60)         YES  MUL None
        phone      char(30)         YES      None
        created    datetime         YES      None
        updated    datetime         YES      None
        last_seen  datetime         YES  MUL None
        created_by int(10) unsigned YES      None
        updated_by int(10) unsigned YES      None
        status     char(1)          YES      None

        >>> migrations = Migrations(site.db, steps)

        >>> migrations.migrate()
        >>> print(site.db('describe users'))  # doctest: +SKIP
        Field      Type             Null Key Default Extra
        ---------- ---------------- ---- --- ------- --------------
        id         int(10) unsigned NO   PRI None    auto_increment
        username   char(50)         NO   UNI None
        password   varchar(125)     YES      None
        name       char(80)         YES      None
        email      char(60)         YES  MUL None
        phone      char(30)         YES      None
        created    datetime         YES      None
        updated    datetime         YES      None
        last_seen  datetime         YES  MUL None
        created_by int(10) unsigned YES      None
        updated_by int(10) unsigned YES      None
        status     char(1)          YES      None
        fax        char(30)         YES      None

        >>> migrations.replay(1)
        >>> print(site.db('describe users'))  # doctest: +SKIP
        Field      Type             Null Key Default Extra
        ---------- ---------------- ---- --- ------- --------------
        id         int(10) unsigned NO   PRI None    auto_increment
        username   char(50)         NO   UNI None
        password   varchar(125)     YES      None
        first_name char(40)         YES      None
        last_name  char(40)         YES      None
        email      char(60)         YES  MUL None
        phone      char(30)         YES      None
        created    datetime         YES      None
        updated    datetime         YES      None
        last_seen  datetime         YES  MUL None
        created_by int(10) unsigned YES      None
        updated_by int(10) unsigned YES      None
        status     char(1)          YES      None
        fax        char(30)         YES      None

        """
        self.migrate(0)
        self.revisions.zap()
        self.migrate(target)



