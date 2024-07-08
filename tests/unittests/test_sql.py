"""
    test sql
"""

import unittest

from zoom.sqltools import (
    summarize,
    make_table_select, make_store_select,
    occurs, greater_than_or_equal_to
)


class TestSummarize(unittest.TestCase):

    def test_one_class_var(self):
        query = summarize('person', ['age'])
        self.assertEqual(
            query,
            (
                'select "*" age, count(*) n from person group by 1\n'
                'union select age age, count(*) n from person group by 1'
            )
        )

    def test_two_class_vars(self):
        query = summarize('person', ['age', 'amount'])
        self.assertEqual(
            query,
            (
                'select "*" age, "*" amount, count(*) n from person group by 1, 2\n'
                'union select "*" age, amount amount, count(*) n from person group by 1, 2\n'
                'union select age age, "*" amount, count(*) n from person group by 1, 2\n'
                'union select age age, amount amount, count(*) n from person group by 1, 2'
            )
        )

    def test_one_class_one_sum(self):
        query = summarize('person', ['region'], ['salary'])
        self.assertEqual(
            query,
            (
                'select "*" region, count(*) n, sum(salary) salary from person group by 1\n'
                'union select region region, count(*) n, sum(salary) salary from person group by 1'
            )
        )

    def test_one_class_two_sum(self):
        query = summarize('person', ['region'], ['sales', 'salary'])
        self.assertEqual(
            query,
            (
                'select "*" region, count(*) n, sum(sales) sales, sum(salary) salary from person group by 1\n'
                'union select region region, count(*) n, sum(sales) sales, sum(salary) salary from person group by 1'
            )
        )


class TestQuery(unittest.TestCase):

    def test_simple(self):
        q1 = make_table_select('people', name='Joe')
        self.assertEqual(
            q1,
            ('select * from people where name==%s', ['Joe'])
        )

    def test_simple_occurs(self):
        q1 = make_table_select('people', name='Joe', age=occurs([4]))
        self.assertEqual(
            q1,
            ('select * from people where age in %s and name==%s', [[4], 'Joe'])
        )

    def test_ge(self):
        q1 = make_table_select('people', name='Joe', age=greater_than_or_equal_to(4))
        self.assertEqual(
            q1,
            ('select * from people where age>=%s and name==%s', [4, 'Joe'])
        )


class TestEntityQuery(unittest.TestCase):

    def test_simple(self):
        q1 = make_store_select('people', name='Joe')
        print(q1)
        self.assertEqual(
            q1,
            (
                'select row_id, attribute, datatype, value from attributes where kind="people" and \n'
                '  row_id in (select row_id from attributes where kind="people" and `attribute`="name" and value="Joe")'
            )
        )

    def test_ge(self):
        q1 = make_store_select('people', name='Joe', age=greater_than_or_equal_to(4))
        print(q1)
        self.assertEqual(
            q1,
            (
                'select row_id, attribute, datatype, value from attributes where kind="people" and \n'
                '  row_id in (select row_id from attributes where kind="people" and `attribute`="age" and CAST(`value` AS INTEGER)>=4) and\n'
                '  row_id in (select row_id from attributes where kind="people" and `attribute`="name" and value="Joe")'
            )
        )

