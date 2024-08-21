"""
    Test the mvc module
"""

import os
import unittest

from zoom.mvc import evaluate, View, Controller, Dispatcher


class MyCallable(object):

    def __call__(self, s):
        return s.lower()


class TestEvaluate(unittest.TestCase):

    class MyView(View):

        v1 = 'avalue'

        def f1(self):
            return 'done'

        def f1a(self):
            def f():
                return 'x'
            return f('unexpected')

        def f1b(self, key, **kwargs):
            def f(t, n):
                return 'x'
            return f(key)

        def f2(self, *args, **kwargs):
            return args, kwargs

        def f3(self, key, *args, **kwargs):
            return key, args, kwargs

        def upper(self, s):
            return s.upper()

        lower = MyCallable()

    view = MyView()

    def test_evaluate(self):
        view = self.view
        self.assertEqual(evaluate(view, 'v1', (), {}), 'avalue')
        self.assertEqual(evaluate(view, 'f1', (), {}), 'done')
        self.assertEqual(evaluate(view, 'f2', ('akey',), {}), (('akey',), {}))
        self.assertEqual(evaluate(view, 'f3', ('akey',), {}), ('akey', (), {}))

    def test_missing_parameters(self):
        with self.assertRaises(TypeError):
            evaluate(self.view, 'f3')

    def test_legacy_parameterless_method(self):
        with self.assertRaises(TypeError):
            evaluate(self.view, 'f1', ('key',), dict(name='test'))
        self.assertEqual(evaluate(self.view, 'f1', ('key',), dict(name='test')), 'done')

    def test_legacy_parameterless_method(self):
        # this form of call is no longer supported, checking to make sure
        # Zoom does the right thing if it encounters it.
        with self.assertRaises(TypeError):
            evaluate(self.view, 'f1', ('key',), dict(name='test'))
        with self.assertRaises(TypeError):
            evaluate(self.view, 'f1a', ('key',), dict(name='test'))
        with self.assertRaises(TypeError) as e:
            evaluate(self.view, 'f1b', ('key',), dict(name='test'))
        # make sure we're reporting the offending call
        self.assertTrue('f() missing' in str(e.exception))

    def test_exception_raising(self):
        self.assertEqual(self.view('upper', 'x'), 'X')
        with self.assertRaises(TypeError) as e:
            self.assertEqual(self.view('upper', 'x', 'y'), 'X')
        self.assertEqual(self.view.lower('Y'), 'y')
        msg = 'upper() takes 2 positional arguments but 3 were given'
        self.assertTrue(msg in str(e.exception))

        self.assertEqual(self.view.lower('X'), 'x')
        with self.assertRaises(TypeError) as e:
            self.assertEqual(self.view.lower('X', 'Y'), 'x')
        msg = '__call__() takes 2 positional arguments but 3 were given'
        self.assertTrue(msg in str(e.exception))

        with self.assertRaises(TypeError) as e:
            self.assertEqual(self.view('lower', 'X', 'Y'), 'x')
        msg = '__call__() takes 2 positional arguments but 3 were given'
        self.assertTrue(msg in str(e.exception))
