import gc
import importlib
import unittest

import pluggable_package


class TestPluggablePackage(unittest.TestCase):
    """Test the pluggable package."""

    class PluggableObject(object):
        pass

    @classmethod
    def setUpClass(class_):
        class_._test_package = importlib.import_module('tests.test_package')
        class_._test_module = importlib.import_module('tests.test_package.test_module')

    def setUp(self):
        self._test_object = self.PluggableObject()

    def tearDown(self):
        del self._test_object
        pluggable_package._teardown(self._test_package)
        pluggable_package._teardown(self._test_module)
        gc.collect()

    def _test_setup(self, pluggable, **kwargs):
        DEFAULT_name = kwargs.get('DEFAULT', 'DEFAULT')
        get_name = kwargs.get('get', 'get')
        registered_name = kwargs.get('registered', 'registered')
        set_default_name = kwargs.get('set_default', 'set_default')

        DEFAULT = lambda: getattr(pluggable, DEFAULT_name)
        get = getattr(pluggable, get_name)
        registered = getattr(pluggable, registered_name)
        set_default = getattr(pluggable, set_default_name)

        functions = {
            get_name: get,
            registered_name: registered,
            set_default_name: set_default}

        for name in functions:
            self.assertIsNotNone(functions.get(name), None)

        self.assertIsNone(DEFAULT())
        self.assertIsInstance(registered(), dict)
        self.assertTrue(registered())
        default = list(registered().keys())[0]
        set_default(default)
        self.assertIs(DEFAULT(), get(default))
        self.assertIsNone(get('maybe', None))
        with self.assertRaises(KeyError):
            get('do_not_exists')

    def test_setup_package(self):
        """Test the setup on a package."""
        pluggable_package.setup(self._test_package)
        self._test_setup(self._test_package)

    def test_setup_module(self):
        """Test the setup on a module."""
        pluggable_package.setup(self._test_module)
        self._test_setup(self._test_module)

    def test_setup_object_without__all__name__(self):
        """Test the setup on a very bad object."""
        with self.assertRaises(AttributeError):
            pluggable_package.setup(self._test_object)

    def test_setup_object_without__all__(self):
        """Test the setup on an object without __all__ attribute."""
        self._test_object.__name__ = 'pluggable_without__all__'
        with self.assertRaises(AttributeError):
            pluggable_package.setup(self._test_object)

    def test_setup_object_with_empty__all__(self):
        """Test the setup on an object with empty __all__ attribute."""
        self._test_object.__name__ = 'pluggable_with_empty__all__'
        self._test_object.ignored_plugin = object()
        self._test_object.__all__ = []
        pluggable_package.setup(self._test_object)
        with self.assertRaises(AssertionError):
            self._test_setup(self._test_object)

    def test_setup_object(self):
        """Test the setup on an object."""
        self._test_object.__name__ = 'pluggable_object'
        self._test_object.test_plugin = object()
        self._test_object.__all__ = ['test_plugin']
        pluggable_package.setup(self._test_object)
        self._test_setup(self._test_object)

    def test_name_remapping(self):
        """Test name remapping."""

