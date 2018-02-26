"""
    zoom.migrations

    Work in progress - experimental
"""

# pragma: no cover

import zoom

class SystemMigrationRecord(zoom.utils.Record):
    """Migration Record"""
    pass


class Migration(object):
    """Migration Logic"""

    def __init__(self, db):
        self.db = db

    def change(self):
        """Apply changes to the database"""
        pass

    def revert(self):
        """Revert changes to the database"""
        pass

    @property
    def name(self):
        return self.__doc__.splitlines()[0]


class StartMigration(Migration):
    """Initial migration"""
    pass


migrations = [
    StartMigration,
]


def migrate(to_revision=None):
    db = zoom.system.site.db

    migration_records = zoom.store.EntityStore(db, SystemMigrationRecord)
    num_migration_records = len(migration_records)

    if len(migrations) > num_migration_records:

        for i, migration in enumerate(migrations):
            if i >= num_migration_records:
                if to_revision == None or i <= to_revision:
                    migration(db).change()
                    record = SystemMigrationRecord(
                        revision=i,
                        timestame=zoom.tools.now(),
                        method='change',
                        name=migration.name,
                    )
                    migration_records.put(record)
                    zoom.system.site.log.info(
                        'migration change {!r} ran', migration.name
                    )


def rollback(to_revision=None):
    db = zoom.system.site.db

    migration_records = zoom.store.EntityStore(db, SystemMigrationRecord)
    num_migration_records = len(migration_records)

    if len(migrations) > num_migration_records:

        for i, migration in enumerate(migrations):
            if i >= num_migration_records:
                if to_revision == None or i <= to_revision:
                    migration(db).change()
                    record = SystemMigrationRecord(
                        revision=i,
                        timestame=zoom.tools.now(),
                        method='change',
                        name=migration.name,
                    )
                    migration_records.put(record)
                    zoom.system.site.log.info(
                        'migration change {!r} ran', migration.name
                    )
