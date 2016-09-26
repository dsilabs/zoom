"""
    Test the database module
"""

# pylint: disable=missing-docstring
# method names are more useful for testing

# pylint: disable=invalid-name

import unittest
import sqlite3
import logging
from decimal import Decimal
from datetime import date, datetime

from zoom.database import Database

logger = logging.getLogger(__name__)

class TestDatabase(unittest.TestCase):
    """test db module"""

    # pylint: disable=too-many-public-methods
    # It's reasonable in this case.

    def setUp(self):
        self.db = Database(
            sqlite3.connect,
            ":memory:"
        )

    def tearDown(self):
        self.db.close()

    # def test_RecordSet(self):
    #     db = self.db
    #     db("""drop table if exists dzdb_test_table""")
    #     db("""create table dzdb_test_table (ID CHAR(10), AMOUNT
    #        NUMERIC(10,2),DTADD DATE,NOTES TEXT)""")
    #     db("""insert into dzdb_test_table values  ("1234",50,"2005-01-14","Hello
    #        there")""")
    #     db("""insert into dzdb_test_table values ("5678",60,"2035-01-24","New
    #        notes")""")
    #     recordset = db('select * from dzdb_test_table')
    #     print recordset
    #     for rec in recordset:
    #         self.assertEquals(rec, ("1234", 50, "2005-01-14", "Hello there"))
    #         break

    def test_db_create_drop_table(self):
        db = self.db
        db('drop table if exists dzdb_test_table')
        self.assert_('dzdb_test_table' not in db.get_tables())
        db(
           'create table dzdb_test_table ('
           '  ID CHAR(10),'
           '  AMOUNT NUMERIC(10,2),'
           '  DTADD DATE,'
           '  NOTES TEXT'
           ')'
        )
        self.assert_('dzdb_test_table' in db.get_tables())
        db('drop table dzdb_test_table')
        self.assert_('dzdb_test_table' not in db.get_tables())

    # def test_db_insert_update_record(self):
    #     # pylint: disable=protected-access
    #     insert_test = """insert into dzdb_test_table (ID, DTADD, amount, notes)
    #     values (%s, %s, %s, %s)"""
    #     select_all = 'select * from dzdb_test_table'
    #
    #     db = self.db
    #     db('drop table if exists dzdb_test_table')
    #     db("""create table dzdb_test_table (ID CHAR(10), NAME CHAR(25), AMOUNT
    #        NUMERIC(10,2), DTADD DATE, NOTES TEXT)""")
    #     dt = datetime(2005, 1, 2)
    #     db(insert_test, '1234', dt, 50, 'Testing')
    #     self.assertEqual(db(select_all).cursor.rowcount, 1)
    #     db(insert_test, '4321', dt, 10.20, 'Testing 2')
    #     self.assertEqual(db(select_all).cursor.rowcount, 2)
    #     db(insert_test, '4321', dt, None, 'Updated')
    #     self.assertEqual(db(select_all).cursor.rowcount, 3)
    #     self.assertEqual(
    #         db(
    #             'select * from dzdb_test_table'
    #         ).cursor._rows[2][4], "Updated")
    #     db('drop table dzdb_test_table')
    #
    # def test_last_rowid(self):
    #     db = self.db
    #     select_all = 'select * from dz_test_contacts'
    #     db('drop table if exists dz_test_contacts')
    #     db("""create table dz_test_contacts (contactid integer PRIMARY KEY
    #        AUTO_INCREMENT,userid char(20) UNIQUE, key (userid),password
    #        char(16), email char(60), key (email))""")
    #     db("""insert into dz_test_contacts values
    #        (1,"testuser","pass","test@datazoomer.net")""")
    #     self.assertEqual(db.lastrowid, 1)
    #     db("""insert into dz_test_contacts values
    #        (4,"2testuser","pass","test@datazoomer.net")""")
    #     self.assertEqual(db.lastrowid, 4)
    #     db.execute_many(
    #         """insert into dz_test_contacts (userid, password, email) values
    #         (%s,%s,%s)""",
    #         [
    #         ('user3', 'pass3', 'user3@datazoomer.net'),
    #         ('user4', 'pass4', 'user4@datazoomer.net'),
    #         ('user5', 'pass5', 'user5@datazoomer.net'),
    #         ('user6', 'pass6', 'user6@datazoomer.net'),
    #         ])
    #     self.assertEqual(db.lastrowid, 5)
    #     self.assertEqual(db(select_all).cursor.rowcount, 6)
    #     db('drop table dz_test_contacts')
    #
    # def test_record(self):
    #     db = self.db
    #     db("""create table dzdb_test_table (ID CHAR(10), AMOUNT
    #        NUMERIC(10,2), DTADD DATE, NOTES TEXT)""")
    #     db("""insert into dzdb_test_table values ("1234", 50, "2005-01-14",
    #        "Hello there")""")
    #     recordset = db('select * from dzdb_test_table')
    #     for rec in recordset:
    #         self.assertEqual(
    #             rec,
    #             ('1234', 50, date(2005, 1, 14), "Hello there")
    #         )
    #     db('drop table dzdb_test_table')
    #
    # def test_metadata(self):
    #     db = self.db
    #     db('drop table if exists dzdb_test_table')
    #     db("""create table dzdb_test_table (ID CHAR(10), AMOUNT
    #        NUMERIC(10,2), DTADD DATE, NOTES TEXT)""")
    #     db("""insert into dzdb_test_table values ("1234", 50, "2005-01-14",
    #        "Hello there")""")
    #     q = db('select * from dzdb_test_table')
    #     rec = [f[0] for f in q.cursor.description]
    #     self.assertEqual(rec, ['ID', 'AMOUNT', 'DTADD', 'NOTES'])
    #     db('drop table dzdb_test_table')
    #
    # def test_Database_decimal(self):
    #     db = self.db
    #
    #     db('drop table if exists dzdb_test_table')
    #     db("""create table dzdb_test_table (ID CHAR(10), AMOUNT
    #        NUMERIC(10,2), DTADD DATE, NOTES TEXT, BUCKS DECIMAL(8,2))""")
    #     db("""insert into dzdb_test_table values ("100", 10.24, %s, "notes",
    #        24.10)""", date(2014, 1, 1))
    #     t = db('select * from dzdb_test_table')
    #     for row in t:
    #         self.assertEqual(row[-1], Decimal("24.10"))
    #     db('drop table dzdb_test_table')
