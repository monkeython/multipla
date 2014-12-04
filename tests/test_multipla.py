import gc
import importlib
import os
import unittest
import sys
import types
import pkg_resources

import multipla

import genty

class NoIteritems(object):
    def __init__(self, items=(), **args):
        self._dict = dict(items, **args)

    def __getitem__(self, key):
        return self._dict[key]

    def keys(self):
        return self._dict.keys()


class Testlock(unittest.TestCase):

    def test_Lock(self):
        lock = multipla.Lock()
        with lock:
            self.assertTrue(lock)
        self.assertFalse(lock)


@genty.genty
class TestRatedDict(unittest.TestCase):
    def setUp(self):
        self.rd = multipla.RatedDict()

    def test___str__(self):
        name = self.rd.__class__.__name__
        self.assertEqual(str(self.rd), "<{} '{}'>".format(name, id(self.rd)))

    def test_dict_syntax(self):
        self.rd['test'] = 7
        self.assertEqual(len(self.rd), 1)
        self.assertEqual(self.rd._dict['test'], 7)
        self.assertEqual(self.rd._ratings['test'], 0)
        self.assertEqual(self.rd['test'], 7)
        with self.assertRaises(KeyError):
            self.rd['exception']
        del self.rd['test']
        self.assertNotIn('test', self.rd._dict)
        self.assertNotIn('test', self.rd._ratings)
        self.assertFalse(self.rd._dict)
        self.assertFalse(self.rd._ratings)
        self.assertNotIn('test', self.rd)
        self.assertFalse(len(self.rd))
        self.rd.update(a=1, b=2, c=3, d=4)
        self.rd.rate(a=5, b=6, c=1, d=3)
        self.assertEqual(list(reversed(self.rd)), ['c', 'd', 'a', 'b'])
        self.assertEqual([k for k in self.rd], ['b', 'a', 'd', 'c'])

    @genty.genty_dataset(
        ({'a': 1, 'b': 2, 'c': 3}, {'d': 4, 'e': 5}),
        ((('f', 6), ('g', 7), ('h', 8)), {'i': 9, 'j': 10}),
        (NoIteritems({'k': 11, 'l': 12}, m=13), {'n': 14, 'o': 15}))
    def test_update_values(self, values, kwargs):
        self.rd.update(values, **kwargs)
        self.assertItemsEqual(list(self.rd._dict.keys()),
                              list(self.rd._ratings.keys()))
        for key in self.rd._dict:
            self.assertEqual(self.rd._ratings[key], 0)

    def test_update(self):
        with self.assertRaises(TypeError):
            self.rd.update(None)
        for update in (tuple(), list(), dict(), set(), frozenset()):
            self.rd.update(update)
            self.assertFalse(self.rd._dict)
            self.assertFalse(self.rd._ratings)

    def test_rate(self):
        self.rd.update(a=1, b=2, c=3)
        self.assertItemsEqual(self.rd._ratings.values(), [0, 0, 0])
        self.rd.rate(a=2, b=3, c=4)
        self.assertItemsEqual(self.rd._ratings.values(), [2, 3, 4])
        self.assertEqual(list(self.rd._ratings.keys()), ['c', 'b', 'a'])
        with self.assertRaises(KeyError):
            self.rd.rate(d=1)

    def test_top(self):
        self.rd.update(a=1, b=2, c=4, d=8, e=16)
        self.rd.rate(a=5, b=4, c=3)
        self.assertEqual(self.rd.top(3), [('a', 1), ('b', 2), ('c', 4)])
        with self.assertRaises(ValueError):
            self.rd.top(10)
        top = self.rd.top()
        self.assertEqual(len(top), 5)

    def test_highest_rated(self):
        with self.assertRaises(ValueError):
            self.rd.highest_rated
        self.rd.update(a=1, b=4, c=16)
        self.rd.rate(a=16)
        self.assertEqual(self.rd.highest_rated, 1)

class TestMultiPlugAdapter(unittest.TestCase):

    def setUp(self):
        super(TestMultiPlugAdapter, self).setUp()
        self.mpa = multipla.MultiPlugAdapter('test')

    def test___str__(self):
        self.assertEqual(str(self.mpa), "<MultiPlugAdapter 'test'>")

    def test_plug_in(self):
        self.assertEqual(1, self.mpa.plug_in('test', 1))
        with self.assertRaises(KeyError):
            self.mpa.plug_in('test', 10)

class TestMultipla(unittest.TestCase):

    def setUp(self):
        super(TestMultipla, self).setUp()
        self.mp = multipla.Multipla('test')

    def test_switch_on(self):
        mpa = self.mp.switch_on('test')
        self.assertEqual(mpa.name, 'test')
        self.assertIs(mpa, self.mp.switch_on('test'))

    def test_get(self):
        self.assertIsNone(self.mp.get('first'))
        test = self.mp.switch_on('test')
        test.plug_in('first', 1)
        test.plug_in('second', 2)
        test.plug_in('third', 3)
        test.rate({'first': 1, 'second': 3})
        self.assertEqual(self.mp.get('test'), 2)

class TestModuleFunctions(unittest.TestCase):

    def test_power_up(self):
        test = multipla.power_up('test', pkg_resources.working_set)
        self.assertIs(test, multipla.power_up('test'))
        self.assertIsInstance(test, multipla.Multipla)