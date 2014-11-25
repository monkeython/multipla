import gc
import importlib
import os
import unittest
import sys
import types

import pluggable_package

import genty


class Common(unittest.TestCase):
    @classmethod
    def setUpClass(class_):
        class_._package_name = 'tests.my_package'
        class_._package = pluggable_package.import_package(class_._package_name)
        class_._plugin = importlib.import_module('tests.my_package.plugin')
        class_._third_party = importlib.import_module('tests.my_package.third_party')

    def setUp(self):
        pluggable_package._plugins[self._package.__name__] = dict()

    @classmethod
    def tearDownClass(class_):
        del class_._package, class_._package_name, class_._plugin
        gc.collect()


class TestFunctions(Common):

    def test_import_package(self):
        self.assertIs(self._package,
                      pluggable_package.import_package(self._package_name))
        self.assertIsInstance(self._package, types.ModuleType)
        self.assertIsInstance(self._package, pluggable_package.PluggablePackage)
        self.assertIsNot(self._package, sys.modules[self._package_name])

dataset = (
    ('test!exclamation', 'test_exclamation'),
    ('test#number', 'test_number'),
    ('test$dollar', 'test_dollar'),
    ('test&ampersand', 'test_ampersand'),
    ('test^circumflex', 'test_circumflex'),
    ('test/slash', 'test_slash'),
    ('test/slash-hyphen', 'test_slash_hyphen'),
    ('test/slash.dot-hyphen+plus', 'test_slash_dot_hyphen_plus'))

@genty.genty
class TestPluggablePackage(Common):
    """Test the pluggable package."""

    def test___str__(self):
        pkg = self._package
        msg = "<pluggable_package '{}' from '{}'>"
        self.assertEqual(str(pkg), msg.format(pkg.__name__, pkg.__file__))

    def test_get(self):
        mediatype = 'application/vnd.mytype-v2+xml'
        self.assertIsNone(self._package.get(mediatype, None))
        with self.assertRaises(NotImplementedError):
            self._package.get('application/vnd.mytype-v2+xml')

    @genty.genty_dataset(*dataset)
    def test_setdefault(self, name, translated):
        setdefault = self._package.setdefault
        get = self._package.get
        plugin = 'tests.my_package.' + translated
        plugin = importlib.import_module(plugin)
        self.assertNotIn(translated, self._package.__all__)
        self.assertIs(setdefault(translated, plugin), plugin)
        self.assertIs(get(name), plugin)
        self.assertIs(setdefault(translated, self._third_party), plugin)
        self.assertIn(translated, self._package.__all__)

#    @genty.genty_dataset(dataset)
#    def test_attrs(self, name, translated):
#        with self.assertRaises(AttributeError):
#            getattr(self._package, translated)
#        setattr(self._package, translated, plugin)
#        self.assertIs(getattr(self._package, translated), plugin)
#        delattr(self._package, translated)
#        with self.assertRaises(AttributeError):
#            getattr(self._package, translated)
